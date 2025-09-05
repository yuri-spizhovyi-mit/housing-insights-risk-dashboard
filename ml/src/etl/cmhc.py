import io
import pandas as pd
import requests
from .base import Context, write_df

# NOTE: Replace the URL below with an actual CMHC/Rentals.ca source
CMHC_URL = "https://example.com/cmhc_rents.csv"


def run(ctx: Context):
    r = requests.get(CMHC_URL, timeout=60)
    r.raise_for_status()
    raw_df = pd.read_csv(io.BytesIO(r.content))

    tidy = raw_df.rename(
        columns={
            "City": "city",
            "Date": "date",
            "MedianRent": "median_rent",
            "BedroomType": "bedroom_type",
        }
    ).assign(source="CMHC")
    tidy["date"] = pd.to_datetime(tidy["date"]).dt.date
    tidy = tidy[["city", "date", "bedroom_type", "median_rent", "source"]].dropna()

    write_df(tidy, "rents", ctx)
