"""
build_features.py — Macro-only feature engineering module
----------------------------------------------------------
Generates a clean contextual feature table (public.features)
aligned on (city, date) using macroeconomic time-series data:
- House Price Index (CREA/CMHC)
- CPI, GDP, Unemployment Rate (StatCan)
- BoC rates (prime, mortgage)
"""

import pandas as pd
from sqlalchemy import text
from datetime import datetime
from ml.src.etl import base


def load_metric(engine, metric: str) -> pd.DataFrame:
    """Load a single metric time series from public.metrics."""
    query = text("""
        SELECT city, date, value
        FROM public.metrics
        WHERE metric = :metric
        ORDER BY city, date
    """)
    df = pd.read_sql(query, engine, params={"metric": metric})
    df.rename(columns={"value": metric}, inplace=True)
    return df


def load_hpi(engine) -> pd.DataFrame:
    """Load CREA/CMHC house price index data."""
    query = text("""
        SELECT city, date, hpi_composite_sa
        FROM public.house_price_index
        ORDER BY city, date
    """)
    return pd.read_sql(query, engine)


def merge_features(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """Outer join all dataframes on city + date."""
    from functools import reduce
    return reduce(
        lambda left, right: pd.merge(left, right, on=["city", "date"], how="outer"),
        dfs
    )


def build_macro_features(engine) -> pd.DataFrame:
    """Create the macroeconomic feature matrix."""
    # --- 1. Load base tables ---
    print("[DEBUG] Loading macroeconomic metrics...")

    hpi_df = load_hpi(engine)
    cpi_df = load_metric(engine, "StatCan_CPI_AllItems")
    gdp_df = load_metric(engine, "StatCan_GDP_GrowthRate")
    unemp_df = load_metric(engine, "StatCan_UnemploymentRate")
    prime_df = load_metric(engine, "BoC_PrimeRate")
    mortgage_df = load_metric(engine, "BoC_MortgageRate")

    # --- 2. Merge ---
    print("[DEBUG] Merging macro datasets...")
    df_merged = merge_features([hpi_df, cpi_df, gdp_df, unemp_df, prime_df, mortgage_df])

    # --- 3. Clean ---
    print("[DEBUG] Cleaning merged dataframe...")
    df_merged["date"] = pd.to_datetime(df_merged["date"])
    df_merged.sort_values(["city", "date"], inplace=True)
    df_merged = df_merged.drop_duplicates(subset=["city", "date"])
    df_merged = df_merged.ffill()

    # Drop global 'Canada' if desired
    df_merged = df_merged[df_merged["city"] != "Canada"]

    # --- 4. Add derived columns ---
    print("[DEBUG] Adding derived features...")
    df_merged["hpi_mom_pct"] = df_merged.groupby("city")["hpi_composite_sa"].pct_change() * 100
    df_merged["cpi_yoy_pct"] = df_merged.groupby("city")["StatCan_CPI_AllItems"].pct_change(12) * 100

    df_merged["features_version"] = "macro_v1.0"
    df_merged["created_at"] = datetime.utcnow()

    return df_merged


def run(ctx):
    """Entrypoint for ETL pipeline."""
    print("[DEBUG] Starting macro-only feature build...")
    engine = base.get_engine()

    df_features = build_macro_features(engine)
    print("[DEBUG] Columns in final feature table:", list(df_features.columns))
    print(f"[DEBUG] Total rows: {len(df_features)}")

    # --- Write to database ---
    base.write_features_upsert(df_features, ctx)
    print("[INFO] ✅ Macro-only features successfully written to public.features")


if __name__ == "__main__":
    from ml.src.utils.context import default_context
    ctx = default_context()
    run(ctx)
