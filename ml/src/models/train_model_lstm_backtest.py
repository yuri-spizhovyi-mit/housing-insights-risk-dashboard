#!/usr/bin/env python3
"""
train_model_lstm_backtest.py

Backtesting LSTM on historical data.

TRAIN:
    2005-01-01 → 2020-12-01
VALIDATE:
    2021-01-01 → last available date in model_features

Writes predictions with y_true into model_predictions.
"""

import os
import uuid
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import MinMaxScaler

# -------------------------------------------------------------------------
# ENVIRONMENT
# -------------------------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
DATABASE_URL = os.getenv("NEON_DATABASE_URL") or os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)

CUTOFF = pd.Timestamp("2020-12-01")
SEQ_LEN = 12  # 12-month input window


# -------------------------------------------------------------------------
# LOAD FEATURES
# -------------------------------------------------------------------------
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


# -------------------------------------------------------------------------
# BUILD LSTM MODEL
# -------------------------------------------------------------------------
def build_lstm(input_shape):
    model = Sequential()
    model.add(
        LSTM(64, activation="tanh", return_sequences=False, input_shape=input_shape)
    )
    model.add(Dense(32, activation="relu"))
    model.add(Dense(1))
    model.compile(optimizer="adam", loss="mse")
    return model


# -------------------------------------------------------------------------
# CREATE SUPERVISED DATA
# X: last 12 months
# y: next value
# -------------------------------------------------------------------------
def create_sequences(series, seq_len=12):
    X, y = [], []
    for i in range(len(series) - seq_len):
        X.append(series[i : i + seq_len])
        y.append(series[i + seq_len])
    return np.array(X), np.array(y)


# -------------------------------------------------------------------------
# BACKTEST PER CITY AND TARGET
# -------------------------------------------------------------------------
def backtest_city_target(df, city, target_col, target_name):
    g = df[df.city == city].sort_values("date").copy()

    train = g[g["date"] <= CUTOFF].copy()
    valid = g[g["date"] > CUTOFF].copy()

    if len(train) < SEQ_LEN + 24:
        print(f"[WARN] LSTM backtest: not enough history for {city}/{target_name}")
        return []

    # Scale series 0–1
    scaler = MinMaxScaler()
    train_scaled = scaler.fit_transform(train[[target_col]]).flatten()

    # Training sequences
    X_train, y_train = create_sequences(train_scaled, SEQ_LEN)
    X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))

    # Build and train LSTM
    model = build_lstm((SEQ_LEN, 1))
    model.fit(
        X_train,
        y_train,
        epochs=50,
        batch_size=8,
        validation_split=0.1,
        callbacks=[
            EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True)
        ],
        verbose=0,
    )

    # Now backtest on validation period (2021–2024)
    rows = []

    # Start history with the last training window
    history = train[target_col].values.tolist()

    for _, row in valid.iterrows():
        # Prepare last 12 months as input window
        hist_scaled = scaler.transform(
            np.array(history[-SEQ_LEN:]).reshape(-1, 1)
        ).flatten()
        X = np.array(hist_scaled).reshape(1, SEQ_LEN, 1)

        # Predict next value
        pred_scaled = model.predict(X, verbose=0)[0][0]
        pred = scaler.inverse_transform([[pred_scaled]])[0][0]

        # Actual value
        y_true = float(row[target_col])
        # Compute horizon versus cutoff
        horizon = int((row["date"].to_period("M") - CUTOFF.to_period("M")).n)

        rows.append(
            {
                "run_id": str(uuid.uuid4()),
                "model_name": "lstm_backtest",
                "target": target_name,
                "horizon_months": horizon,
                "city": city,
                "property_type": None,
                "beds": None,
                "baths": None,
                "sqft_min": None,
                "sqft_max": None,
                "year_built_min": None,
                "year_built_max": None,
                "predict_date": row["date"],
                "yhat": float(max(0.0, pred)),
                "yhat_lower": None,
                "yhat_upper": None,
                "y_true": y_true,
                "features_version": "features_backtest_v1",
                "model_artifact_uri": None,
                "created_at": datetime.now(timezone.utc),
                "is_micro": False,
            }
        )

        # Update history with ACTUAL value (realistic recursive forecasting)
        history.append(y_true)

    print(f"[OK] LSTM backtest: {city}/{target_name} ({len(rows)} rows)")
    return rows


# -------------------------------------------------------------------------
# WRITE PREDICTIONS TO DB
# -------------------------------------------------------------------------
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

    print(f"[OK] Inserted {len(rows)} LSTM BACKTEST predictions.")


# -------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------
def main():
    print("[DEBUG] Starting LSTM BACKTEST...")

    df = load_features()
    all_rows = []

    for city in df.city.unique():
        all_rows.extend(backtest_city_target(df, city, "hpi_benchmark", "price"))
        all_rows.extend(backtest_city_target(df, city, "rent_avg_city", "rent"))

    write_predictions(all_rows)

    print("[DONE] LSTM BACKTEST complete.")


if __name__ == "__main__":
    main()
