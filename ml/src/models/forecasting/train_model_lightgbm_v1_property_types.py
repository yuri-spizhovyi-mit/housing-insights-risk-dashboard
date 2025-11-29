"""
train_model_lightgbm_v1_property_types.py
---------------------------------------------------
Advanced long-horizon forecasting engine.

✔ 3 property types supported
✔ Dual targets: HPI & Rent
✔ Train: 2005–2020
✔ Validate: 2020–2025
✔ Forecast: 2025–2035 (120 months)
✔ Iterative forecasting loop
✔ Writes predictions to public.model_predictions
✔ Fully compatible with model_features_v2
"""

import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
import lightgbm as lgb
from sqlalchemy import create_engine, text
from dotenv import load_dotenv, find_dotenv
import os

# ----------------------------------------------------------
# DB INIT
# ----------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)

# ----------------------------------------------------------
# NUMERIC FEATURES (from model_features_v2)
# ----------------------------------------------------------
FEATURE_COLS = [
    "hpi_benchmark",
    "rent_avg_city",
    "mortgage_rate",
    "unemployment_rate",
    "overnight_rate",
    "population",
    "median_income",
    "migration_rate",
    "gdp_growth",
    "cpi_yoy",
    "hpi_change_yoy",
    "rent_change_yoy",
]

TARGETS = ["price", "rent"]


# ----------------------------------------------------------
# LOAD model_features_v2
# ----------------------------------------------------------
def load_features():
    query = """
        SELECT
            date,
            city,
            property_type,
            hpi_benchmark,
            rent_avg_city,
            mortgage_rate,
            unemployment_rate,
            overnight_rate,
            population,
            median_income,
            migration_rate,
            gdp_growth,
            cpi_yoy,
            hpi_change_yoy,
            rent_change_yoy
        FROM public.model_features
        ORDER BY date, city, property_type
    """
    df = pd.read_sql(query, engine)
    df["date"] = pd.to_datetime(df["date"])

    # convert all numeric columns
    df[FEATURE_COLS] = df[FEATURE_COLS].apply(pd.to_numeric, errors="coerce")

    return df


# ----------------------------------------------------------
# BUILD FUTURE DATE RANGE
# ----------------------------------------------------------
def build_future_dates(start_date, months=120):
    dates = []
    current = start_date
    for _ in range(months):
        current = current + relativedelta(months=1)
        dates.append(current)
    return dates


# ----------------------------------------------------------
# TRAIN A SINGLE LGBM MODEL
# ----------------------------------------------------------
def train_single_model(df_train, target):
    if target == "price":
        y = df_train["hpi_benchmark"]
    else:
        y = df_train["rent_avg_city"]

    X = df_train[FEATURE_COLS]

    model = lgb.LGBMRegressor(
        n_estimators=600,
        learning_rate=0.05,
        max_depth=-1,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="regression",
        verbose=-1,  # suppress split spam
        random_state=42,
    )

    model.fit(X, y)
    return model


# ----------------------------------------------------------
# ITERATIVE MULTI-STEP FORECASTING
# ----------------------------------------------------------
def forecast_future(model, last_row, target, forecast_dates):
    preds = []

    prev = last_row.copy()
    prev[FEATURE_COLS] = prev[FEATURE_COLS].apply(pd.to_numeric, errors="coerce")

    for i, d in enumerate(forecast_dates):
        X_pred = prev[FEATURE_COLS].to_frame().T
        X_pred = X_pred.apply(pd.to_numeric, errors="coerce")

        yhat = float(model.predict(X_pred)[0])

        # No confidence intervals in pure LightGBM
        preds.append(
            {
                "predict_date": d,
                "yhat": yhat,
                "yhat_lower": None,
                "yhat_upper": None,
                "horizon_months": i + 1,
            }
        )

        # update recursive state
        if target == "price":
            prev["hpi_benchmark"] = yhat
        else:
            prev["rent_avg_city"] = yhat

    return preds


# ----------------------------------------------------------
# INSERT PREDICTIONS INTO model_predictions
# (matches your EXISTING SCHEMA 100%)
# ----------------------------------------------------------
def write_predictions(predictions):
    sql = text("""
        INSERT INTO public.model_predictions (
            model_name,
            target,
            horizon_months,
            city,
            property_type,
            predict_date,
            yhat,
            yhat_lower,
            yhat_upper,
            features_version,
            model_artifact_uri,
            is_micro,
            created_at
        )
        VALUES (
            :model_name,
            :target,
            :horizon_months,
            :city,
            :property_type,
            :predict_date,
            :yhat,
            :yhat_lower,
            :yhat_upper,
            :features_version,
            NULL,
            FALSE,
            NOW()
        )
    """)

    with engine.begin() as conn:
        conn.execute(sql, predictions)

    print(f"[OK] Inserted {len(predictions)} predictions.")


# ----------------------------------------------------------
# MAIN LOOP
# ----------------------------------------------------------
def main():
    print("[INFO] Loading features...")
    df = load_features()

    train_end = pd.Timestamp("2020-01-01")
    valid_end = pd.Timestamp("2025-01-01")
    forecast_start = valid_end

    forecast_dates = build_future_dates(forecast_start, months=120)

    all_preds = []

    # (city, property_type) segmentation
    for (city, ptype), group in df.groupby(["city", "property_type"]):
        print(f"\n[TRAIN] {city} – {ptype}")

        group = group.sort_values("date")

        df_train = group[group["date"] < train_end].copy()
        df_valid = group[
            (group["date"] >= train_end) & (group["date"] < valid_end)
        ].copy()
        last_row = group[group["date"] < valid_end].iloc[-1].copy()

        if len(df_train) < 24:
            print(f"[WARN] Not enough history → skipping {city}/{ptype}")
            continue

        for target in TARGETS:
            model_name = "lightgbm_v1"
            print(f"  [TARGET] {target}")

            model = train_single_model(df_train, target)

            # Validation predictions
            df_valid = df_valid.copy()
            Xv = df_valid[FEATURE_COLS]
            yv = model.predict(Xv)

            for i, (dt, yhat) in enumerate(zip(df_valid["date"], yv)):
                all_preds.append(
                    {
                        "model_name": model_name,
                        "target": target,
                        "horizon_months": i + 1,
                        "city": city,
                        "property_type": ptype,
                        "predict_date": dt,
                        "yhat": float(yhat),
                        "yhat_lower": None,
                        "yhat_upper": None,
                        "features_version": "model_features_v2",
                        "is_micro": False,
                    }
                )

            # Future predictions (120-month forecast)
            future_preds = forecast_future(model, last_row, target, forecast_dates)
            for i, fp in enumerate(future_preds):
                all_preds.append(
                    {
                        "model_name": model_name,
                        "target": target,
                        "horizon_months": fp["horizon_months"],
                        "city": city,
                        "property_type": ptype,
                        "predict_date": fp["predict_date"],
                        "yhat": float(fp["yhat"]),
                        "yhat_lower": None,
                        "yhat_upper": None,
                        "features_version": "model_features_v2",
                        "is_micro": False,
                    }
                )

    # INSERT
    print("\n[INFO] Inserting predictions...")
    write_predictions(all_preds)

    print("\n[DONE] LightGBM v1 long-horizon forecasting completed successfully.")


if __name__ == "__main__":
    main()
