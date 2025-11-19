"""
train_model_lstm_v1.py
----------------------------------------------------------
Unified dual-target LSTM model training script.
Forecasts both 'price' (hpi_benchmark) and 'rent' (rent_avg_city) per city.
Splits data chronologically for backtesting:
- Train: 2005–2020
- Validation: 2020–2025 (MAE & MAPE evaluation)
- Production forecast: 2025–2035 (120 monthly steps)
Writes results into public.model_predictions for both targets.
"""

from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler
import os
import warnings

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------
# 1. Environment setup
# ---------------------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
NEON_DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("DATABASE_URL")
if not NEON_DATABASE_URL:
    raise RuntimeError("NEON_DATABASE_URL not found in .env")

engine = create_engine(NEON_DATABASE_URL, pool_pre_ping=True, future=True)
print("[DEBUG] Connected to Neon via .env")


# ---------------------------------------------------------------------
# 2. Load data from public.features
# ---------------------------------------------------------------------
def load_features():
    query = "SELECT date, city, hpi_benchmark, rent_avg_city FROM public.features ORDER BY city, date;"
    df = pd.read_sql_query(query, engine)
    df["date"] = pd.to_datetime(df["date"])
    print(f"[INFO] Loaded {len(df):,} rows from public.features")
    return df


# ---------------------------------------------------------------------
# 3. Helper functions
# ---------------------------------------------------------------------
def create_sequences(data, seq_length):
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i : i + seq_length])
        y.append(data[i + seq_length])
    return np.array(X), np.array(y)


def evaluate_performance(y_true, y_pred):
    mae = np.mean(np.abs(y_true - y_pred))
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    return mae, mape


# ---------------------------------------------------------------------
# 4. Train LSTM per city for both targets
# ---------------------------------------------------------------------
def train_lstm_dual_target(df: pd.DataFrame):
    results = []
    metrics = []
    model_name = "lstm_v1"
    seq_length = 12  # 12-month lookback window

    for target, column in [("price", "hpi_benchmark"), ("rent", "rent_avg_city")]:
        print(f"\n[INFO] ===== Training target: {target.upper()} =====")

        for city, group in df.groupby("city"):
            group = group.sort_values("date")
            y = group[column].astype(float).values.reshape(-1, 1)

            if np.all(y == 0) or len(y) < seq_length * 2:
                print(f"[WARN] Skipping {city}/{target}: insufficient or zero data.")
                continue

            scaler = MinMaxScaler()
            y_scaled = scaler.fit_transform(y)

            # Split chronologically
            split_train = group["date"] <= "2020-12-01"
            split_valid = (group["date"] > "2020-12-01") & (
                group["date"] <= "2025-12-01"
            )

            train_data = y_scaled[split_train]
            valid_data = y_scaled[split_valid]

            X_train, y_train = create_sequences(train_data, seq_length)
            X_valid, y_valid = create_sequences(valid_data, seq_length)

            X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
            X_valid = X_valid.reshape((X_valid.shape[0], X_valid.shape[1], 1))

            # ---------------- Build Model ----------------
            model = Sequential(
                [LSTM(64, activation="tanh", input_shape=(seq_length, 1)), Dense(1)]
            )
            model.compile(optimizer="adam", loss="mae")

            model.fit(X_train, y_train, epochs=50, batch_size=8, verbose=0)

            # ---------------- Validation ----------------
            if len(X_valid) > 0:
                y_pred_val = model.predict(X_valid, verbose=0)
                y_true = scaler.inverse_transform(y_valid.reshape(-1, 1)).flatten()
                y_pred = scaler.inverse_transform(y_pred_val).flatten()
                mae, mape = evaluate_performance(y_true, y_pred)
                metrics.append(
                    {"target": target, "city": city, "mae": mae, "mape": mape}
                )
                print(f"[VAL] {city}/{target}: MAE={mae:,.0f}, MAPE={mape:.2f}%")

            # ---------------- Retrain on Full Data ----------------
            X_full, y_full = create_sequences(y_scaled, seq_length)
            X_full = X_full.reshape((X_full.shape[0], X_full.shape[1], 1))
            model.fit(X_full, y_full, epochs=50, batch_size=8, verbose=0)

            # ---------------- Forecast Next 120 Months ----------------
            last_sequence = y_scaled[-seq_length:].reshape((1, seq_length, 1))
            preds_scaled = []

            for _ in range(120):
                next_pred = model.predict(last_sequence, verbose=0)[0, 0]
                preds_scaled.append(next_pred)
                last_sequence = np.append(
                    last_sequence[:, 1:, :], [[[next_pred]]], axis=1
                )

            preds = scaler.inverse_transform(
                np.array(preds_scaled).reshape(-1, 1)
            ).flatten()
            last_date = pd.to_datetime(group["date"].iloc[-1])

            for i in range(120):
                predict_date = last_date + pd.DateOffset(months=i + 1)
                yhat = float(preds[i])
                yhat_lower, yhat_upper = yhat * 0.95, yhat * 1.05

                results.append(
                    {
                        "model_name": model_name,
                        "target": target,
                        "horizon_months": i + 1,
                        "city": city,
                        "predict_date": predict_date,
                        "yhat": yhat,
                        "yhat_lower": yhat_lower,
                        "yhat_upper": yhat_upper,
                        "features_version": "features_build_etl_v9",
                        "model_artifact_uri": None,
                        "is_micro": False,
                    }
                )

            print(
                f"[OK] LSTM trained for {city}/{target} ({len(group)} records, 120 forecasts)"
            )

    return pd.DataFrame(results), pd.DataFrame(metrics)


# ---------------------------------------------------------------------
# 5. Write predictions to public.model_predictions
# ---------------------------------------------------------------------
def write_predictions(df_preds: pd.DataFrame):
    if df_preds.empty:
        print("[WARN] No predictions to insert.")
        return

    insert_sql = text("""
        INSERT INTO public.model_predictions (
            model_name, target, horizon_months, city, predict_date,
            yhat, yhat_lower, yhat_upper, features_version, model_artifact_uri, is_micro, created_at
        )
        VALUES (
            :model_name, :target, :horizon_months, :city, :predict_date,
            :yhat, :yhat_lower, :yhat_upper, :features_version, :model_artifact_uri, :is_micro, NOW()
        );
    """)

    with engine.begin() as conn:
        conn.exec_driver_sql("SELECT 1;")
        conn.execute(insert_sql, df_preds.to_dict(orient="records"))

    print(
        f"[OK] Inserted {len(df_preds):,} LSTM predictions (both targets) into public.model_predictions"
    )


# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
if __name__ == "__main__":
    start = datetime.now()
    print("[DEBUG] train_model_lstm_v1 started ...")

    df_features = load_features()
    df_preds, df_metrics = train_lstm_dual_target(df_features)
    write_predictions(df_preds)

    if not df_metrics.empty:
        print("\n[SUMMARY] Validation results (2020–2025):")
        print(
            df_metrics.sort_values("mape").to_string(
                index=False, formatters={"mape": "{:.2f}%".format}
            )
        )

    print(f"\n[DONE] train_model_lstm_v1 completed in {datetime.now() - start}")
