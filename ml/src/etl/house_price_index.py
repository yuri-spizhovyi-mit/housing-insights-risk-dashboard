# ml/src/etl/house_price_index.py
import pandas as pd
from sqlalchemy import text
from ml.src.etl.db import get_engine


def fetch_sales_data(ctx):
    engine = get_engine(ctx)
    return pd.read_sql(
        """
        SELECT date_posted, city, price, property_type
        FROM listings_raw
        WHERE listing_type = 'Sale'
    """,
        engine,
    )


def transform_house_index(df):
    df["month"] = pd.to_datetime(df["date_posted"]).dt.to_period("M").dt.to_timestamp()
    agg = (
        df.groupby(["city", "month"])
        .apply(
            lambda g: pd.Series(
                {
                    "median_price_house": g[g["property_type"] == "House"][
                        "price"
                    ].median(),
                    "median_price_condo": g[g["property_type"] == "Condo"][
                        "price"
                    ].median(),
                    "active_listings_count": len(g),
                    "avg_listing_days": None,  # TODO: requires lifespan info
                    "index_value": g["price"].median(),  # TODO: normalize base=100
                }
            )
        )
        .reset_index()
    )
    agg.rename(columns={"month": "date"}, inplace=True)
    return agg


def write_house_index(df, ctx):
    engine = get_engine(ctx)
    with engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(
                text("""
                INSERT INTO house_price_index
                (date, city, index_value, median_price_house, median_price_condo,
                 active_listings_count, avg_listing_days)
                VALUES (:date, :city, :idx, :h, :c, :count, :days)
                ON CONFLICT (date, city) DO UPDATE
                SET index_value = EXCLUDED.index_value,
                    median_price_house = EXCLUDED.median_price_house,
                    median_price_condo = EXCLUDED.median_price_condo,
                    active_listings_count = EXCLUDED.active_listings_count,
                    avg_listing_days = EXCLUDED.avg_listing_days
            """),
                {
                    "date": row["date"],
                    "city": row["city"],
                    "idx": row["index_value"],
                    "h": row["median_price_house"],
                    "c": row["median_price_condo"],
                    "count": row["active_listings_count"],
                    "days": row["avg_listing_days"],
                },
            )


def run(ctx):
    df = fetch_sales_data(ctx)
    agg = transform_house_index(df)
    write_house_index(agg, ctx)
