"""
train_model_lightgbm.py
----------------------------------------------------------
Trains LightGBM regression models per city using scaled input features
and raw HPI benchmark as target. Forecasts 1, 2, 5, and 10-year horizons
and writes predictions to public.model_predictions in Neon.
"""

from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import pandas as pd
import lightgbm as lgb
import numpy as np
import os

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
# 2. Load model_features
# ---------------------------------------------------------------------
def load_model_features():
    query = "SELECT * FROM public.model_features ORDER BY city, date;"
    df = pd.read_sql_query(query, engine)
    print(f"[INFO] Loaded {len(df):,} rows from public.model_features")
    return df


# ---------------------------------------------------------------------
# 3. Train LightGBM per city
# ---------------------------------------------------------------------
def train_lightgbm_per_city(df: pd.DataFrame):
    results = []
    model_name = "lightgbm_v1"
    feature_cols = [
        "hpi_benchmark_scaled",
        "rent_avg_city_scaled",
        "mortgage_rate_scaled",
        "unemployment_rate_scaled",
        "overnight_rate_scaled",
        "population_scaled",
        "median_income_scaled",
        "migration_rate_scaled",
        "gdp_growth_scaled",
        "cpi_yoy_scaled",
    ]

    for city, group in df.groupby("city"):
        group = group.sort_values("date")
        X = group[feature_cols]
        y = group["hpi_benchmark"]

        # train/test split by time (80/20)
        split_idx = int(len(group) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        train_set = lgb.Dataset(X_train, y_train)
        valid_set = lgb.Dataset(X_test, y_test, reference=train_set)

        params = {
            "objective": "regression",
            "metric": "mae",
            "learning_rate": 0.05,
            "num_leaves": 31,
            "verbose": -1,
        }

        model = lgb.train(
            params,
            train_set,
            num_boost_round=500,
            valid_sets=[train_set, valid_set],
            callbacks=[
                lgb.early_stopping(stopping_rounds=50),
                lgb.log_evaluation(period=0),
            ],
        )

        # Forecast future horizons (1, 2, 5, 10 years → 12, 24, 60, 120 months)
        last_features = X.iloc[-1].values.reshape(1, -1)
        last_date = pd.to_datetime(group["date"].iloc[-1])

        for horizon, months in [(1, 12), (2, 24), (5, 60), (10, 120)]:
            yhat = float(model.predict(last_features)[0])
            yhat_lower, yhat_upper = yhat * 0.95, yhat * 1.05

            results.append(
                {
                    "model_name": model_name,
                    "target": "hpi_benchmark",
                    "horizon_months": months,
                    "city": city,
                    "predict_date": last_date + pd.DateOffset(months=months),
                    "yhat": yhat,
                    "yhat_lower": yhat_lower,
                    "yhat_upper": yhat_upper,
                    "features_version": "features_to_model_etl_v1",
                    "model_artifact_uri": None,
                    "is_micro": False,
                }
            )

        print(f"[OK] Trained LightGBM for {city} ({len(group)} records)")

    return pd.DataFrame(results)


# ---------------------------------------------------------------------
# 4. Write predictions to public.model_predictions
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
        conn.exec_driver_sql("SELECT 1;")  # warm-up Neon
        conn.execute(insert_sql, df_preds.to_dict(orient="records"))

    print(f"[OK] Inserted {len(df_preds):,} predictions into public.model_predictions")


# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
if __name__ == "__main__":
    start = datetime.now()
    print("[DEBUG] train_model_lightgbm started ...")

    df_features = load_model_features()
    df_preds = train_lightgbm_per_city(df_features)
    write_predictions(df_preds)

    print(f"[DONE] train_model_lightgbm completed in {datetime.now() - start}")
