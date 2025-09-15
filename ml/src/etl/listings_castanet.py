# listings_castanet.py
from __future__ import annotations
import re, time, hashlib
from datetime import datetime
from typing import Tuple, List, Dict, Optional
import requests
from bs4 import BeautifulSoup

from .utils import save_snapshot, is_kelowna_city

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; HIRD-ETL/1.0)"}
BASE = "https://classifieds.castanet.net"
INDEX_PATH = "/search/"
SLEEP_SEC = 1.0

# Default search parameters for rental listings
DEFAULT_SEARCH_PARAMS = {
    "rent_ptype": "88",  # Property type for rentals
    "rent_location": "4",  # Location filter
    "re_neighborhood4": "",
    "re_neighborhood56": "",
    "re_neighborhood58": "",
    "other_city": "1836",  # Kelowna city ID
    "furnished": "",
    "minprice": "0",
    "maxprice": "0",
    "numbeds": "0-0",
    "numbaths": "0-0",
    "pet_friendly": "",
    "perpage": "50",
}

# --- add these helpers near the top of the file ---

DETAIL_KV_LABELS = {
    "bedrooms": re.compile(r"^\s*bedrooms?\s*:\s*", re.I),
    "bathrooms": re.compile(r"^\s*bathrooms?\s*:\s*", re.I),
    "post_date": re.compile(r"^\s*post\s*date\s*:\s*", re.I),
    "ad_number": re.compile(r"^\s*ad\s*number\s*:\s*", re.I),
}


def _clean_text(el) -> str | None:
    if not el:
        return None
    t = el.get_text(" ", strip=True)
    return t if t else None


def _parse_details_panel(soup: BeautifulSoup) -> dict:
    """
    Scrape the right-hand 'Details' panel:
      Bedrooms, Bathrooms, Post Date, Ad Number, etc.
    Returns dict with raw strings; call _parse_* helpers to normalize.
    """
    out = {"bedrooms": None, "bathrooms": None, "post_date": None, "ad_number": None}

    # The panel is often a <div> with legend/header 'Details' followed by rows <tr> or <li>
    panel = None
    # try common containers
    for sel in [
        "div:has(> h3:-soup-contains('Details'))",
        "div:has(> h4:-soup-contains('Details'))",
        "div.details",
        "section.details",
        "#details",
    ]:
        panel = soup.select_one(sel)
        if panel:
            break

    # fall back: scan any table/list near text 'Details'
    if not panel:
        for hdr in soup.find_all(text=re.compile(r"^\s*Details\s*$", re.I)):
            panel = hdr.parent if hdr and hdr.parent else None
            if panel:
                break

    if not panel:
        return out

    # collect text lines from table rows or list items
    lines = []
    for tr in panel.select("tr"):
        lines.append(_clean_text(tr))
    for li in panel.select("li"):
        lines.append(_clean_text(li))
    if not lines:
        lines = [_clean_text(panel)]

    for raw in filter(None, lines):
        low = raw.lower()
        for key, rx in DETAIL_KV_LABELS.items():
            if rx.search(low):
                val = rx.sub("", raw).strip()
                out[key] = val
    return out


def _parse_breadcrumb_type(soup: BeautifulSoup) -> str | None:
    """
    Breadcrumb like: Rentals / Apartment-Condo  -> 'Apartment' or 'Condo'
    """
    crumb = soup.select_one(".breadcrumbs, nav.breadcrumbs, .bread, .crumbs")
    txt = _clean_text(crumb)
    if not txt:
        return None
    # last token after slash
    tail = txt.split("/")[-1].strip()
    # normalize a couple of cases
    if "condo" in tail.lower():
        return "Condo"
    if "apartment" in tail.lower():
        return "Apartment"
    if "town" in tail.lower():
        return "Townhouse"
    if "house" in tail.lower():
        return "Detached"
    return tail[:50]


def _parse_price_from_detail(soup: BeautifulSoup) -> str | None:
    """
    Try multiple spots for the blue $ amount near title.
    Returns raw text like '$1,995.00'
    """
    for sel in [
        ".price",
        ".amount",
        ".price-blue",
        "span:-soup-contains('$')",
        "strong:-soup-contains('$')",
    ]:
        el = soup.select_one(sel)
        if el and "$" in el.get_text():
            return el.get_text(strip=True)
    # fallback: scan title line
    t = soup.select_one("h1, h2, .title")
    if t and "$" in t.get_text():
        return t.get_text(strip=True)
    return None


def _hash_id(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]


def _parse_price(txt: str | None) -> Optional[int]:
    if not txt:
        return None
    # $1,995 /month → 1995 ; $2,100 → 2100
    m = re.findall(r"\d[\d,]*", txt.replace("\xa0", " "))
    if not m:
        return None
    try:
        return int(m[0].replace(",", ""))
    except ValueError:
        return None


