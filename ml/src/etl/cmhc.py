import pandas as pd
from .base import Context, write_df, month_floor, put_raw_bytes
from .statcan_wds import download_table_csv

PID = "3410014501"  # 34-10-0145-01


def run(ctx: Context):
    df = download_table_csv(PID)
    # snapshot CSV too (optional)
    csv_bytes = df.to_csv(index=False).encode()
    key = f"{ctx.s3_raw_prefix}/cmhc/{ctx.run_date.isoformat()}/{PID}.csv"
    put_raw_bytes(ctx, key, csv_bytes, "text/csv")

    # Typical columns: REF_DATE, GEO, VALUE, ...
    tidy = df.rename(
        columns={"REF_DATE": "date", "VALUE": "value", "GEO": "geo"}
    ).assign(metric="mortgage_5y_conventional", source="StatCan-CMHC")
    tidy["date"] = month_floor(tidy["date"])
    tidy["city"] = None  # national series
    tidy = tidy.rename(columns={"geo": "city"})  # leave as None/Canada if needed
    tidy["city"] = "Canada"
    tidy = tidy[["city", "date", "metric", "value", "source"]].dropna(subset=["value"])
    write_df(tidy, "metrics", ctx)
