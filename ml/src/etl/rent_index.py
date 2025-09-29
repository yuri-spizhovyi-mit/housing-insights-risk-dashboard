# ml/src/etl/rent_index.py
import pandas as pd
from datetime import datetime
from sqlalchemy import text
from ml.utils.db import get_engine


def fetch_rent_data(ctx):
    """Fetch rental listings from listings_raw (or external API)."""
    engine = get_engine(ctx)
    query = """
        SELECT date_posted, city, price, bedrooms
        FROM listings_raw
        WHERE listing_type = 'Rental'
    """
    return pd.read_sql(query, engine)


def transform_rent_index(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate monthly rent metrics."""
    df["month"] = pd.to_datetime(df["date_posted"]).dt.to_period("M").dt.to_timestamp()
    agg = (
        df.groupby(["city", "month"])
        .apply(
            lambda g: pd.Series(
                {
                    "median_rent_apartment_1br": g[g["bedrooms"] == 1][
                        "price"
                    ].median(),
                    "median_rent_apartment_2br": g[g["bedrooms"] == 2][
                        "price"
                    ].median(),
                    "median_rent_apartment_3br": g[g["bedrooms"] == 3][
                        "price"
                    ].median(),
                    "active_rental_count": len(g),
                    "avg_rental_days": None,  # TODO: requires scraped "days_active"
                    "index_value": g["price"].median(),  # TODO: normalize later
                }
            )
        )
        .reset_index()
    )
    agg.rename(columns={"month": "date"}, inplace=True)
    return agg


def write_rent_index(df, ctx):
    engine = get_engine(ctx)
    with engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(
                text("""
                INSERT INTO rent_index 
                (date, city, index_value, median_rent_apartment_1br, 
                 median_rent_apartment_2br, median_rent_apartment_3br,
                 active_rental_count, avg_rental_days)
                VALUES (:date, :city, :index_value, :r1, :r2, :r3, :count, :days)
                ON CONFLICT (date, city) DO UPDATE
                SET index_value = EXCLUDED.index_value,
                    median_rent_apartment_1br = EXCLUDED.median_rent_apartment_1br,
                    median_rent_apartment_2br = EXCLUDED.median_rent_apartment_2br,
                    median_rent_apartment_3br = EXCLUDED.median_rent_apartment_3br,
                    active_rental_count = EXCLUDED.active_rental_count,
                    avg_rental_days = EXCLUDED.avg_rental_days
            """),
                {
                    "date": row["date"],
                    "city": row["city"],
                    "index_value": row["index_value"],
                    "r1": row["median_rent_apartment_1br"],
                    "r2": row["median_rent_apartment_2br"],
                    "r3": row["median_rent_apartment_3br"],
                    "count": row["active_rental_count"],
                    "days": row["avg_rental_days"],
                },
            )


def run(ctx):
    df = fetch_rent_data(ctx)
    agg = transform_rent_index(df)
    write_rent_index(agg, ctx)
