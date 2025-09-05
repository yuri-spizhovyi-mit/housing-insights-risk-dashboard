import io
import pandas as pd
import requests
from .base import Context, write_df

# NOTE: Replace with actual StatCan series endpoints or CSV extracts
STATCAN_URL = "https://example.com/statcan_metrics.csv"


def run(ctx: Context):
    r = requests.get(STATCAN_URL, timeout=60)
    r.raise_for_status()
    raw_df = pd.read_csv(io.BytesIO(r.content))

    tidy = raw_df.rename(
        columns={"Date": "date", "Metric": "metric", "Value": "value", "City": "city"}
    ).assign(source="StatCan")
    tidy["date"] = pd.to_datetime(tidy["date"]).dt.date
    tidy = tidy[["city", "date", "metric", "value", "source"]].dropna()

    write_df(tidy, "metrics", ctx)
