# -*- coding: utf-8 -*-
"""
Craigslist → listings_raw
- Uses your db.py connection (no DATABASE_URL needed).
- Supports rent (apa) and sale (rea).
- Safe UPSERT with COALESCE to avoid null-overwrites.
"""

import os
import re
import time
import uuid
import math
import datetime as dt
from decimal import Decimal
from typing import Dict, Iterable, List, Optional

import requests
from bs4 import BeautifulSoup

# ---- import your existing DB connector ----
try:
    from .db import get_conn
except Exception:
    from db import get_conn

# ---------- Constants ----------
SNAPSHOT_DIR = "./.debug/craigslist"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36 (+housing-insights-etl)"
)
HEADERS = {"User-Agent": USER_AGENT, "Accept-Language": "en-CA,en;q=0.9"}

CATEGORY_MAP = {"rent": "apa", "sale": "rea"}  # Craigslist search paths

# Supported city → Craigslist domain mapping
CITY_TO_BASE_URL = {
    "vancouver": "https://vancouver.craigslist.org",
    "kelowna": "https://kelowna.craigslist.org",
    "toronto": "https://toronto.craigslist.org",
    "victoria": "https://victoria.craigslist.org",
    "calgary": "https://calgary.craigslist.org",
    "edmonton": "https://edmonton.craigslist.org",
    "montreal": "https://montreal.craigslist.org",
    "ottawa": "https://ottawa.craigslist.org",
    "winnipeg": "https://winnipeg.craigslist.org",
}

# ---------- Regex helpers ----------
RE_POSTAL = re.compile(r"[A-Za-z]\d[A-Za-z][ -]?\d[A-Za-z]\d")
RE_BEDS = re.compile(r"(\d+)\s*br\b", re.I)
RE_BATHS = re.compile(r"(\d+(\.\d+)?)\s*ba\b", re.I)
RE_SQFT = re.compile(r"(\d{3,5})\s*(?:ft|sq ?ft|sf)\b", re.I)
RE_PRICE = re.compile(r"[\$€£]\s?([\d,]+(?:\.\d{1,2})?)")

# ---------- SQL ----------
UPSERT_SQL = """
INSERT INTO public.listings_raw (
    listing_id, url, date_posted, city, postal_code,
    property_type, listing_type, price, bedrooms, bathrooms,
    area_sqft, year_built, description
)
VALUES (
    %(listing_id)s, %(url)s, %(date_posted)s, %(city)s, %(postal_code)s,
    %(property_type)s, %(listing_type)s, %(price)s, %(bedrooms)s, %(bathrooms)s,
    %(area_sqft)s, %(year_built)s, %(description)s
)
ON CONFLICT (listing_id) DO UPDATE SET
    url = EXCLUDED.url,
    date_posted = COALESCE(EXCLUDED.date_posted, listings_raw.date_posted),
    city = COALESCE(EXCLUDED.city, listings_raw.city),
    postal_code = COALESCE(EXCLUDED.postal_code, listings_raw.postal_code),
    property_type = COALESCE(EXCLUDED.property_type, listings_raw.property_type),
    listing_type = COALESCE(EXCLUDED.listing_type, listings_raw.listing_type),
    price = COALESCE(EXCLUDED.price, listings_raw.price),
    bedrooms = COALESCE(EXCLUDED.bedrooms, listings_raw.bedrooms),
    bathrooms = COALESCE(EXCLUDED.bathrooms, listings_raw.bathrooms),
    area_sqft = COALESCE(EXCLUDED.area_sqft, listings_raw.area_sqft),
    year_built = COALESCE(EXCLUDED.year_built, listings_raw.year_built),
    description = COALESCE(EXCLUDED.description, listings_raw.description);
"""


