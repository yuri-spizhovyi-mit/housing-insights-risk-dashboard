"""
ETL: Prepare model-ready dataset from public.features
-----------------------------------------------------
Input : public.features
Output: public.model_features
Purpose: Clean, normalize, and export standardized features for ML models
Supports: Min–Max scaling (0–1) or Z-score standardization
"""

from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime
import pandas as pd
import numpy as np
import os
import argparse

# ---------------------------------------------------------------------
# 1. Config
# ---------------------------------------------------------------------
DEFAULT_SCALING = "minmax"   # options: 'minmax' or 'zscore'

# ---------------------------------------------------------------------
# 2. Connect to Neon
# ---------------------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")
if not NEON_DATABASE_URL:
    raise RuntimeError("NEON_DATABASE_URL not found in .env")

engine = create_engine(NEON_DATABASE_URL, pool_pre_ping=True, future=True)
print("[DEBUG] Connected to Neon via .env")

# ---------------------------------------------------------------------
# 3. Load data
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
# 4. Transform & scale
# ---------------------------------------------------------------------
def transform(df: pd.DataFrame, scaling_mode: str = "minmax") -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df.sort_values(["city", "date"], inplace=True)

    # Fill missing numeric values (forward/backward fill per city)
    num_cols = df.select_dtypes(include=[np.number]).columns
    df[num_cols] = df.groupby("city")[num_cols].ffill().bfill()

    # Apply chosen normalization
    print(f"[INFO] Applying {scaling_mode.upper()} scaling...")

    for col in num_cols:
        if not df[col].notna().any():
            continue

        if scaling_mode == "zscore":
            mean_val = df[col].mean()
            std_val = df[col].std(ddof=0)
            if pd.notna(std_val) and std_val != 0:
                df[col + "_scaled"] = (df[col] - mean_val) / std_val
            else:
                df[col + "_scaled"] = 0.0

        else:  # default: minmax
            min_val = df[col].min()
            max_val = df[col].max()
            if pd.notna(max_val) and pd.notna(min_val) and max_val != min_val:
                df[col + "_scaled"] = (df[col] - min_val) / (max_val - min_val)
            else:
                df[col + "_scaled"] = 0.0

    print(f"[INFO] Added {len(num_cols)} scaled columns.")
    return df

# ---------------------------------------------------------------------
# 5. Write to DB
# ---------------------------------------------------------------------
def write_to_db(df: pd.DataFrame):
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
            hpi_benchmark_scaled NUMERIC(14,6),
            rent_avg_city_scaled NUMERIC(14,6),
            mortgage_rate_scaled NUMERIC(14,6),
            unemployment_rate_scaled NUMERIC(14,6),
            overnight_rate_scaled NUMERIC(14,6),
            population_scaled NUMERIC(14,6),
            median_income_scaled NUMERIC(14,6),
            gdp_growth_scaled NUMERIC(14,6),
            cpi_yoy_scaled NUMERIC(14,6),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (date, city)
        );
    """
    with engine.begin() as conn:
        conn.execute(text(create_sql))
        conn.execute(text("TRUNCATE TABLE public.model_features;"))

    total = len(df)
    print(f"[INFO] Writing {total:,} rows to public.model_features ...")

    df.to_sql(
        "model_features", engine, schema="public",
        if_exists="append", index=False, method="multi", chunksize=500
    )

    print(f"[OK] model_features table updated with {total:,} rows")

# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build model_features table from features.")
    parser.add_argument("--scaling", type=str, default=DEFAULT_SCALING,
                        choices=["minmax", "zscore"],
                        help="Scaling mode: 'minmax' or 'zscore'")
    args = parser.parse_args()

    start = datetime.now()
    print(f"[DEBUG] Model features ETL started using {args.scaling.upper()} scaling ...")

    df_raw = load_features()
    df_model = transform(df_raw, scaling_mode=args.scaling)
    write_to_db(df_model)

    print(f"[DONE] Model features ETL completed in {datetime.now() - start}")
