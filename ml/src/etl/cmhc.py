import pandas as pd
from . import base
from .statcan_wds import download_table_csv

# Use either table number OR 8-digit ProductId:
PID = "34-10-0145-01"  # will normalize to '34100145'


def _tidy(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={c: str(c).strip() for c in df.columns})
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
        return pd.DataFrame(columns=["metric", "city", "date", "value", "source"])

    tidy = pd.DataFrame(
        {
            "metric": "CMHC_Series",
            "city": df[geo_col].astype("string").str.strip(),
            "date": base.month_floor(df[date_col]),
            "value": pd.to_numeric(df[val_col], errors="coerce"),
            "source": "StatCan/CMHC",
        }
    ).dropna(subset=["city", "date", "value"])

    return tidy


def run(ctx: base.Context):
    df = download_table_csv(PID, lang="en")  # normalization happens inside
    # snapshot raw
    base.put_raw_bytes(
        ctx,
        f"{ctx.s3_raw_prefix}/cmhc/{ctx.run_date.isoformat()}/{PID}.csv",
        df.to_csv(index=False).encode("utf-8"),
        "text/csv",
    )
    # tidy + UPSERT
    tidy = _tidy(df).drop_duplicates(subset=["metric", "city", "date"])
    # Use generic writer so tests can monkeypatch and capture output
    base.write_df(tidy, "metrics", ctx)
