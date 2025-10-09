# ml/src/features/build_features.py
"""
Feature Engineering Module
==========================
Builds city-date macro-level features for forecasting, risk, and anomaly models.

Reads:
  - public.house_price_index     (CREA HPI)
  - public.rent_index            (aggregated listing rents)
  - public.metrics               (BoC, StatCan, macro factors)

Writes:
  - public.features (via upsert)

This script uses DATABASE_URL from your .env file for the Postgres connection.
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime

# -----------------------------------------------------------
# 1. Load environment variables
# -----------------------------------------------------------
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise EnvironmentError("DATABASE_URL not found in .env file.")

# -----------------------------------------------------------
# 2. Utility functions
# -----------------------------------------------------------

def log(msg: str):
    """Pretty logger with timestamp."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def _load(engine):
    with engine.begin() as conn:
        hpi = pd.read_sql("SELECT date, city, measure, index_value FROM public.house_price_index", conn)
        rent = pd.read_sql("""
            SELECT date, city,
                   index_value AS rent_index,
                   median_rent_apartment_1br AS median_rent_1br,
                   median_rent_apartment_2br AS median_rent_2br,
                   median_rent_apartment_3br AS median_rent_3br
            FROM public.rent_index
        """, conn)
        metrics = pd.read_sql("SELECT date, city, metric, value FROM public.metrics", conn)
    return hpi, rent, metrics


def _pivot_hpi(df: pd.DataFrame) -> pd.DataFrame:
    rename = {
        "Composite_Benchmark_SA": "hpi_composite_sa",
        "Apartment_Benchmark_SA": "hpi_apartment_sa",
        "Townhouse_Benchmark_SA": "hpi_townhouse_sa",
    }
    df["measure"] = df["measure"].map(lambda m: rename.get(m, m))
    wide = df.pivot_table(index=["date", "city"], columns="measure", values="index_value").reset_index()
    return wide


def _pivot_metrics(df: pd.DataFrame) -> pd.DataFrame:
    return df.pivot_table(index=["date", "city"], columns="metric", values="value").reset_index()


def _spread_canada_macros(df: pd.DataFrame, cities: list) -> pd.DataFrame:
    """Spread national metrics ('Canada') to all local cities."""
    if "Canada" not in df["city"].unique():
        return df

    canada = df[df["city"] == "Canada"].drop(columns=["city"])
    out = []

    for city in cities:
        if city == "Canada":
            out.append(df[df["city"] == "Canada"])
            continue

        city_df = df[df["city"] == city]
        merged = pd.merge(city_df, canada, on="date", how="left", suffixes=("", "_national"))
        merged["city"] = city
        out.append(merged)

    return pd.concat(out, ignore_index=True)


def _engineer(df: pd.DataFrame) -> pd.DataFrame:
    """Create simple derived features."""
    df = df.sort_values(["city", "date"]).copy()

    # Price-to-rent ratio
    if "hpi_composite_sa" in df.columns and "rent_index" in df.columns:
        df["price_to_rent"] = df["hpi_composite_sa"] / df["rent_index"].replace({0: pd.NA})

    # Month-over-month percentage changes
    for col, newcol in [("hpi_composite_sa", "hpi_mom_pct"), ("rent_index", "rent_mom_pct")]:
        if col in df.columns:
            df[newcol] = df.groupby("city")[col].pct_change()

    return df


def write_features(engine, df: pd.DataFrame):
    """Upsert features into the database."""
    if df.empty:
        log("⚠️ No features to write.")
        return

    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS public._features_stage;"))
        df.to_sql("_features_stage", conn.connection, schema="public", if_exists="replace", index=False)
        conn.execute(text("""
            INSERT INTO public.features AS f
            (date, city,
             hpi_composite_sa, hpi_apartment_sa, hpi_townhouse_sa,
             rent_index, median_rent_1br, median_rent_2br, median_rent_3br,
             BoC_OvernightRate, BoC_PrimeRate, CPI_AllItems, UnemploymentRate, GDP_GrowthRate,
             price_to_rent, hpi_mom_pct, rent_mom_pct, features_version)
            SELECT date, city,
                   hpi_composite_sa, hpi_apartment_sa, hpi_townhouse_sa,
                   rent_index, median_rent_1br, median_rent_2br, median_rent_3br,
                   BoC_OvernightRate, BoC_PrimeRate, CPI_AllItems, UnemploymentRate, GDP_GrowthRate,
                   price_to_rent, hpi_mom_pct, rent_mom_pct, 'v1.0'
            FROM public._features_stage
            ON CONFLICT (date, city) DO UPDATE SET
                hpi_composite_sa = EXCLUDED.hpi_composite_sa,
                rent_index = EXCLUDED.rent_index,
                BoC_OvernightRate = EXCLUDED.BoC_OvernightRate,
                price_to_rent = EXCLUDED.price_to_rent,
                hpi_mom_pct = EXCLUDED.hpi_mom_pct,
                rent_mom_pct = EXCLUDED.rent_mom_pct,
                features_version = EXCLUDED.features_version;
            DROP TABLE public._features_stage;
        """))
        log(f"✅ Upserted {len(df)} feature rows.")


def build_features(engine):
    """Main builder logic."""
    log("📥 Loading source tables...")
    hpi, rent, metrics = _load(engine)
    log(f"Loaded hpi={len(hpi)}, rent={len(rent)}, metrics={len(metrics)}")

    hpi_wide = _pivot_hpi(hpi)
    metrics_wide = _pivot_metrics(metrics)
    cities = sorted(set(hpi_wide["city"]).union(set(rent["city"])))

    metrics_spread = _spread_canada_macros(metrics_wide, cities)
    merged = hpi_wide.merge(rent, on=["date", "city"], how="outer")
    merged = merged.merge(metrics_spread, on=["date", "city"], how="left")

    features = _engineer(merged)
    features = features.dropna(subset=["date"]).sort_values(["city", "date"]).reset_index(drop=True)

    log(f"✅ Built feature table: {features.shape[0]} rows, {features.shape[1]} columns.")
    return features


def main():
    """Entry point."""
    log("🚀 Starting Feature Engineering")
    engine = create_engine(DATABASE_URL)
    df = build_features(engine)
    write_features(engine, df)
    log("🏁 Feature engineering completed successfully.")


if __name__ == "__main__":
    main()
