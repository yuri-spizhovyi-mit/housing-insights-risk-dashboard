"""
train_model_arima_v4.py
----------------------------------------------------------
Trains ARIMA models per city using statsmodels with time-based backtesting.
- Training: 2005–2020
- Validation: 2020–2025 (evaluate MAPE & MAE)
- Production forecast: 2025–2035 (120 monthly steps)
Writes results into public.model_predictions and logs validation metrics.
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
    df["date"] = pd.to_datetime(df["date"])
    print(f"[INFO] Loaded {len(df):,} rows from public.features")
    return df


# ---------------------------------------------------------------------
# 3. Evaluate model performance
# ---------------------------------------------------------------------
def evaluate_performance(y_true, y_pred):
    mae = np.mean(np.abs(y_true - y_pred))
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    return mae, mape


# ---------------------------------------------------------------------
# 4. Train ARIMA per city with backtesting
# ---------------------------------------------------------------------
def train_arima_per_city(df: pd.DataFrame):
    results = []
    model_name = "arima_v1"
    metrics = []

    for city, group in df.groupby("city"):
        group = group.sort_values("date")
        y = group["hpi_benchmark"].astype(float)

        if y.nunique() <= 1:
            print(f"[WARN] Skipping {city}: constant or zero HPI.")
            continue

        # Split data chronologically
        train_df = group[group["date"] <= "2020-12-01"]
        valid_df = group[
            (group["date"] > "2020-12-01") & (group["date"] <= "2025-12-01")
        ]

        try:
            # ---------------- TRAIN ----------------
            model = ARIMA(train_df["hpi_benchmark"], order=(1, 1, 1))
            fitted = model.fit()

            # ---------------- VALIDATION ----------------
            if not valid_df.empty:
                forecast_val = fitted.forecast(steps=len(valid_df))
                mae, mape = evaluate_performance(
                    valid_df["hpi_benchmark"].values, forecast_val.values
                )
                metrics.append({"city": city, "mae": mae, "mape": mape})
                print(f"[VAL] {city}: MAE={mae:,.0f}, MAPE={mape:.2f}%")

            # ---------------- RETRAIN ON FULL DATA ----------------
            full_model = ARIMA(group["hpi_benchmark"], order=(1, 1, 1))
            fitted_full = full_model.fit()

            forecast_res = fitted_full.get_forecast(steps=120)  # 10 years (monthly)
            forecast = forecast_res.predicted_mean
            conf_int = forecast_res.conf_int(alpha=0.05)

            last_date = pd.to_datetime(group["date"].iloc[-1])

            for i in range(120):
                predict_date = last_date + pd.DateOffset(months=i + 1)
                results.append(
                    {
                        "model_name": model_name,
                        "target": "hpi_benchmark",
                        "horizon_months": i + 1,
                        "city": city,
                        "predict_date": predict_date,
                        "yhat": float(forecast.iloc[i]),
                        "yhat_lower": float(conf_int.iloc[i, 0]),
                        "yhat_upper": float(conf_int.iloc[i, 1]),
                        "features_version": "features_build_etl_v9",
                        "model_artifact_uri": None,
                        "is_micro": False,
                    }
                )

            print(
                f"[OK] ARIMA trained for {city} ({len(group)} records, 120 forecasts)"
            )

        except Exception as e:
            print(f"[ERROR] ARIMA failed for {city}: {e}")

    return pd.DataFrame(results), pd.DataFrame(metrics)


# ---------------------------------------------------------------------
# 5. Write predictions to public.model_predictions
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
        f"[OK] Inserted {len(df_preds):,} ARIMA monthly predictions into public.model_predictions"
    )


# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
if __name__ == "__main__":
    start = datetime.now()
    print("[DEBUG] train_model_arima_v4 started ...")

    df_features = load_features()
    df_preds, df_metrics = train_arima_per_city(df_features)
    write_predictions(df_preds)

    if not df_metrics.empty:
        print("\n[SUMMARY] Validation results (2020–2025):")
        print(
            df_metrics.sort_values("mape").to_string(
                index=False, formatters={"mape": "{:.2f}%".format}
            )
        )

    print(f"\n[DONE] train_model_arima_v4 completed in {datetime.now() - start}")