# ---------- I/O helpers ----------
def _save_snapshot(kind: str, ident: str, html: str) -> None:
    path = os.path.join(SNAPSHOT_DIR, f"{kind}_{ident}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def _get(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def _clean_text(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    s = re.sub(r"\s+", " ", s).strip()
    return s or None


def _parse_money(txt: Optional[str]) -> Optional[Decimal]:
    if not txt:
        return None
    m = RE_PRICE.search(txt.replace(",", ""))
    if m:
        try:
            return Decimal(m.group(1))
        except Exception:
            return None
    return None


def _first_int(pat: re.Pattern, txt: str) -> Optional[int]:
    if not txt:
        return None
    m = pat.search(txt)
    if not m:
        return None
    try:
        return int(float(m.group(1)))
    except Exception:
        return None


def _find_postal(texts: Iterable[str]) -> Optional[str]:
    for t in texts:
        m = RE_POSTAL.search(t or "")
        if m:
            return m.group(0).upper().replace(" ", "")
    return None


def _list_total_pages(soup: BeautifulSoup, per_page: int = 120) -> int:
    el = soup.select_one("span.totalcount")
    total = int(el.get_text(strip=True)) if el else per_page
    return max(1, math.ceil(total / per_page))


# ---------- Search (list pages) ----------
def _collect_detail_urls(
    base_url: str, category: str, query: Optional[str], max_pages: int, sleep_sec: float
) -> List[str]:
    cat = CATEGORY_MAP[category]
    per_page = 120
    urls: List[str] = []

    def extract_urls(soup: BeautifulSoup):
        for a in soup.select("a.result-title.hdrlnk"):
            href = a.get("href")
            if href and href.startswith("http"):
                urls.append(href)
        for li in soup.select("li.cl-search-result, li.result-row, ul.rows > li"):
            a = li.find("a", href=True)
            if a and a["href"].startswith("http"):
                urls.append(a["href"])
        if not urls:
            for a in soup.select("a[href*='.craigslist.org/']"):
                href = a.get("href")
                if href and href.endswith(".html"):
                    urls.append(href)

    def build_url(s: int) -> str:
        base = f"{base_url}/search/{cat}?s={s}"
        return f"{base}&query={requests.utils.quote(query)}" if query else base

    # page 0
    s = 0
    html0 = _get(build_url(s))
    _save_snapshot("list", f"{cat}_{s}", html0)
    soup0 = BeautifulSoup(html0, "lxml")
    pages = min(_list_total_pages(soup0, per_page), max_pages)

    extract_urls(soup0)
    time.sleep(sleep_sec)

    for page in range(1, pages):
        s = page * per_page
        html = _get(build_url(s))
        _save_snapshot("list", f"{cat}_{s}", html)
        soup = BeautifulSoup(html, "lxml")
        extract_urls(soup)
        time.sleep(sleep_sec)

    return list(dict.fromkeys(urls))


# ---------- Detail parsing ----------
def _parse_detail(html: str) -> Dict:
    soup = BeautifulSoup(html, "lxml")

    canonical = soup.find("link", {"rel": "canonical"})
    url = canonical["href"] if canonical and canonical.get("href") else None

    pid = None
    body = soup.find("body")
    if body and body.get("data-pid"):
        pid = body.get("data-pid")
    if not pid and url:
        m = re.search(r"/(\d+)\.html", url)
        if m:
            pid = m.group(1)
    listing_id = f"cl_{pid}" if pid else f"cl_{uuid.uuid4().hex}"

    title_el = soup.select_one("span#titletextonly")
    title = _clean_text(title_el.get_text(strip=True)) if title_el else None

    price_el = soup.select_one(".price")
    price = _parse_money(price_el.get_text()) if price_el else None

    # date
    date_posted = None
    t = soup.find("time")
    if t and t.get("datetime"):
        try:
            date_posted = dt.datetime.fromisoformat(
                t["datetime"].replace("Z", "+00:00")
            ).date()
        except Exception:
            pass

    attr_texts = [
        el.get_text(" ", strip=True)
        for el in soup.select(".attrgroup span, .attrgroup b, .mapaddress")
    ]
    postal_code = _find_postal(attr_texts + [soup.get_text(" ", strip=True)])

    joined = " | ".join([title or ""] + attr_texts)
    bedrooms = _first_int(RE_BEDS, joined)
    bathrooms = _first_int(RE_BATHS, joined)
    area_sqft = _first_int(RE_SQFT, joined)

    # ---- property_type detection (RESTORED) ----
    property_type: Optional[str] = None

    # 1) explicit field
    for span in soup.select(".attrgroup span"):
        txt = span.get_text(" ", strip=True).lower()
        if "housing type:" in txt:
            property_type = _clean_text(txt.split(":", 1)[-1])
            break

    # 2) infer from text
    if not property_type:
        text_blob = " ".join([title or "", soup.get_text(" ", strip=True).lower()])
        if any(k in text_blob for k in ["townhome", "townhouse"]):
            property_type = "townhouse"
        elif "condo" in text_blob:
            property_type = "condo"
        elif "apartment" in text_blob or "apt" in text_blob:
            property_type = "apartment"
        elif "basement" in text_blob:
            property_type = "basement"
        elif "suite" in text_blob:
            property_type = "suite"
        elif "duplex" in text_blob:
            property_type = "duplex"
        elif "house" in text_blob or "home" in text_blob:
            property_type = "house"
        else:
            property_type = "unknown"

    # ---- year_built detection (RESTORED) ----
    year_built: Optional[int] = None

    # 1) explicit attribute
    for span in soup.select(".attrgroup span"):
        txt = span.get_text(" ", strip=True).lower()
        if "year built" in txt:
            m = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})\b", txt)
            if m:
                y = int(m.group(1))
                if 1850 <= y <= dt.date.today().year:
                    year_built = y
            break

    # 2) phrases in body
    if not year_built:
        body_txt = soup.get_text(" ", strip=True).lower()
        m = re.search(
            r"\b(?:year\s*built|built(?:\s*in)?)\s*[:\-]?\s*(18\d{2}|19\d{2}|20\d{2})\b",
            body_txt,
        )
        if m:
            y = int(m.group(1))
            if 1850 <= y <= dt.date.today().year:
                year_built = y

    desc_el = soup.select_one("#postingbody")
    description = _clean_text(desc_el.get_text("\n", strip=True)) if desc_el else None

    return {
        "listing_id": listing_id,
        "url": url,
        "date_posted": date_posted,
        "postal_code": postal_code,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "area_sqft": area_sqft,
        "property_type": property_type,
        "year_built": year_built,
        "description": description,
        "price": price,
    }


