"""
features_build_etl_v10_full.py
----------------------------------------------------------
Full rebuild based on v9 with property_type support.
Preserves ALL logic, validation, and batching from v9.
Adds:
✅ property_type dimension for house prices
✅ rent, macro, and demo data broadcasted per property_type
✅ ON CONFLICT (date, city, property_type) safe upsert for Neon
"""

from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime
import pandas as pd
import numpy as np
import os
import time

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
# 2. Helper functions
# ---------------------------------------------------------------------
def load_table(name: str, columns: str):
    query = f"SELECT {columns} FROM public.{name} ORDER BY date, city;"
    df = pd.read_sql_query(query, engine)
    df["date"] = pd.to_datetime(df["date"])
    print(f"[INFO] Loaded {len(df):,} rows from {name}")
    return df


def fill_missing(df, cols, group_cols):
    df = df.sort_values(group_cols + ["date"])
    for c in cols:
        df[c] = df.groupby(group_cols)[c].ffill().bfill()
    return df


def pct_change_yoy(series):
    return series.pct_change(periods=12) * 100


# ---------------------------------------------------------------------
# 3. Build unified features with property_type
# ---------------------------------------------------------------------
def build_features():
    print("[STEP] Loading source tables...")

    # Core datasets
    hpi = load_table(
        "house_price_index",
        "date, city, property_type, benchmark_price AS hpi_benchmark",
    )
    rent = load_table("rent_index", "date, city, rent_value AS rent_avg_city")
    metrics = load_table(
        "metrics", "date, city, hpi_growth, rent_growth, hpi_to_rent_ratio"
    )
    macro = load_table(
        "macro_indicators",
        "date, mortgage_rate, unemployment_rate, overnight_rate, population, median_income, gdp_growth, cpi_yoy, migration_rate",
    )
    demo = load_table(
        "demographics", "date, city, median_age, avg_household_size, education_index"
    )

    # Ensure cities and property types are comprehensive
    all_months = pd.date_range(hpi["date"].min(), hpi["date"].max(), freq="MS")
    cities = sorted(hpi["city"].unique())
    property_types = sorted(hpi["property_type"].unique())

    # Create full base grid including property_type
    base = pd.MultiIndex.from_product(
        [all_months, cities, property_types], names=["date", "city", "property_type"]
    ).to_frame(index=False)

    print(
        f"[INFO] Created base grid: {len(base):,} records ({len(all_months)} months × {len(cities)} cities × {len(property_types)} types)"
    )

    # Merge house price index (property_type aware)
    df = base.merge(hpi, on=["date", "city", "property_type"], how="left")

    # Broadcast rent index across property types
    rent_expanded = base[["date", "city"]].drop_duplicates()
    rent_expanded = rent_expanded.merge(rent, on=["date", "city"], how="left")
    df = df.merge(
        rent_expanded[["date", "city", "rent_avg_city"]],
        on=["date", "city"],
        how="left",
    )

    # Merge macroeconomic indicators (same for all property types)
    for src, name in zip([macro, metrics, demo], ["macro", "metrics", "demo"]):
        df = df.merge(src, on=["date", "city"], how="left")
        print(f"[MERGE] Added {name} → shape now: {df.shape}")

    # Fill missing values and clean
    df = fill_missing(df, ["hpi_benchmark", "rent_avg_city"], ["city", "property_type"])

    # Derived YoY change metrics
    df["hpi_change_yoy"] = df.groupby(["city", "property_type"])[
        "hpi_benchmark"
    ].transform(pct_change_yoy)
    df["rent_change_yoy"] = df.groupby(["city"])["rent_avg_city"].transform(
        pct_change_yoy
    )

    # Cleanup infinities and NaN
    df = df.replace([np.inf, -np.inf], np.nan)

    # Metadata columns
    df["source"] = "features_build_etl_v10_full"
    df["created_at"] = datetime.utcnow()

    print(f"[INFO] Final features shape: {df.shape}")
    print(df.head(3))
    return df


# ---------------------------------------------------------------------
# 4. Write to Postgres (safe upsert with warm-up and batching)
# ---------------------------------------------------------------------
def write_to_db(df: pd.DataFrame):
    print("[STEP] Writing to public.features ...")

    cols = [
        "date",
        "city",
        "property_type",
        "hpi_benchmark",
        "rent_avg_city",
        "hpi_growth",
        "rent_growth",
        "hpi_to_rent_ratio",
        "mortgage_rate",
        "unemployment_rate",
        "overnight_rate",
        "population",
        "median_income",
        "gdp_growth",
        "cpi_yoy",
        "migration_rate",
        "median_age",
        "avg_household_size",
        "education_index",
        "hpi_change_yoy",
        "rent_change_yoy",
        "source",
        "created_at",
    ]

    insert_sql = text(f"""
        INSERT INTO public.features ({", ".join(cols)})
        VALUES ({", ".join([":" + c for c in cols])})
        ON CONFLICT (date, city, property_type)
        DO UPDATE SET
            hpi_benchmark = EXCLUDED.hpi_benchmark,
            rent_avg_city = EXCLUDED.rent_avg_city,
            hpi_change_yoy = EXCLUDED.hpi_change_yoy,
            rent_change_yoy = EXCLUDED.rent_change_yoy,
            source = EXCLUDED.source,
            created_at = EXCLUDED.created_at;
    """)

    with engine.begin() as conn:
        conn.exec_driver_sql("SELECT 1;")  # warm-up Neon connection
        total = len(df)
        batch_size = 5000
        for i in range(0, total, batch_size):
            batch = df.iloc[i : i + batch_size]
            conn.execute(insert_sql, batch.to_dict(orient="records"))
            print(f"[WRITE] Batch {i // batch_size + 1} → {len(batch)} rows")

    print(f"[OK] Written {len(df):,} rows to public.features")


# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
if __name__ == "__main__":
    start = datetime.now()
    print("[DEBUG] features_build_etl_v10_full started ...")

    df_features = build_features()
    write_to_db(df_features)

    print(f"\n[DONE] features_build_etl_v10_full completed in {datetime.now() - start}")
