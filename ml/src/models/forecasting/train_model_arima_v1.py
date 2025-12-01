"""
train_model_arima_v1.py
----------------------------------------------------------
Auto-ARIMA dual-target forecasting model.
Produces forecasts for:
- Home price (target='price')   → hpi_benchmark
- Rent price (target='rent')    → rent_avg_city

Performs:
- Train: 2005–2020
- Validation: 2020–2025
- Forecast: 2025–2035 (120 months)

Writes results into public.model_predictions using the correct schema.
"""

import pandas as pd
import numpy as np
import uuid
from datetime import datetime, timezone
from pmdarima import auto_arima
from sqlalchemy import create_engine, text
from dotenv import load_dotenv, find_dotenv
import os
import warnings

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------
# Environment & Database
# ---------------------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)


# ---------------------------------------------------------------------
# Load model_features (NOT public.features)
# ---------------------------------------------------------------------
def load_model_features():
    q = """
        SELECT
            date,
            city,
            property_type,
            hpi_benchmark,
            rent_avg_city
        FROM public.model_features
        ORDER BY city, property_type, date;
    """
    df = pd.read_sql(q, engine)
    df["date"] = pd.to_datetime(df["date"])
    print(f"[INFO] Loaded {len(df)} rows from model_features")
    return df


# ---------------------------------------------------------------------
# Validation Metrics
# ---------------------------------------------------------------------
def mae(y_true, y_pred):
    return float(np.mean(np.abs(y_true - y_pred)))


def mape(y_true, y_pred):
    return float(np.mean(np.abs((y_true - y_pred) / y_true))) * 100


# ---------------------------------------------------------------------
# Forecasting using Auto-ARIMA
# ---------------------------------------------------------------------
def forecast_auto_arima(series, n_steps=120):
    """Fits auto_arima() and produces forecasts + confidence intervals."""
    model = auto_arima(
        series,
        seasonal=False,
        error_action="ignore",
        suppress_warnings=True,
        stepwise=True,
        trace=False,
        max_p=6,
        max_q=6,
        max_d=2,
    )
    model_fit = model

    fc, conf_int = model_fit.predict(n_periods=n_steps, return_conf_int=True)
    return fc, conf_int, model_fit


# ---------------------------------------------------------------------
# Main training logic per (city, property_type, target)
# ---------------------------------------------------------------------
def train_city_property(df, city, ptype, target, col_name):
    """Returns forecast rows for a single (city, property_type, target)."""

    g = df[(df.city == city) & (df.property_type == ptype)].sort_values("date")

    # Split chronologically:
    train = g[g.date <= "2020-12-01"]
    valid = g[(g.date > "2020-12-01") & (g.date <= "2025-12-01")]

    y_train = train[col_name].astype(float)
    y_valid = valid[col_name].astype(float)

    if y_train.nunique() <= 1:
        print(f"[WARN] Not enough variation: {city}/{ptype}/{target}")
        return []

    # ---------------- TRAIN AUTO-ARIMA ----------------
    try:
        # Fit model on training data
        valid_steps = len(y_valid)
        preds_val, conf_val, model_fit = forecast_auto_arima(y_train, n_steps=valid_steps)

        # Validation metrics
        if valid_steps > 0:
            v_mae = mae(y_valid.values, preds_val)
            v_mape = mape(y_valid.values, preds_val)
            print(f"[VAL] {city}/{ptype}/{target}: MAE={v_mae:,.0f}, MAPE={v_mape:.2f}%")

        # Retrain on full dataset
        full_series = g[col_name].astype(float)
        fc, conf, model_fit_full = forecast_auto_arima(full_series, n_steps=120)

        last_date = g.date.max()

        rows = []
        for i in range(120):
            forecast_date = last_date + pd.DateOffset(months=i + 1)

            rows.append(
                {
                    "run_id": str(uuid.uuid4()),
                    "model_name": "arima_v1",
                    "target": target,
                    "horizon_months": i + 1,
                    "city": city,
                    "property_type": ptype,
                    "beds": None,
                    "baths": None,
                    "sqft_min": None,
                    "sqft_max": None,
                    "year_built_min": None,
                    "year_built_max": None,
                    "predict_date": forecast_date,
                    "yhat": float(fc[i]),
                    "yhat_lower": float(conf[i][0]),
                    "yhat_upper": float(conf[i][1]),
                    "features_version": "model_features_v1",
                    "model_artifact_uri": None,
                    "created_at": datetime.now(timezone.utc),
                    "is_micro": False,
                }
            )

        print(f"[OK] Forecasted {city}/{ptype}/{target} (120 months)")
        return rows

    except Exception as e:
        print(f"[ERROR] AutoARIMA failed for {city}/{ptype}/{target}: {e}")
        return []


# ---------------------------------------------------------------------
# Insert into public.model_predictions
# ---------------------------------------------------------------------
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

    print(f"[OK] Inserted {len(rows)} ARIMA predictions.")


# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
def main():
    print("[DEBUG] Starting ARIMA v1 training...")

    df = load_model_features()

    all_rows = []

    for (city, ptype), _ in df.groupby(["city", "property_type"]):
        # Home Price (target='price')
        rows_price = train_city_property(df, city, ptype, "price", "hpi_benchmark")
        all_rows.extend(rows_price)

        # Rent Price (target='rent')
        rows_rent = train_city_property(df, city, ptype, "rent", "rent_avg_city")
        all_rows.extend(rows_rent)

    write_predictions(all_rows)
    print("[DONE] ARIMA v1 training complete.")


if __name__ == "__main__":
    main()
