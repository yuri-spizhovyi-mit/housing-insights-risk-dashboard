# --- at top of file ---
import os, time, io, hashlib, datetime as dt, re, logging
import requests
from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
    "Accept-Language": "en-CA,en-US;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
}

DEBUG_SNAP_DIR = os.path.join(".debug", "rentfaster")


def fetch_rentfaster_kelowna(max_pages=1, sleep_sec=1.0, log=None):
    """
    Scrape RentFaster Kelowna list pages, with graceful fallbacks.
    - Saves HTML snapshots for inspection under ./.debug/rentfaster/
    - Tries multiple card patterns; if price/beds missing, follows detail link.
    """
    if log is None:
        log = logging.getLogger(__name__)
    os.makedirs(DEBUG_SNAP_DIR, exist_ok=True)

    session = requests.Session()
    session.headers.update(HEADERS)

    all_rows = []
    base = "https://www.rentfaster.ca"
    for page in range(1, max_pages + 1):
        url = f"{base}/bc/kelowna/rentals/?page={page}&view=list"
        r = session.get(url, timeout=30)
        r.raise_for_status()
        html = r.text

        # snapshot for debugging
        snap_path = os.path.join(DEBUG_SNAP_DIR, f"kelowna_list_p{page}.html")
        with open(snap_path, "w", encoding="utf-8") as f:
            f.write(html)

        soup = BeautifulSoup(html, "html.parser")

        # Try a few patterns for cards (class names change over time)
        card_selectors = [
            ".listingCard",                   # old guess
            "article.listing",               # common semantic tag
            "[data-cy='listing-card']",      # test-tag pattern
            ".rf-listing-card",              # hypothetical newer class
            "li[class*='listing']",          # generic
        ]
        cards = []
        for sel in card_selectors:
            found = soup.select(sel)
            if found:
                cards = found
                break

        if not cards:
            log.info("RentFaster: page %s had 0 cards (inspect %s)", page, snap_path)
            time.sleep(sleep_sec)
            continue

        page_rows = []
        for card in cards:
            # Try to pick up title + link
            a = card.select_one("a[href*='/bc/kelowna/']")
            if not a:
                a = card.select_one("a[href*='/bc/']")
            href = a["href"] if a and a.has_attr("href") else ""
            if href and href.startswith("/"):
                href = base + href

            title = (a.get_text(" ", strip=True) if a else card.get_text(" ", strip=True))[:200]

            # Try list-page price and beds
            price = _extract_price(card.get_text(" ", strip=True))
            beds = _extract_beds(card.get_text(" ", strip=True))

            # If missing, try common sub-elements
            if price is None:
                price_el = card.select_one(".listingCardPrice, .price, [class*='price']")
                if price_el:
                    price = _extract_price(price_el.get_text(" ", strip=True))

            if beds is None:
                beds_el = card.select_one(".listingCardBed, .beds, [class*='bed']")
                if beds_el:
                    beds = _extract_beds(beds_el.get_text(" ", strip=True))

            # Fallback: fetch the detail page (only when needed)
            if (price is None or beds is None) and href:
                try:
                    dr = session.get(href, timeout=30)
                    if dr.ok:
                        dhtml = dr.text
                        # save a tiny snapshot for first few detail fetches for debugging
                        if len(page_rows) < 3:
                            dh_path = os.path.join(DEBUG_SNAP_DIR, f"kelowna_detail_{hashlib.md5(href.encode()).hexdigest()[:8]}.html")
                            with open(dh_path, "w", encoding="utf-8") as f:
                                f.write(dhtml)
                        dsoup = BeautifulSoup(dhtml, "html.parser")
                        if price is None:
                            # Try microdata and obvious labels
                            sel = [
                                "[itemprop='price']",
                                ".price", ".rent", ".rf-price", ".listing-price",
                            ]
                            for s in sel:
                                el = dsoup.select_one(s)
                                if el:
                                    price = _extract_price(el.get_text(" ", strip=True))
                                    if price is not None:
                                        break
                        if beds is None:
                            sel = [".beds", ".bedrooms", "[data-beds]", ".rf-beds"]
                            for s in sel:
                                el = dsoup.select_one(s)
                                if el:
                                    beds = _extract_beds(el.get_text(" ", strip=True))
                                    if beds is not None:
                                        break
                except Exception as e:
                    log.debug("Detail fetch failed for %s: %s", href, e)

            # Build row only if we have a price
            if price is None:
                continue

            bedrooms = None
            if beds is not None:
                try:
                    bedrooms = int(beds)
                except Exception:
                    bedrooms = None

            rid = hashlib.sha256(("rentfaster|" + (href or title)).encode("utf-8")).hexdigest()[:32]
            row = {
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
            page_rows.append(row)

        log.info("RentFaster: page %s extracted %d listings (inspect %s)", page, len(page_rows), snap_path)
        all_rows.extend(page_rows)
        time.sleep(sleep_sec)

    return all_rows


def _extract_price(text: str):
    # finds first $1,234 or 1234; ignores “+” suffixes
    m = re.search(r"\$?\s*([0-9][0-9,]{2,})(?!\S)", text)
    if m:
        return float(m.group(1).replace(",", ""))
    return None


def _extract_beds(text: str):
    # accepts Studio/ bachelor -> 0; 1 bed/1br -> 1, etc.
    t = text.lower()
    if "studio" in t or "bachelor" in t:
        return 0
    m = re.search(r"(\d+)\s*(?:br|bed|beds|bedroom|bedrooms)\b", t)
    if m:
        return int(m.group(1))
    # sometimes just a bare digit near "bd"
    m2 = re.search(r"\b(\d)\s*bd\b", t)
    if m2:
        return int(m2.group(1))
    return None
