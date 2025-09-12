# ml/src/etl/rentals_ca.py
from __future__ import annotations

import io
import os
import re
import json
import logging
import datetime as dt
from typing import Optional, Tuple

import pandas as pd
import requests

from . import base  # your shared ETL helpers (Session, S3/MinIO utils, DB writers, Context, etc.)

# -----------------------------
# Config
# -----------------------------
SOURCE_NAME = "Rentals.ca"

# Canonical set we keep in the DB
TARGET_CITIES = {"Kelowna", "Vancouver", "Toronto"}

# Common bedroom labels we’ll normalize to {0BR, 1BR, 2BR, 3BR, 4BR+}
BEDROOM_MAP = {
    # studio / bachelor
    "studio": "0BR",
    "bachelor": "0BR",
    "0": "0BR",
    "0 br": "0BR",
    "0br": "0BR",
    "0-bedroom": "0BR",
    "0 bedroom": "0BR",
    # 1+
    "1": "1BR",
    "1 br": "1BR",
    "1br": "1BR",
    "1-bedroom": "1BR",
    "1 bedroom": "1BR",
    "one bedroom": "1BR",
    # 2
    "2": "2BR",
    "2 br": "2BR",
    "2br": "2BR",
    "2-bedroom": "2BR",
    "2 bedroom": "2BR",
    "two bedroom": "2BR",
    # 3
    "3": "3BR",
    "3 br": "3BR",
    "3br": "3BR",
    "3-bedroom": "3BR",
    "3 bedroom": "3BR",
    "three bedroom": "3BR",
    # 4+
    "4": "4BR+",
    "4 br": "4BR+",
    "4br": "4BR+",
    "4-bedroom": "4BR+",
    "4 bedroom": "4BR+",
    "four bedroom": "4BR+",
    "5": "4BR+",
    "5 br": "4BR+",
    "5br": "4BR+",
    "5-bedroom": "4BR+",
    "5 bedroom": "4BR+",
    "five bedroom": "4BR+",
}

# City normalization to our canonical set
CITY_MAP = {
    # typical variants seen in reports
    "vancouver, bc": "Vancouver",
    "city of vancouver": "Vancouver",
    "vancouver": "Vancouver",
    "toronto, on": "Toronto",
    "city of toronto": "Toronto",
    "toronto": "Toronto",
    "kelowna, bc": "Kelowna",
    "kelowna": "Kelowna",
}

# Where to snapshot raw files in MinIO
RAW_BUCKET = os.getenv("RAW_BUCKET", "raw")
RAW_PREFIX = "rentals_ca"  # becomes raw/rentals_ca/...


# -----------------------------
# Public entrypoint
# -----------------------------
def run(ctx: base.Context) -> pd.DataFrame:
    """
    Downloads real Rentals.ca data (CSV/Excel or endpoint), snapshots raw into MinIO,
    normalizes to (city, date, bedroom_type, median_rent, source), and performs
    an idempotent upsert into Postgres public.rents.

    Returns the tidy DataFrame that was written.
    """
    log = logging.getLogger(__name__)
    session = base.get_session(ctx)  # your shared requests.Session with retries/timeouts

    # --- CHOOSE ONE LOADER ---
    # 1) If you already have a local CSV/Excel file (manually downloaded)
    #    put its path into ctx.params.get("rentals_ca_path"), e.g. data/raw/rentals_2025-08.csv
    local_path = (ctx.params or {}).get("rentals_ca_path")

    # 2) Or specify a direct CSV/XLSX URL via ctx.params["rentals_ca_url"]
    csv_url = (ctx.params or {}).get("rentals_ca_url")

    # 3) Or later plug your private/proxy API into load_from_endpoint()
    endpoint_url = (ctx.params or {}).get("rentals_ca_endpoint")

    raw_bytes: Optional[bytes] = None
    raw_name: Optional[str] = None
    content_type: Optional[str] = None

    if local_path:
        raw_bytes, raw_name, content_type = load_from_file(local_path)
    elif csv_url:
        raw_bytes, raw_name, content_type = load_via_http(session, csv_url)
    elif endpoint_url:
        raw_bytes, raw_name, content_type = load_from_endpoint(session, endpoint_url)
    else:
        # Fallback: raise a helpful error so this never silently uses synthetic data
        raise RuntimeError(
            "No Rentals.ca source configured. "
            "Provide one of: ctx.params['rentals_ca_path'] (local CSV/XLSX), "
            "ctx.params['rentals_ca_url'] (HTTP CSV/XLSX), or "
            "ctx.params['rentals_ca_endpoint'] (API/JSON)."
        )

    # Snapshot raw → MinIO (best-effort)
    try:
        snapshot_key = snapshot_raw_to_minio(ctx, raw_bytes, raw_name, content_type)
        if snapshot_key:
            log.info("Snapshotted raw Rentals.ca to minio://%s/%s", RAW_BUCKET, snapshot_key)
    except Exception as e:
        log.warning("Failed to snapshot Rentals.ca raw to MinIO (continuing): %s", e)

    # Parse & normalize
    tidy = normalize_to_rents(raw_bytes, raw_name, content_type, ctx)

    # Persist
    base.write_rents_upsert(tidy, ctx)

    log.info("Wrote %d Rentals.ca rows to public.rents", len(tidy))
    return tidy


