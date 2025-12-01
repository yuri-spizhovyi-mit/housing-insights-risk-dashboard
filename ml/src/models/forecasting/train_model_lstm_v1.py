"""
train_model_lstm_v1.py
------------------------------------------------------------
Dual-target LSTM forecasting system.

Targets:
- Home price  (target="price") → hpi_benchmark
- Rent price  (target="rent")  → rent_avg_city

For each (city, property_type):
- Train windowing: past 24 months → predict next month
- Train: 2005–2020
- Validate: 2020–2025 (MAE/MAPE)
- Forecast: recursively 120 months (2025–2035)

Writes results into public.model_predictions.
"""

import pandas as pd
import numpy as np
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from dotenv import load_dotenv, find_dotenv
import os
import warnings
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping

warnings.filterwarnings("ignore")


# ==========================================================
# ENVIRONMENT
# ==========================================================
load_dotenv(find_dotenv(usecwd=True))
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)


# ==========================================================
# LOAD model_features
# ==========================================================
def load_model_features():
    q = """
        SELECT
            date,
            city,
            property_type,
            hpi_benchmark,
            rent_avg_city,
            hpi_z,
            rent_z,
            macro_composite_z,
            demographics_composite_z,
            hpi_change_yoy,
            rent_change_yoy,
            lag_1,
            lag_3,
            lag_6,
            lag_12,
            roll_3,
            roll_6,
            roll_12
        FROM public.model_features
        ORDER BY city, property_type, date;
    """

    df = pd.read_sql(q, engine)
    df["date"] = pd.to_datetime(df["date"])
    print(f"[INFO] Loaded {len(df)} rows from model_features")
    return df


# ==========================================================
# FEATURE SET
# ==========================================================
FEATURE_COLS = [
    "hpi_z",
    "rent_z",
    "macro_composite_z",
    "demographics_composite_z",
    "hpi_change_yoy",
    "rent_change_yoy",
    "lag_1",
    "lag_3",
    "lag_6",
    "lag_12",
    "roll_3",
    "roll_6",
    "roll_12",
]


# ==========================================================
# CREATE WINDOWED DATASET FOR LSTM
# ==========================================================
def create_dataset(df, feature_cols, target_col, window=24):
    X, y = [], []

    values = df[feature_cols + [target_col]].values

    for i in range(len(values) - window):
        window_slice = values[i : i + window]
        X.append(window_slice[:, :-1])   # all features but target
        y.append(values[i + window, -1]) # next month's target

    return np.array(X), np.array(y)


# ==========================================================
# BUILD LSTM MODEL
# ==========================================================
def build_lstm_model(n_features, window=24):
    model = Sequential()
    model.add(LSTM(64, activation="tanh", return_sequences=False, input_shape=(window, n_features)))
    model.add(Dropout(0.2))
    model.add(Dense(32, activation="relu"))
    model.add(Dense(1))

    model.compile(optimizer="adam", loss="mse")
    return model


# ==========================================================
# TRAIN + VALIDATE + FORECAST
# ==========================================================
def train_lstm_for_group(df, city, ptype, target_name, target_col):

    g = df[(df.city == city) & (df.property_type == ptype)].sort_values("date")

    # Drop first 12 rows (NaNs in lag/roll)
    g = g.iloc[12:].dropna(subset=FEATURE_COLS + [target_col])
    if g.empty:
        print(f"[WARN] No valid data for LSTM {city}/{ptype}/{target_name}")
        return []

    # -------------------------------------------
    # TRAIN/VALIDATION SPLIT
    # -------------------------------------------
    train_df = g[g.date <= "2020-12-01"]
    val_df = g[(g.date > "2020-12-01") & (g.date <= "2025-12-01")]

    # Create windowed datasets
    WINDOW = 24
    X_train, y_train = create_dataset(train_df, FEATURE_COLS, target_col, window=WINDOW)
    X_val, y_val = create_dataset(val_df, FEATURE_COLS, target_col, window=WINDOW)

    if len(X_train) < 12:
        print(f"[WARN] Not enough LSTM history for {city}/{ptype}/{target_name}")
        return []

    # -------------------------------------------
    # BUILD MODEL
    # -------------------------------------------
    model = build_lstm_model(n_features=len(FEATURE_COLS), window=WINDOW)

    es = EarlyStopping(monitor="val_loss", patience=15, restore_best_weights=True)

    print(f"[TRAIN] LSTM {city}/{ptype}/{target_name}: X_train={X_train.shape}")

    model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val) if len(X_val) > 0 else None,
        epochs=120,
        batch_size=16,
        callbacks=[es],
        verbose=0
    )

    # -------------------------------------------
    # FORECAST 120 MONTHS (recursive)
    # -------------------------------------------
    rows = []

    # Prepare last window
    last_window_df = g.iloc[-WINDOW:][FEATURE_COLS]
    last_window = last_window_df.values.reshape(1, WINDOW, len(FEATURE_COLS))

    last_date = g["date"].max()

    for horizon in range(1, 121):

        # Predict next month
        yhat = model.predict(last_window, verbose=0)[0][0]

        # Create simple +/- 5% bands
        y_low = yhat * 0.95
        y_high = yhat * 1.05

        forecast_date = last_date + pd.DateOffset(months=horizon)

        rows.append(
            {
                "run_id": str(uuid.uuid4()),
                "model_name": "lstm_v1",
                "target": target_name,
                "horizon_months": horizon,
                "city": city,
                "property_type": ptype,
                "beds": None,
                "baths": None,
                "sqft_min": None,
                "sqft_max": None,
                "year_built_min": None,
                "year_built_max": None,
                "predict_date": forecast_date,
                "yhat": float(yhat),
                "yhat_lower": float(y_low),
                "yhat_upper": float(y_high),
                "features_version": "model_features_v1",
                "model_artifact_uri": None,
                "created_at": datetime.now(timezone.utc),
                "is_micro": False,
            }
        )

        # -------------------------------------------
        # UPDATE LAST WINDOW (rolling)
        # -------------------------------------------
        new_features = last_window_df.iloc[1:].copy()  # drop first row

        # Approximated rolling update (consistent with LightGBM)
        for col in FEATURE_COLS:
            new_features.at[new_features.index[-1], col] = new_features[col].iloc[-1]

        last_window_df = new_features
        last_window = last_window_df.values.reshape(1, WINDOW, len(FEATURE_COLS))

    print(f"[OK] LSTM forecast for {city}/{ptype}/{target_name}")
    return rows


# ==========================================================
# INSERT INTO model_predictions
# ==========================================================
def write_predictions(rows):
    if not rows:
        print("[WARN] No LSTM predictions to insert.")
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

    print(f"[OK] Inserted {len(rows)} LSTM predictions.")


# ==========================================================
# MAIN
# ==========================================================
def main():
    print("[DEBUG] Starting LSTM v1...")

    df = load_model_features()
    all_rows = []

    for (city, ptype), _ in df.groupby(["city", "property_type"]):

        # HOME PRICE
        rows_price = train_lstm_for_group(df, city, ptype, "price", "hpi_benchmark")
        all_rows.extend(rows_price)

        # RENT PRICE
        rows_rent = train_lstm_for_group(df, city, ptype, "rent", "rent_avg_city")
        all_rows.extend(rows_rent)

    write_predictions(all_rows)
    print("[DONE] LSTM v1 complete.")


if __name__ == "__main__":
    main()
