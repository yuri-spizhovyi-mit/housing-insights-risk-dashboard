# -*- coding: utf-8 -*-
"""
Craigslist → listings_raw (Vancouver)
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
from urllib.parse import urljoin, urlsplit, urlunsplit
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
# ---- import your existing DB connector ----
try:
    # adjust the path if your db.py lives in a different package
    from .db import get_conn  # same style as your other scrapers
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
HEADERS = HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://vancouver.craigslist.org/",
}


CATEGORY_MAP = {"rent": "apa", "sale": "rea"}  # Craigslist paths

# Regex helpers
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
def _abs_url(base_url: str, href: str) -> str:
    """Make href absolute and strip query/hash to dedupe."""
    u = urljoin(base_url, href)
    parts = urlsplit(u)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))

def _get_playwright(url: str, sleep_sec: float = 2.0) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_timeout(int(sleep_sec * 1000))  # wait for JS to load
        html = page.content()
        browser.close()
        return html

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
    digits = re.sub(r"[^\d.]", "", txt)
    if digits:
        try:
            return Decimal(digits)
        except Exception:
            pass
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
    base_url: str, category: str, query: str, max_pages: int, sleep_sec: float
) -> List[str]:
    cat = CATEGORY_MAP[category]
    per_page = 120
    urls: List[str] = []

    def extract_urls(soup: BeautifulSoup):
        found = 0
        for li in soup.select("li.cl-search-result"):
            a = li.find("a", class_="cl-app-anchor", href=True)
            if a and a["href"]:
                urls.append(_abs_url(base_url, a["href"]))
                found += 1
        for li in soup.select("li.result-row, ul.rows > li"):
            a = li.find("a", href=True)
            if a and a["href"].endswith(".html"):
                urls.append(_abs_url(base_url, a["href"]))
                found += 1
        print(f"Found {found} listing URLs on this page")

    # ---- First page ----
    s = 0
    url0 = f"{base_url}/search/{cat}?query={requests.utils.quote(query)}&s={s}"
    print(f"Fetching: {url0}")
    if category == "sale":
        html0 = _get_playwright(url0, sleep_sec)
    else:
        html0 = _get(url0)
    _save_snapshot("list", f"{cat}_{s}", html0)
    soup0 = BeautifulSoup(html0, "lxml")
    pages = min(_list_total_pages(soup0, per_page), max_pages)
    print(f"Total pages found: {pages}")

    extract_urls(soup0)
    time.sleep(sleep_sec)

    # ---- Remaining pages ----
    for page in range(1, pages):
        s = page * per_page
        url = f"{base_url}/search/{cat}?query={requests.utils.quote(query)}&s={s}"
        if category == "sale":
            html = _get_playwright(url, sleep_sec)
        else:
            html = _get(url)
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

    property_type = None
    for span in soup.select(".attrgroup span"):
        txt = span.get_text(" ", strip=True).lower()
        if "housing type:" in txt:
            property_type = _clean_text(txt.split(":", 1)[-1])
            break

    year_built = None
    for span in soup.select(".attrgroup span"):
        txt = span.get_text(" ", strip=True).lower()
        if "year built" in txt:
            m = re.search(r"(\d{4})", txt)
            if m:
                year_built = int(m.group(1))
                break
    if not year_built:
        m = re.search(r"\b(19\d{2}|20\d{2})\b", soup.get_text(" ", strip=True))
        if m:
            y = int(m.group(1))
            if 1900 <= y <= dt.date.today().year:
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
    base_url: str = "https://vancouver.craigslist.org",
    category: str = "rent",  # "rent" -> apa; "sale" -> rea
    query: str = "vancouver",
    city: str = "Vancouver",
    max_pages: int = 5,
    sleep_sec: float = 1.0,
) -> int:
    """
    Scrape Craigslist and upsert into public.listings_raw.
    Returns number of rows written in the final batch (for quick feedback).
    """
    print(f"Starting scrape: {category} listings for '{query}' in {city}")
    print(f"Base URL: {base_url}")
    print(f"Max pages: {max_pages}")

    detail_urls = _collect_detail_urls(base_url, category, query, max_pages, sleep_sec)
    print(f"Found {len(detail_urls)} detail URLs to scrape")

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


# ---------- Orchestrator hook (optional) ----------
def run(ctx) -> dict:
    """
    Plug-and-play with your existing pipeline style.
    ctx.params example:
        {
          "cl_query": "vancouver",
          "cl_max_pages": 10,
          "cl_sleep_sec": 1.0,
          "cl_rent": True,
          "cl_sale": True
        }
    """
    p = getattr(ctx, "params", {}) or {}
    query = p.get("cl_query", "vancouver")
    max_pages = int(p.get("cl_max_pages", 5))
    sleep_sec = float(p.get("cl_sleep_sec", 1.0))

    total = 0
    if p.get("cl_rent", True):
        total += scrape_craigslist_to_listings_raw(
            category="rent", query=query, max_pages=max_pages, sleep_sec=sleep_sec
        )
    if p.get("cl_sale", False):
        total += scrape_craigslist_to_listings_raw(
            category="sale", query=query, max_pages=max_pages, sleep_sec=sleep_sec
        )
    return {"rows_upserted": total}


# ---------- CLI (optional) ----------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scrape Craigslist listings")
    parser.add_argument(
        "--category",
        choices=["rent", "sale"],
        default="rent",
        help="Category to scrape: rent or sale",
    )
    parser.add_argument(
        "--query", default="", help="Search query (default: vancouver)"
    )
    parser.add_argument(
        "--max-pages", type=int, default=3, help="Maximum pages to scrape (default: 3)"
    )
    parser.add_argument(
        "--sleep-sec",
        type=float,
        default=1.2,
        help="Sleep between requests in seconds (default: 1.2)",
    )
    parser.add_argument(
        "--base-url",
        default="https://vancouver.craigslist.org",
        help="Base URL for Craigslist (default: vancouver)",
    )
    parser.add_argument(
        "--city",
        default="Vancouver",
        help="City name for database (default: Vancouver)",
    )

    args = parser.parse_args()

    print(
        "Wrote rows:",
        scrape_craigslist_to_listings_raw(
            category=args.category,
            query=args.query,
            max_pages=args.max_pages,
            sleep_sec=args.sleep_sec,
            base_url=args.base_url,
            city=args.city,
        ),
    )
