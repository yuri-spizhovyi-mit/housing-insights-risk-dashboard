# ml/src/etl/market_listings.py
from __future__ import annotations

import os
import time
import re
import hashlib
import logging
import datetime as dt
from typing import List, Dict, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup

from . import base  # project helpers (DB engine, write_rents_upsert, Context, etc.)

# -----------------------------
# Config / Constants
# -----------------------------
TARGET_CITIES = {
    # city -> (craigslist subdomain, region path)
    "Vancouver": ("vancouver", "search/apa"),
    "Toronto": ("toronto", "search/apa"),
    "Kelowna": ("kelowna", "search/apa"),
}

# bedroom -> label mapping for final rents table
BEDROOM_MAP = {0: "0BR", 1: "1BR", 2: "2BR", 3: "3BR"}

# HTTP headers
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
    "Accept-Language": "en-CA,en-US;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
}

# Where to store debug HTML snapshots so you can inspect selectors locally
DEBUG_SNAP_DIR = os.path.join(".debug", "rentfaster")


# -----------------------------
# Public entrypoint
# -----------------------------
def run(ctx: base.Context) -> pd.DataFrame:
    """
    Ingest permitted listing sources (RentFaster, Craigslist*), compute monthly medians per city/bedroom,
    and upsert into public.rents with source='ListingsMedian'.

    Control sources via ctx.params, e.g.:
      ctx.params = {
        "enable_rentfaster": True,
        "enable_craigslist": False,
        "max_pages": 1,
        "rf_headless": True,      # render with Playwright if list page looks empty
        "rf_sleep_sec": 1.0
      }
    """
    log = logging.getLogger(__name__)
    params = getattr(ctx, "params", {}) or {}

    listings: List[Dict] = []

    # ---- RentFaster (Kelowna) ----
    if params.get("enable_rentfaster", False):
        try:
            max_pages = int(params.get("max_pages", 1))
            sleep_sec = float(params.get("rf_sleep_sec", 1.0))
            headless = bool(params.get("rf_headless", False))
            rf = fetch_rentfaster_kelowna(
                max_pages=max_pages, sleep_sec=sleep_sec, headless=headless, log=log
            )
            listings.extend(rf)
            log.info("Fetched %d listings from RentFaster", len(rf))
        except Exception as e:
            log.warning("RentFaster fetch failed (skipping): %s", e, exc_info=True)

    # ---- Craigslist (optional, only if permitted) ----
    if params.get("enable_craigslist", False):
        try:
            cl_pages = int(params.get("cl_max_pages", 2))
            cl = fetch_craigslist_batch(max_pages=cl_pages)
            listings.extend(cl)
            log.info("Fetched %d listings from Craigslist", len(cl))
        except Exception as e:
            log.warning("Craigslist fetch failed (skipping): %s", e, exc_info=True)

    if not listings:
        log.info("No listings ingested; nothing to write")
        return pd.DataFrame(
            columns=["city", "date", "bedroom_type", "median_rent", "source"]
        )

    raw_df = pd.DataFrame(listings)

    # 1) Persist raw listings (idempotent on id)
    write_raw_listings(raw_df, ctx)

    # 2) Aggregate → monthly medians → tidy rents
    tidy = listings_to_monthly_medians(raw_df)

    # 3) Upsert into public.rents
    base.write_rents_upsert(tidy, ctx)
    log.info("Upserted %d rows into public.rents from ListingsMedian", len(tidy))
    return tidy