# -----------------------------
# Loaders (CSV/Excel/Endpoint)
# -----------------------------
def load_from_file(path: str) -> Tuple[bytes, str, str]:
    with open(path, "rb") as f:
        raw = f.read()
    name = os.path.basename(path)
    content_type = guess_content_type(name)
    return raw, name, content_type


def load_via_http(session: requests.Session, url: str) -> Tuple[bytes, str, str]:
    resp = session.get(url, timeout=60)
    resp.raise_for_status()
    # try to get a file-ish name
    name = _filename_from_headers_or_url(resp.headers, url)
    return resp.content, name, resp.headers.get("Content-Type") or guess_content_type(name)


def load_from_endpoint(session: requests.Session, url: str) -> Tuple[bytes, str, str]:
    """
    Stub for a JSON/API response (e.g., from a proxy or partner).
    Shape this to return the raw payload. normalize_to_rents() will handle CSV/Excel/JSON.
    """
    resp = session.get(url, timeout=60)
    resp.raise_for_status()
    # We store the *raw* JSON text as our snapshot
    raw = resp.content
    name = f"rentals_ca_endpoint_{dt.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json"
    return raw, name, "application/json"


# -----------------------------
# Normalization
# -----------------------------
def normalize_to_rents(raw: bytes, name: str, content_type: str, ctx: base.Context) -> pd.DataFrame:
    """
    Accepts CSV/Excel/JSON bytes; returns tidy DataFrame with columns:
      city, date, bedroom_type, median_rent, source
    Filters to TARGET_CITIES and to the run month (if the file encodes a single month)
    or uses the per-row month when available.
    """
    # 1) Parse to a raw DataFrame
    if content_type.startswith("application/json") or name.lower().endswith(".json"):
        df = _parse_json(raw)
    elif content_type in ("application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet") or name.lower().endswith((".xls", ".xlsx")):
        df = _parse_excel(raw)
    else:
        # default to CSV/TSV
        df = _parse_csv(raw)

    if df.empty:
        raise ValueError(f"Parsed an empty Rentals.ca DataFrame from {name}")

    # 2) Standardize columns (robust column finders)
    col_city = _first_present(df.columns, ["city", "location", "market", "metro"])
    col_bed  = _first_present(df.columns, ["bedroom", "bedrooms", "bedroom_type", "type"])
    col_med  = _first_present(df.columns, ["median_rent", "median", "median rent", "median_rent_$", "median ($)"])
    col_avg  = _first_present(df.columns, ["average_rent", "avg", "average rent", "avg_rent", "average_rent_$"])
    col_month = _first_present(df.columns, ["month", "date", "period"])

    if not col_med and not col_avg:
        raise ValueError(
            "Could not find a median or average rent column in Rentals.ca file. "
            "Looked for: median_rent/median/average_rent/avg"
        )

    # 3) Build working DF with best available rent metric (prefer median; fallback to average)
    rent_col = col_med or col_avg
    work = df[[c for c in [col_city, col_bed, rent_col, col_month] if c is not None]].copy()
    work.columns = ["city_raw", "bedraw", "rent_raw"][: len(work.columns)] + (["month_raw"] if col_month else [])

    # 4) Normalize bedrooms → our canonical labels
    work["bedroom_type"] = (
        work["bedraw"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map(BEDROOM_MAP)
        .fillna(
            work["bedraw"]
            .astype(str)
            .str.extract(r"(\d+)")[0]  # try to capture a digit
            .map({"0": "0BR", "1": "1BR", "2": "2BR", "3": "3BR", "4": "4BR+"})
        )
    )
    work = work.dropna(subset=["bedroom_type"])

    # 5) Normalize city → canonical + filter to our target set
    work["city"] = (
        work["city_raw"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map(CITY_MAP)
        .fillna(work["city_raw"].astype(str).str.strip().str.title())  # graceful fallback
    )
    work = work[work["city"].isin(TARGET_CITIES)]

    # 6) Derive month (first of month)
    if "month_raw" in work.columns:
        work["date"] = work["month_raw"].apply(_coerce_month_start)
    else:
        # Try to infer from filename (e.g., rentals_2025-08.csv or 2025_08)
        inferred = _infer_month_from_name(name)
        if inferred is None:
            # fallback to run month in context (use previous month—it’s typical for rent reports)
            run_date = getattr(ctx, "run_date", dt.date.today())
            inferred = (run_date.replace(day=1) - dt.timedelta(days=1)).replace(day=1)
        work["date"] = inferred

    # 7) numeric rent
    work["median_rent"] = pd.to_numeric(work["rent_raw"], errors="coerce")
    work = work.dropna(subset=["median_rent"])

    # 8) final shape
    tidy = work[["city", "date", "bedroom_type", "median_rent"]].copy()
    tidy["source"] = SOURCE_NAME

    # 9) (Optional) collapse very large bedrooms to 4BR+
    tidy.loc[tidy["bedroom_type"].isin(["5BR", "6BR", "7BR"]), "bedroom_type"] = "4BR+"

    # 10) de-dup (idempotent)
    tidy = (
        tidy.sort_values(["city", "date", "bedroom_type"])
        .drop_duplicates(subset=["city", "date", "bedroom_type"], keep="last")
        .reset_index(drop=True)
    )
    return tidy


# -----------------------------
# Raw snapshot to MinIO (best-effort)
# -----------------------------
def snapshot_raw_to_minio(ctx: base.Context, raw: bytes, name: str, content_type: str) -> Optional[str]:
    """
    Attempts to write the raw payload to MinIO/S3. This is best-effort and will not
    fail the run if the client isn’t available. Returns the object key on success.
    """
    ts = dt.datetime.utcnow()
    yyyymm = ts.strftime("%Y-%m")
    key = f"{RAW_PREFIX}/{yyyymm}/{name}"

    # Preferred: if your project exposes a helper (uncomment if you have it)
    # return base.snapshot_raw(ctx, bucket=RAW_BUCKET, key=key, data=raw, content_type=content_type)

    # Generic attempt through a client on Context (minio or s3)
    client = getattr(ctx, "minio", None) or getattr(ctx, "s3", None)
    if client:
        # minio client typically: put_object(bucket, key, data, length, content_type=...)
        try:
            buf = io.BytesIO(raw)
            length = len(raw)
            if hasattr(client, "put_object"):
                client.put_object(RAW_BUCKET, key, buf, length, content_type=content_type or "application/octet-stream")
                return key
        except Exception as e:
            logging.getLogger(__name__).warning("MinIO put_object failed: %s", e)

    # If the project has a filesystem staging, use it (optional)
    try:
        local_raw_dir = os.path.join(ctx.workdir if hasattr(ctx, "workdir") else ".", "raw_snapshots", RAW_PREFIX, yyyymm)
        os.makedirs(local_raw_dir, exist_ok=True)
        with open(os.path.join(local_raw_dir, name), "wb") as f:
            f.write(raw)
        return f"{RAW_PREFIX}/{yyyymm}/{name}"
    except Exception:
        pass

    return None


# -----------------------------
# Parsers
# -----------------------------
def _parse_csv(raw: bytes) -> pd.DataFrame:
    # Try comma, then semicolon/TSV
    try:
        return pd.read_csv(io.BytesIO(raw))
    except Exception:
        try:
            return pd.read_csv(io.BytesIO(raw), sep=";")
        except Exception:
            return pd.read_csv(io.BytesIO(raw), sep="\t")


def _parse_excel(raw: bytes) -> pd.DataFrame:
    return pd.read_excel(io.BytesIO(raw))


def _parse_json(raw: bytes) -> pd.DataFrame:
    payload = json.loads(raw.decode("utf-8"))
    # Accept either list-of-objects or {"data": [...]} shells
    if isinstance(payload, dict):
        records = payload.get("data", payload.get("rows", payload))
        if isinstance(records, dict):
            # if it's still a dict, try any first list
            for v in records.values():
                if isinstance(v, list):
                    records = v
                    break
    else:
        records = payload
    return pd.json_normalize(records)


# -----------------------------
# Utilities
# -----------------------------
def _first_present(columns, candidates):
    cols_norm = {str(c).strip().lower(): c for c in columns}
    for cand in candidates:
        key = cand.lower()
        if key in cols_norm:
            return cols_norm[key]
    return None


def _coerce_month_start(x) -> dt.date:
    """
    Accepts formats like:
      - 2025-08
      - 2025-08-01
      - Aug 2025 / August 2025
      - 2025/08
    Returns date(...) set to first day of the month.
    """
    if pd.isna(x):
        return None
    s = str(x).strip()

    # ISO-like
    m = re.match(r"^\s*(\d{4})[-/](\d{1,2})(?:[-/](\d{1,2}))?\s*$", s)
    if m:
        y, mo = int(m.group(1)), int(m.group(2))
        return dt.date(y, mo, 1)

    # Month name + year
    try:
        dtm = pd.to_datetime(s, errors="raise")
        return dt.date(dtm.year, dtm.month, 1)
    except Exception:
        pass

    # Excel serial?
    try:
        dtm = pd.to_datetime(float(s), unit="d", origin="1899-12-30", errors="raise")
        return dt.date(dtm.year, dtm.month, 1)
    except Exception:
        pass

    # If completely unknown, try today’s month
    today = dt.date.today()
    return dt.date(today.year, today.month, 1)


def _infer_month_from_name(name: str) -> Optional[dt.date]:
    """
    Tries to extract YYYY-MM or YYYY_MM from filename.
    """
    s = name.lower()
    m = re.search(r"(20\d{2})[-_](0?[1-9]|1[0-2])", s)
    if m:
        y, mo = int(m.group(1)), int(m.group(2))
        return dt.date(y, mo, 1)
    # Also try month names
    month_map = {m.lower(): i for i, m in enumerate(["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], start=1)}
    m2 = re.search(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[_-]?(20\d{2})", s)
    if m2:
        mo = month_map[m2.group(1)]
        y = int(m2.group(2))
        return dt.date(y, mo, 1)
    return None


def guess_content_type(filename: str) -> str:
    fn = filename.lower()
    if fn.endswith(".xlsx"):
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if fn.endswith(".xls"):
        return "application/vnd.ms-excel"
    if fn.endswith(".json"):
        return "application/json"
    if fn.endswith(".csv"):
        return "text/csv"
    if fn.endswith(".tsv"):
        return "text/tab-separated-values"
    return "application/octet-stream"


def _filename_from_headers_or_url(headers, url: str) -> str:
    cd = headers.get("Content-Disposition", "")
    m = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', cd)
    if m:
        return m.group(1)
    # fallback to URL tail
    tail = url.split("?")[0].rstrip("/").split("/")[-1]
    return tail or f"rentals_ca_{dt.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.csv"
