import io
import os
import datetime as dt
import pandas as pd
import requests
from etl.base import Context, write_df


def run(ctx: Context):
    # 1) download raw (placeholder URL; plug actual source)
    url = "https://example.crea/download.csv"  # TODO: replace with real source
    r = requests.get(url, timeout=60)
    r.raise_for_status()

    # 2) raw snapshot to MinIO-like path (local disk in MVP; MinIO integration later)
    raw_bytes = r.content
    raw_df = pd.read_csv(io.BytesIO(raw_bytes))

    # 3) tidy transform -> house_price_index
    tidy = raw_df.rename(
        columns={"City": "city", "Date": "date", "BenchmarkPrice": "index_value"}
    ).assign(measure="benchmark_price", source="CREA")
    tidy["date"] = pd.to_datetime(tidy["date"]).dt.date
    tidy = tidy[["city", "date", "index_value", "measure", "source"]].dropna()

    # 4) load to Postgres
    write_df(tidy, "house_price_index", ctx)
