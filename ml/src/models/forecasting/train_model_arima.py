"""
train_model_arima.py
-----------------------------------------
City-level ARIMA forecasting
Targets:
- price  -> hpi_benchmark
- rent   -> rent_avg_city
Forecasting horizon: 1–60 months

"""

import pandas as pd
import numpy as np
import uuid
import os
import warnings
from datetime import datetime, timezone
from sqlalchemy import text, create_engine
from dotenv import load_dotenv, find_dotenv
import pmdarima as pm

warnings.filterwarnings("ignore")

# ---------------------------------------------------------
# ENVIRONMENT
# ---------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)


# ---------------------------------------------------------
# LOAD FEATURES
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# TRAIN AUTO ARIMA
# ---------------------------------------------------------
def fit_arima(series):
    return pm.auto_arima(
        series,
        seasonal=False,
        error_action="ignore",
        suppress_warnings=True,
        stepwise=True,
        max_p=5,
        max_q=5,
        max_d=2
    )


# ---------------------------------------------------------
# TRAIN FOR ONE CITY + TARGET
# ---------------------------------------------------------
def forecast_city_target(df, city, target_col, target_name):
    g = df[df.city == city].sort_values("date")

    if len(g) < 36:
        print(f"[WARN] Not enough data for {city}/{target_name}")
        return []

    model = fit_arima(g[target_col])

    # Forecast 60 months
    fc, conf = model.predict(n_periods=60, return_conf_int=True)
    fc = np.asarray(fc).reshape(-1)
    conf = np.asarray(conf)

    start_date = g["date"].max()

    rows = []
    for h in range(60):
        forecast_date = start_date + pd.DateOffset(months=h + 1)

        y_raw = max(0.0, float(fc[h]))
        lo_raw = max(0.0, float(conf[h, 0]))
        hi_raw = max(0.0, float(conf[h, 1]))

        rows.append({
            "run_id": str(uuid.uuid4()),
            "model_name": "arima",
            "target": target_name,
            "horizon_months": h + 1,
            "city": city,
            "property_type": None,
            "beds": None,
            "baths": None,
            "sqft_min": None,
            "sqft_max": None,
            "year_built_min": None,
            "year_built_max": None,
            "predict_date": forecast_date,
            "yhat": float(y_raw),
            "yhat_lower": float(lo_raw),
            "yhat_upper": float(hi_raw),
            "features_version": "features_to_model_v1",
            "model_artifact_uri": None,
            "created_at": datetime.now(timezone.utc),
            "is_micro": False
        })

    print(f"[OK] ARIMA v2 forecast: {city}/{target_name}")
    return rows


# ---------------------------------------------------------
# INSERT PREDICTIONS
# ---------------------------------------------------------
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

    print(f"[OK] Inserted {len(rows)} ARIMA predictions.")


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
def main():
    print("[DEBUG] Starting ARIMA ...")

    df = load_features()
    all_rows = []

    for city in df.city.unique():
        all_rows.extend(forecast_city_target(df, city, "hpi_benchmark", "price"))
        all_rows.extend(forecast_city_target(df, city, "rent_avg_city", "rent"))

    write_predictions(all_rows)
    print("[DONE] ARIMA complete.")


if __name__ == "__main__":
    main()
