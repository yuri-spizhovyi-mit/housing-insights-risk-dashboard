"""
LightGBM v4 — stable forecasting model
--------------------------------------
- Uses minimal high-signal feature set (Z-features)
- No recursion
- Forecasts 1–60 months
- Writes to model_predictions
"""

import os
import uuid
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import lightgbm as lgb
from sqlalchemy import create_engine, text
from dotenv import load_dotenv, find_dotenv

# -------------------------------------------
# ENV
# -------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
DATABASE_URL = os.getenv("NEON_DATABASE_URL") or os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)

# -------------------------------------------
# FEATURES — FINAL A2-Z FEATURE SET
# -------------------------------------------
FEATURE_COLS = [
    "lag_1_z", "lag_3_z", "lag_6_z",
    "roll_3_z", "roll_6_z",
    "hpi_benchmark_yoy_z", "rent_avg_city_yoy_z",
    "mortgage_rate_z", "unemployment_rate_z", "cpi_yoy_z"
]

# -------------------------------------------
# LOAD DATA
# -------------------------------------------
def load_model_features():
    q = """
        SELECT *
        FROM public.model_features
        ORDER BY city, date;
    """
    df = pd.read_sql(q, engine)
    df["date"] = pd.to_datetime(df["date"])
    return df

# -------------------------------------------
# TRAIN ONE CITY + ONE TARGET
# -------------------------------------------
def train_city_target(df_city, target_col, target_name):
    df_city = df_city.sort_values("date").copy()

    # target cannot be NaN
    df_city[target_col] = df_city[target_col].fillna(method="ffill").fillna(method="bfill")

    X = df_city[FEATURE_COLS]
    y = df_city[target_col]

    if len(df_city) < 40:
        print(f"[WARN] Skipping {df_city.city.iloc[0]} / {target_name} — too few rows")
        return []

    # LightGBM regressor
    model = lgb.LGBMRegressor(
        n_estimators=800,
        learning_rate=0.03,
        subsample=0.9,
        colsample_bytree=0.9,
        max_depth=-1,
    )
    model.fit(X, y)

    # last row for forecasting
    last_features = X.iloc[-1].values.reshape(1, -1)
    last_date = df_city["date"].max()

    rows = []

    for horizon in range(1, 61):
        yhat = float(model.predict(last_features)[0])
        yhat = max(0.0, yhat)

        lo = yhat * 0.90
        hi = yhat * 1.10

        forecast_date = last_date + pd.DateOffset(months=horizon)

        rows.append({
            "run_id": str(uuid.uuid4()),
            "model_name": "lightgbm_v4",
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
            "predict_date": forecast_date,
            "yhat": yhat,
            "yhat_lower": lo,
            "yhat_upper": hi,
            "features_version": "model_features_city_simple_v1",
            "model_artifact_uri": None,
            "created_at": datetime.now(timezone.utc),
            "is_micro": False
        })

    print(f"[OK] LightGBM v4: {df_city.city.iloc[0]} / {target_name}")
    return rows

# -------------------------------------------
# WRITE TO DB
# -------------------------------------------
def write_predictions(rows):
    if not rows:
        return

    sql = text("""
        INSERT INTO public.model_predictions (
            run_id, model_name, target, horizon_months,
            city, property_type, beds, baths, sqft_min, sqft_max,
            year_built_min, year_built_max,
            predict_date, yhat, yhat_lower, yhat_upper,
            features_version, model_artifact_uri,
            created_at, is_micro
        )
        VALUES (
            :run_id, :model_name, :target, :horizon_months,
            :city, :property_type, :beds, :baths, :sqft_min, :sqft_max,
            :year_built_min, :year_built_max,
            :predict_date, :yhat, :yhat_lower, :yhat_upper,
            :features_version, :model_artifact_uri,
            :created_at, :is_micro
        );
    """)

    with engine.begin() as conn:
        conn.execute(sql, rows)

    print(f"[OK] Inserted {len(rows)} LightGBM v4 predictions")

# -------------------------------------------
# MAIN
# -------------------------------------------
def main():
    print("[DEBUG] LightGBM v4 starting...")

    df = load_model_features()
    all_rows = []

    for city in df.city.unique():
        df_city = df[df.city == city].copy()

        all_rows.extend(train_city_target(df_city, "hpi_benchmark", "price"))
        all_rows.extend(train_city_target(df_city, "rent_avg_city", "rent"))

    write_predictions(all_rows)
    print("[DONE] LightGBM v4 complete.")

if __name__ == "__main__":
    main()
