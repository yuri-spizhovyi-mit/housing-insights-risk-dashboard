from typing import Iterable, Dict, Optional
import os
import pandas as pd

from ml.src.etl.base import Context, month_floor, put_raw_bytes
from ml.src.etl.statcan_wds import download_table_csv
from ml.src.etl import base
from ml.src.etl.utils import canonical_geo
import sys

# --- DEBUG LOGGING TO FILE ---
sys.stdout = open("statcan_debug.log", "w", encoding="utf-8")
sys.stderr = sys.stdout

# Default table to load when calling run(ctx)
# CPI, all-items, monthly: 18-10-0004-01 -> 1810000401
# DEFAULT_PID = os.getenv("STATCAN_PID", "1810000401")
# DEFAULT_METRIC = os.getenv("STATCAN_METRIC", "StatCan_CPI_AllItems")
# --- METRIC DEFINITIONS ---
# PID references from StatCan Data Tables
# - CPI All-items:        18-10-0004-01 → 1810000401
# - Unemployment rate:    14-10-0287-03 → 1410028703
# - GDP growth rate (%):  36-10-0434-02 → 3610043402

DEFAULT_PIDS = ["1810000401", "1410028703", "3610043402"]
DEFAULT_METRIC_NAMES = {
    "1810000401": "cpi_allitems",
    "1410028703": "unemploymentrate",
    "3610043402": "gdp_growthrate",
}


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
    base.write_metrics_upsert(tidy, ctx)
    return tidy


def load_many(
    pids: Iterable[str],
    metric_names: Optional[Dict[str, str]],
    ctx: Context,
    product_filter_by_pid: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    frames = []
    for pid in pids:
        m = (metric_names or {}).get(pid)
        pf = (product_filter_by_pid or {}).get(pid)
        frames.append(load_statcan_table(pid, m, ctx, pf))
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
    StatCan pipeline entrypoint:
      - Loads CPI (All-items), Unemployment Rate, GDP Growth Rate
      - Writes to `public.metrics` using base.write_metrics_upsert
      - Snapshots raw and tidy CSVs to MinIO
    """
    print("[DEBUG] Starting StatCan ETL (CPI, Unemployment, GDP)")

    pids = DEFAULT_PIDS
    metric_names = DEFAULT_METRIC_NAMES
    product_filter_by_pid = {
        "1810000401": "All-items",  # CPI filter
        # GDP and Unemployment tables don't need filtering
    }

    tidy = load_many(
        pids=pids,
        metric_names=metric_names,
        ctx=ctx,
        product_filter_by_pid=product_filter_by_pid,
    )

    if tidy is None or tidy.empty:
        print("[DEBUG] WARNING: No rows loaded from StatCan")
        return tidy

    # Normalize to lowercase just in case
    tidy["metric"] = tidy["metric"].str.lower()

    print(f"[DEBUG] Step: Writing {len(tidy)} rows to database → 'metrics'")
    base.write_metrics_upsert(tidy, ctx)

    # Snapshot tidy
    put_raw_bytes(
        ctx,
        f"{ctx.s3_raw_prefix}/statcan/{ctx.run_date.isoformat()}/statcan_metrics.tidy.csv",
        tidy.to_csv(index=False).encode("utf-8"),
        "text/csv",
    )

    print("[DEBUG] StatCan ETL complete — rows written:", len(tidy))
    print("[DEBUG] Metrics present:", tidy["metric"].unique().tolist())
    return tidy


if __name__ == "__main__":
    from datetime import date
    from ml.src.etl import base

    ctx = base.Context(run_date=date.today())
    tidy = run(ctx)
    print(f"[DEBUG] StatCan run() completed — returned {len(tidy)} rows.")
