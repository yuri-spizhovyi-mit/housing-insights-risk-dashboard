"""
features_to_model_etl_v1_legacy_checker.py
-------------------------------------------------------
Enhanced QA & diagnostic tool for the restored v1-legacy
model_features table.

Checks:
  ✓ Schema correctness
  ✓ Missing values
  ✓ Duplicate keys
  ✓ Monthly timeseries continuity per city
  ✓ Raw value ranges
  ✓ MinMax scaled stability
  ✓ YoY sanity
  ✓ property_type_id validity
  ✓ Correlation structure
  ✓ Summary statistics

Does NOT modify the database. This is a safe validator.
"""

import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from dotenv import load_dotenv, find_dotenv
import os

# For optional plots — safe even if no display available
import matplotlib.pyplot as plt
import seaborn as sns


# ----------------------------------------------------------
# DB INIT
# ----------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)


# ----------------------------------------------------------
# EXPECTED SCHEMA FOR v1-legacy
# ----------------------------------------------------------
EXPECTED_COLUMNS = [
    "date",
    "city",
    "hpi_benchmark",
    "rent_avg_city",
    "mortgage_rate",
    "unemployment_rate",
    "overnight_rate",
    "population",
    "median_income",
    "migration_rate",
    "gdp_growth",
    "cpi_yoy",
    "hpi_change_yoy",
    "rent_change_yoy",
    "property_type_id",
    "hpi_scaled",
    "rent_scaled",
    "macro_scaled",
    "demographics_scaled",
    "features_version",
    "created_at",
]


# ----------------------------------------------------------
# LOAD FEATURES
# ----------------------------------------------------------
def load_features():
    df = pd.read_sql_query(
        "SELECT * FROM public.model_features ORDER BY date, city;", engine
    )
    df["date"] = pd.to_datetime(df["date"])
    return df


# ----------------------------------------------------------
# CHECK 1: Schema correctness
# ----------------------------------------------------------
def check_schema(df):
    print("\n=== CHECK 1: SCHEMA VALIDATION ===")

    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    extra = [c for c in df.columns if c not in EXPECTED_COLUMNS]

    if missing:
        print("[ERROR] Missing columns:", missing)
    else:
        print("[OK] No missing columns.")

    if extra:
        print("[WARN] Unexpected extra columns:", extra)
    else:
        print("[OK] No unexpected columns.")


# ----------------------------------------------------------
# CHECK 2: Missing values
# ----------------------------------------------------------
def check_missing(df):
    print("\n=== CHECK 2: MISSING VALUES ===")
    nulls = df.isna().sum()
    nulls = nulls[nulls > 0]

    if nulls.empty:
        print("[OK] No missing values.")
    else:
        print("[WARN] Missing values found:")
        print(nulls)


# ----------------------------------------------------------
# CHECK 3: Key uniqueness
# ----------------------------------------------------------
def check_primary_key(df):
    print("\n=== CHECK 3: DUPLICATE (date, city) ===")
    dups = df.duplicated(subset=["date", "city"]).sum()

    if dups > 0:
        print(f"[ERROR] Found {dups} duplicate rows for (date, city).")
    else:
        print("[OK] No duplicate keys.")


# ----------------------------------------------------------
# CHECK 4: Monthly continuity per city
# ----------------------------------------------------------
def check_continuity(df):
    print("\n=== CHECK 4: TIMESERIES CONTINUITY ===")

    for city, group in df.groupby("city"):
        group = group.sort_values("date")
        diffs = group["date"].diff().dt.days.dropna()

        if not all((diffs >= 28) & (diffs <= 31)):
            print(f"[WARN] {city}: Missing or irregular monthly dates.")
        else:
            print(f"[OK] {city}: monthly continuity good.")


# ----------------------------------------------------------
# CHECK 5: Property type sanity
# ----------------------------------------------------------
def check_property_type(df):
    print("\n=== CHECK 5: PROPERTY TYPE ID ===")

    allowed = {0, 1, 2}
    invalid = df[~df["property_type_id"].isin(allowed)]

    if len(invalid) > 0:
        print(
            f"[ERROR] Invalid property_type_id values found:\n{invalid[['date', 'city', 'property_type_id']]}"
        )
    else:
        print("[OK] All property_type_id values are valid (0, 1, 2).")


# ----------------------------------------------------------
# CHECK 6: Range sanity for raw data
# ----------------------------------------------------------
def check_ranges(df):
    print("\n=== CHECK 6: RAW FEATURE RANGES ===")

    checks = {
        "hpi_benchmark": (50_000, 3_000_000),
        "rent_avg_city": (300, 5000),
        "population": (1000, 10_000_000),
        "mortgage_rate": (0, 20),
        "unemployment_rate": (0, 20),
        "overnight_rate": (-5, 50),
        "median_income": (10_000, 200_000),
        "migration_rate": (-5, 5),
        "gdp_growth": (-10, 10),
        "cpi_yoy": (-5, 20),
    }

    for col, (lo, hi) in checks.items():
        bad = df[(df[col] < lo) | (df[col] > hi)]
        if not bad.empty:
            print(f"[WARN] {col}: {len(bad)} values outside expected range.")
        else:
            print(f"[OK] {col} within expected range.")


# ----------------------------------------------------------
# CHECK 7: Scaled feature sanity (0–1 bounds)
# ----------------------------------------------------------
def check_scaled(df):
    print("\n=== CHECK 7: SCALED FEATURES ===")

    scaled_cols = ["hpi_scaled", "rent_scaled", "macro_scaled", "demographics_scaled"]

    for col in scaled_cols:
        if (df[col] < -0.01).any() or (df[col] > 1.01).any():
            print(f"[ERROR] {col}: Values out of expected MinMax [0,1] range.")
        else:
            print(f"[OK] {col}: within [0,1] range.")


# ----------------------------------------------------------
# CHECK 8: YoY realism
# ----------------------------------------------------------
def check_yoy(df):
    print("\n=== CHECK 8: YOY FEATURES ===")

    for col in ["hpi_change_yoy", "rent_change_yoy"]:
        if df[col].abs().max() > 1:
            print(f"[WARN] {col}: Extreme YoY values detected (>100%).")
        else:
            print(f"[OK] {col} reasonably scaled.")


# ----------------------------------------------------------
# CHECK 9: Correlation heatmap (optional)
# ----------------------------------------------------------
def check_correlation(df):
    print("\n=== CHECK 9: CORRELATIONS (saved to correlation.png) ===")

    corr = df.select_dtypes(include=[float, int]).corr(numeric_only=True)

    plt.figure(figsize=(15, 12))
    sns.heatmap(corr, cmap="coolwarm", annot=False)
    plt.title("Feature Correlation Heatmap")
    plt.tight_layout()
    plt.savefig("correlation.png")

    print("[OK] correlation.png generated.")


# ----------------------------------------------------------
# RUN ALL CHECKS
# ----------------------------------------------------------
def main():
    print("[INFO] Loading model_features...")
    df = load_features()

    print("[INFO] Running full diagnostics...")

    check_schema(df)
    check_missing(df)
    check_primary_key(df)
    check_continuity(df)
    check_property_type(df)
    check_ranges(df)
    check_scaled(df)
    check_yoy(df)

    # optional: visually inspect correlations
    check_correlation(df)

    print("\n[DONE] Model feature diagnostics completed.\n")


if __name__ == "__main__":
    main()
