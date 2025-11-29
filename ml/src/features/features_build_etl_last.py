"""
features_build_etl_v1.py
------------------------------------------------------------
Rebuilds the FULL v1-compatible feature store with:
- Raw features (HPI, Rent, Macro, Demographics)
- Legacy YoY
- Legacy MinMax scaled features
- Composite macro_scaled + demographics_scaled
- property_type_id as an INPUT FEATURE
- ONE unified timeseries per city (NO splitting by property type)

Outputs → public.model_features (overwrites table)
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
# PROPERTY TYPE → ID (Option A)
# ----------------------------------------------------------
PROPERTY_TYPE_MAP = {
    "Apartment": 0,
    "House": 1,
    "Town House": 2,
}

# ----------------------------------------------------------
# LOAD v10 base data (your patched features table)
# ----------------------------------------------------------
def load_raw():
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
# Legacy YoY (v1 formula)
# ----------------------------------------------------------
def compute_yoy(df):
    df = df.sort_values(["city", "date"])
    df["hpi_change_yoy"] = df.groupby("city")["hpi_benchmark"].pct_change(12)
    df["rent_change_yoy"] = df.groupby("city")["rent_avg_city"].pct_change(12)
    return df

# ----------------------------------------------------------
# MinMax scaler
# ----------------------------------------------------------
def minmax(x):
    mn, mx = x.min(), x.max()
    if mn == mx:
        return x * 0
    return (x - mn) / (mx - mn)

# ----------------------------------------------------------
# Compute v1 scaled features
# ----------------------------------------------------------
def compute_scaled(df):
    df = df.sort_values(["city", "date"])

    # Individual MinMax scaled (legacy behavior)
    df["hpi_benchmark_scaled"] = df.groupby("city")["hpi_benchmark"].transform(minmax)
    df["rent_avg_city_scaled"] = df.groupby("city")["rent_avg_city"].transform(minmax)
    df["mortgage_rate_scaled"] = df.groupby("city")["mortgage_rate"].transform(minmax)
    df["unemployment_rate_scaled"] = df.groupby("city")["unemployment_rate"].transform(minmax)
    df["overnight_rate_scaled"] = df.groupby("city")["overnight_rate"].transform(minmax)
    df["population_scaled"] = df.groupby("city")["population"].transform(minmax)
    df["median_income_scaled"] = df.groupby("city")["median_income"].transform(minmax)
    df["migration_rate_scaled"] = df.groupby("city")["migration_rate"].transform(minmax)
    df["gdp_growth_scaled"] = df.groupby("city")["gdp_growth"].transform(minmax)
    df["cpi_yoy_scaled"] = df.groupby("city")["cpi_yoy"].transform(minmax)

    # Composite macro
    macro_cols = ["mortgage_rate", "unemployment_rate", "overnight_rate", "gdp_growth", "cpi_yoy"]
    df["macro_mean_tmp"] = df[macro_cols].mean(axis=1)
    df["macro_scaled"] = df.groupby("city")["macro_mean_tmp"].transform(minmax)
    df.drop(columns=["macro_mean_tmp"], inplace=True)

    # Composite demographics
    demo_cols = ["population", "median_income", "migration_rate"]
    df["demo_mean_tmp"] = df[demo_cols].mean(axis=1)
    df["demographics_scaled"] = df.groupby("city")["demo_mean_tmp"].transform(minmax)
    df.drop(columns=["demo_mean_tmp"], inplace=True)

    # Legacy shorthand
    df["hpi_scaled"] = df["hpi_benchmark_scaled"]
    df["rent_scaled"] = df["rent_avg_city_scaled"]

    return df

# ----------------------------------------------------------
# Build unified features per city
# ----------------------------------------------------------
def build_features():
    df = load_raw()

    # property_type → id
    df["property_type_id"] = df["property_type"].map(PROPERTY_TYPE_MAP)

    # unify timeseries by city (NO property_type splitting)
    df = df.sort_values(["city", "date"])
    df = df.groupby(["city", "date"]).agg({
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
        "property_type_id": "max"
    }).reset_index()

    # YoY
    df = compute_yoy(df)

    # scaled features
    df = compute_scaled(df)

    df["features_version"] = "v1_legacy_with_property_type"
    df["created_at"] = datetime.now(timezone.utc)

    return df

# ----------------------------------------------------------
# Write to DB (overwrite)
# ----------------------------------------------------------
def write_to_db(df):
    print("[INFO] Overwriting public.model_features ...")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE public.model_features;"))

        cols = list(df.columns)
        sql = text(f"""
            INSERT INTO public.model_features ({", ".join(cols)})
            VALUES ({", ".join(":"+c for c in cols)});
        """)

        batch = 3000
        for i in range(0, len(df), batch):
            part = df.iloc[i:i+batch]
            conn.execute(sql, part.to_dict(orient="records"))
            print(f"  Inserted rows {i}–{i+len(part)}")

    print(f"[DONE] Inserted {len(df)} rows.")

# ----------------------------------------------------------
if __name__ == "__main__":
    df = build_features()
    write_to_db(df)