def _parse_beds_baths(chunk: str | None) -> Tuple[Optional[float], Optional[float]]:
    if not chunk:
        return None, None
    # "2 Bed 1.5 Bath" or "Bedrooms: 3 Bathrooms: 2"
    beds = baths = None
    mb = re.search(r"(\d+(\.\d+)?)\s*(bed|br|bedroom)", chunk, flags=re.I)
    if mb:
        beds = float(mb.group(1))
    mt = re.search(r"(\d+(\.\d+)?)\s*(bath|ba|bathroom)", chunk, flags=re.I)
    if mt:
        baths = float(mt.group(1))
    return beds, baths


def _parse_area(chunk: str | None) -> Optional[int]:
    if not chunk:
        return None
    # "850 sq ft" or "78 m2"
    m_sqft = re.search(r"(\d[\d,]*)\s*(sq\s*ft|ft²)", chunk, flags=re.I)
    if m_sqft:
        return int(m_sqft.group(1).replace(",", ""))
    m_m2 = re.search(r"(\d[\d,]*)\s*m2", chunk, flags=re.I)
    if m_m2:
        sqft = float(m_m2.group(1).replace(",", "")) * 10.7639
        return int(round(sqft))
    return None


def _parse_date(txt: str | None) -> Optional[str]:
    # Support formats like "Posted: Sep 10, 2025"
    if not txt:
        return None
    m = re.search(r"(\w{3,9})\s+(\d{1,2}),\s*(\d{4})", txt)
    if m:
        try:
            dt = datetime.strptime(" ".join(m.groups()), "%b %d %Y")
            return dt.date().isoformat()
        except Exception:
            try:
                dt = datetime.strptime(" ".join(m.groups()), "%B %d %Y")
                return dt.date().isoformat()
            except Exception:
                pass
    # fallback to today if site hides exact date
    return datetime.utcnow().date().isoformat()


def _normalize_property_type(txt: str | None) -> Optional[str]:
    if not txt:
        return None
    t = txt.lower()
    if any(k in t for k in ["townhouse", "town house"]):
        return "Townhouse"
    if any(k in t for k in ["condo", "apartment", "suite"]):
        return "Condo" if "condo" in t else "Apartment"
    if any(k in t for k in ["house", "detached", "home"]):
        return "Detached"
    # Truncate to fit VARCHAR(50) constraint
    return txt.strip().title()[:50]


def _extract_postal_code(text: str | None) -> Optional[str]:
    if not text:
        return None
    # Canadian postal code pattern: V1Y 1A1 or V1Y1A1
    m = re.search(
        r"\b([A-CEGHJ-NPR-TVXY]\d[A-CEGHJ-NPR-TV-Z])\s?(\d[ A-CEGHJ-NPR-TV-Z]\d)\b",
        text,
        flags=re.I,
    )
    if m:
        code = (m.group(1) + m.group(2)).upper()
        return code[:3] + " " + code[3:]
    return None


def _make_listing_row(
    url: str,
    date_posted: Optional[str],
    title: str | None,
    city: str | None,
    price_text: str | None,
    meta_chunk: str | None,
    details_text: str | None,
    listing_type: str = "rent",
) -> Dict:
    price = _parse_price(price_text)
    beds, baths = _parse_beds_baths(meta_chunk or details_text or "")
    area = _parse_area(meta_chunk or details_text or "")
    postal = _extract_postal_code((meta_chunk or "") + " " + (details_text or ""))
    prop_type = _normalize_property_type(title or meta_chunk or "")

    # Only Kelowna
    if not is_kelowna_city(city or ""):
        return {}

    return {
        "listing_id": f"castanet:{_hash_id(url)}",
        "url": (url or "")[:500],  # Truncate URL if too long
        "date_posted": date_posted or datetime.utcnow().date().isoformat(),
        "city": "Kelowna",
        "postal_code": (postal or "")[:20]
        if postal
        else None,  # VARCHAR(20) constraint
        "property_type": prop_type,
        "listing_type": (listing_type or "")[:10],  # VARCHAR(10) constraint
        "price": price,
        "bedrooms": beds,
        "bathrooms": baths,
        "area_sqft": area,
        "year_built": None,
        "description": (details_text or "").strip()[:5000] or None,
    }


