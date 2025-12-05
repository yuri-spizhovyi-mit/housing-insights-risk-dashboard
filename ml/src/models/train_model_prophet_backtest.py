#!/usr/bin/env python3
"""
train_model_prophet_backtest.py

Backtesting Prophet on historical data.
Train:   2005-01-01 → 2020-12-01
Validate:2021-01-01 → last available date

Writes predictions with y_true into model_predictions.
"""

import pandas as pd
import uuid
import os
from datetime import datetime, timezone
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from prophet import Prophet

# -------------------------------------------------------------------
# ENVIRONMENT
# -------------------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
DATABASE_URL = os.getenv("NEON_DATABASE_URL") or os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)

CUTOFF = pd.Timestamp("2020-12-01")

REGRESSORS = [
    "mortgage_rate_z",
    "unemployment_rate_z",
    "cpi_yoy_z",
    "roll_3_z",
    "roll_6_z",
]


# -------------------------------------------------------------------
# LOAD FEATURES (processed dataset)
# -------------------------------------------------------------------
def load_features():
    q = """
        SELECT
            date,
            city,
            hpi_benchmark,
            rent_avg_city,
            mortgage_rate_z, unemployment_rate_z, cpi_yoy_z,
            roll_3_z, roll_6_z
        FROM public.model_features
        ORDER BY city, date;
    """
    df = pd.read_sql(q, engine)
    df["date"] = pd.to_datetime(df["date"])
    return df


# -------------------------------------------------------------------
# TRAIN + FORECAST CITY/TARGET
# -------------------------------------------------------------------
def backtest_city_target(df, city, target_col, target_name):
    g = df[df.city == city].sort_values("date").copy()

    # Split train vs validation
    train = g[g["date"] <= CUTOFF].copy()
    valid = g[g["date"] > CUTOFF].copy()

    if len(train) < 24 or len(valid) < 6:
        print(f"[WARN] Prophet backtest: not enough data for {city}/{target_name}")
        return []

    # Prepare Prophet frames
    dfp_train = train.rename(columns={"date": "ds", target_col: "y"})
    dfp_train["y"] = dfp_train["y"].astype(float)

    model = Prophet()
    for r in REGRESSORS:
        model.add_regressor(r)

    model.fit(dfp_train[["ds", "y"] + REGRESSORS])

    # Predict only VALIDATION period
    future = valid.rename(columns={"date": "ds"}).copy()
    future["y"] = None  # unused but required for Prophet internal consistency

    fc = model.predict(future)

    rows = []

    # fc rows correspond exactly to valid dates
    for (_, pred_row), (_, val_row) in zip(fc.iterrows(), valid.iterrows()):
        # Calculate horizon in months since cutoff date
        horizon = int((pred_row["ds"].to_period("M") - CUTOFF.to_period("M")).n)

        rows.append(
            {
                "run_id": str(uuid.uuid4()),
                "model_name": "prophet_backtest",
                "target": target_name,
                "horizon_months": horizon,  # <-- FIXED HERE
                "city": city,
                "property_type": None,
                "beds": None,
                "baths": None,
                "sqft_min": None,
                "sqft_max": None,
                "year_built_min": None,
                "year_built_max": None,
                "predict_date": pred_row["ds"],
                "yhat": float(max(0.0, pred_row["yhat"])),
                "yhat_lower": float(max(0.0, pred_row["yhat_lower"])),
                "yhat_upper": float(max(0.0, pred_row["yhat_upper"])),
                "y_true": float(val_row[target_col]),
                "features_version": "features_backtest_v1",
                "model_artifact_uri": None,
                "created_at": datetime.now(timezone.utc),
                "is_micro": False,
            }
        )

    print(f"[OK] Prophet backtest: {city}/{target_name} ({len(rows)} rows)")
    return rows


# -------------------------------------------------------------------
# WRITE RESULTS
# -------------------------------------------------------------------
def write_predictions(rows):
    if not rows:
        return

    sql = text("""
        INSERT INTO public.model_predictions(
            run_id, model_name, target, horizon_months,
            city, property_type,
            beds, baths, sqft_min, sqft_max,
            year_built_min, year_built_max,
            predict_date, yhat, yhat_lower, yhat_upper,
            y_true,                         -- <-- NEW!!
            features_version, model_artifact_uri,
            created_at, is_micro
        )
        VALUES (
            :run_id, :model_name, :target, :horizon_months,
            :city, :property_type,
            :beds, :baths, :sqft_min, :sqft_max,
            :year_built_min, :year_built_max,
            :predict_date, :yhat, :yhat_lower, :yhat_upper,
            :y_true,
            :features_version, :model_artifact_uri,
            :created_at, :is_micro
        );
    """)

    with engine.begin() as conn:
        conn.execute(sql, rows)

    print(f"[OK] Inserted {len(rows)} Prophet BACKTEST predictions.")


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------
def main():
    print("[DEBUG] Starting Prophet BACKTEST...")

    df = load_features()
    all_rows = []

    for city in df.city.unique():
        all_rows.extend(backtest_city_target(df, city, "hpi_benchmark", "price"))
        all_rows.extend(backtest_city_target(df, city, "rent_avg_city", "rent"))

    write_predictions(all_rows)

    print("[DONE] Prophet BACKTEST complete.")


if __name__ == "__main__":
    main()
