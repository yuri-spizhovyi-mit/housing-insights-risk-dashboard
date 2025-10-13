"""
Feature Engineering Module (v2.5 hybrid)
----------------------------------------
Combines macro-level (BoC, StatCan, CREA) and micro-level (Craigslist-derived) data.

Reads:
  - public.house_price_index
  - public.listings_raw
  - public.listings_features
  - public.metrics
Writes:
  - public.features
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
    raise EnvironmentError("DATABASE_URL not found in .env file")

engine = create_engine(DATABASE_URL)


def log(msg: str):
    print(f"[build_features] {msg}")


# -----------------------------------------------------------
# 2. Load sources
# -----------------------------------------------------------
def _load(engine):
    """Load HPI, listings_raw, listings_features, and macro metrics."""
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
        listings_micro = pd.read_sql(
            """
            SELECT
                lr.city,
                date_trunc('month', lr.date_posted)::date AS date,
                AVG(lf.price_per_sqft) AS price_to_sqft,
                AVG(lf.bedrooms)       AS bedrooms_avg,
                AVG(lf.bathrooms)      AS bathrooms_avg,
                AVG(lf.area_sqft)      AS sqft_avg
            FROM public.listings_features lf
            JOIN public.listings_raw lr ON lf.listing_id = lr.listing_id
            WHERE lr.date_posted IS NOT NULL
            GROUP BY 1, 2
        """,
            conn,
        )
        metrics = pd.read_sql(
            "SELECT date, city, metric, value FROM public.metrics", conn
        )
    return hpi, listings, listings_micro, metrics


# -----------------------------------------------------------
# 3. Helpers
# -----------------------------------------------------------
def _aggregate_rent(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate monthly rent metrics per city."""
    grouped = (
        df.groupby(["city", "date"])
        .agg(
            rent_index=("price", "median"),
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
    return df.pivot_table(
        index=["date", "city"], columns="measure", values="index_value"
    ).reset_index()


def _pivot_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df["metric"] = df["metric"].str.lower()
    return df.pivot_table(
        index=["date", "city"], columns="metric", values="value"
    ).reset_index()


def _spread_canada_macros(df: pd.DataFrame, cities: list) -> pd.DataFrame:
    """
    Spread national (city='Canada') macro metrics to all local cities.
    """
    if "Canada" not in df["city"].unique():
        return df

    canada = df[df["city"] == "Canada"].drop(columns=["city"])
    local = df[df["city"] != "Canada"]

    out = []
    for city in cities:
        city_df = local[local["city"] == city]
        merged = pd.merge(
            city_df, canada, on="date", how="left", suffixes=("", "_national")
        )
        merged["city"] = city
        out.append(merged)

    return pd.concat(out, ignore_index=True)


# -----------------------------------------------------------
# 4. Feature engineering
# -----------------------------------------------------------
def _engineer(df: pd.DataFrame) -> pd.DataFrame:
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
            df[newcol] = df.groupby("city")[col].pct_change(fill_method=None)

    return df


# -----------------------------------------------------------
# 5. Build
# -----------------------------------------------------------
def build_features(engine):
    log("📥 Loading source tables...")
    hpi, listings, listings_micro, metrics = _load(engine)
    log(
        f"Loaded hpi={len(hpi)}, listings={len(listings)}, micro={len(listings_micro)}, metrics={len(metrics)}"
    )

    rent = _aggregate_rent(listings)
    hpi_wide = _pivot_hpi(hpi)
    metrics_wide = _pivot_metrics(metrics)

    cities = sorted(set(hpi_wide["city"]).union(set(rent["city"])))
    metrics_expanded = _spread_canada_macros(metrics_wide, cities)

    merged = (
        hpi_wide.merge(rent, on=["date", "city"], how="outer")
        .merge(metrics_expanded, on=["date", "city"], how="left")
        .merge(listings_micro, on=["date", "city"], how="left", suffixes=("", "_micro"))
    )

    features = _engineer(merged)
    features = (
        features.dropna(subset=["date"])
        .drop_duplicates(subset=["city", "date"])
        .sort_values(["city", "date"])
        .reset_index(drop=True)
    )

    log(f"✅ Built features: {features.shape[0]} rows × {features.shape[1]} cols")
    return features


# -----------------------------------------------------------
# 6. Write
# -----------------------------------------------------------
def write_features(engine, df: pd.DataFrame):
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
                price_avg, bedrooms_avg, bathrooms_avg, sqft_avg,
                price_to_rent, price_to_sqft, hpi_mom_pct, rent_mom_pct,
                features_version
            )
            SELECT
                date, city,
                hpi_composite_sa, hpi_apartment_sa, hpi_townhouse_sa,
                rent_index,
                overnightrate, primerate, cpi_allitems, unemploymentrate, gdp_growthrate,
                price_avg, bedrooms_avg, bathrooms_avg, sqft_avg,
                price_to_rent, price_to_sqft, hpi_mom_pct, rent_mom_pct,
                'v2.5'
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
                price_to_rent = EXCLUDED.price_to_rent,
                price_to_sqft = EXCLUDED.price_to_sqft,
                hpi_mom_pct = EXCLUDED.hpi_mom_pct,
                rent_mom_pct = EXCLUDED.rent_mom_pct,
                features_version = EXCLUDED.features_version;
            DROP TABLE public._features_stage;
        """)
        )

    log(f"✅ Upserted {len(df)} rows into public.features")


# -----------------------------------------------------------
# 7. Main
# -----------------------------------------------------------
if __name__ == "__main__":
    log("🚀 Starting build_features")
    df = build_features(engine)
    write_features(engine, df)
    log("🏁 build_features completed successfully")
