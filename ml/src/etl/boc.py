import io
import pandas as pd
import requests
from .base import Context, write_df

# NOTE: Replace with actual Bank of Canada CSV endpoint(s)
BOC_URL = "https://example.com/boc_rates.csv"


def run(ctx: Context):
    r = requests.get(BOC_URL, timeout=60)
    r.raise_for_status()
    raw_df = pd.read_csv(io.BytesIO(r.content))

    tidy = raw_df.rename(
        columns={"Date": "date", "Series": "metric", "Value": "value"}
    ).assign(source="BoC", city=None)
    tidy["date"] = pd.to_datetime(tidy["date"]).dt.date
    tidy = tidy[["city", "date", "metric", "value", "source"]].dropna(
        subset=["date", "metric", "value"]
    )

    write_df(tidy, "metrics", ctx)
