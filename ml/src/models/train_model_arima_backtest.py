#!/usr/bin/env python3
"""
train_model_arima_backtest.py

Backtesting ARIMA on historical data.

TRAIN:
    date <= 2020-12-01
VALIDATE:
    2021-01-01 → last available date

Writes predictions with y_true to model_predictions.
"""

import pandas as pd
import numpy as np
import uuid
import os
import warnings
from datetime import datetime, timezone
from sqlalchemy import text, create_engine
from dotenv import load_dotenv, find_dotenv
import pmdarima as pm

warnings.filterwarnings("ignore")

# ---------------------------------------------------------
# ENVIRONMENT
# ---------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
DATABASE_URL = os.getenv("NEON_DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)

CUTOFF = pd.Timestamp("2020-12-01")


# ---------------------------------------------------------
# LOAD FEATURES
# ---------------------------------------------------------
def load_features():
    q = """
        SELECT
            date,
            city,
            hpi_benchmark,
            rent_avg_city
        FROM public.model_features
        ORDER BY city, date;
    """
    df = pd.read_sql(q, engine)
    df["date"] = pd.to_datetime(df["date"])
    return df


# ---------------------------------------------------------
# FIT AUTO ARIMA ON TRAINING SET
# ---------------------------------------------------------
def fit_arima(series):
    return pm.auto_arima(
        series,
        seasonal=False,
        error_action="ignore",
        suppress_warnings=True,
        stepwise=True,
        max_p=5,
        max_q=5,
        max_d=2,
    )


# ---------------------------------------------------------
# BACKTEST CITY + TARGET
# ---------------------------------------------------------
def backtest_city_target(df, city, target_col, target_name):
    g = df[df.city == city].sort_values("date")

    # Split into train and validation
    train = g[g["date"] <= CUTOFF].copy()
    valid = g[g["date"] > CUTOFF].copy()

    if len(train) < 36 or len(valid) < 6:
        print(f"[WARN] ARIMA backtest: not enough data for {city}/{target_name}")
        return []

    # Train ARIMA only on TRAIN data
    model = fit_arima(train[target_col])

    rows = []

    # Validation predictions: one-step ahead recursive forecasting
    # ARIMA must be refit / updated as ground truth becomes available
    history = train[target_col].tolist()

    for _, row in valid.iterrows():
        # Forecast next step
        fc, conf = model.predict(n_periods=1, return_conf_int=True)
        # Ensure consistent array shapes
        fc = np.array(fc).reshape(-1)
        conf = np.array(conf).reshape(-1, 2)
        pred = float(fc[0])
        lo = float(conf[0][0])
        hi = float(conf[0][1])

        # Append backtest prediction
        rows.append(
            {
                "run_id": str(uuid.uuid4()),
                "model_name": "arima_backtest",
                "target": target_name,
                "horizon_months": int(
                    (row["date"].to_period("M") - CUTOFF.to_period("M")).n
                ),
                "city": city,
                "property_type": None,
                "beds": None,
                "baths": None,
                "sqft_min": None,
                "sqft_max": None,
                "year_built_min": None,
                "year_built_max": None,
                "predict_date": row["date"],
                "yhat": max(0.0, pred),
                "yhat_lower": max(0.0, lo),
                "yhat_upper": max(0.0, hi),
                "y_true": float(row[target_col]),  # <- TRUE VALUE
                "features_version": "features_backtest_v1",
                "model_artifact_uri": None,
                "created_at": datetime.now(timezone.utc),
                "is_micro": False,
            }
        )

        # Update ARIMA model with ACTUAL value so it stays realistic
        history.append(row[target_col])
        model.update(row[target_col])

    print(f"[OK] ARIMA backtest: {city}/{target_name} ({len(rows)} rows)")
    return rows


# ---------------------------------------------------------
# WRITE RESULTS
# ---------------------------------------------------------
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
            y_true,
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

    print(f"[OK] Inserted {len(rows)} ARIMA BACKTEST predictions.")


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
def main():
    print("[DEBUG] Starting ARIMA BACKTEST...")

    df = load_features()
    all_rows = []

    for city in df.city.unique():
        all_rows.extend(backtest_city_target(df, city, "hpi_benchmark", "price"))
        all_rows.extend(backtest_city_target(df, city, "rent_avg_city", "rent"))

    write_predictions(all_rows)

    print("[DONE] ARIMA BACKTEST complete.")


if __name__ == "__main__":
    main()
