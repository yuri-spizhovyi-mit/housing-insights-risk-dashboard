"""
ETL: Build unified features table for housing models
----------------------------------------------------
Sources:
- public.house_price_index
- public.rent_index
- public.metrics
- public.demographics
- public.macro_economic_data
- public.listings

Output:
- public.features

Grain: (date, city)
Range: 2005-01-01 → 2025-08-01
"""

from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime
import pandas as pd
import os

# ---------------------------------------------------------------------
# 1. Load environment and connect to Neon
# ---------------------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")
if not NEON_DATABASE_URL:
    raise RuntimeError("NEON_DATABASE_URL not found in .env")

engine = create_engine(NEON_DATABASE_URL, pool_pre_ping=True, future=True)
print("[DEBUG] Connected to Neon via .env")

# ---------------------------------------------------------------------
# 2. Load all source tables into DataFrames
# ---------------------------------------------------------------------
def load_table(table_name: str, columns: str = "*") -> pd.DataFrame:
    query = f"SELECT {columns} FROM public.{table_name};"
    try:
        df = pd.read_sql_query(query, engine)
        print(f"[INFO] Loaded {len(df):,} rows from {table_name}")
        return df
    except Exception as e:
        print(f"[WARN] Failed to load {table_name}: {e}")
        return pd.DataFrame()

# ---------------------------------------------------------------------
# 3. Transform and merge datasets
# ---------------------------------------------------------------------
def build_features():
    # Load data
    hpi = load_table("house_price_index", "date, city, hpi_benchmark, hpi_change_yoy")
    rent = load_table("rent_index", "date, city, rent_avg_city, rent_change_yoy")
    metrics = load_table("metrics", "date, city, mortgage_rate, unemployment_rate, overnight_rate")
    demo = load_table("demographics", "date, city, population, median_income")
    macro = load_table("macro_economic_data", "date, city, gdp_growth, cpi_yoy")
    listings = load_table("listings", "date, city, listings_count, new_listings, sales_to_listings_ratio")

    # Standardize types
    for df in [hpi, rent, metrics, demo, macro, listings]:
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df["city"] = df["city"].astype(str)

    # Base frame of all months × all cities
    cities = ["Victoria", "Vancouver", "Calgary", "Edmonton", "Winnipeg", "Ottawa", "Toronto", "Montreal"]
    all_months = pd.date_range("2005-01-01", "2025-08-01", freq="MS")
    base = pd.MultiIndex.from_product([all_months, cities], names=["date", "city"]).to_frame(index=False)
    print(f"[INFO] Base grid created: {len(base):,} (months × cities)")

    # Merge everything on (date, city)
    df = (
        base.merge(hpi, on=["date", "city"], how="left")
        .merge(rent, on=["date", "city"], how="left")
        .merge(metrics, on=["date", "city"], how="left")
        .merge(demo, on=["date", "city"], how="left")
        .merge(macro, on=["date", "city"], how="left")
        .merge(listings, on=["date", "city"], how="left")
    )

    df["source"] = "features_build_etl_v1"
    print(f"[INFO] Final merged features DataFrame: {len(df):,} rows")
    return df


# ---------------------------------------------------------------------
# 4. Upsert to public.features
# ---------------------------------------------------------------------
def upsert_features(df: pd.DataFrame, batch_size: int = 500):
    if df.empty:
        print("[WARN] No data to upsert — skipping database write.")
        return

    upsert_sql = text("""
        INSERT INTO public.features (
            date, city,
            hpi_benchmark, hpi_change_yoy,
            rent_avg_city, rent_change_yoy,
            mortgage_rate, unemployment_rate, overnight_rate,
            population, median_income,
            listings_count, new_listings, sales_to_listings_ratio,
            gdp_growth, cpi_yoy,
            source, created_at
        )
        VALUES (
            :date, :city,
            :hpi_benchmark, :hpi_change_yoy,
            :rent_avg_city, :rent_change_yoy,
            :mortgage_rate, :unemployment_rate, :overnight_rate,
            :population, :median_income,
            :listings_count, :new_listings, :sales_to_listings_ratio,
            :gdp_growth, :cpi_yoy,
            :source, NOW()
        )
        ON CONFLICT (date, city)
        DO UPDATE SET
            hpi_benchmark = EXCLUDED.hpi_benchmark,
            hpi_change_yoy = EXCLUDED.hpi_change_yoy,
            rent_avg_city = EXCLUDED.rent_avg_city,
            rent_change_yoy = EXCLUDED.rent_change_yoy,
            mortgage_rate = EXCLUDED.mortgage_rate,
            unemployment_rate = EXCLUDED.unemployment_rate,
            overnight_rate = EXCLUDED.overnight_rate,
            population = EXCLUDED.population,
            median_income = EXCLUDED.median_income,
            listings_count = EXCLUDED.listings_count,
            new_listings = EXCLUDED.new_listings,
            sales_to_listings_ratio = EXCLUDED.sales_to_listings_ratio,
            gdp_growth = EXCLUDED.gdp_growth,
            cpi_yoy = EXCLUDED.cpi_yoy,
            source = EXCLUDED.source,
            created_at = NOW();
    """)

    total = len(df)
    with engine.begin() as conn:
        for start in range(0, total, batch_size):
            end = start + batch_size
            chunk = df.iloc[start:end]
            conn.execute(upsert_sql, chunk.to_dict(orient="records"))
            print(f"[DEBUG] Upserted {min(end, total)}/{total} rows...")

    print(f"[OK] Upserted {total:,} feature rows into public.features")


# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
if __name__ == "__main__":
    start = datetime.now()
    print("[DEBUG] Features build ETL started ...")
    df_features = build_features()
    upsert_features(df_features)
    print(f"[DONE] Features build ETL completed in {datetime.now() - start}")
