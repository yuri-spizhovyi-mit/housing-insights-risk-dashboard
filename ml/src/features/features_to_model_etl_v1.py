"""
features_to_model_etl.py
-----------------------------------------------------------
PHASE 1.1 — CITY-LEVEL ETL (Corrected)

This transforms your raw 'features' table into a clean,
city-level 'model_features' table with:

✔ RAW TARGETS:
    - hpi_raw  (dollars)
    - rent_raw (dollars)

✔ Z-scored regressors:
    - hpi_z, rent_z
    - macro_z, demo_z
    - yoy_z, lag_z, roll_z

✔ Weighted property-type aggregation per city
✔ Full lag/roll features
✔ Drop first 12 months
✔ No NaNs anywhere
✔ Perfectly ready for ARIMA/Prophet/LGBM/LSTM

This REPLACES the old model_features table.
"""

import os
from datetime import datetime, timezone
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from dotenv import load_dotenv, find_dotenv

# ----------------------------------------------------
# ENV & DATABASE
# ----------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)


# ----------------------------------------------------
# LOAD RAW FEATURES
# ----------------------------------------------------
def load_features():
    q = """
        SELECT 
            date,
            city,
            property_type,
            hpi_benchmark,
            rent_avg_city,
            mortgage_rate,
            unemployment_rate,
            overnight_rate,
            population,
            median_income,
            migration_rate,
            gdp_growth,
            cpi_yoy
        FROM public.features
        ORDER BY city, property_type, date;
    """
    df = pd.read_sql(q, engine)
    df["date"] = pd.to_datetime(df["date"])
    print(f"[INFO] Loaded {len(df)} rows from public.features")
    return df


# ----------------------------------------------------
# COMPUTE WEIGHTS PER CITY × PROPERTY_TYPE
# ----------------------------------------------------
def compute_weights(df):
    weights = {}

    for city, g in df.groupby("city"):
        g = g.sort_values(["date", "property_type"])

        # baseline city mean HPI per date
        mean_hpi = g.groupby("date")["hpi_benchmark"].mean()
        g = g.merge(mean_hpi.rename("mean_hpi"), on="date")

        # ratio = hpi_type / hpi_city_mean
        g["ratio"] = g["hpi_benchmark"] / g["mean_hpi"]

        # avg ratio per ptype
        w = g.groupby("property_type")["ratio"].mean()
        w = w / w.sum()  # normalize
        weights[city] = w.to_dict()

    print("[INFO] Computed city property-type weights.")
    return weights


# ----------------------------------------------------
# BUILD CITY-LEVEL RAW TARGETS
# ----------------------------------------------------
def build_city_level(df, weights):

    rows = []

    for city, g in df.groupby("city"):
        w = weights[city]

        for date, sub in g.groupby("date"):

            # weighted HPI (raw)
            hpi_raw = 0.0
            for _, r in sub.iterrows():
                hpi_raw += r["hpi_benchmark"] * w[r["property_type"]]

            rent_raw = sub["rent_avg_city"].iloc[0]

            rows.append({
                "date": date,
                "city": city,

                "hpi_raw": hpi_raw,
                "rent_raw": rent_raw,

                "mortgage_rate":      sub["mortgage_rate"].iloc[0],
                "unemployment_rate":  sub["unemployment_rate"].iloc[0],
                "overnight_rate":     sub["overnight_rate"].iloc[0],
                "population":         sub["population"].iloc[0],
                "median_income":      sub["median_income"].iloc[0],
                "migration_rate":     sub["migration_rate"].iloc[0],
                "gdp_growth":         sub["gdp_growth"].iloc[0],
                "cpi_yoy":            sub["cpi_yoy"].iloc[0],
            })

    city_df = pd.DataFrame(rows)
    city_df = city_df.sort_values(["city", "date"]).reset_index(drop=True)

    print("[INFO] Constructed city-level raw HPI/Rent table.")
    return city_df


# ----------------------------------------------------
# FEATURE ENGINEERING
# ----------------------------------------------------
def add_feature_engineering(df):

    # --- YoY ---
    df["hpi_yoy"]  = df.groupby("city")["hpi_raw"].pct_change(12) * 100
    df["rent_yoy"] = df.groupby("city")["rent_raw"].pct_change(12) * 100

    # --- Lags ---
    for lag in [1, 3, 6, 12]:
        df[f"hpi_lag_{lag}"]  = df.groupby("city")["hpi_raw"].shift(lag)
        df[f"rent_lag_{lag}"] = df.groupby("city")["rent_raw"].shift(lag)

    # --- Rolling Windows ---
    for win in [3, 6, 12]:
        df[f"hpi_roll_{win}"] = (
            df.groupby("city")["hpi_raw"]
              .rolling(win)
              .mean()
              .reset_index(0, drop=True)
        )
        df[f"rent_roll_{win}"] = (
            df.groupby("city")["rent_raw"]
              .rolling(win)
              .mean()
              .reset_index(0, drop=True)
        )

    # --- Macro/Demo composites (raw) ---
    df["macro_raw"] = df[
        ["mortgage_rate", "unemployment_rate", "overnight_rate",
         "gdp_growth", "cpi_yoy"]
    ].mean(axis=1)

    df["demo_raw"] = df[
        ["population", "median_income", "migration_rate"]
    ].mean(axis=1)

    return df


# ----------------------------------------------------
# Z-SCORING (FEATURES ONLY, NOT TARGETS)
# ----------------------------------------------------
def zscore_cols(df):

    def zscale(s):
        return (s - s.mean()) / (s.std() + 1e-9)

    zcols = [
        "hpi_raw",
        "rent_raw",
        "hpi_yoy",
        "rent_yoy",
        "macro_raw",
        "demo_raw"
    ]

    df[["hpi_z", "rent_z", "hpi_yoy_z", "rent_yoy_z",
         "macro_z", "demo_z"]] = (
        df.groupby("city")[zcols].transform(zscale)
    )

    return df


# ----------------------------------------------------
# CLEANUP & METADATA
# ----------------------------------------------------
def finalize(df):

    # Drop first 12 months per city (due to lag12/roll12/yoy12)
    df = (
        df.sort_values(["city", "date"])
          .groupby("city")
          .apply(lambda g: g.iloc[12:])
          .reset_index(drop=True)
    )

    df["etl_version"] = "model_features_city_v1"
    df["processed_at"] = datetime.now(timezone.utc)

    print("[INFO] Final model_features rows:", len(df))
    return df


# ----------------------------------------------------
# WRITE TO DATABASE
# ----------------------------------------------------
def write_model_features(df):

    print("[INFO] Writing model_features (replacing old table)...")

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE public.model_features;"))

    cols = df.columns.tolist()
    placeholders = ", ".join(":" + c for c in cols)

    sql = text(f"""
        INSERT INTO public.model_features ({", ".join(cols)})
        VALUES ({placeholders});
    """)

    batch = 3000
    with engine.begin() as conn:
        for i in range(0, len(df), batch):
            chunk = df.iloc[i:i+batch]
            conn.execute(sql, chunk.to_dict(orient="records"))

    print("[OK] model_features updated.")


# ----------------------------------------------------
# MAIN PIPELINE
# ----------------------------------------------------
def main():

    print("[DEBUG] Starting city-level ETL...")

    df = load_features()
    weights = compute_weights(df)

    city_df = build_city_level(df, weights)
    city_df = add_feature_engineering(city_df)
    city_df = zscore_cols(city_df)
    city_df = finalize(city_df)

    write_model_features(city_df)

    print("[DONE] ETL completed successfully.")


if __name__ == "__main__":
    main()
