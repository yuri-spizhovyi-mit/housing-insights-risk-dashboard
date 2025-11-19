"""
features_build_etl_v10.py
----------------------------------------------------------
Builds the unified 'features' table with property_type preserved for house prices.
Merges:
- House price index (with property_type)
- Rent index (city-level)
- Macro indicators (mortgage rate, unemployment, CPI, etc.)

This version ensures:
✅ property_type is preserved for house prices only
✅ rent data is merged at the city level (broadcasted across property types)
✅ full compatibility with model_features and train_model_* pipelines
"""

from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime
import pandas as pd
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
# 2. Load source tables
# ---------------------------------------------------------------------
def load_table(name: str, columns: str):
    query = f"SELECT {columns} FROM public.{name} ORDER BY date, city;"
    df = pd.read_sql_query(query, engine)
    df["date"] = pd.to_datetime(df["date"])
    print(f"[INFO] Loaded {len(df):,} rows from {name}")
    return df


# ---------------------------------------------------------------------
# 3. Build unified features
# ---------------------------------------------------------------------
def build_features():
    print("[STEP] Loading source tables...")

    hpi = load_table(
        "house_price_index",
        "date, city, property_type, benchmark_price AS hpi_benchmark",
    )
    rent = load_table("rent_index", "date, city, rent_value AS rent_avg_city")
    macro = load_table(
        "macro_indicators",
        "date, mortgage_rate, unemployment_rate, overnight_rate, population, median_income, gdp_growth, cpi_yoy, migration_rate",
    )

    # All unique months, cities, property types
    all_months = pd.date_range(hpi["date"].min(), hpi["date"].max(), freq="MS")
    cities = sorted(hpi["city"].unique())
    property_types = sorted(hpi["property_type"].unique())

    base = pd.MultiIndex.from_product(
        [all_months, cities, property_types], names=["date", "city", "property_type"]
    ).to_frame(index=False)

    print(f"[INFO] Created base grid: {len(base):,} records")

    # Merge house price index (with property_type)
    df = base.merge(hpi, on=["date", "city", "property_type"], how="left")

    # Merge rent index (city-level, broadcast to all property types)
    rent_expanded = base[["date", "city"]].drop_duplicates()
    rent_expanded = rent_expanded.merge(rent, on=["date", "city"], how="left")
    df = df.merge(
        rent_expanded[["date", "city", "rent_avg_city"]],
        on=["date", "city"],
        how="left",
    )

    # Merge macro indicators (same for all cities and property types)
    df = df.merge(macro, on="date", how="left")

    # Sort and clean
    df = df.sort_values(["city", "property_type", "date"]).reset_index(drop=True)
    df["source"] = "features_build_etl_v10"
    df["created_at"] = datetime.utcnow()

    print(f"[INFO] Final features shape: {df.shape}")
    print(df.head())
    return df


# ---------------------------------------------------------------------
# 4. Write to Postgres
# ---------------------------------------------------------------------
def write_to_db(df: pd.DataFrame):
    print("[STEP] Writing to public.features ...")

    with engine.begin() as conn:
        conn.exec_driver_sql("DELETE FROM public.features;")
        df.to_sql(
            "features", con=conn, schema="public", if_exists="append", index=False
        )

    print(f"[OK] Written {len(df):,} rows to public.features")


# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
if __name__ == "__main__":
    start = datetime.now()
    print("[DEBUG] features_build_etl_v10 started ...")

    df_features = build_features()
    write_to_db(df_features)

    print(f"\n[DONE] features_build_etl_v10 completed in {datetime.now() - start}")
