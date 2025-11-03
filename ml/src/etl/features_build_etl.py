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

Output: public.features
Grain: (date, city)
Range: 2005-01-01 → 2025-08-01
"""

from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime
import pandas as pd
import os

# ---------------------------------------------------------------------
# 1. Environment
# ---------------------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")
if not NEON_DATABASE_URL:
    raise RuntimeError("NEON_DATABASE_URL not found in .env")
engine = create_engine(NEON_DATABASE_URL, pool_pre_ping=True, future=True)
print("[DEBUG] Connected to Neon via .env")

# ---------------------------------------------------------------------
# 2. Load helper
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
# 3. Transform + merge
# ---------------------------------------------------------------------
def build_features():
    # Load raw tables
    hpi = load_table("house_price_index", "date, city, benchmark_price")
    rent = load_table("rent_index", "date, city, rent_value")
    metrics = load_table("metrics", "date, city, metric, value")
    demo = load_table("demographics", "date, city, population, median_income")
    macro = load_table("macro_economic_data", "date, city, gdp_growth, cpi_yoy")
    listings = load_table("listings", "date, city, listings_count, new_listings, sales_to_listings_ratio")

    # --- rename HPI and rent ---
    if not hpi.empty:
        hpi.rename(columns={"benchmark_price": "hpi_benchmark"}, inplace=True)
    if not rent.empty:
        rent.rename(columns={"rent_value": "rent_avg_city"}, inplace=True)

    # --- pivot metrics ---
    if not metrics.empty:
        metrics_wide = metrics.pivot_table(
            index=["date", "city"],
            columns="metric",
            values="value",
            aggfunc="first"
        ).reset_index()
        metrics_wide.columns.name = None
        metrics = metrics_wide
        print(f"[INFO] Pivoted metrics into {len(metrics.columns)-2} columns.")
    else:
        metrics = pd.DataFrame(columns=["date", "city"])

    # --- date + city normalization ---
    for df in [hpi, rent, metrics, demo, macro, listings]:
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df["city"] = df["city"].astype(str)

    # --- base grid ---
    cities = ["Victoria", "Vancouver", "Calgary", "Edmonton", "Winnipeg", "Ottawa", "Toronto", "Montreal"]
    all_months = pd.date_range("2005-01-01", "2025-08-01", freq="MS")
    base = pd.MultiIndex.from_product([all_months, cities], names=["date", "city"]).to_frame(index=False)
    print(f"[INFO] Base grid created: {len(base):,} rows (months × cities)")

    # --- join everything ---
    df = base.copy()
    sources = {
        "hpi": hpi,
        "rent": rent,
        "metrics": metrics,
        "demo": demo,
        "macro": macro,
        "listings": listings
    }

    for name, src in sources.items():
        if not src.empty and all(col in src.columns for col in ["date", "city"]):
            df = df.merge(src, on=["date", "city"], how="left")
            print(f"[INFO] Merged {name} ({len(src)} rows)")
        else:
            print(f"[WARN] Skipped {name} — empty or missing date/city.")

    df["source"] = "features_build_etl_v2"
    print(f"[INFO] Final merged features DataFrame: {len(df):,} rows")
    return df

# ---------------------------------------------------------------------
# 4. Upsert
# ---------------------------------------------------------------------
def upsert_features(df: pd.DataFrame, batch_size: int = 500):
    if df.empty:
        print("[WARN] No data to upsert — skipping write.")
        return

    upsert_sql = text("""
        INSERT INTO public.features (
            date, city,
            hpi_benchmark, rent_avg_city,
            mortgage_rate, unemployment_rate, overnight_rate,
            population, median_income,
            listings_count, new_listings, sales_to_listings_ratio,
            gdp_growth, cpi_yoy,
            source, created_at
        )
        VALUES (
            :date, :city,
            :hpi_benchmark, :rent_avg_city,
            :mortgage_rate, :unemployment_rate, :overnight_rate,
            :population, :median_income,
            :listings_count, :new_listings, :sales_to_listings_ratio,
            :gdp_growth, :cpi_yoy,
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

    print(f"[OK] Upserted {total:,} rows into public.features")

# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
if __name__ == "__main__":
    start = datetime.now()
    print("[DEBUG] Features build ETL started ...")
    df_features = build_features()
    upsert_features(df_features)
    print(f"[DONE] Features build ETL completed in {datetime.now() - start}")
