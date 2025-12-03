"""
train_model_lstm_v3.py
-------------------------------------------------------
Direct Multi-Horizon LSTM (v3)
Predicts 60-month vector directly (no recursion).
Targets:
- price (hpi_benchmark)
- rent  (rent_avg_city)
"""

import pandas as pd
import numpy as np
import uuid
import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from dotenv import load_dotenv, find_dotenv
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping

load_dotenv(find_dotenv(usecwd=True))
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)

FEATURES_Z = [
    "hpi_benchmark_z",
    "rent_avg_city_z",
    "mortgage_rate_z",
    "unemployment_rate_z",
    "cpi_yoy_z",
    "lag_1_z",
    "lag_3_z",
    "lag_6_z",
    "roll_3_z",
    "roll_6_z"
]

def load_data():
    q = """
        SELECT *
        FROM public.model_features
        ORDER BY city, date;
    """
    df = pd.read_sql(q, engine)
    df["date"] = pd.to_datetime(df["date"])
    return df

def create_direct_dataset(g, target_col, window=24, horizon=60):
    X, y = [], []
    vals = g[FEATURES_Z + [target_col]].values

    for i in range(len(vals) - window - horizon):
        X.append(vals[i:i+window, :-1])
        y.append(vals[i+window : i+window+horizon, -1])

    return np.array(X), np.array(y)

def build_model(n_features, window=24, horizon=60):
    model = Sequential()
    model.add(LSTM(64, activation="tanh", input_shape=(window, n_features)))
    model.add(Dropout(0.2))
    model.add(Dense(32, activation="relu"))
    model.add(Dense(horizon))   # predict full 60 steps
    model.compile(optimizer="adam", loss="mse")
    return model

def forecast_city_target(df, city, target_col, target_name):
    g = df[df.city == city].sort_values("date").copy()
    g = g.drop.na(subset=FEATURES_Z + [target_col])

    if len(g) < 120:
        print(f"[WARN] LSTM v3 insufficient data for {city}/{target_name}")
        return []

    WINDOW = 24
    HORIZON = 60

    X, y = create_direct_dataset(g, target_col, window=WINDOW, horizon=HORIZON)
    if len(X) < 50:
        print(f"[WARN] LSTM v3 no valid windows for {city}/{target_name}")
        return []

    model = build_model(n_features=len(FEATURES_Z), window=WINDOW, horizon=HORIZON)
    es = EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True)

    # train/val split
    split = int(len(X) * 0.8)
    X_train, y_train = X[:split], y[:split]
    X_val, y_val = X[split:], y[split:]

    model.fit(X_train, y_train, validation_data=(X_val, y_val),
              epochs=80, batch_size=16, callbacks=[es], verbose=0)

    # Forecast using last window in data
    last_window = g.iloc[-WINDOW:][FEATURES_Z].values.reshape(1, WINDOW, len(FEATURES_Z))
    pred_vec = model.predict(last_window, verbose=0)[0]

    last_date = g["date"].max()
    rows = []

    for h in range(1, HORIZON+1):
        y = float(max(0.0, pred_vec[h-1]))
        lo = y * 0.95
        hi = y * 1.05

        pred_date = last_date + pd.DateOffset(months=h)

        rows.append({
            "run_id": str(uuid.uuid4()),
            "model_name": "lstm_v3",
            "target": target_name,
            "horizon_months": h,
            "city": city,
            "property_type": None,
            "beds": None,
            "baths": None,
            "sqft_min": None,
            "sqft_max": None,
            "year_built_min": None,
            "year_built_max": None,
            "predict_date": pred_date,
            "yhat": y,
            "yhat_lower": lo,
            "yhat_upper": hi,
            "features_version": "features_to_model_v1",
            "model_artifact_uri": None,
            "created_at": datetime.now(timezone.utc),
            "is_micro": False
        })

    print(f"[OK] LSTM v3 forecast: {city}/{target_name}")
    return rows

def write_predictions(rows):
    if not rows:
        return

    sql = text("""
        INSERT INTO public.model_predictions (
            run_id, model_name, target, horizon_months,
            city, property_type,
            beds, baths, sqft_min, sqft_max,
            year_built_min, year_built_max,
            predict_date, yhat, yhat_lower, yhat_upper,
            features_version, model_artifact_uri,
            created_at, is_micro
        )
        VALUES (
            :run_id, :model_name, :target, :horizon_months,
            :city, :property_type,
            :beds, :baths, :sqft_min, :sqft_max,
            :year_built_min, :year_built_max,
            :predict_date, :yhat, :yhat_lower, :yhat_upper,
            :features_version, :model_artifact_uri,
            :created_at, :is_micro
        );
    """)

    with engine.begin() as conn:
        conn.execute(sql, rows)

    print(f"[OK] Inserted {len(rows)} LSTM v3 predictions.")

def main():
    print("[DEBUG] Starting LSTM v3...")

    df = load_data()
    all_rows = []

    for city in df.city.unique():
        all_rows.extend(forecast_city_target(df, city, "hpi_benchmark", "price"))
        all_rows.extend(forecast_city_target(df, city, "rent_avg_city", "rent"))

    write_predictions(all_rows)
    print("[DONE] LSTM v3 complete.")

if __name__ == "__main__":
    main()
