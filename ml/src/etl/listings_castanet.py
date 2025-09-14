# listings_castanet.py
from __future__ import annotations
import re, time, hashlib
from datetime import datetime
from typing import Tuple, List, Dict, Optional
import requests
from bs4 import BeautifulSoup

from utils import save_snapshot, is_kelowna_city

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; HIRD-ETL/1.0)"}
BASE = (
    "https://classifieds.castanet.net"  # listings live under /real-estate/ or /rental/
)
INDEX_PATH = "/real-estate/rentals/"  # adjust if needed
SLEEP_SEC = 1.0


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
    return txt.strip().title()


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
        "url": url,
        "date_posted": date_posted or datetime.utcnow().date().isoformat(),
        "city": "Kelowna",
        "postal_code": postal,
        "property_type": prop_type,
        "listing_type": listing_type,
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
    city: str = "Kelowna", max_pages: int = 2, sleep_sec: float = SLEEP_SEC
):
    rows: List[Dict] = []
    raw_blobs: List[str] = []

    for page in range(1, max_pages + 1):
        index_url = f"{BASE}{INDEX_PATH}?p={page}"
        html = _get(index_url)
        raw_blobs.append(html)
        soup = BeautifulSoup(html, "lxml")

        # Listing cards (use multiple selectors in case of layout variants)
        cards = soup.select("div.listing, div.result, li.listing, article") or []
        for card in cards:
            # grab basics safely
            a = card.select_one("a[href]") or card.find("a", href=True)
            if not a:
                continue
            href = a["href"]
            url = href if href.startswith("http") else f"{BASE}{href}"

            title = (
                (card.select_one(".title, h2, h3") or {}).get_text(strip=True)
                if card.select_one(".title, h2, h3")
                else None
            )
            price_text = (
                (card.select_one(".price, .listing-price, .amount") or {}).get_text(
                    strip=True
                )
                if card.select_one(".price, .listing-price, .amount")
                else None
            )
            meta_chunk = (
                (card.select_one(".meta, .details, .attributes") or {}).get_text(
                    " ", strip=True
                )
                if card.select_one(".meta, .details, .attributes")
                else None
            )
            date_text = (
                (card.select_one(".date, .posted") or {}).get_text(" ", strip=True)
                if card.select_one(".date, .posted")
                else None
            )

            # often city appears in the snippet; if not, enforce later via detail page
            city_guess = (
                "Kelowna"
                if "kelowna" in (meta_chunk or "").lower()
                or "kelowna" in (title or "").lower()
                else city
            )

            # follow detail page for description/postal code
            try:
                dhtml = _get(url)
                raw_blobs.append(dhtml)
                dsoup = BeautifulSoup(dhtml, "lxml")
                desc_el = dsoup.select_one(
                    ".description, #description, .content, article"
                )
                details_text = desc_el.get_text(" ", strip=True) if desc_el else None

                # Sometimes city appears clearly on the detail page
                city_el = dsoup.find(string=re.compile(r"Kelowna", re.I))
                if city_el:
                    city_guess = "Kelowna"

                row = _make_listing_row(
                    url=url,
                    date_posted=_parse_date(date_text),
                    title=title,
                    city=city_guess,
                    price_text=price_text,
                    meta_chunk=meta_chunk,
                    details_text=details_text,
                    listing_type="rent",
                )
                if row and row["city"] == "Kelowna":
                    rows.append(row)
            except Exception:
                # skip problematic listing but continue
                continue

            time.sleep(sleep_sec)

        time.sleep(sleep_sec)

    return rows, raw_blobs
