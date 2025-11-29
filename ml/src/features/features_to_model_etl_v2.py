"""
features_to_model_etl_v2.py
----------------------------------------
Builds the model_features table from public.features.

Key improvements:
- Uses patched v10 feature schema
- Includes mortgage_rate, unemployment_rate, overnight_rate
- Scales per (city, property_type)
- Includes all model-required columns
- National fallback already applied in features_build step
- Compatible with ARIMA, Prophet, LSTM, LightGBM
"""

from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime, timezone
import pandas as pd
import numpy as np
import os

# -------------------------------
# Load DB ENV
# -------------------------------
load_dotenv(find_dotenv(usecwd=True))
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")
if not NEON_DATABASE_URL:
    raise RuntimeError("DATABASE_URL not found in .env")

engine = create_engine(NEON_DATABASE_URL, pool_pre_ping=True, future=True)


# -------------------------------
# Helper
# -------------------------------
def load_features():
    query = """
        SELECT
            date, city, property_type,
            hpi_benchmark,
            rent_avg_city,
            mortgage_rate, unemployment_rate, overnight_rate,
            population, median_income, migration_rate,
            gdp_growth, cpi_yoy,
            hpi_change_yoy, rent_change_yoy,
            source, created_at
        FROM public.features
        ORDER BY date, city, property_type;
    """
    df = pd.read_sql_query(query, engine)
    df["date"] = pd.to_datetime(df["date"])
    print("[INFO] Loaded", len(df), "rows from public.features")
    return df


# -------------------------------
# Normalize per (city, property_type)
# -------------------------------
def scale_group(df):
    numeric_cols = [
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

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.sort_values(["city", "property_type", "date"])

    df[numeric_cols] = df.groupby(["city", "property_type"])[numeric_cols].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-9)
    )

    return df


# -------------------------------
# Build model_features
# -------------------------------
def build_model_features():
    df = load_features()
    df = scale_group(df)

    df["etl_version"] = "features_to_model_etl_v2"
    df["processed_at"] = datetime.now(timezone.utc)

    print("[INFO] Final model_features shape:", df.shape)
    return df


# -------------------------------
# Write to DB
# -------------------------------
def write_to_db(df):
    cols = [
        "date",
        "city",
        "property_type",
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
        "etl_version",
        "processed_at",
    ]

    sql = text(f"""
        INSERT INTO public.model_features ({", ".join(cols)})
        VALUES ({", ".join(":" + c for c in cols)})
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

    batch_size = 3000
    total = len(df)

    with engine.begin() as conn:
        conn.exec_driver_sql("SELECT 1;")
        print("[DEBUG] Writing model_features...")

        for i in range(0, total, batch_size):
            batch = df.iloc[i : i + batch_size]
            conn.execute(sql, batch.to_dict(orient="records"))
            print(f"[WRITE] Batch {i // batch_size + 1} → {len(batch)} rows")

    print(f"[OK] Written {total} rows to public.model_features")


# -------------------------------
# Entrypoint
# -------------------------------
if __name__ == "__main__":
    print("[DEBUG] Starting features_to_model_etl_v2...")
    df = build_model_features()
    write_to_db(df)
    print("[DONE] ETL completed.")