def _get(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text


def fetch_castanet(
    city: str = "Kelowna",
    max_pages: int = 2,
    sleep_sec: float = SLEEP_SEC,
):
    """
    Scrape Castanet rentals for Kelowna and return:
      rows: list[dict] normalized to listings_raw schema
      raw_blobs: list[str] of raw HTML (index & detail pages) for snapshots

    Depends on helpers in this module:
      - _get, _parse_details_panel, _parse_breadcrumb_type, _parse_price_from_detail
      - _parse_date, _parse_beds_baths, _normalize_property_type, _extract_postal_code
      - _make_listing_row
    """
    rows: List[Dict] = []
    raw_blobs: List[str] = []

    for page in range(1, max_pages + 1):
        # Build the search URL (Kelowna rentals)
        params = DEFAULT_SEARCH_PARAMS.copy()
        params["p"] = str(page)
        param_string = "&".join(f"{k}={v}" for k, v in params.items() if v != "")
        index_url = f"{BASE}{INDEX_PATH}?{param_string}"

        try:
            html = _get(index_url)
        except Exception:
            # skip whole page on transient issues
            time.sleep(sleep_sec)
            continue

        raw_blobs.append(html)
        soup = BeautifulSoup(html, "lxml")

        # Card links (Castanet uses <a class="prod_container" href="/details/...">)
        cards = soup.select("a.prod_container")
        if not cards:
            # fallback selectors if layout changes
            cards = soup.select("a[href*='/details/']")

        for card in cards:
            href = card.get("href")
            if not href:
                continue
            url = href if href.startswith("http") else f"{BASE}{href}"

            # Some quick info from the card (optional)
            descr_el = card.select_one(".descr")
            title_card = (
                descr_el.select_one("h3, h4, .title, strong") if descr_el else None
            )
            title_text = title_card.get_text(strip=True) if title_card else None
            price_card_el = descr_el.select_one(".price, .amount") if descr_el else None
            price_card_text = (
                price_card_el.get_text(strip=True) if price_card_el else None
            )
            meta_card = descr_el.get_text(" ", strip=True) if descr_el else None

            # Open the detail page for authoritative fields
            try:
                dhtml = _get(url)
            except Exception:
                # If detail fetch fails, try to salvage row from card data (still filtered by city)
                tmp_row = _make_listing_row(
                    url=url,
                    date_posted=datetime.utcnow().date().isoformat(),
                    title=title_text,
                    city=city,  # assume Kelowna from search filter
                    price_text=price_card_text,
                    meta_chunk=meta_card,
                    details_text=None,
                    listing_type="rent",
                )
                if tmp_row:
                    rows.append(tmp_row)
                time.sleep(sleep_sec)
                continue

            raw_blobs.append(dhtml)
            dsoup = BeautifulSoup(dhtml, "lxml")

            # Title (detail page)
            dt_title_el = dsoup.select_one(
                "h1, h1.title, .title h1"
            ) or dsoup.select_one(".det_title")
            dt_title = dt_title_el.get_text(strip=True) if dt_title_el else title_text

            # Price (detail page has the blue $ amount near the title)
            price_text_detail = _parse_price_from_detail(dsoup) or price_card_text

            # Breadcrumb -> property type
            prop_type_bc = _parse_breadcrumb_type(dsoup)

            # Details panel: Bedrooms / Bathrooms / Post Date / Ad Number
            detail = _parse_details_panel(dsoup)
            beds_d, baths_d = _parse_beds_baths(
                " ".join(
                    filter(None, [detail.get("bedrooms"), detail.get("bathrooms")])
                )
            )
            date_d = _parse_date(detail.get("post_date"))
            adnum = detail.get("ad_number")
            native_id = adnum.strip() if adnum and adnum.strip().isdigit() else None

            # Description
            desc_el = (
                dsoup.select_one(
                    ".description, #description, .content, article, .prod-description"
                )
                or dsoup.select_one("#details + *")  # sometimes immediately after panel
            )
            details_text = desc_el.get_text(" ", strip=True) if desc_el else None

            # Postal code anywhere on page
            postal_from_page = _extract_postal_code(dsoup.get_text(" ", strip=True))

            # City guard (should be Kelowna; confirm if visible on page)
            city_guess = "Kelowna"
            if "kelowna" not in dsoup.get_text(" ", strip=True).lower():
                # still enforce Kelowna (search filter), but keep the guard in case you expand later
                city_guess = city

            # Build base row from generic normalizer
            row = _make_listing_row(
                url=url,
                date_posted=date_d,  # may be None; normalizer will backfill today
                title=dt_title or title_text,
                city=city_guess,
                price_text=price_text_detail,
                meta_chunk=meta_card,  # keep meta text to help parse sqft/beds if needed
                details_text=details_text,
                listing_type="rent",
            )

            # Strengthen fields with detail-derived values
            if row:
                if prop_type_bc and not row.get("property_type"):
                    row["property_type"] = prop_type_bc
                if beds_d is not None:
                    row["bedrooms"] = beds_d
                if baths_d is not None:
                    row["bathrooms"] = baths_d
                if postal_from_page and not row.get("postal_code"):
                    row["postal_code"] = postal_from_page
                if native_id:
                    row["listing_id"] = f"castanet:{native_id}"

                # Final Kelowna filter
                if row["city"] == "Kelowna" and is_kelowna_city(row["city"]):
                    rows.append(row)

            time.sleep(sleep_sec)

        time.sleep(sleep_sec)

    return rows, raw_blobs
