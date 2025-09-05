import io
import pandas as pd
import requests
from .base import Context, write_df

# NOTE: Replace the URL below with an actual CREA/HPI source
CREA_URL = "https://example.com/crea_hpi.csv"


def run(ctx: Context):
    r = requests.get(CREA_URL, timeout=60)
    r.raise_for_status()
    raw_df = pd.read_csv(io.BytesIO(r.content))

    tidy = raw_df.rename(
        columns={"City": "city", "Date": "date", "BenchmarkPrice": "index_value"}
    ).assign(measure="benchmark_price", source="CREA")
    tidy["date"] = pd.to_datetime(tidy["date"]).dt.date
    tidy = tidy[["city", "date", "index_value", "measure", "source"]].dropna()

    write_df(tidy, "house_price_index", ctx)
