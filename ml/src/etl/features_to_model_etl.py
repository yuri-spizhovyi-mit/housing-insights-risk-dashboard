"""
ETL: Prepare model-ready dataset from public.features
-----------------------------------------------------
Input : public.features
Output: public.model_features
Purpose: Clean, normalize, and export standardized features for ML models
"""

from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime
import pandas as pd
import numpy as np
import os

# ---------------------------------------------------------------------
# 1. Connect to Neon
# ---------------------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")
if not NEON_DATABASE_URL:
    raise RuntimeError("NEON_DATABASE_URL not found in .env")

engine = create_engine(NEON_DATABASE_URL, pool_pre_ping=True, future=True)
print("[DEBUG] Connected to Neon via .env")

# ---------------------------------------------------------------------
# 2. Load data from features table
# ---------------------------------------------------------------------
def load_features() -> pd.DataFrame:
    query = """
        SELECT
            date, city,
            hpi_benchmark, rent_avg_city,
            mortgage_rate, unemployment_rate, overnight_rate,
            population, median_income,
            gdp_growth, cpi_yoy
        FROM public.features
        ORDER BY city, date;
    """
    df = pd.read_sql_query(query, engine)
    print(f"[INFO] Loaded {len(df):,} rows from public.features")
    return df

# ---------------------------------------------------------------------
# 3. Clean and normalize
# ---------------------------------------------------------------------
def transform(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Ensure date format and sort
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df.sort_values(["city", "date"], inplace=True)

    # Fill missing numeric values with last known value (forward-fill)
    num_cols = df.select_dtypes(include=[np.number]).columns
    df[num_cols] = df.groupby("city")[num_cols].ffill().bfill()

    # Optional normalization (0–1 scaling)
    for col in num_cols:
        if df[col].notna().any():
            min_val, max_val = df[col].min(), df[col].max()
            if pd.notna(min_val) and pd.notna(max_val) and max_val != min_val:
                df[col + "_scaled"] = (df[col] - min_val) / (max_val - min_val)
            else:
                df[col + "_scaled"] = 0.0

    print(f"[INFO] Added normalized columns ({len(num_cols)} scaled features)")
    return df

# ---------------------------------------------------------------------
# 4. Write cleaned data to public.model_features
# ---------------------------------------------------------------------
def write_to_db(df: pd.DataFrame):
    # Create table if not exists
    create_sql = """
        CREATE TABLE IF NOT EXISTS public.model_features (
            date DATE NOT NULL,
            city TEXT NOT NULL,
            hpi_benchmark NUMERIC(14,2),
            rent_avg_city NUMERIC(14,2),
            mortgage_rate NUMERIC(6,3),
            unemployment_rate NUMERIC(6,3),
            overnight_rate NUMERIC(6,3),
            population BIGINT,
            median_income NUMERIC(14,2),
            gdp_growth NUMERIC(6,3),
            cpi_yoy NUMERIC(6,3),
            -- Scaled features
            hpi_benchmark_scaled NUMERIC(8,5),
            rent_avg_city_scaled NUMERIC(8,5),
            mortgage_rate_scaled NUMERIC(8,5),
            unemployment_rate_scaled NUMERIC(8,5),
            overnight_rate_scaled NUMERIC(8,5),
            population_scaled NUMERIC(8,5),
            median_income_scaled NUMERIC(8,5),
            gdp_growth_scaled NUMERIC(8,5),
            cpi_yoy_scaled NUMERIC(8,5),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (date, city)
        );
    """
    with engine.begin() as conn:
        conn.execute(text(create_sql))
        conn.execute(text("TRUNCATE TABLE public.model_features;"))

    # Write data in chunks
    total = len(df)
    print(f"[INFO] Writing {total:,} rows to public.model_features ...")

    df.to_sql("model_features", engine, schema="public",
              if_exists="append", index=False, method="multi", chunksize=500)

    print(f"[OK] model_features table updated with {total:,} rows")

# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
if __name__ == "__main__":
    start = datetime.now()
    print("[DEBUG] Model features ETL started ...")

    df_raw = load_features()
    df_model = transform(df_raw)
    write_to_db(df_model)

    print(f"[DONE] Model features ETL completed in {datetime.now() - start}")
