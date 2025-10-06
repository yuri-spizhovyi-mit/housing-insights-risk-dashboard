import pandas as pd
from . import base
from .statcan_wds import download_table_csv
from .utils import canonical_geo

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
    from .utils import canonical_geo

    df[geo_col] = df[geo_col].apply(lambda x: canonical_geo(x) or "OTHER")

    tidy_full = pd.DataFrame(
        {
            "metric": "CMHC_Series",
            "city": df[geo_col].astype("string").str.strip(),
            "date": base.month_floor(df[date_col]),
            "value": pd.to_numeric(df[val_col], errors="coerce"),
            "source": "StatCan/CMHC",
        }
    ).dropna(subset=["city", "date", "value"])

    # Keep only our target geographies; if empty, fall back to national or unfiltered
    tidy = tidy_full[
        tidy_full["city"].isin(["Kelowna", "Vancouver", "Toronto", "Canada"])
    ]
    if tidy.empty:
        fallback = tidy_full[tidy_full["city"] == "Canada"]
        tidy = fallback if not fallback.empty else tidy_full

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


if __name__ == "__main__":
    from datetime import date

    ctx = base.Context(run_date=date.today())
    run(ctx)
    print("[DEBUG] Finished.")
