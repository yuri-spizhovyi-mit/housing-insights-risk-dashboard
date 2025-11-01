"""
ETL: Aggregate monthly housing listings (from listings_raw)
Source: public.listings_raw
Target: public.listings

Creates monthly aggregates by (date, city):
- listings_count: total listings (rent + sale)
- new_listings: listings with type 'sale'
- sales_to_listings_ratio: sale listings / total
"""

from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime
import os
import pandas as pd

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
# 2. Load raw listings
# ---------------------------------------------------------------------
def load_raw_listings() -> pd.DataFrame:
    query = """
        SELECT city, date_posted::date AS date_posted, listing_type, price
        FROM public.listings_raw
        WHERE price IS NOT NULL AND city IS NOT NULL
    """
    df = pd.read_sql_query(query, engine)
    print(f"[INFO] Loaded {len(df):,} listings_raw rows from database")
    return df


# ---------------------------------------------------------------------
# 3. Transform → monthly aggregates
# ---------------------------------------------------------------------
def transform(df: pd.DataFrame) -> pd.DataFrame:
    # Normalize to month start
    df["date"] = pd.to_datetime(df["date_posted"]).dt.to_period("M").dt.to_timestamp()
    df = df.drop(columns=["date_posted"])

    agg = (
        df.groupby(["date", "city"])
        .agg(
            listings_count=("city", "size"),
            new_listings=("listing_type", lambda x: (x == "sale").sum()),
        )
        .reset_index()
    )

    agg["sales_to_listings_ratio"] = (
        agg["new_listings"] / agg["listings_count"]
    ).round(3)
    agg["source"] = "ETL_listings_agg_v1"

    print(f"[INFO] Aggregated {len(agg)} monthly city-level records")
    return agg


# ---------------------------------------------------------------------
# 4. Create target table if not exists
# ---------------------------------------------------------------------
def create_target_table():
    create_sql = text("""
        CREATE TABLE IF NOT EXISTS public.listings (
            date DATE NOT NULL,
            city TEXT NOT NULL,
            listings_count INT,
            new_listings INT,
            sales_to_listings_ratio NUMERIC(6,3),
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (date, city)
        );
    """)
    with engine.begin() as conn:
        conn.execute(create_sql)
    print("[DEBUG] Ensured public.listings table exists")


# ---------------------------------------------------------------------
# 5. Upsert to database
# ---------------------------------------------------------------------
def upsert_listings(df: pd.DataFrame):
    upsert_sql = text("""
        INSERT INTO public.listings (date, city, listings_count, new_listings, sales_to_listings_ratio, source, created_at)
        VALUES (:date, :city, :listings_count, :new_listings, :sales_to_listings_ratio, :source, NOW())
        ON CONFLICT (date, city)
        DO UPDATE SET
            listings_count = EXCLUDED.listings_count,
            new_listings = EXCLUDED.new_listings,
            sales_to_listings_ratio = EXCLUDED.sales_to_listings_ratio,
            source = EXCLUDED.source,
            created_at = NOW();
    """)
    with engine.begin() as conn:
        conn.execute(upsert_sql, df.to_dict(orient="records"))
    print(f"[OK] Upserted {len(df):,} rows into public.listings")


# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
if __name__ == "__main__":
    start = datetime.now()
    print("[DEBUG] Listings aggregation ETL started ...")
    create_target_table()
    df_raw = load_raw_listings()
    df_agg = transform(df_raw)
    upsert_listings(df_agg)
    print(f"[DONE] Listings aggregation ETL completed in {datetime.now() - start}")
