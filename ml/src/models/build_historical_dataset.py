# ================================================================
# build_historical_dataset.py (v2)
# ------------------------------------------------
# Creates a supervised training dataset for LightGBM models
# by merging macro (HPI, rents, metrics) and micro (features)
# using the correct Housing Insights database schema.
# ================================================================

import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path
import os
from datetime import datetime


# ---------------------------------------------------------------
# 🔌 Database connection
# ---------------------------------------------------------------
def get_engine():
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5433/hird",
    )
    print(f"[DEBUG] Connecting to DB → {db_url}")
    return create_engine(db_url, future=True)


# ---------------------------------------------------------------
# 🧩 Build dataset
# ---------------------------------------------------------------
def build_historical_dataset(engine, lookback_years: int = 10) -> pd.DataFrame:
    with engine.connect() as conn:
        # 1️⃣ House Price Index (target)
        hpi = pd.read_sql(
            text(
                """
                SELECT date, city, index_value AS hpi_composite_sa
                FROM public.house_price_index
                WHERE measure = 'Composite' AND date > (CURRENT_DATE - interval ':yrs year')
            """.replace(":yrs", str(lookback_years))
            ),
            conn,
        )

        # 2️⃣ Rent Index
        rent = pd.read_sql(
            text(
                """
                SELECT date, city, rent_index, median_rent_apartment_1br,
                       median_rent_apartment_2br, active_rental_count, avg_rental_days
                FROM public.rent_index
                WHERE date > (CURRENT_DATE - interval ':yrs year')
            """.replace(":yrs", str(lookback_years))
            ),
            conn,
        )

        # 3️⃣ Demographics
        demo = pd.read_sql(
            text(
                """
                SELECT date, city, population, net_migration,
                       age_distribution_25_34_perc, avg_disposable_income
                FROM public.demographics
                WHERE date > (CURRENT_DATE - interval ':yrs year')
            """.replace(":yrs", str(lookback_years))
            ),
            conn,
        )

        # 4️⃣ Macro Economic Data
        macro = pd.read_sql(
            text(
                """
                SELECT date, province AS city,
                       unemployment_rate, gdp_growth_rate, prime_lending_rate, housing_starts
                FROM public.macro_economic_data
                WHERE date > (CURRENT_DATE - interval ':yrs year')
            """.replace(":yrs", str(lookback_years))
            ),
            conn,
        )

        # 5️⃣ Listings Features (micro-level context)
        listings = pd.read_sql(
            text(
                """
                SELECT date AS ref_date, city, price_avg, rent_index, hpi_composite_sa,
                       bedrooms_avg, bathrooms_avg, sqft_avg, property_type,
                       price_to_rent, price_mom_pct, rent_mom_pct, hpi_mom_pct
                FROM public.features
                WHERE date > (CURRENT_DATE - interval ':yrs year')
            """.replace(":yrs", str(lookback_years))
            ),
            conn,
        )

    # -----------------------------------------------------------
    # 🔗 Merge datasets by (city, date)
    # -----------------------------------------------------------
    df = (
        listings.merge(hpi, on=["city", "ref_date"], how="left")
        .merge(rent, on=["city", "ref_date"], how="left")
        .merge(demo, on=["city", "ref_date"], how="left")
        .merge(macro, on=["city", "ref_date"], how="left")
    )

    df = df.sort_values(["city", "ref_date"]).drop_duplicates(
        subset=["city", "ref_date"]
    )

    # -----------------------------------------------------------
    # 🎯 Supervised targets (HPI ahead)
    # -----------------------------------------------------------
    for horizon, months in [(12, "12m"), (24, "24m"), (60, "5y"), (120, "10y")]:
        df[f"target_hpi_{months}_ahead"] = df.groupby("city")["hpi_composite_sa"].shift(
            -horizon
        )

    df = df.dropna(subset=["target_hpi_12m_ahead"])
    df["created_at"] = datetime.now().astimezone()

    print(
        f"[INFO] ✅ Historical dataset built → {len(df)} rows, {len(df.columns)} columns"
    )
    return df


# ---------------------------------------------------------------
# 💾 Save locally
# ---------------------------------------------------------------
def save_to_parquet(df: pd.DataFrame, path: str = "data/historical_features.parquet"):
    Path("data").mkdir(exist_ok=True)
    df.to_parquet(path, index=False)
    print(f"[OK] Saved dataset → {path}")


# ---------------------------------------------------------------
# 🚀 CLI Entry
# ---------------------------------------------------------------
if __name__ == "__main__":
    engine = get_engine()
    df = build_historical_dataset(engine, lookback_years=10)
    save_to_parquet(df)
