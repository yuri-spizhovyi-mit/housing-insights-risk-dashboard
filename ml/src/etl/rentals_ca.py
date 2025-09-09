# rentals_ca.py
from typing import Iterable, Dict, Optional, Callable, Any, List
import time
import pandas as pd
import requests

from . import base

DEFAULT_SOURCE = "Rentals.ca"


def _safe_get(
    url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 20
) -> Optional[dict]:
    try:
        r = requests.get(
            url,
            headers=headers
            or {
                "Accept": "application/json, text/plain, */*",
                "User-Agent": "Mozilla/5.0 (compatible; ETL/1.0)",
                "Referer": "https://www.rentals.ca/",
            },
            timeout=timeout,
        )
        if r.status_code == 200:
            return r.json()
        return None
    except requests.RequestException:
        return None


def _normalize_rentals_json(
    items: List[Dict[str, Any]], city: str, bedroom_type: str, date: pd.Timestamp
) -> pd.DataFrame:
    """
    Normalize a list of rental observations (already filtered/aggregated)
    into rents table shape.
    """
    # Expect items like [{"value": 2150}] or any shape where average rent is present.
    # Customize the path to value if needed.
    vals = []
    for it in items:
        # You may adjust key names depending on your endpoint.
        # Try keys in order of preference:
        for key in ("average_rent", "avgRent", "value", "avg_price"):
            if key in it and isinstance(it[key], (int, float)):
                vals.append(float(it[key]))
                break
    if not vals:
        return pd.DataFrame()

    df = pd.DataFrame(
        {
            "city": [city] * len(vals),
            "date": [date] * len(vals),
            "bedroom_type": [bedroom_type] * len(vals),
            "value": vals,
            "source": DEFAULT_SOURCE,
        }
    )
    # If multiple values in one day, keep mean
    df = df.groupby(["city", "date", "bedroom_type", "source"], as_index=False)[
        "value"
    ].mean()
    return df


def load_from_endpoint(
    city: str,
    bedroom_type: str,
    date: Optional[pd.Timestamp],
    build_url: Callable[[str, str], str],
    engine,
    schema: str = "public",
    sleep_sec: float = 0.75,
) -> pd.DataFrame:
    """
    Hit a (possibly private/proxied) endpoint that returns summary stats for a (city, bedroom).
    - build_url(city, bedroom_type) should return a URL string.
    - date: the 'as_of' date to record; if None, use today (UTC).
    """
    as_of = pd.Timestamp.utcnow().normalize() if date is None else pd.to_datetime(date)
    url = build_url(city, bedroom_type)
    data = _safe_get(url)
    if data is None:
        return pd.DataFrame()

    # Adjust this selection to your endpoint structure:
    # Example: data = {"rows":[{"avgRent": 2200}, ...]}
    rows = data.get("rows") or data.get("data") or data.get("items") or []
    tidy = _normalize_rentals_json(rows, city, bedroom_type, as_of)
    if not tidy.empty:
        base.write_rents_upsert(tidy, engine, schema=schema)
    time.sleep(sleep_sec)  # be polite
    return tidy


def load_from_file(
    path: str,
    city_map: Dict[str, str],
    bedroom_map: Dict[str, str],
    date_field: str,
    price_field: str,
    engine=None,
    schema: str = "public",
) -> pd.DataFrame:
    """
    Fallback loader for CSV/JSON you’ve pre-downloaded (e.g., monthly report extract).
    Expects columns including: city name, bedroom type, date_field, price_field.
    City and bedroom values are normalized via the provided maps.
    """
    if path.lower().endswith(".csv"):
        raw = pd.read_csv(path)
    else:
        raw = pd.read_json(path)

    # Required columns check is flexible; you map them below.
    # Example: raw has columns ["City","Bedroom","Month","AverageRent"]
    # Map to canonical
    df = pd.DataFrame(
        {
            "city": raw["City"].map(city_map).fillna(raw["City"]),
            "bedroom_type": raw["Bedroom"].map(bedroom_map).fillna(raw["Bedroom"]),
            "date": pd.to_datetime(raw[date_field], errors="coerce"),
            "value": pd.to_numeric(raw[price_field], errors="coerce"),
            "source": DEFAULT_SOURCE,
        }
    ).dropna(subset=["date", "value"])

    df["date"] = df["date"].dt.date
    if engine is not None:
        base.write_rents_upsert(df, engine, schema=schema)
    return df


def run(ctx):
    """
    Rentals.ca production-friendly run:
    - Build or fetch a tidy DataFrame with columns:
      city, date, bedroom_type, median_rent, source
    - UPSERT into public.rents (PK: city, "date", bedroom_type)
    """
    import datetime as _dt
    import pandas as _pd

    today = _dt.date.today()

    # Example synthetic frame. Replace with load_from_endpoint(...) or load_from_file(...)
    df = _pd.DataFrame(
        {
            "city": ["Kelowna", "Kelowna", "Vancouver"],
            "date": [_pd.to_datetime(today).date()] * 3,
            "bedroom_type": ["1BR", "2BR", "1BR"],
            # If you currently compute 'value', you can keep it and we'll rename:
            "median_rent": [2300.0, 2800.0, 3100.0],
            "source": [DEFAULT_SOURCE] * 3,
        }
    )

    # Safety: if some upstream path still produces 'value', map it:
    if "median_rent" not in df.columns and "value" in df.columns:
        df = df.rename(columns={"value": "median_rent"})

    base.write_df(df, "rents", ctx)
    return {"rents": df}