# -----------------------------
# RentFaster adapter (Kelowna) with optional headless render
# -----------------------------
def fetch_rentfaster_kelowna(
    max_pages: int = 1,
    sleep_sec: float = 1.0,
    headless: bool = False,
    log: Optional[logging.Logger] = None,
) -> List[Dict]:
    """
    Scrape RentFaster Kelowna list pages with robust fallbacks:
      - Saves HTML snapshots to ./.debug/rentfaster/ for inspection
      - Tries multiple card selectors
      - If zero/weak content from plain HTTP, can render with Playwright (headless=True)
      - If price/beds missing on list card, fetches the detail page

    Returns list of dict rows with keys:
      id, source, city, bedrooms, price, posted_at, captured_at, url, title
    """
    log = log or logging.getLogger(__name__)
    os.makedirs(DEBUG_SNAP_DIR, exist_ok=True)

    session = requests.Session()
    session.headers.update(HEADERS)

    all_rows: List[Dict] = []
    base_url = "https://www.rentfaster.ca"

    for page in range(1, max_pages + 1):
        list_url = f"{base_url}/bc/kelowna/rentals/?page={page}&view=list"

        # fetch HTML (plain requests; optionally render JS if needed)
        html = get_html(list_url, session=session, headless=False, log=log)
        snap_path = os.path.join(DEBUG_SNAP_DIR, f"kelowna_list_p{page}.html")
        with open(snap_path, "w", encoding="utf-8") as f:
            f.write(html or "")

        soup = BeautifulSoup(html or "", "html.parser")
        cards = _select_rentfaster_cards(soup)

        # If no cards and headless is enabled -> render via Playwright & retry
        if not cards and headless:
            log.info(
                "RentFaster: page %s had 0 cards with requests; retrying headless …",
                page,
            )
            html2 = get_html(list_url, session=None, headless=True, log=log)
            snap_path2 = os.path.join(
                DEBUG_SNAP_DIR, f"kelowna_list_p{page}_headless.html"
            )
            with open(snap_path2, "w", encoding="utf-8") as f:
                f.write(html2 or "")
            soup = BeautifulSoup(html2 or "", "html.parser")
            cards = _select_rentfaster_cards(soup)

        if not cards:
            log.info(
                "RentFaster Kelowna: page %s had 0 cards (inspect %s)", page, snap_path
            )
            time.sleep(sleep_sec)
            continue

        page_rows: List[Dict] = []
        for card in cards:
            # Link + title
            a = card.select_one("a[href*='/bc/kelowna/']") or card.select_one(
                "a[href*='/bc/']"
            )
            href = a["href"].strip() if a and a.has_attr("href") else ""
            if href and href.startswith("/"):
                href = base_url + href
            title = (
                a.get_text(" ", strip=True) if a else card.get_text(" ", strip=True)
            )[:200]

            # Try to read price/beds from card
            card_text = card.get_text(" ", strip=True)
            price = _extract_price(card_text)
            beds = _extract_beds(card_text)

            # Try common child elements
            if price is None:
                price_el = card.select_one(
                    ".listingCardPrice, .price, [class*='price']"
                )
                if price_el:
                    price = _extract_price(price_el.get_text(" ", strip=True))
            if beds is None:
                beds_el = card.select_one(".listingCardBed, .beds, [class*='bed']")
                if beds_el:
                    beds = _extract_beds(beds_el.get_text(" ", strip=True))

            # Fallback: fetch the detail page only if necessary
            if (price is None or beds is None) and href:
                try:
                    dhtml = get_html(href, session=session, headless=headless, log=log)
                    if dhtml:
                        # Save some details for inspection
                        if len(page_rows) < 3:
                            dh_path = os.path.join(
                                DEBUG_SNAP_DIR,
                                f"kelowna_detail_{hashlib.md5(href.encode()).hexdigest()[:8]}.html",
                            )
                            with open(dh_path, "w", encoding="utf-8") as f:
                                f.write(dhtml)
                        dsoup = BeautifulSoup(dhtml, "html.parser")
                        if price is None:
                            for s in (
                                "[itemprop='price']",
                                ".price",
                                ".rent",
                                ".rf-price",
                                ".listing-price",
                            ):
                                el = dsoup.select_one(s)
                                if el:
                                    price = _extract_price(el.get_text(" ", strip=True))
                                    if price is not None:
                                        break
                        if beds is None:
                            for s in (".beds", ".bedrooms", "[data-beds]", ".rf-beds"):
                                el = dsoup.select_one(s)
                                if el:
                                    beds = _extract_beds(el.get_text(" ", strip=True))
                                    if beds is not None:
                                        break
                except Exception as e:
                    log.debug("RentFaster detail fetch failed for %s: %s", href, e)

            if price is None:
                # Require price
                continue

            bedrooms: Optional[int] = None
            if beds is not None:
                try:
                    bedrooms = int(beds)
                except Exception:
                    bedrooms = None

            rid = hashlib.sha256(
                ("rentfaster|" + (href or title)).encode("utf-8")
            ).hexdigest()[:32]
            page_rows.append(
                {
                    "id": rid,
                    "source": "RentFaster",
                    "city": "Kelowna",
                    "bedrooms": bedrooms,
                    "price": float(price) if price is not None else None,
                    "posted_at": None,
                    "captured_at": dt.datetime.utcnow(),
                    "url": href,
                    "title": title,
                }
            )

        log.info(
            "RentFaster: page %s extracted %d listings (inspect %s)",
            page,
            len(page_rows),
            snap_path,
        )
        all_rows.extend(page_rows)
        time.sleep(sleep_sec)

    return all_rows


def _select_rentfaster_cards(soup: BeautifulSoup):
    # Try multiple card selectors; order matters (first hit wins)
    for sel in (
        ".listingCard",  # older style
        "article.listing",  # semantic
        "[data-cy='listing-card']",  # test-tag style
        ".rf-listing-card",  # hypothetical newer
        "li[class*='listing']",  # generic fallback
    ):
        cards = soup.select(sel)
        if cards:
            return cards
    return []


