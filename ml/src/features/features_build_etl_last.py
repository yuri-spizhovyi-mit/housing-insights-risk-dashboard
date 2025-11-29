"""
features_build_etl_v1_legacy_with_property_type.py
----------------------------------------------------
Rebuilds the ORIGINAL v1-style feature store with
- raw features
- v1 YoY
- v1 MinMax scaling
- macro_scaled
- demographics_scaled
- property_type_id
- unified per-city monthly time series (no splitting)

Outputs → public.model_features
Schema matches the SQL you recreated.
"""

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from datetime import datetime, timezone
from dotenv import load_dotenv, find_dotenv
import os

# ----------------------------------------------------------
# DB INIT
# ----------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)


# ----------------------------------------------------------
# PROPERTY TYPE → ID mapping
# ----------------------------------------------------------
PROPERTY_TYPE_MAP = {
    "Apartment": 0,
    "House": 1,
    "Town House": 2,
}


# ----------------------------------------------------------
# LOAD RAW BASE TABLE (your v10 patched features table)
# ----------------------------------------------------------
def load_raw_features():
    query = """
        SELECT
            date,
            city,
            property_type,
            hpi_benchmark,
            rent_avg_city,
            mortgage_rate,
            unemployment_rate,
            overnight_rate,
            population,
            median_income,
            migration_rate,
            gdp_growth,
            cpi_yoy
        FROM public.features
        ORDER BY date, city;
    """
    df = pd.read_sql_query(query, engine)
    df["date"] = pd.to_datetime(df["date"])
    return df


# ----------------------------------------------------------
# v1 YoY computation
# ----------------------------------------------------------
def compute_yoy(df):
    df = df.sort_values(["city", "date"])
    df["hpi_change_yoy"] = df.groupby("city")["hpi_benchmark"].pct_change(periods=12)
    df["rent_change_yoy"] = df.groupby("city")["rent_avg_city"].pct_change(periods=12)
    return df


# ----------------------------------------------------------
# v1 MinMax scaling (0–1 normalization)
# ----------------------------------------------------------
def minmax(series):
    if series.max() == series.min():
        return (series - series.min()) * 0
    return (series - series.min()) / (series.max() - series.min())


def compute_scaled(df):
    df = df.sort_values(["city", "date"])

    # HPI
    df["hpi_scaled"] = df.groupby("city")["hpi_benchmark"].transform(minmax)

    # RENT
    df["rent_scaled"] = df.groupby("city")["rent_avg_city"].transform(minmax)

    # MACRO composite scaling
    macro_cols = [
        "mortgage_rate",
        "unemployment_rate",
        "overnight_rate",
        "gdp_growth",
        "cpi_yoy",
    ]
    df["macro_mean_tmp"] = df[macro_cols].mean(axis=1)
    df["macro_scaled"] = df.groupby("city")["macro_mean_tmp"].transform(minmax)
    df.drop(columns=["macro_mean_tmp"], inplace=True)

    # DEMOGRAPHICS composite scaling
    demo_cols = [
        "population",
        "median_income",
        "migration_rate",
    ]
    df["demo_mean_tmp"] = df[demo_cols].mean(axis=1)
    df["demographics_scaled"] = df.groupby("city")["demo_mean_tmp"].transform(minmax)
    df.drop(columns=["demo_mean_tmp"], inplace=True)

    return df


# ----------------------------------------------------------
# build unified per-city features
# ----------------------------------------------------------
def build_features():
    df = load_raw_features()

    # convert property_type → property_type_id
    df["property_type_id"] = df["property_type"].map(PROPERTY_TYPE_MAP)

    # because we DO NOT SPLIT series,
    # we aggregate property_type_id by taking the mode per (city, date)
    df = df.sort_values(["city", "date"])
    df = (
        df.groupby(["city", "date"])
        .agg(
            {
                "hpi_benchmark": "mean",
                "rent_avg_city": "mean",
                "mortgage_rate": "first",
                "unemployment_rate": "first",
                "overnight_rate": "first",
                "population": "first",
                "median_income": "first",
                "migration_rate": "first",
                "gdp_growth": "first",
                "cpi_yoy": "first",
                "property_type_id": "max",  # simple encoding – legacy-compatible
            }
        )
        .reset_index()
    )

    # YOY (legacy formula)
    df = compute_yoy(df)

    # scaled features
    df = compute_scaled(df)

    df["features_version"] = "v1_legacy_property_type"
    df["created_at"] = datetime.now(timezone.utc)

    return df


# ----------------------------------------------------------
# write final dataset to DB
# ----------------------------------------------------------
def write_to_db(df):
    print("[INFO] Overwriting public.model_features ...")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE public.model_features;"))

        insert_cols = list(df.columns)
        sql = text(f"""
            INSERT INTO public.model_features ({", ".join(insert_cols)})
            VALUES ({", ".join(":" + c for c in insert_cols)});
        """)

        batch = 3000
        for i in range(0, len(df), batch):
            part = df.iloc[i : i + batch]
            conn.execute(sql, part.to_dict(orient="records"))
            print(f"  inserted rows {i}–{i + len(part)}")

    print(f"[DONE] Inserted {len(df)} rows into model_features.")


# ----------------------------------------------------------
if __name__ == "__main__":
    df = build_features()
    write_to_db(df)
