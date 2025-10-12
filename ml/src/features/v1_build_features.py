# ml/src/features/build_features.py
"""
Feature Engineering Module
==========================
Builds city-date macro-level features for forecasting, risk, and anomaly models.

Reads:
  - public.house_price_index     (CREA HPI)
  - public.listings_raw          (raw rental listings)
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
# 1. Environment setup
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
    """Load HPI, listings, and macro metrics."""
    with engine.begin() as conn:
        hpi = pd.read_sql(
            "SELECT date, city, measure, index_value FROM public.house_price_index",
            conn,
        )
        listings = pd.read_sql(
            """
            SELECT
                city,
                date_trunc('month', date_posted)::date AS date,
                price,
                bedrooms,
                bathrooms,
                area_sqft,
                property_type
            FROM public.listings_raw
            WHERE listing_type = 'rent'
              AND price IS NOT NULL
              AND city IS NOT NULL
            """,
            conn,
        )
        metrics = pd.read_sql(
            "SELECT date, city, metric, value FROM public.metrics", conn
        )
    return hpi, listings, metrics


def _aggregate_rent(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate monthly rent medians and averages per city."""
    grouped = (
        df.groupby(["city", "date"])
        .agg(
            rent_index=("price", "median"),
            median_rent_1br=(
                "price",
                lambda x: x[df.loc[x.index, "bedrooms"] == 1].median(),
            ),
            median_rent_2br=(
                "price",
                lambda x: x[df.loc[x.index, "bedrooms"] == 2].median(),
            ),
            median_rent_3br=(
                "price",
                lambda x: x[df.loc[x.index, "bedrooms"] == 3].median(),
            ),
            price_avg=("price", "mean"),
            bedrooms_avg=("bedrooms", "mean"),
            bathrooms_avg=("bathrooms", "mean"),
            sqft_avg=("area_sqft", "mean"),
        )
        .reset_index()
    )
    return grouped


def _pivot_hpi(df: pd.DataFrame) -> pd.DataFrame:
    rename = {
        "Composite_Benchmark_SA": "hpi_composite_sa",
        "Apartment_Benchmark_SA": "hpi_apartment_sa",
        "Townhouse_Benchmark_SA": "hpi_townhouse_sa",
    }
    df["measure"] = df["measure"].map(lambda m: rename.get(m, m))
    wide = df.pivot_table(
        index=["date", "city"], columns="measure", values="index_value"
    ).reset_index()
    return wide


def _pivot_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df["metric"] = df["metric"].str.lower()
    wide = df.pivot_table(
        index=["date", "city"], columns="metric", values="value"
    ).reset_index()
    return wide


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
        merged = pd.merge(
            city_df, canada, on="date", how="left", suffixes=("", "_national")
        )
        merged["city"] = city
        out.append(merged)
    return pd.concat(out, ignore_index=True)


def _engineer(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived ratios and growth rates."""
    df = df.sort_values(["city", "date"]).copy()

    if "hpi_composite_sa" in df.columns and "rent_index" in df.columns:
        df["price_to_rent"] = df["hpi_composite_sa"] / df["rent_index"].replace(
            {0: pd.NA}
        )

    if "price_avg" in df.columns and "sqft_avg" in df.columns:
        df["price_to_sqft"] = df["price_avg"] / df["sqft_avg"].replace({0: pd.NA})

    for col, newcol in [
        ("hpi_composite_sa", "hpi_mom_pct"),
        ("rent_index", "rent_mom_pct"),
    ]:
        if col in df.columns:
            df[newcol] = df.groupby("city")[col].pct_change()

    return df


def write_features(engine, df: pd.DataFrame):
    """Upsert features into public.features table."""
    if df.empty:
        log("⚠️ No features to write.")
        return

    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS public._features_stage;"))
        df.to_sql(
            "_features_stage",
            con=conn,
            schema="public",
            if_exists="replace",
            index=False,
        )

        conn.execute(
            text("""
            INSERT INTO public.features (
                date, city,
                hpi_composite_sa, hpi_apartment_sa, hpi_townhouse_sa,
                rent_index,
                overnightrate, primerate, cpi_allitems, unemploymentrate, gdp_growthrate,
                price_avg, bedrooms_avg, bathrooms_avg, sqft_avg, property_type,
                price_to_rent, price_to_sqft, hpi_mom_pct, rent_mom_pct, price_mom_pct,
                features_version
            )
            SELECT date, city,
                hpi_composite_sa, hpi_apartment_sa, hpi_townhouse_sa,
                rent_index,
                overnightrate, primerate, cpi_allitems, unemploymentrate, gdp_growthrate,
                price_avg, bedrooms_avg, bathrooms_avg, sqft_avg, property_type,
                price_to_rent, price_to_sqft, hpi_mom_pct, rent_mom_pct, price_mom_pct,
                'v2.0'
            FROM public._features_stage
            ON CONFLICT (date, city)
            DO UPDATE SET
                rent_index = EXCLUDED.rent_index,
                overnightrate = EXCLUDED.overnightrate,
                primerate = EXCLUDED.primerate,
                cpi_allitems = EXCLUDED.cpi_allitems,
                unemploymentrate = EXCLUDED.unemploymentrate,
                gdp_growthrate = EXCLUDED.gdp_growthrate,
                price_avg = EXCLUDED.price_avg,
                bedrooms_avg = EXCLUDED.bedrooms_avg,
                bathrooms_avg = EXCLUDED.bathrooms_avg,
                sqft_avg = EXCLUDED.sqft_avg,
                property_type = EXCLUDED.property_type,
                price_to_rent = EXCLUDED.price_to_rent,
                price_to_sqft = EXCLUDED.price_to_sqft,
                hpi_mom_pct = EXCLUDED.hpi_mom_pct,
                rent_mom_pct = EXCLUDED.rent_mom_pct,
                price_mom_pct = EXCLUDED.price_mom_pct,
                features_version = EXCLUDED.features_version;
            DROP TABLE public._features_stage;
        """)
        )

        log(f"✅ Upserted {len(df)} feature rows.")


def build_features(engine):
    """Main feature building workflow."""
    log("📥 Loading source tables...")
    hpi, listings, metrics = _load(engine)
    log(f"Loaded hpi={len(hpi)}, listings={len(listings)}, metrics={len(metrics)}")

    rent = _aggregate_rent(listings)
    hpi_wide = _pivot_hpi(hpi)
    metrics_wide = _pivot_metrics(metrics)

    cities = sorted(set(hpi_wide["city"]).union(set(rent["city"])))
    metrics_spread = _spread_canada_macros(metrics_wide, cities)

    merged = hpi_wide.merge(rent, on=["date", "city"], how="outer").merge(
        metrics_spread, on=["date", "city"], how="left"
    )

    features = _engineer(merged)
    features = (
        features.dropna(subset=["date"])
        .sort_values(["city", "date"])
        .reset_index(drop=True)
    )

    log(
        f"✅ Built feature table: {features.shape[0]} rows, {features.shape[1]} columns."
    )
    return features


def main():
    log("🚀 Starting Feature Engineering")
    engine = create_engine(DATABASE_URL)
    df = build_features(engine)
    write_features(engine, df)
    log("🏁 Feature engineering completed successfully.")


if __name__ == "__main__":
    main()
