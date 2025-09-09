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
    df = download_table_csv(PID_CPI)
    put_raw_bytes(
        ctx,
        f"{ctx.s3_raw_prefix}/statcan/{ctx.run_date.isoformat()}/{PID_CPI}.csv",
        df.to_csv(index=False).encode(),
        "text/csv",
    )

    # Common columns: REF_DATE, GEO, DGUID, UOM, UOM_ID, SCALAR_ID, VECTOR, COORDINATE, VALUE, STATUS, SYMBOL, DECIMALS
    # Filter to All-items only, CMAs of interest
    # There is usually a 'Products and product groups' dimension; the 'All-items' selection varies—look for a column named 'Products and product groups' or 'Products'
    prod_col = next((c for c in df.columns if "product" in c.lower()), None)
    geo_col = "GEO"
    value_col = "VALUE"

    sel = df
    if prod_col:
        sel = sel[sel[prod_col].str.contains("All-items", case=False, na=False)]

    # Prefer CMAs in whitelist, but if that yields nothing, fallback to national/any
    preferred = (
        sel[sel[geo_col].isin(CMA_WHITELIST)]
        if geo_col in sel.columns
        else sel.iloc[0:0]
    )
    if not preferred.empty:
        sel2 = preferred
    else:
        # fallback: national if available; else keep whatever we have
        if geo_col in sel.columns:
            national = sel[sel[geo_col].str.contains("Canada", case=False, na=False)]
            sel2 = national if not national.empty else sel
        else:
            sel2 = sel

    sel2 = sel2.rename(columns={"REF_DATE": "date"})
    if geo_col in sel2.columns:
        sel2 = sel2.rename(columns={geo_col: "city"})
    else:
        sel2 = sel2.assign(city="Canada")
    sel2 = sel2.rename(columns={value_col: "value"}).assign(
        metric="cpi_all_items", source="StatCan"
    )
    sel2["date"] = month_floor(sel2["date"])
    out = sel2[["city", "date", "metric", "value", "source"]].dropna(subset=["value"])
    base.write_df(out, "metrics", ctx)


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
