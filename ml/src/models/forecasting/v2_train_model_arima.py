"""
train_model_arima_v2.py
----------------------------------------------------------
Trains ARIMA models per city using statsmodels (stable, pure Python).
Forecasts 1, 2, 5, and 10-year horizons and writes predictions to
public.model_predictions in Neon database.
"""

from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime
from statsmodels.tsa.arima.model import ARIMA
import pandas as pd
import numpy as np
import os
import warnings

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------
# 1. Environment setup
# ---------------------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL") or os.getenv("DATABASE_URL")
if not NEON_DATABASE_URL:
    raise RuntimeError("NEON_DATABASE_URL not found in .env")

engine = create_engine(NEON_DATABASE_URL, pool_pre_ping=True, future=True)
print("[DEBUG] Connected to Neon via .env")


# ---------------------------------------------------------------------
# 2. Load data from public.features
# ---------------------------------------------------------------------
def load_features():
    query = "SELECT date, city, hpi_benchmark FROM public.features ORDER BY city, date;"
    df = pd.read_sql_query(query, engine)
    print(f"[INFO] Loaded {len(df):,} rows from public.features")
    return df


# ---------------------------------------------------------------------
# 3. Train ARIMA per city (using statsmodels)
# ---------------------------------------------------------------------
def train_arima_per_city(df: pd.DataFrame):
    results = []
    model_name = "arima_v2"

    for city, group in df.groupby("city"):
        group = group.sort_values("date")
        y = group["hpi_benchmark"].astype(float)

        if y.nunique() <= 1:
            print(f"[WARN] Skipping {city}: constant or zero HPI.")
            continue

        try:
            # Difference non-stationary data automatically
            d = 1 if (y.diff().abs().sum() > 0) else 0

            model = ARIMA(y, order=(1, d, 1))
            fitted = model.fit()

            forecast_res = fitted.get_forecast(steps=120)  # 10 years (12 months * 10)
            forecast = forecast_res.predicted_mean
            conf_int = forecast_res.conf_int(alpha=0.05)

            last_date = pd.to_datetime(group["date"].iloc[-1])

            for horizon, months in [(1, 12), (2, 24), (5, 60), (10, 120)]:
                if months > len(forecast):
                    continue
                yhat = float(forecast.iloc[months - 1])
                yhat_lower = float(conf_int.iloc[months - 1, 0])
                yhat_upper = float(conf_int.iloc[months - 1, 1])

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
                        "features_version": "features_build_etl_v9",
                        "model_artifact_uri": None,
                        "is_micro": False,
                    }
                )

            print(f"[OK] ARIMA trained for {city} ({len(group)} records)")

        except Exception as e:
            print(f"[ERROR] ARIMA failed for {city}: {e}")

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

    print(
        f"[OK] Inserted {len(df_preds):,} ARIMA predictions into public.model_predictions"
    )


# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
if __name__ == "__main__":
    start = datetime.now()
    print("[DEBUG] train_model_arima started ...")

    df_features = load_features()
    df_preds = train_arima_per_city(df_features)
    write_predictions(df_preds)

    print(f"[DONE] train_model_arima completed in {datetime.now() - start}")
