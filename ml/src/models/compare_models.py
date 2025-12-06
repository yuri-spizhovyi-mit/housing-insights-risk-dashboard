#!/usr/bin/env python3
"""
compare_models.py

Evaluates Prophet, ARIMA, and LSTM using BACKTEST predictions.
Reads rows from model_predictions where:

    model_name IN ('prophet_backtest', 'arima_backtest', 'lstm_backtest')
    AND y_true IS NOT NULL

Computes:
    - MAE
    - MAPE
    - RMSE
    - MSE
    - R²

Writes metrics into public.model_comparison.
"""

import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text

# ---------------------------------------------------------
# ENVIRONMENT
# ---------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)

BACKTEST_MODELS = ["prophet_backtest", "arima_backtest", "lstm_backtest"]


# ---------------------------------------------------------
# METRICS
# ---------------------------------------------------------
def mae(y_true, y_pred):
    return float(np.mean(np.abs(y_true - y_pred)))


def mape(y_true, y_pred):
    return float(np.mean(np.abs((y_true - y_pred) / y_true)) * 100)


def mse(y_true, y_pred):
    return float(np.mean((y_true - y_pred) ** 2))


def rmse(y_true, y_pred):
    return float(np.sqrt(mse(y_true, y_pred)))


def r2_score(y_true, y_pred):
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return float(1 - ss_res / ss_tot)


# ---------------------------------------------------------
# LOAD PREDICTIONS WITH y_true (BACKTEST ROWS)
# ---------------------------------------------------------
def load_backtest_predictions():
    q = text("""
        SELECT
            city,
            target,
            model_name,
            horizon_months,
            predict_date,
            yhat AS y_pred,
            y_true
        FROM public.model_predictions
        WHERE model_name = ANY(:models)
          AND y_true IS NOT NULL
        ORDER BY city, target, model_name, predict_date;
    """)

    with engine.connect() as conn:
        return pd.read_sql(q, conn, params={"models": BACKTEST_MODELS})


# ---------------------------------------------------------
# UPSERT INTO model_comparison
# ---------------------------------------------------------
def upsert_comparison_row(row):
    sql = text("""
        INSERT INTO public.model_comparison (
            city, target, horizon_months, model_name,
            mae, mape, rmse, mse, r2, evaluated_at
        )
        VALUES (
            :city, :target, :horizon_months, :model_name,
            :mae, :mape, :rmse, :mse, :r2, NOW()
        )
        ON CONFLICT (city, target, horizon_months, model_name)
        DO UPDATE SET
            mae = EXCLUDED.mae,
            mape = EXCLUDED.mape,
            rmse = EXCLUDED.rmse,
            mse = EXCLUDED.mse,
            r2 = EXCLUDED.r2,
            evaluated_at = NOW();
    """)

    with engine.begin() as conn:
        conn.execute(sql, row)


# ---------------------------------------------------------
# MAIN EVALUATION ROUTINE
# ---------------------------------------------------------
def main():
    print("[DEBUG] Loading backtest predictions...")

    df = load_backtest_predictions()

    if df.empty:
        print("[WARN] No backtest data found! Did you run the backtest scripts?")
        return

    results = []

    # Group by model, city, target, horizon
    grouped = df.groupby(["model_name", "city", "target", "horizon_months"])

    for (model, city, target, horizon), g in grouped:
        y_true = g["y_true"].astype(float).values
        y_pred = g["y_pred"].astype(float).values

        res = {
            "model_name": model,
            "city": city,
            "target": target,
            "horizon_months": int(horizon),
            "mae": round(mae(y_true, y_pred), 4),
            "mape": round(mape(y_true, y_pred), 4),
            "rmse": round(rmse(y_true, y_pred), 4),
            "mse": round(mse(y_true, y_pred), 4),
            "r2": round(r2_score(y_true, y_pred), 4),
        }

        upsert_comparison_row(res)
        results.append(res)

        print(f"[OK] {model} — {city}/{target}, h={horizon}: MAPE={res['mape']}")

    # Export JSON for dashboard
    Path("./.debug").mkdir(exist_ok=True)
    with open("./.debug/model_comparison.json", "w") as f:
        json.dump(results, f, indent=2)

    print("[DONE] Model comparison updated.")


if __name__ == "__main__":
    main()
