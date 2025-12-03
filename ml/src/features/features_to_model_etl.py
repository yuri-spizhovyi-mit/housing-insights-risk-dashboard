"""
features_to_model_etl.py  (Option B2 — simplified city-level ETL)
------------------------------------------------------------------

This version removes all property_type weighting and produces a
clean, stable, per-city-per-date dataset for all 4 models:

✔ ARIMA
✔ Prophet
✔ LightGBM
✔ LSTM

Pipeline:

1. Load features from public.features
2. Aggregate per city/date (simple mean/median)
3. Add lag, rolling, yoy features
4. Z-score scale all numeric fields
5. Write clean model_features table

No property_type logic. No ratios. No complex weights.
Simple, stable, reliable.
"""

import os
from datetime import datetime, timezone
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from dotenv import load_dotenv, find_dotenv


# ---------------------------------------------------------
# ENVIRONMENT + DB CONNECTION
# ---------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL")

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)


# ---------------------------------------------------------
# 1. LOAD RAW FEATURES
# ---------------------------------------------------------
def load_features():
    q = """
        SELECT 
            date,
            city,
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
        ORDER BY city, date;
    """
    df = pd.read_sql(q, engine)
    df["date"] = pd.to_datetime(df["date"])
    print(f"[INFO] Loaded {len(df)} rows from features")
    return df


# ---------------------------------------------------------
# 2. SIMPLE CITY-LEVEL AGGREGATION (no property_type)
# ---------------------------------------------------------
def aggregate_city_level(df):
    """
    For each city/date, compute median of macro variables.
    This avoids weighting, property-type issues, and noise.
    """
    agg = (
        df.groupby(["city", "date"])
        .agg({
            "hpi_benchmark": "median",
            "rent_avg_city": "median",
            "mortgage_rate": "median",
            "unemployment_rate": "median",
            "overnight_rate": "median",
            "population": "median",
            "median_income": "median",
            "migration_rate": "median",
            "gdp_growth": "median",
            "cpi_yoy": "median",
        })
        .reset_index()
        .sort_values(["city", "date"])
    )

    print(f"[INFO] Aggregated to {len(agg)} city-level rows")
    return agg


# ---------------------------------------------------------
# 3. ADD FEATURE ENGINEERING: YoY, lag, rolling
# ---------------------------------------------------------
def add_feature_engineering(df):
    df = df.sort_values(["city", "date"]).copy()

    # year-over-year
    for col in ["hpi_benchmark", "rent_avg_city"]:
        df[f"{col}_yoy"] = df.groupby("city")[col].pct_change(12)

    # lag and rolling for core targets
    df["lag_1"] = df.groupby("city")["hpi_benchmark"].shift(1)
    df["lag_3"] = df.groupby("city")["hpi_benchmark"].shift(3)
    df["lag_6"] = df.groupby("city")["hpi_benchmark"].shift(6)

    df["roll_3"] = (
        df.groupby("city")["hpi_benchmark"].rolling(3).mean().reset_index(level=0, drop=True)
    )
    df["roll_6"] = (
        df.groupby("city")["hpi_benchmark"].rolling(6).mean().reset_index(level=0, drop=True)
    )

    return df


# ---------------------------------------------------------
# 4. Z-SCORE NORMALIZATION PER CITY
# ---------------------------------------------------------
def zscore_group(df, cols):
    for col in cols:
        df[f"{col}_z"] = (
            df.groupby("city")[col].transform(lambda x: (x - x.mean()) / (x.std() + 1e-6))
        )
    return df


def zscore_cols(df):
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
        "hpi_benchmark_yoy",
        "rent_avg_city_yoy",
        "lag_1", "lag_3", "lag_6",
        "roll_3", "roll_6",
    ]
    df = zscore_group(df, [c for c in zcols if c in df.columns])
    return df


# ---------------------------------------------------------
# 5. CLEANUP & METADATA
# ---------------------------------------------------------
def finalize(df):
    # drop first 12 months to remove NaNs from lag/yoy
    df = (
        df.sort_values(["city", "date"])
        .groupby("city")
        .apply(lambda g: g.iloc[12:])
        .reset_index(drop=True)
    )

    df["etl_version"] = "model_features_city_simple_v1"
    df["processed_at"] = datetime.now(timezone.utc)

    print(f"[INFO] Final model_features rows: {len(df)}")
    return df


# ---------------------------------------------------------
# 6. WRITE TABLE
# ---------------------------------------------------------
def write_model_features(df):
    print("[INFO] Writing model_features...")

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE public.model_features;"))

    cols = df.columns.tolist()
    placeholders = ", ".join(":" + c for c in cols)

    sql = text(f"""
        INSERT INTO public.model_features ({", ".join(cols)})
        VALUES ({placeholders});
    """)

    batch = 3000
    with engine.begin() as conn:
        for i in range(0, len(df), batch):
            chunk = df.iloc[i : i + batch]
            conn.execute(sql, chunk.to_dict(orient="records"))

    print("[OK] model_features updated.")


# ---------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------
def main():
    print("[DEBUG] Starting simplified city-level model_features ETL...")

    raw = load_features()
    agg = aggregate_city_level(raw)
    feat = add_feature_engineering(agg)
    feat = zscore_cols(feat)
    final = finalize(feat)

    write_model_features(final)

    print("[DONE] ETL completed successfully.")


if __name__ == "__main__":
    main()
