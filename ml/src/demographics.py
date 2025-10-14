"""
etl/demographics.py — ETL adapter for demographic indicators
------------------------------------------------------------
Loads and writes population, migration, and income data per city and date.
Source: ml/data/demographics.csv (StatCan or custom local file)
Destination: public.demographics
"""

import pandas as pd
from datetime import datetime
from sqlalchemy import text
from ml.src.etl import base


def load_raw_demographics(path: str) -> pd.DataFrame:
    """Load demographics CSV file."""
    print(f"[DEBUG] Loading demographics from: {path}")
    df = pd.read_csv(path)
    print("[DEBUG] Columns:", list(df.columns))
    return df


def clean_demographics(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize demographics data."""
    print("[DEBUG] Cleaning demographics data...")
    df = df.copy()

    # Rename columns to match target table
    rename_map = {
        "avg_disposable_income": "median_income",
        "net_migration": "migration_rate",  # rename for consistency
    }
    df.rename(columns=rename_map, inplace=True)

    # Parse date and enforce monthly period
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["date"] = df["date"].dt.to_period("M").dt.to_timestamp()

    # Standardize city naming
    df["city"] = df["city"].str.title()

    # Convert numeric fields
    for col in ["population", "migration_rate", "median_income"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Sort and drop duplicates
    df = df.sort_values(["city", "date"]).drop_duplicates(subset=["city", "date"])

    # Fill missing months per city if any gaps
    df = df.groupby("city").apply(lambda g: g.ffill()).reset_index(drop=True)

    df["created_at"] = datetime.utcnow()
    print(f"[DEBUG] Cleaned demographics rows: {len(df)}")
    return df


def run(ctx):
    """Entrypoint for demographics ETL."""
    print("[DEBUG] Starting demographics ETL...")
    engine = base.get_engine()

    # Path to CSV (you can parameterize this later)
    csv_path = "ml/data/demographics.csv"

    df_raw = load_raw_demographics(csv_path)
    df_clean = clean_demographics(df_raw)

    base.write_table(df_clean, "demographics", ctx)
    print("[INFO] ✅ Demographics successfully written to public.demographics")


if __name__ == "__main__":
    from ml.src.etl.utils.context import default_context

    ctx = default_context()
    run(ctx)