# ---------- Writer ----------
def _write_rows(rows: List[Dict]) -> int:
    if not rows:
        return 0
    conn = get_conn()
    try:
        with conn, conn.cursor() as cur:
            from psycopg2.extras import execute_batch

            execute_batch(cur, UPSERT_SQL, rows, page_size=100)
        return len(rows)
    finally:
        conn.close()


# ---------- Public API ----------
def scrape_craigslist_to_listings_raw(
    *,
    base_url: Optional[str] = None,
    category: str = "rent",
    query: Optional[str] = None,  # <-- optional now
    city: str = "Vancouver",
    max_pages: int = 5,
    sleep_sec: float = 1.0,
) -> int:
    if not base_url:
        base_url = CITY_TO_BASE_URL.get(city.lower())
        if not base_url:
            raise ValueError(f"Unknown city '{city}', provide --base-url manually")

    print(
        f"[INFO] category={category} query={query} city={city} "
        f"pages={max_pages} sleep={sleep_sec} base_url={base_url}"
    )

    detail_urls = _collect_detail_urls(base_url, category, query, max_pages, sleep_sec)
    listing_type = "rent" if category == "rent" else "sale"
    batch: List[Dict] = []
    written_total = 0

    for url in detail_urls:
        try:
            html = _get(url)
            _save_snapshot("detail", re.sub(r"\W+", "_", url[-40:]), html)
            rec = _parse_detail(html)

            row = {
                "listing_id": rec["listing_id"],
                "url": url,
                "date_posted": rec["date_posted"],
                "city": city,
                "postal_code": rec["postal_code"],
                "property_type": rec["property_type"],
                "listing_type": listing_type,
                "price": rec["price"],
                "bedrooms": rec["bedrooms"],
                "bathrooms": rec["bathrooms"],
                "area_sqft": rec["area_sqft"],
                "year_built": rec["year_built"],
                "description": rec["description"],
            }
            batch.append(row)

            if len(batch) >= 50:
                written_total += _write_rows(batch)
                batch.clear()
        except Exception as e:
            print(f"[WARN] {e} -> {url}")
        time.sleep(sleep_sec)

    written_total += _write_rows(batch)
    return written_total


# ---------- Orchestrator hook ----------
def run(ctx) -> dict:
    """
    ctx.params example:
      {
        "cl_query": None,          # optional
        "cl_city": "vancouver",
        "cl_max_pages": 10,
        "cl_sleep_sec": 1.0,
        "cl_rent": True,
        "cl_sale": False
      }
    """
    p = getattr(ctx, "params", {}) or {}
    query = p.get("cl_query", None)  # default None (no filter)
    max_pages = int(p.get("cl_max_pages", 5))
    sleep_sec = float(p.get("cl_sleep_sec", 1.0))
    city = p.get("cl_city", "vancouver")

    total = 0
    if p.get("cl_rent", True):
        total += scrape_craigslist_to_listings_raw(
            category="rent",
            query=query,
            city=city,
            max_pages=max_pages,
            sleep_sec=sleep_sec,
        )
    if p.get("cl_sale", False):
        total += scrape_craigslist_to_listings_raw(
            category="sale",
            query=query,
            city=city,
            max_pages=max_pages,
            sleep_sec=sleep_sec,
        )
    return {"rows_upserted": total}


# ---------- CLI ----------
if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--category", choices=["rent", "sale"], default="rent")
    p.add_argument(
        "--query", default=None, help="Optional keyword filter (default: None)"
    )
    p.add_argument("--city", choices=list(CITY_TO_BASE_URL.keys()), default="vancouver")
    p.add_argument("--base-url", default=None, help="Override base_url if not mapped")
    p.add_argument("--max-pages", type=int, default=3)
    p.add_argument("--sleep-sec", type=float, default=1.2)
    p.add_argument(
        "--dryrun", action="store_true", help="Collect URLs only, no DB writes"
    )
    args = p.parse_args()

    base_url = args.base_url or CITY_TO_BASE_URL.get(args.city.lower())
    if not base_url:
        raise ValueError(f"Unknown city '{args.city}', provide --base-url manually")

    print(
        f"[INFO] category={args.category} query={args.query} city={args.city} "
        f"pages={args.max_pages} sleep={args.sleep_sec} base_url={base_url}"
    )

    if args.dryrun:
        urls = _collect_detail_urls(
            base_url, args.category, args.query, args.max_pages, args.sleep_sec
        )
        print(f"[INFO] collected {len(urls)} detail URLs (dryrun)")
    else:
        wrote = scrape_craigslist_to_listings_raw(
            base_url=base_url,
            category=args.category,
            query=args.query,  # may be None
            city=args.city,
            max_pages=args.max_pages,
            sleep_sec=args.sleep_sec,
        )
        print(f"Wrote rows: {wrote}")
