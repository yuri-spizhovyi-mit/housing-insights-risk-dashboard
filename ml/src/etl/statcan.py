from io import BytesIO
from typing import Iterable, Dict, Optional
import pandas as pd
from .base import Context, month_floor, put_raw_bytes
from .statcan_wds import download_table_csv
from . import base

PID_CPI = "1810000401"  # 18-10-0004-01

CMA_WHITELIST = {
    "Kelowna (CMA)",
    "Vancouver (CMA)",
    "Toronto (CMA)",
}


def run(ctx: Context):
    """
    Load StatCan CPI (PID 1810000401) and upsert into public.metrics with:
    metric = 'StatCan_CPI_AllItems'
    city   = whitelist CMAs or 'Canada' fallback
    """
    pid = PID_CPI  # "1810000401"
    alias_metric = "StatCan_CPI_AllItems"

    # 1) Download full CSV and snapshot
    df_raw = download_table_csv(pid)
    put_raw_bytes(
        ctx,
        f"{ctx.s3_raw_prefix}/statcan/{ctx.run_date.isoformat()}/{pid}.csv",
        df_raw.to_csv(index=False).encode("utf-8"),
        "text/csv",
    )

    # 2) Column detection (StatCan WDS varies by table but these are standard)
    cols = {c: c for c in df_raw.columns}
    date_col = "REF_DATE"
    geo_col = "GEO"
    value_col = "VALUE"

    # Optional product filter if present (keep All-items)
    prod_cols = [c for c in df_raw.columns if "product" in c.lower()]
    df = df_raw.copy()
    for pc in prod_cols:
        df = df[df[pc].astype(str).str.contains("All-items", case=False, na=False)]

    # 3) Whitelist CMAs + Canada fallback
    df[geo_col] = df[geo_col].astype(str)
    cmask = df[geo_col].isin(CMA_WHITELIST)
    df_pref = df[cmask]
    if df_pref.empty:
        # Fallback to national if present; otherwise keep whatever we have
        df_nat = df[df[geo_col].str.contains("Canada", case=False, na=False)]
        df_sel = df_nat if not df_nat.empty else df
    else:
        df_sel = df_pref

    # 4) Normalize
    tidy = (
        pd.DataFrame(
            {
                "city": df_sel[geo_col].where(df_sel[geo_col].notna(), "Canada"),
                "date": pd.to_datetime(df_sel[date_col], errors="coerce"),
                "metric": alias_metric,
                "value": pd.to_numeric(df_sel[value_col], errors="coerce"),
                "source": f"StatCan_{pid}",
            }
        )
        .dropna(subset=["date", "value"])
        .assign(date=month_floor(lambda s=...: s["date"]) if False else month_floor)
    )

    # month_floor utility expects a Series, so do it explicitly:
    tidy["date"] = month_floor(tidy["date"])

    # 5) Idempotent upsert
    base.write_metrics_upsert(tidy, ctx)

    # Optional: snapshot tidy for auditing
    put_raw_bytes(
        ctx,
        f"{ctx.s3_raw_prefix}/statcan/{ctx.run_date.isoformat()}/{pid}.tidy.csv",
        tidy.to_csv(index=False).encode("utf-8"),
        "text/csv",
    )

    return tidy


# you mentioned this exists

DEFAULT_SOURCE = "StatCan"


def _normalize_statcan(
    df: pd.DataFrame, metric_name: str, city_col_present: bool
) -> pd.DataFrame:
    """
    Normalize StatCan CSV into metrics table shape:
    metric, city, date, value, source
    """
    # Canonicalize expected columns, tolerate column-case variations
    cols = {c.upper(): c for c in df.columns}
    if "REF_DATE" not in cols or "VALUE" not in cols:
        raise ValueError("StatCan CSV missing REF_DATE and/or VALUE columns")

    date_col = cols["REF_DATE"]
    value_col = cols["VALUE"]
    geo_col = cols.get("GEO")

    out = pd.DataFrame(
        {
            "metric": metric_name,
            "city": df[geo_col]
            if (city_col_present and geo_col is not None)
            else "Canada",
            "date": pd.to_datetime(df[date_col], errors="coerce"),
            "value": pd.to_numeric(df[value_col], errors="coerce"),
            "source": DEFAULT_SOURCE,
        }
    )

    # Drop null dates/values; StatCan often has footers/aggregates
    out = out.dropna(subset=["date", "value"])
    # Keep only date and value granularity (monthly/quarterly/annual)
    out["date"] = out["date"].dt.date
    return out


def load_statcan_table(
    pid: str, metric_name: Optional[str], engine, schema: str = "public"
) -> pd.DataFrame:
    """
    Download a StatCan table by PID, normalize, and UPSERT to metrics.

    If metric_name is None, derive metric as f"StatCan_{pid}".
    Returns the normalized DataFrame actually upserted.
    """
    content = download_table_csv(pid)  # bytes-like
    df = pd.read_csv(BytesIO(content))

    # If GEO column exists, map to city; else "Canada"
    city_col_present = any(c.upper() == "GEO" for c in df.columns)
    metric = metric_name or f"StatCan_{pid}"

    tidy = _normalize_statcan(df, metric, city_col_present)
    base.write_metrics_upsert(tidy, engine, schema=schema)
    return tidy


def load_many(
    pids: Iterable[str],
    metric_names: Optional[Dict[str, str]],
    engine,
    schema: str = "public",
) -> pd.DataFrame:
    """
    Convenience: load multiple PIDs. metric_names maps pid->metric label.
    Returns concatenated normalized DataFrame for all.
    """
    frames = []
    for pid in pids:
        m = (metric_names or {}).get(pid)
        frames.append(load_statcan_table(pid, m, engine, schema))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
