"""
train_model_arima_v1.py
----------------------------------------------------------
CITY-LEVEL ARIMA FORECASTING (PHASE 2)

Targets:
- price (city-level HPI)
- rent  (city-level rent)

Per city:
- Train: all data <= 2020-12-01
- Validate: 2021-01-01 → 2025-12-01
- Forecast: 120 months ahead (2025–2035)

Writes predictions into public.model_predictions.
"""

import pandas as pd
import numpy as np
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from dotenv import load_dotenv, find_dotenv
import os
import warnings
import pmdarima as pm

warnings.filterwarnings("ignore")


# ---------------------------------------------------------
# ENVIRONMENT
# ---------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)


# ---------------------------------------------------------
# LOAD CITY-LEVEL MODEL FEATURES
# ---------------------------------------------------------
def load_city_features():
    q = """
        SELECT
            date,
            city,
            hpi,
            rent
        FROM public.model_features
        ORDER BY city, date;
    """
    df = pd.read_sql(q, engine)
    df["date"] = pd.to_datetime(df["date"])
    print(f"[INFO] Loaded {len(df)} rows from model_features (city level).")
    return df


# ---------------------------------------------------------
# TRAIN AUTO_ARIMA
# ---------------------------------------------------------
def train_arima_series(series):
    """
    Fit AutoARIMA on the given 1D city-level series.
    Always returns a trained pmdarima model.
    """
    model = pm.auto_arima(
        series,
        seasonal=False,
        stepwise=True,
        suppress_warnings=True,
        error_action="ignore",
        max_p=5,
        max_q=5,
        max_d=2,
    )
    return model


# ---------------------------------------------------------
# VALIDATION METRICS
# ---------------------------------------------------------
def mae(y, yhat):
    return float(np.mean(np.abs(y - yhat)))


def mape(y, yhat):
    return float(np.mean(np.abs((y - yhat) / y))) * 100


# ---------------------------------------------------------
# TRAIN FOR ONE CITY + ONE TARGET
# ---------------------------------------------------------
def train_arima_for_city(df, city, target_col, target_name):

    g = df[df.city == city].sort_values("date")

    # -------------------------------------------
    # TRAIN / VALIDATION SPLIT
    # -------------------------------------------
    train = g[g.date <= "2020-12-01"]
    valid = g[(g.date > "2020-12-01") & (g.date <= "2025-12-01")]

    if len(train) < 50:
        print(f"[WARN] Not enough history for {city} {target_name}")
        return []

    # -------------------------------------------
    # TRAIN AUTO ARIMA
    # -------------------------------------------
    model = train_arima_series(train[target_col])

    # -------------------------------------------
    # VALIDATION
    # -------------------------------------------
    if len(valid) > 0:
        pred_val = model.predict(n_periods=len(valid))
        pred_val = np.asarray(pred_val).reshape(-1)

        v_mae = mae(valid[target_col].values, pred_val)
        v_mape = mape(valid[target_col].values, pred_val)
        print(f"[VAL] {city}/{target_name}: MAE={v_mae:.0f}, MAPE={v_mape:.2f}%")

    # -------------------------------------------
    # RETRAIN ON FULL CITY HISTORY
    # -------------------------------------------
    model_final = train_arima_series(g[target_col])

    # -------------------------------------------
    # FORECAST 120 MONTHS AHEAD
    # -------------------------------------------
    fc, conf = model_final.predict(
        n_periods=120,
        return_conf_int=True
    )

    # ❗ SAFETY CONVERSION — THE FIX
    fc = np.asarray(fc).reshape(-1)
    conf = np.asarray(conf).reshape(-1, 2)

    start_date = g["date"].max()
    rows = []

    for i in range(120):
        forecast_date = start_date + pd.DateOffset(months=i + 1)

        y = float(fc[i])
        lo = float(conf[i, 0])
        hi = float(conf[i, 1])

        rows.append({
            "run_id": str(uuid.uuid4()),
            "model_name": "arima_v1",
            "target": target_name,      # "price" or "rent"
            "horizon_months": i + 1,
            "city": city,
            "property_type": None,      # None = city-level model
            "beds": None,
            "baths": None,
            "sqft_min": None,
            "sqft_max": None,
            "year_built_min": None,
            "year_built_max": None,
            "predict_date": forecast_date,
            "yhat": y,
            "yhat_lower": lo,
            "yhat_upper": hi,
            "features_version": "model_features_city_v1",
            "model_artifact_uri": None,
            "created_at": datetime.now(timezone.utc),
            "is_micro": False
        })

    print(f"[OK] ARIMA forecast created for {city}/{target_name}")
    return rows


# ---------------------------------------------------------
# WRITE PREDICTIONS
# ---------------------------------------------------------
def write_predictions(rows):
    if not rows:
        print("[WARN] No predictions to write.")
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
            :run_id, :model_name, :target, :horizon_monthths,
            :city, :property_type,
            :beds, :baths, :sqft_min, :sqft_max,
            :year_built_min, :year_built_max,
            :predict_date, :yhat, :yhat_lower, :yhat_upper,
            :features_version, :model_artifact_uri,
            :created_at, :is_micro
        );
    """)

    # Correction: horizon_monthths -> horizon_months
    sql = text(sql.text.replace("horizon_monthths", "horizon_months"))

    with engine.begin() as conn:
        conn.execute(sql, rows)

    print(f"[OK] Inserted {len(rows)} ARIMA v1 predictions.")


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
def main():
    print("[DEBUG] Starting ARIMA v1 city-level training...")

    df = load_city_features()
    all_rows = []

    for city in df.city.unique():

        # city-level price forecast
        rows_hpi = train_arima_for_city(df, city, "hpi", "price")
        all_rows.extend(rows_hpi)

        # city-level rent forecast
        rows_rent = train_arima_for_city(df, city, "rent", "rent")
        all_rows.extend(rows_rent)

    write_predictions(all_rows)

    print("[DONE] ARIMA v1 completed successfully.")


if __name__ == "__main__":
    main()
