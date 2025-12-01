"""
ETL: Build model-ready features for forecasting
------------------------------------------------
Inputs:  public.features (already includes House, Town House, Apartment)
Output:  public.model_features (stable for ARIMA, Prophet, LSTM, LightGBM)

Key principles:
- pure z-score per (city, property_type)
- monthly continuity guaranteed
- correct YoY
- lag & rolling features
- composite macro & demographic signals
"""

from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
import pandas as pd
import numpy as np
import os
from datetime import datetime, timezone

# ----------------------------------------------------------
# Load DB
# ----------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)


# ----------------------------------------------------------
# Load features table
# ----------------------------------------------------------
def load_features():
    q = """
        SELECT
            date, city, property_type,
            hpi_benchmark, rent_avg_city,
            mortgage_rate, unemployment_rate, overnight_rate,
            population, median_income, migration_rate,
            gdp_growth, cpi_yoy,
            hpi_change_yoy, rent_change_yoy
        FROM public.features
        ORDER BY date, city, property_type;
    """
    df = pd.read_sql(q, engine)
    df["date"] = pd.to_datetime(df["date"])
    return df


# ----------------------------------------------------------
# Ensure monthly continuity for each (city, property_type)
# ----------------------------------------------------------
def enforce_continuity(df):
    all_dates = pd.date_range(df["date"].min(), df["date"].max(), freq="MS")
    out = []

    for (city, prop), g in df.groupby(["city", "property_type"]):
        g = g.set_index("date").reindex(all_dates)
        g["city"] = city
        g["property_type"] = prop

        g = g.reset_index().rename(columns={"index": "date"})
        out.append(g)

    df2 = pd.concat(out, ignore_index=True)
    return df2.sort_values(["city", "property_type", "date"])


# ----------------------------------------------------------
# Fill missing YoY
# ----------------------------------------------------------
def fill_yoy(df):
    df["hpi_benchmark"] = df["hpi_benchmark"].astype(float)
    df["rent_avg_city"] = df["rent_avg_city"].astype(float)

    df["hpi_change_yoy"] = (
        df.groupby(["city", "property_type"])["hpi_benchmark"].transform(
            lambda s: s.pct_change(12)
        )
        * 100
    )

    df["rent_change_yoy"] = (
        df.groupby(["city", "property_type"])["rent_avg_city"].transform(
            lambda s: s.pct_change(12)
        )
        * 100
    )

    return df


# ----------------------------------------------------------
# Compute z-score scaling per group
# ----------------------------------------------------------
def zscore_group(df, cols):
    for col in cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    def z(x):
        return (x - x.mean()) / (x.std() + 1e-9)

    df[cols] = df.groupby(["city", "property_type"])[cols].transform(z)
    return df


# ----------------------------------------------------------
# Composite signals
# ----------------------------------------------------------
def add_composites(df):
    df["macro_composite_z"] = df[
        [
            "mortgage_rate",
            "unemployment_rate",
            "overnight_rate",
            "gdp_growth",
            "cpi_yoy",
        ]
    ].mean(axis=1)

    df["demographics_composite_z"] = df[
        ["population", "median_income", "migration_rate"]
    ].mean(axis=1)

    return df


# -------------------------------
# FIX Z-SCORE COLUMNS
# -------------------------------
def add_zscore_patch(df):
    # hpi_z and rent_z
    df["hpi_z"] = df.groupby(["city", "property_type"])["hpi_benchmark"].transform(
        lambda s: (s - s.mean()) / (s.std() + 1e-9)
    )

    df["rent_z"] = df.groupby(["city", "property_type"])["rent_avg_city"].transform(
        lambda s: (s - s.mean()) / (s.std() + 1e-9)
    )

    # Now z-score the composite signals
    df["macro_composite_z"] = df.groupby(["city", "property_type"])[
        "macro_composite_z"
    ].transform(lambda s: (s - s.mean()) / (s.std() + 1e-9))

    df["demographics_composite_z"] = df.groupby(["city", "property_type"])[
        "demographics_composite_z"
    ].transform(lambda s: (s - s.mean()) / (s.std() + 1e-9))

    return df


# ----------------------------------------------------------
# Lag & rolling features
# ----------------------------------------------------------
def add_lag_roll(df):
    df = df.sort_values(["city", "property_type", "date"])

    group = df.groupby(["city", "property_type"])

    df["lag_1"] = group["hpi_benchmark"].shift(1)
    df["lag_3"] = group["hpi_benchmark"].shift(3)
    df["lag_6"] = group["hpi_benchmark"].shift(6)
    df["lag_12"] = group["hpi_benchmark"].shift(12)

    df["roll_3"] = (
        group["hpi_benchmark"].rolling(3).mean().reset_index(level=[0, 1], drop=True)
    )
    df["roll_6"] = (
        group["hpi_benchmark"].rolling(6).mean().reset_index(level=[0, 1], drop=True)
    )
    df["roll_12"] = (
        group["hpi_benchmark"].rolling(12).mean().reset_index(level=[0, 1], drop=True)
    )

    return df


# ----------------------------------------------------------
# Main ETL
# ----------------------------------------------------------
def build_model_features():
    df = load_features()
    df = enforce_continuity(df)
    df = fill_yoy(df)

    # z-score scaling inputs
    zcols = [
        "hpi_benchmark",
        "rent_avg_city",
        "mortgage_rate",
        "unemployment_rate",
        "overnight_rate",
        "population",
        "median_income",
        "migration_rate",
        "gdp_growth",
        "cpi_yoy",
        "hpi_change_yoy",
        "rent_change_yoy",
    ]
    df = zscore_group(df, zcols)

    df = add_composites(df)
    df = add_lag_roll(df)

    df["etl_version"] = "model_features_etl_v1"
    df["processed_at"] = datetime.now(timezone.utc)

    return df


# ----------------------------------------------------------
# UPSERT to DB
# ----------------------------------------------------------
def write_to_db(df):
    cols = df.columns.tolist()
    placeholders = ", ".join(":" + c for c in cols)
    sql = text(f"""
        INSERT INTO public.model_features ({", ".join(cols)})
        VALUES ({placeholders})
        ON CONFLICT (date, city, property_type)
        DO UPDATE SET
            hpi_benchmark = EXCLUDED.hpi_benchmark,
            rent_avg_city = EXCLUDED.rent_avg_city,
            mortgage_rate = EXCLUDED.mortgage_rate,
            unemployment_rate = EXCLUDED.unemployment_rate,
            overnight_rate = EXCLUDED.overnight_rate,
            population = EXCLUDED.population,
            median_income = EXCLUDED.median_income,
            migration_rate = EXCLUDED.migration_rate,
            gdp_growth = EXCLUDED.gdp_growth,
            cpi_yoy = EXCLUDED.cpi_yoy,
            hpi_change_yoy = EXCLUDED.hpi_change_yoy,
            rent_change_yoy = EXCLUDED.rent_change_yoy,
            etl_version = EXCLUDED.etl_version,
            processed_at = EXCLUDED.processed_at;
    """)

    with engine.begin() as conn:
        batch = 3000
        for i in range(0, len(df), batch):
            part = df.iloc[i : i + batch]
            conn.execute(sql, part.to_dict(orient="records"))

    print("[OK] model_features updated.")


# ----------------------------------------------------------
# Entrypoint
# ----------------------------------------------------------
if __name__ == "__main__":
    df = build_model_features()
    print("Final shape:", df.shape)
    write_to_db(df)
