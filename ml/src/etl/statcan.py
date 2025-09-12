from typing import Iterable, Dict, Optional
import os
import pandas as pd

from ml.src.etl.base import Context, month_floor, put_raw_bytes
from ml.src.etl.statcan_wds import download_table_csv
from ml.src.etl import base
from ml.src.etl.utils import canonical_geo

# Default table to load when calling run(ctx)
# CPI, all-items, monthly: 18-10-0004-01 -> 1810000401
DEFAULT_PID = os.getenv("STATCAN_PID", "1810000401")
DEFAULT_METRIC = os.getenv("STATCAN_METRIC", "StatCan_CPI_AllItems")

# Canonical geographies we keep for the MVP
TARGET_GEOS = {"Kelowna", "Vancouver", "Toronto", "Canada"}


# ---------------------------
# Utilities
# ---------------------------


def _normalize_common(
    df: pd.DataFrame,
    metric_name: str,
    geo_col: str = "GEO",
    date_col: str = "REF_DATE",
    value_col: str = "VALUE",
) -> pd.DataFrame:
    """
    Normalize a StatCan DataFrame into the `metrics` long shape:

        city | date | metric | value | source

    - canonicalizes geo into {Kelowna, Vancouver, Toronto, Canada}
    - floors dates to month-start
    - drops rows outside TARGET_GEOS
    """
    # Robust column detection (case-insensitive)
    cols = {c.upper(): c for c in df.columns}
    if "REF_DATE" not in cols or "VALUE" not in cols:
        raise ValueError("StatCan CSV missing REF_DATE and/or VALUE columns")

    date_col = cols.get("REF_DATE", date_col)
    value_col = cols.get("VALUE", value_col)
    geo_col = cols.get("GEO", geo_col) if "GEO" in cols else None

    # Canonicalize geography (if present), else national
    if geo_col is not None:
        geo_ser = df[geo_col].apply(canonical_geo)
    else:
        geo_ser = pd.Series(["Canada"] * len(df))

    tidy = pd.DataFrame(
        {
            "city": geo_ser,
            "date": pd.to_datetime(df[date_col], errors="coerce"),
            "metric": metric_name,
            "value": pd.to_numeric(df[value_col], errors="coerce"),
            "source": f"StatCan_{_pidish(metric_name)}",  # best-effort tag
        }
    ).dropna(subset=["date", "value"])

    # Month floor & filter to target geos
    tidy["date"] = month_floor(tidy["date"])
    tidy = tidy[tidy["city"].isin(TARGET_GEOS)]
    return tidy


def _pidish(metric_name: str) -> str:
    """
    Attempt to surface a PID-like suffix from the metric label for 'source' tagging.
    If none detected, return the metric itself; harmless.
    """
    # Expect labels like "StatCan_<PID>" or "StatCan_SomeMetric"
    if "_" in metric_name:
        return metric_name.split("_", 1)[-1]
    return metric_name


# ---------------------------
# Public helpers (generic)
# ---------------------------


def load_statcan_table(
    pid: str,
    metric_name: Optional[str],
    engine,
    schema: str = "public",
    product_filter: Optional[str] = None,
) -> pd.DataFrame:
    """
    Download a StatCan table via WDS, normalize, and **UPSERT** into `metrics`.

    - pid: e.g., "1810000401" or "18-10-0004-01"
    - metric_name: stored in `metric` column (defaults to f"StatCan_{pid}")
    - product_filter: optional substring filter for columns like 'Products'/'Product'
                      (e.g., "All-items" for CPI tables)

    Returns the DataFrame that was upserted.
    """
    df = download_table_csv(pid)  # <-- returns a DataFrame (not bytes)
    if product_filter:
        prod_cols = [c for c in df.columns if "product" in str(c).lower()]
        for pc in prod_cols:
            df = df[
                df[pc].astype(str).str.contains(product_filter, case=False, na=False)
            ]

    metric = metric_name or f"StatCan_{_normalize_pid_like(pid)}"
    tidy = _normalize_common(df, metric_name=metric)

    # Idempotent upsert into metrics (PK: city, date, metric)
    base.write_metrics_upsert(tidy, engine, schema=schema)
    return tidy


def load_many(
    pids: Iterable[str],
    metric_names: Optional[Dict[str, str]],
    engine,
    schema: str = "public",
    product_filter_by_pid: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    """
    Convenience loader for multiple StatCan tables.
    - metric_names: optional mapping pid -> metric label
    - product_filter_by_pid: optional mapping pid -> product substring filter
    """
    frames = []
    for pid in pids:
        m = (metric_names or {}).get(pid)
        pf = (product_filter_by_pid or {}).get(pid)
        frames.append(load_statcan_table(pid, m, engine, schema, pf))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _normalize_pid_like(pid_like: str) -> str:
    """Return the 8-digit numeric PID form if possible; else original."""
    import re

    digits = re.sub(r"\D", "", str(pid_like))
    return digits[:8] if len(digits) >= 8 else str(pid_like)


# ---------------------------
# CLI-style entrypoint used by tests
# ---------------------------


def run(ctx: Context):
    """
    Default 'statcan' pipeline entry:
      - Loads CPI (all-items) monthly series
      - Writes via base.write_df(...) so tests can intercept the 'metrics' table
      - Snapshots raw + tidy to MinIO
    """
    pid = DEFAULT_PID
    metric = DEFAULT_METRIC

    # Download full table and snapshot RAW
    df_raw = download_table_csv(pid)
    put_raw_bytes(
        ctx,
        f"{ctx.s3_raw_prefix}/statcan/{ctx.run_date.isoformat()}/{_normalize_pid_like(pid)}.csv",
        df_raw.to_csv(index=False).encode("utf-8"),
        "text/csv",
    )

    # Optional: for CPI tables keep only "All-items"
    prod_cols = [c for c in df_raw.columns if "product" in str(c).lower()]
    df = df_raw.copy()
    for pc in prod_cols:
        df = df[df[pc].astype(str).str.contains("All-items", case=False, na=False)]

    # Normalize & keep target CMAs + Canada
    tidy = _normalize_common(df, metric_name=metric)

    # Write via generic writer so your existing tests (that monkeypatch write_df) still work
    base.write_df(tidy, "metrics", ctx)

    # Snapshot TIDY for auditability
    put_raw_bytes(
        ctx,
        f"{ctx.s3_raw_prefix}/statcan/{ctx.run_date.isoformat()}/{_normalize_pid_like(pid)}.tidy.csv",
        tidy.to_csv(index=False).encode("utf-8"),
        "text/csv",
    )

    return tidy
