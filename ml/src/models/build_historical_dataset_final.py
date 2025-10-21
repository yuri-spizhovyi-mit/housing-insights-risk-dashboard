# ================================================================
# build_historical_dataset.py — Final (city-month panel, 2005+)
# ------------------------------------------------
# - Uses HOUSE PRICE INDEX (Composite_Benchmark) as target in CAD
# - Joins clean sources: house_price_index, rent_index, macro_economic_data, demographics
# - NO dependency on legacy 'features' or 'listings_features' tables
# - Saves to data/historical_features.parquet
# ================================================================

import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


def get_engine():
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5433/hird",
    )
    print(f"[DEBUG] Connecting to DB → {db_url}")
    return create_engine(db_url, future=True, pool_pre_ping=True)


def month_floor(s: pd.Series) -> pd.Series:
    dt = pd.to_datetime(s, errors="coerce")
    return dt.dt.to_period("M").dt.to_timestamp()  # month start


def build_historical_dataset(engine, lookback_years: int = 25) -> pd.DataFrame:
    with engine.begin() as conn:
        hpi_q = text(f"""
            SELECT date, city, measure, index_value
            FROM public.house_price_index
            WHERE measure = 'Composite_Benchmark'
              AND date > (CURRENT_DATE - interval '{lookback_years} year')
        """)
        hpi = pd.read_sql(hpi_q, conn)
        if hpi.empty:
            raise RuntimeError("house_price_index → no rows for Composite_Benchmark.")
        hpi["date"] = month_floor(hpi["date"])
        hpi = (
            hpi.groupby(["city", "date"], as_index=False)["index_value"]
            .mean()
            .rename(columns={"index_value": "price_benchmark"})
        )

        rent_q = text(f"""
            SELECT date, city,
                   index_value AS rent_index,
                   median_rent_apartment_1br,
                   median_rent_apartment_2br,
                   median_rent_apartment_3br
            FROM public.rent_index
            WHERE date > (CURRENT_DATE - interval '{lookback_years} year')
        """)
        rent = pd.read_sql(rent_q, conn)
        rent["date"] = month_floor(rent["date"])
        rent = rent.groupby(["city", "date"], as_index=False)[
            [
                "rent_index",
                "median_rent_apartment_1br",
                "median_rent_apartment_2br",
                "median_rent_apartment_3br",
            ]
        ].mean()

        demo_q = text(f"""
            SELECT date, city, population, migration_rate,
                   age_25_34_perc, median_income
            FROM public.demographics
            WHERE date > (CURRENT_DATE - interval '{lookback_years} year')
        """)
        demo = pd.read_sql(demo_q, conn)
        if not demo.empty:
            demo["date"] = month_floor(demo["date"])
            demo = demo.groupby(["city", "date"], as_index=False)[
                ["population", "migration_rate", "age_25_34_perc", "median_income"]
            ].mean()

        macro_q = text(f"""
            SELECT date, city,
                   unemployment_rate, gdp_growth_rate,
                   prime_lending_rate, housing_starts
            FROM public.macro_economic_data
            WHERE date > (CURRENT_DATE - interval '{lookback_years} year')
        """)
        macro = pd.read_sql(macro_q, conn)
        if not macro.empty:
            macro["date"] = month_floor(macro["date"])
            macro = macro.groupby(["city", "date"], as_index=False)[
                [
                    "unemployment_rate",
                    "gdp_growth_rate",
                    "prime_lending_rate",
                    "housing_starts",
                ]
            ].mean()

    df = hpi.merge(rent, on=["city", "date"], how="left")
    if not demo.empty:
        df = df.merge(demo, on=["city", "date"], how="left")
    if not macro.empty:
        df = df.merge(macro, on=["city", "date"], how="left")

    df = df.sort_values(["city", "date"]).drop_duplicates(["city", "date"], keep="last")

    for horizon, label in [(12, "12m"), (24, "24m"), (60, "5y"), (120, "10y")]:
        df[f"target_price_{label}_ahead"] = df.groupby("city")["price_benchmark"].shift(
            -horizon
        )

    df = df.dropna(subset=["target_price_12m_ahead"]).copy()

    df["created_at"] = datetime.now().astimezone()
    print(
        f"[INFO] ✅ Historical dataset built → {len(df)} rows, {len(df.columns)} columns"
    )
    print(f"[INFO] Cities: {sorted(df['city'].unique().tolist())}")
    print(f"[INFO] Date span: {df['date'].min().date()} → {df['date'].max().date()}")

    return df


def save_to_parquet(df: pd.DataFrame, path: str = "data/historical_features.parquet"):
    Path("data").mkdir(exist_ok=True, parents=True)
    df.to_parquet(path, index=False)
    print(f"[OK] Saved dataset → {path}")


if __name__ == "__main__":
    eng = get_engine()
    df = build_historical_dataset(eng, lookback_years=25)
    save_to_parquet(df)
