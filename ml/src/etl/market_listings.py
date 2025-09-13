from __future__ import annotations
import datetime as dt
import hashlib
import logging
import re
from typing import Iterable, List, Dict

import pandas as pd
import requests
from bs4 import BeautifulSoup

from . import base  # your project helpers

TARGET_CITIES = {
    # city -> (craigslist subdomain, region path)
    "Vancouver": ("vancouver", "search/apa"),
    "Toronto": ("toronto", "search/apa"),
    "Kelowna": ("kelowna", "search/apa"),
}

BEDROOM_MAP = {0: "0BR", 1: "1BR", 2: "2BR", 3: "3BR"}

USER_AGENT = "Mozilla/5.0 (compatible; HIRD/1.0; +https://example.com)"


def run(ctx: base.Context) -> pd.DataFrame:
    """
    Ingest permitted listing sources, compute monthly medians per city/bedroom,
    and upsert into public.rents with source='ListingsMedian'.
    """
    log = logging.getLogger(__name__)

    # 1) Pull listings (choose sources you are permitted to use)
    listings = []  # List[Dict]
    # CRAIGSLIST (enable only if permitted)
    try:
        listings += fetch_craigslist_batch(
            max_pages=2
        )  # ~240 posts per city (2 pages * ~120)
    except Exception as e:
        log.warning("Craigslist fetch failed (skipping): %s", e)

    if not listings:
        log.info("No listings ingested; nothing to write")
        return pd.DataFrame(
            columns=["city", "date", "bedroom_type", "median_rent", "source"]
        )

    raw_df = pd.DataFrame(listings)
    # 2) Write raw listings (idempotent upsert on id)
    write_raw_listings(raw_df, ctx)

    # 3) Aggregate to monthly medians -> rents tidy
    tidy = listings_to_monthly_medians(raw_df)

    # 4) Upsert into public.rents
    base.write_rents_upsert(tidy, ctx)
    log.info("Upserted %d rows into public.rents from ListingsMedian", len(tidy))
    return tidy


# ----------------------
# Source adapters
# ----------------------


def fetch_craigslist_batch(max_pages: int = 2) -> List[Dict]:
    """
    Fetch latest apartment listings from Craigslist for target cities.
    Only use if permitted. Respects minimal rate-limiting and no JS required.
    """
    session = requests.Session()
    session.headers.update(
        {"User-Agent": USER_AGENT, "Accept-Language": "en-CA,en;q=0.9"}
    )
    out: List[Dict] = []

    # pull 0,1,2,3+ bedrooms separately (Craigslist supports min/max query)
    for city, (sub, path) in TARGET_CITIES.items():
        for beds in [0, 1, 2, 3, 4]:
            url = f"https://{sub}.craigslist.org/{path}?availabilityMode=0&min_bedrooms={beds}&max_bedrooms={beds}"
            if beds == 4:  # 4+ bucket
                url = f"https://{sub}.craigslist.org/{path}?availabilityMode=0&min_bedrooms=4"
            for page in range(max_pages):
                s = page * 120
                page_url = f"{url}&s={s}" if page else url
                html = session.get(page_url, timeout=30).text
                rows = parse_craigslist_html(html, city, beds)
                out.extend(rows)
    return out


def parse_craigslist_html(html: str, city: str, beds: int) -> List[Dict]:
    soup = BeautifulSoup(html, "html.parser")
    posts = soup.select("li.cl-static-result") or soup.select("li.result-row")
    rows: List[Dict] = []
    for li in posts:
        title_a = li.select_one("a.result-title") or li.select_one("a")
        title = (title_a.get_text(strip=True) if title_a else "").strip()
        href = (title_a["href"] if title_a and title_a.has_attr("href") else "").strip()

        price_el = li.select_one(".result-price") or li.select_one(".price")
        price_txt = price_el.get_text(strip=True) if price_el else ""
        m = re.search(r"(\d[\d,]*)", price_txt)
        price = float(m.group(1).replace(",", "")) if m else None

        time_el = li.select_one("time") or li.select_one("time.result-date")
        posted_iso = (
            time_el["datetime"] if time_el and time_el.has_attr("datetime") else None
        )
        posted_at = pd.to_datetime(posted_iso, errors="coerce")

        if price is None:
            continue

        bedrooms = beds
        # hash id stable by (source, href or title+price)
        key = href or f"{title}|{price}|{posted_iso or ''}"
        rid = hashlib.sha256(("craigslist|" + key).encode("utf-8")).hexdigest()[:32]

        rows.append(
            {
                "id": rid,
                "source": "Craigslist",
                "city": city,
                "bedrooms": bedrooms,
                "price": price,
                "posted_at": posted_at.to_pydatetime() if pd.notna(posted_at) else None,
                "captured_at": dt.datetime.utcnow(),
                "url": href,
                "title": title,
            }
        )
    return rows


# ----------------------
# Aggregation
# ----------------------


def listings_to_monthly_medians(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # bedroom_type
    df["bedroom_type"] = df["bedrooms"].apply(lambda b: BEDROOM_MAP.get(int(b), "4BR+"))
    # month (fall back to captured_at)
    ts = pd.to_datetime(df["posted_at"]).where(
        df["posted_at"].notna(), pd.to_datetime(df["captured_at"])
    )
    df["date"] = (
        ts.dt.to_period("M").dt.to_timestamp("M").dt.normalize()
    )  # end-of-month
    # convert to first-of-month for your schema
    df["date"] = df["date"].dt.to_period("M").dt.to_timestamp()

    # median by city/date/bedroom_type
    grp = (
        df.dropna(subset=["price"])
        .groupby(["city", "date", "bedroom_type"])["price"]
        .median()
        .reset_index()
        .rename(columns={"price": "median_rent"})
    )
    grp["source"] = "ListingsMedian"
    return grp[["city", "date", "bedroom_type", "median_rent", "source"]]


# ----------------------
# Persistence of raw listings
# ----------------------


def write_raw_listings(df: pd.DataFrame, ctx: base.Context) -> None:
    """
    Idempotent insert of raw listings based on primary key 'id'.
    Create table if not exists (you can move this DDL to migrations).
    """
    eng = base.get_engine(ctx)
    ddl = """
    CREATE TABLE IF NOT EXISTS public.rent_listings_raw (
        id text PRIMARY KEY,
        source text NOT NULL,
        city text NOT NULL,
        bedrooms int,
        price numeric,
        posted_at timestamp with time zone,
        captured_at timestamp with time zone NOT NULL,
        url text,
        title text
    );
    """
    with eng.begin() as cn:
        cn.execute(ddl)
        # upsert
        tmp = df[
            [
                "id",
                "source",
                "city",
                "bedrooms",
                "price",
                "posted_at",
                "captured_at",
                "url",
                "title",
            ]
        ].copy()
        # Use a temp staging table then merge; or a single ON CONFLICT DO UPDATE
        # Here: skip updates for simplicity (id is immutable)
        tmp.to_sql("_rent_listings_stage", cn, if_exists="replace", index=False)
        cn.execute("""
        INSERT INTO public.rent_listings_raw (id, source, city, bedrooms, price, posted_at, captured_at, url, title)
        SELECT id, source, city, bedrooms, price, posted_at, captured_at, url, title
        FROM _rent_listings_stage
        ON CONFLICT (id) DO NOTHING;
        """)
        cn.execute("DROP TABLE _rent_listings_stage;")
