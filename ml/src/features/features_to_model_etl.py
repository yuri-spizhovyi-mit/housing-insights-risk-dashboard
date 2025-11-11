"""
ETL: Convert cleaned features into model-ready scaled dataset (v1)
------------------------------------------------------------------
Reads data from public.features, scales numeric fields optimally using MinMaxScaler,
fills missing values, drops unused columns, and writes to public.model_features.
Optimized for Neon DB with warm-up and batch insert.
"""

from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
import pandas as pd
import numpy as np
import os

# ---------------------------------------------------------------------
# 1. Environment setup
# ---------------------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL") or os.getenv("DATABASE_URL")
if not NEON_DATABASE_URL:
    raise RuntimeError("NEON_DATABASE_URL not found in .env")

engine = create_engine(NEON_DATABASE_URL, pool_pre_ping=True, future=True)
print("[DEBUG] Connected to Neon via .env")


# ---------------------------------------------------------------------
# 2. Load features table
# ---------------------------------------------------------------------
def load_features():
    query = "SELECT * FROM public.features;"
    df = pd.read_sql_query(query, engine)
    print(f"[INFO] Loaded {len(df):,} rows from public.features")
    return df


# ---------------------------------------------------------------------
# 3. Transform into model-ready dataset
# ---------------------------------------------------------------------
def build_model_features(df: pd.DataFrame) -> pd.DataFrame:
    # Drop irrelevant columns
    drop_cols = [
        "listings_count",
        "new_listings",
        "sales_to_listings_ratio",
        "source",
        "created_at",
    ]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns], errors="ignore")

    # Fill missing rent_avg_city with median per city
    if "rent_avg_city" in df.columns:
        df["rent_avg_city"] = df.groupby("city")["rent_avg_city"].transform(
            lambda s: s.fillna(s.median())
        )

    # Identify numeric columns to scale
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
    ]

    # Ensure numeric dtype and replace NaN
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # Apply MinMax scaling city-wise for more balanced normalization
    scaler = MinMaxScaler()
    scaled_dfs = []

    for city, group in df.groupby("city"):
        scaled = group.copy()
        scaled_values = scaler.fit_transform(scaled[numeric_cols])
        scaled_cols = [f"{c}_scaled" for c in numeric_cols]
        scaled[scaled_cols] = scaled_values
        scaled_dfs.append(scaled)

    df_scaled = pd.concat(scaled_dfs, ignore_index=True)
    df_scaled.sort_values(["date", "city"], inplace=True)

    print(
        f"[INFO] Scaled {len(numeric_cols)} numeric columns for {df['city'].nunique()} cities."
    )
    df_scaled["source"] = "features_to_model_etl_v1"
    return df_scaled


# ---------------------------------------------------------------------
# 4. Write to public.model_features
# ---------------------------------------------------------------------
def upsert_model_features(df: pd.DataFrame, batch_size: int = 5000):
    if df.empty:
        print("[WARN] No data to upsert — skipping database write.")
        return

    upsert_sql = text("""
        INSERT INTO public.model_features (
            date, city,
            hpi_benchmark, rent_avg_city, mortgage_rate, unemployment_rate, overnight_rate,
            population, median_income, migration_rate, gdp_growth, cpi_yoy,
            hpi_benchmark_scaled, rent_avg_city_scaled, mortgage_rate_scaled,
            unemployment_rate_scaled, overnight_rate_scaled, population_scaled,
            median_income_scaled, migration_rate_scaled, gdp_growth_scaled, cpi_yoy_scaled,
            source, created_at
        )
        VALUES (
            :date, :city,
            :hpi_benchmark, :rent_avg_city, :mortgage_rate, :unemployment_rate, :overnight_rate,
            :population, :median_income, :migration_rate, :gdp_growth, :cpi_yoy,
            :hpi_benchmark_scaled, :rent_avg_city_scaled, :mortgage_rate_scaled,
            :unemployment_rate_scaled, :overnight_rate_scaled, :population_scaled,
            :median_income_scaled, :migration_rate_scaled, :gdp_growth_scaled, :cpi_yoy_scaled,
            :source, NOW()
        )
        ON CONFLICT (date, city)
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
            hpi_benchmark_scaled = EXCLUDED.hpi_benchmark_scaled,
            rent_avg_city_scaled = EXCLUDED.rent_avg_city_scaled,
            mortgage_rate_scaled = EXCLUDED.mortgage_rate_scaled,
            unemployment_rate_scaled = EXCLUDED.unemployment_rate_scaled,
            overnight_rate_scaled = EXCLUDED.overnight_rate_scaled,
            population_scaled = EXCLUDED.population_scaled,
            median_income_scaled = EXCLUDED.median_income_scaled,
            migration_rate_scaled = EXCLUDED.migration_rate_scaled,
            gdp_growth_scaled = EXCLUDED.gdp_growth_scaled,
            cpi_yoy_scaled = EXCLUDED.cpi_yoy_scaled,
            source = EXCLUDED.source,
            created_at = NOW();
    """)

    total = len(df)
    with engine.begin() as conn:
        conn.exec_driver_sql("SELECT 1;")
        print("[DEBUG] Neon warmed up, starting model_features upserts...")

        for start in range(0, total, batch_size):
            end = start + batch_size
            chunk = df.iloc[start:end]
            conn.execute(upsert_sql, chunk.to_dict(orient="records"))
            print(f"[DEBUG] Upserted {min(end, total)}/{total} rows...")

    print(f"[OK] Upserted {total:,} rows into public.model_features")


# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
if __name__ == "__main__":
    start = datetime.now()
    print("[DEBUG] features_to_model_etl_v1 started ...")
    df_features = load_features()
    df_model = build_model_features(df_features)
    upsert_model_features(df_model)
    print(f"[DONE] features_to_model_etl_v1 completed in {datetime.now() - start}")