def _extract_price(text: str) -> Optional[float]:
    """Find first $1,234 or 1234-like number (ignore trailing +)."""
    m = re.search(r"\$?\s*([0-9][0-9,]{2,})(?!\S)", text)
    if m:
        try:
            return float(m.group(1).replace(",", ""))
        except Exception:
            return None
    return None


def _extract_beds(text: str) -> Optional[int]:
    """Normalize bedroom count from a text blob."""
    t = text.lower()
    if "studio" in t or "bachelor" in t:
        return 0
    m = re.search(r"(\d+)\s*(?:br|bed|beds|bedroom|bedrooms)\b", t)
    if m:
        return int(m.group(1))
    m2 = re.search(r"\b(\d)\s*bd\b", t)
    if m2:
        return int(m2.group(1))
    return None


# -----------------------------
# HTML loader (requests or headless Playwright)
# -----------------------------
def get_html(
    url: str, session: Optional[requests.Session], headless: bool, log: logging.Logger
) -> str:
    """
    Returns HTML via requests (session) or headless Playwright when headless=True.
    """
    if not headless:
        s = session or requests.Session()
        s.headers.update(HEADERS)
        r = s.get(url, timeout=30)
        r.raise_for_status()
        return r.text

    # Headless render with Playwright
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        log.warning(
            "Playwright not available; falling back to requests for %s (%s)", url, e
        )
        s = session or requests.Session()
        s.headers.update(HEADERS)
        return s.get(url, timeout=30).text

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT, locale="en-CA")
        page = context.new_page()
        page.goto(url, wait_until="networkidle", timeout=60_000)
        # small settle delay
        page.wait_for_timeout(500)
        html = page.content()
        context.close()
        browser.close()
        return html


# -----------------------------
# Craigslist adapter (optional; enable only if permitted)
# -----------------------------
def fetch_craigslist_batch(max_pages: int = 2) -> List[Dict]:
    session = requests.Session()
    session.headers.update(
        {"User-Agent": USER_AGENT, "Accept-Language": "en-CA,en;q=0.9"}
    )
    out: List[Dict] = []
    for city, (sub, path) in TARGET_CITIES.items():
        for beds in [0, 1, 2, 3, 4]:
            url = f"https://{sub}.craigslist.org/{path}?availabilityMode=0&min_bedrooms={beds}&max_bedrooms={beds}"
            if beds == 4:
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
        key = href or f"{title}|{price}|{posted_iso or ''}"
        rid = hashlib.sha256(("craigslist|" + key).encode("utf-8")).hexdigest()[:32]
        rows.append(
            {
                "id": rid,
                "source": "Craigslist",
                "city": city,
                "bedrooms": beds,
                "price": price,
                "posted_at": posted_at.to_pydatetime() if pd.notna(posted_at) else None,
                "captured_at": dt.datetime.utcnow(),
                "url": href,
                "title": title,
            }
        )
    return rows


# -----------------------------
# Aggregation → monthly medians → rents tidy
# -----------------------------
def listings_to_monthly_medians(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["bedroom_type"] = df["bedrooms"].apply(
        lambda b: BEDROOM_MAP.get(int(b), "4BR+") if pd.notna(b) else "4BR+"
    )
    ts = pd.to_datetime(df["posted_at"]).where(
        df["posted_at"].notna(), pd.to_datetime(df["captured_at"])
    )
    df["date"] = ts.dt.to_period("M").dt.to_timestamp()  # first-of-month
    grp = (
        df.dropna(subset=["price"])
        .groupby(["city", "date", "bedroom_type"])["price"]
        .median()
        .reset_index()
        .rename(columns={"price": "median_rent"})
    )
    grp["source"] = "ListingsMedian"
    return grp[["city", "date", "bedroom_type", "median_rent", "source"]]


# -----------------------------
# Persistence of raw listings
# -----------------------------
def write_raw_listings(df: pd.DataFrame, ctx: base.Context) -> None:
    """
    Idempotent insert of raw listings based on primary key 'id'.
    Prefer to manage the DDL via migration V2__rent_listings_raw.sql.
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
        tmp.to_sql("_rent_listings_stage", cn, if_exists="replace", index=False)
        cn.execute("""
        INSERT INTO public.rent_listings_raw (id, source, city, bedrooms, price, posted_at, captured_at, url, title)
        SELECT id, source, city, bedrooms, price, posted_at, captured_at, url, title
        FROM _rent_listings_stage
        ON CONFLICT (id) DO NOTHING;
        """)
        cn.execute("DROP TABLE _rent_listings_stage;")
