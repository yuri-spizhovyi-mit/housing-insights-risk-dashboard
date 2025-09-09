# ml/src/etl/cmhc.py
import pandas as pd
from . import base
from .statcan_wds import download_table_csv

# CMHC table (example): change PID if you need a different one later
PID = "3410014501"  # your current PID from the test


def _tidy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map CMHC/StatCan table to metrics:
      columns: metric, city, date, value, source='StatCan/CMHC'
    """
    # normalize headers
    df = df.rename(columns={c: str(c).strip() for c in df.columns})

    # Common StatCan shapes include: REF_DATE, GEO, VALUE
    date_col = next(
        (c for c in df.columns if c.lower() in ("ref_date", "date", "period")), None
    )
    geo_col = next(
        (c for c in df.columns if c.lower() in ("geo", "geography", "city", "cma")),
        None,
    )
    val_col = next(
        (c for c in df.columns if c.lower() in ("value", "val", "obs_value")), None
    )

    if not (date_col and geo_col and val_col):
        # minimal fallback: return empty
        return pd.DataFrame(columns=["metric", "city", "date", "value", "source"])

    tidy = pd.DataFrame(
        {
            "metric": "CMHC_Rent"
            if "rent" in " ".join(df.columns).lower()
            else "CMHC_Series",
            "city": df[geo_col].astype("string").str.strip(),
            "date": base.month_floor(df[date_col]),
            "value": pd.to_numeric(df[val_col], errors="coerce"),
            "source": "StatCan/CMHC",
        }
    )

    # clean
    tidy = tidy.dropna(subset=["city", "date", "value"])
    return tidy


def run(ctx: base.Context):
    # 1) download via StatCan WDS (with robust headers/retry)
    df = download_table_csv(PID, lang="en")

    # 2) snapshot raw -> MinIO
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    key = f"{ctx.s3_raw_prefix}/cmhc/{ctx.run_date.isoformat()}/{PID}.csv"
    base.put_raw_bytes(ctx, key, csv_bytes, "text/csv")

    # 3) tidy to metrics shape
    tidy = _tidy(df).drop_duplicates(subset=["metric", "city", "date"])

    # 4) UPSERT to metrics (idempotent for re-runs/tests)
    base.write_metrics_upsert(tidy, ctx)
