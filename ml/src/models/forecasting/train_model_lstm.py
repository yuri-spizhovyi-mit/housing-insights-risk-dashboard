"""
LSTM v1 — multivariate forecasting
Option B (macro features)
"""

import os
import uuid
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv, find_dotenv
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense

# -------------------------------------------
# ENV
# -------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)

SEQ_LEN = 12
FORECAST_HORIZON = 60


# -------------------------------------------
# LOAD DATA
# -------------------------------------------
def load_model_features():
    q = """
        SELECT city, date,
               hpi_benchmark, rent_avg_city,
               mortgage_rate, unemployment_rate, cpi_yoy
        FROM public.model_features
        ORDER BY city, date;
    """
    df = pd.read_sql(q, engine)
    df["date"] = pd.to_datetime(df["date"])
    return df


# -------------------------------------------
# MODEL
# -------------------------------------------
def build_lstm(n_features):
    model = Sequential()
    model.add(
        LSTM(
            48,
            activation="tanh",
            return_sequences=False,
            input_shape=(SEQ_LEN, n_features)
        )
    )
    model.add(Dense(1))
    model.compile(optimizer="adam", loss="mse")
    return model


# -------------------------------------------
# FORECAST ONE CITY/TARGET
# -------------------------------------------
def forecast_city(df_city, target_col, target_name, feature_cols):
    df_city = df_city.sort_values("date").copy()

    # fill missing
    for c in feature_cols:
        df_city[c] = df_city[c].ffill().bfill()

    values = df_city[feature_cols].values
    target_vals = df_city[target_col].values

    X, y = [], []

    # build supervised pairs
    for i in range(len(values) - SEQ_LEN):
        window = values[i:i+SEQ_LEN]
        last_target = target_vals[i+SEQ_LEN-1]
        next_target = target_vals[i+SEQ_LEN]
        pct_change = (next_target - last_target) / last_target

        X.append(window)
        y.append(pct_change)

    X = np.array(X)
    y = np.array(y)

    if len(X) < 50:
        return []

    model = build_lstm(n_features=len(feature_cols))
    model.fit(X, y, epochs=35, batch_size=16, verbose=0)

    # last window (multivariate)
    last_window = values[-SEQ_LEN:].reshape(1, SEQ_LEN, len(feature_cols))
    last_real_price = float(target_vals[-1])
    last_date = df_city["date"].max()

    rows = []

    for horizon in range(1, FORECAST_HORIZON + 1):
        pct = float(model.predict(last_window, verbose=0)[0][0])
        pct = np.clip(pct, -0.30, 0.30)

        yhat = last_real_price * (1 + pct)
        yhat_lower = last_real_price * (1 + pct - 0.05)
        yhat_upper = last_real_price * (1 + pct + 0.05)

        predict_date = last_date + pd.DateOffset(months=horizon)

        rows.append({
            "run_id": str(uuid.uuid4()),
            "model_name": "lstm",
            "target": target_name,
            "horizon_months": horizon,
            "city": df_city.city.iloc[0],
            "property_type": None,
            "beds": None,
            "baths": None,
            "sqft_min": None,
            "sqft_max": None,
            "year_built_min": None,
            "year_built_max": None,
            "predict_date": predict_date,
            "yhat": float(yhat),
            "yhat_lower": float(max(0, yhat_lower)),
            "yhat_upper": float(max(0, yhat_upper)),
            "features_version": "model_features_city_simple_v1",
            "model_artifact_uri": None,
            "created_at": datetime.now(timezone.utc),
            "is_micro": False
        })

        last_real_price = yhat

        # recursive forecast
        new_row = values[-1].copy()
        new_row[feature_cols.index(target_col)] = yhat   # replace only target

        new_val = new_row.reshape(1, 1, len(feature_cols))
        last_window = np.concatenate([last_window[:, 1:, :], new_val], axis=1)

    print(f"[OK] LSTM: {df_city.city.iloc[0]} / {target_name}")
    return rows


# -------------------------------------------
# WRITE PREDICTIONS
# -------------------------------------------
def write_predictions(rows):
    if not rows:
        return

    sql = text("""
        INSERT INTO public.model_predictions (
            run_id, model_name, target, horizon_months,
            city, property_type, beds, baths,
            sqft_min, sqft_max,
            year_built_min, year_built_max,
            predict_date, yhat, yhat_lower, yhat_upper,
            features_version, model_artifact_uri,
            created_at, is_micro
        )
        VALUES (
            :run_id, :model_name, :target, :horizon_months,
            :city, :property_type, :beds, :baths,
            :sqft_min, :sqft_max,
            :year_built_min, :year_built_max,
            :predict_date, :yhat, :yhat_lower, :yhat_upper,
            :features_version, :model_artifact_uri,
            :created_at, :is_micro
        );
    """)

    with engine.begin() as conn:
        conn.execute(sql, rows)

    print(f"[OK] Inserted {len(rows)} LSTM rows")


# -------------------------------------------
# MAIN
# -------------------------------------------
def main():
    print("[DEBUG] LSTM starting...")

    df = load_model_features()
    all_rows = []

    for city in df.city.unique():
        df_city = df[df.city == city].copy()

        # PRICE MODEL
        all_rows.extend(
            forecast_city(
                df_city,
                target_col="hpi_benchmark",
                target_name="price",
                feature_cols=["hpi_benchmark", "mortgage_rate", "unemployment_rate", "cpi_yoy"]
            )
        )

        # RENT MODEL
        all_rows.extend(
            forecast_city(
                df_city,
                target_col="rent_avg_city",
                target_name="rent",
                feature_cols=["rent_avg_city", "mortgage_rate", "unemployment_rate", "cpi_yoy"]
            )
        )

    write_predictions(all_rows)
    print("[DONE] LSTM v1 complete.")


if __name__ == "__main__":
    main()
