"""
train_model_lightgbm_v1.py
----------------------------------------------------------
Dual-target LightGBM forecasting system.

Targets:
- Home price  (target="price") → hpi_benchmark
- Rent price  (target="rent")  → rent_avg_city

Per city × property_type:
- Train: 2005–2020
- Validate: 2020–2025
- Forecast: 2025–2035 (120 months)

Writes results to public.model_predictions using correct schema.
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from dotenv import load_dotenv, find_dotenv
import os
import warnings

warnings.filterwarnings("ignore")


# ----------------------------------------------------------
# Environment
# ----------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)


# ----------------------------------------------------------
# Load model_features
# ----------------------------------------------------------
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


# ----------------------------------------------------------
# Feature columns (X)
# ----------------------------------------------------------
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


# ----------------------------------------------------------
# Compute quantile predictions for intervals
# ----------------------------------------------------------
def quantile_prediction(model, X, lower=0.1, upper=0.9):
    """
    LightGBM doesn't output prediction intervals directly.
    We approximate using quantile models.
    """
    # Train quantile models
    params_low = model.get_params()
    params_low["objective"] = "quantile"
    params_low["alpha"] = lower

    params_high = model.get_params()
    params_high["objective"] = "quantile"
    params_high["alpha"] = upper

    model_low = lgb.LGBMRegressor(**params_low)
    model_low.fit(model.train_X, model.train_y)

    model_high = lgb.LGBMRegressor(**params_high)
    model_high.fit(model.train_X, model.train_y)

    y_low = model_low.predict(X)
    y_high = model_high.predict(X)

    return y_low, y_high


# ----------------------------------------------------------
# Train LightGBM for one target
# ----------------------------------------------------------
def train_lightgbm_for_group(df, city, ptype, target_name, col_name):
    g = df[(df.city == city) & (df.property_type == ptype)].sort_values("date")

    # Drop initial NaNs from lag/roll
    g = g.iloc[12:].dropna(subset=FEATURE_COLS + [col_name])
    if g.empty:
        print(f"[WARN] No data after cleaning for {city}/{ptype}/{target_name}")
        return []

    # Train/validation split
    train = g[g.date <= "2020-12-01"]
    val = g[(g.date > "2020-12-01") & (g.date <= "2025-12-01")]

    X_train = train[FEATURE_COLS]
    y_train = train[col_name]

    X_val = val[FEATURE_COLS]
    y_val = val[col_name]

    # Set aside last known row for rolling forecast
    last_row = g.iloc[-1:][FEATURE_COLS]

    # ----------------------------------------------------------
    # MODEL
    # ----------------------------------------------------------
    model = lgb.LGBMRegressor(
        n_estimators=800,
        learning_rate=0.03,
        max_depth=-1,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="regression",
        num_leaves=64,
    )

    model.train_X, model.train_y = X_train, y_train.values
    model.fit(X_train, y_train)

    # Validation metrics
    if not X_val.empty:
        preds = model.predict(X_val)
        mae = np.mean(np.abs(preds - y_val))
        mape = np.mean(np.abs((preds - y_val) / y_val)) * 100
        print(f"[VAL] {city}/{ptype}/{target_name}: MAE={mae:,.0f}, MAPE={mape:.2f}%")

    # ----------------------------------------------------------
    # FORECAST 120 MONTHS (rolling prediction)
    # ----------------------------------------------------------
    rows = []
    last_vals = g[col_name].values[-1]

    current_features = last_row.copy()

    for horizon in range(1, 121):
        # Predict next month
        y_pred = model.predict(current_features)[0]

        # Compute interval estimates
        y_low, y_high = quantile_prediction(model, current_features)

        forecast_date = g["date"].max() + pd.DateOffset(months=horizon)

        rows.append(
            {
                "run_id": str(uuid.uuid4()),
                "model_name": "lightgbm_v1",
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
                "yhat": float(y_pred),
                "yhat_lower": float(y_low),
                "yhat_upper": float(y_high),
                "features_version": "model_features_v1",
                "model_artifact_uri": None,
                "created_at": datetime.now(timezone.utc),
                "is_micro": False,
            }
        )

        # Update rolling features
        # Replace lag_1..lag_12 & roll windows with shifted values
        current_features = current_features.copy()
        # Shift lag features
        for lag in [1, 3, 6, 12]:
            col = f"lag_{lag}"
            current_features[col] = y_pred

        # Shift rolling windows
        for r in [3, 6, 12]:
            col = f"roll_{r}"
            current_features[col] = y_pred

        # Also update hpi_z using last known scale (approximate)
        current_features["hpi_z"] = current_features["hpi_z"]

    print(f"[OK] LightGBM forecast for {city}/{ptype}/{target_name}")
    return rows


# ----------------------------------------------------------
# Insert predictions
# ----------------------------------------------------------
def write_predictions(rows):
    if not rows:
        print("[WARN] No predictions to insert.")
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
        )
    """)

    with engine.begin() as conn:
        conn.execute(sql, rows)

    print(f"[OK] Inserted {len(rows)} LightGBM predictions.")


# ----------------------------------------------------------
# Entrypoint
# ----------------------------------------------------------
def main():
    print("[DEBUG] Starting LightGBM v1...")

    df = load_model_features()
    all_rows = []

    for (city, ptype), _ in df.groupby(["city", "property_type"]):
        # Home Price
        rows_price = train_lightgbm_for_group(df, city, ptype, "price", "hpi_benchmark")
        all_rows.extend(rows_price)

        # Rent Price
        rows_rent = train_lightgbm_for_group(df, city, ptype, "rent", "rent_avg_city")
        all_rows.extend(rows_rent)

    write_predictions(all_rows)
    print("[DONE] LightGBM v1 completed.")


if __name__ == "__main__":
    main()
