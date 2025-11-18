"""
train_model_arima_v1.py
----------------------------------------------------------
Unified dual-target ARIMA model training script.
Forecasts both 'price' (hpi_benchmark) and 'rent' (rent_avg_city) per city.
Splits data chronologically for backtesting:
- Train: 2005–2020
- Validation: 2020–2025 (MAE & MAPE evaluation)
- Production forecast: 2025–2035 (120 monthly steps)
Writes results into public.model_predictions for both targets.
"""

from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime
from statsmodels.tsa.arima.model import ARIMA
import pandas as pd
import numpy as np
import os
import warnings

warnings.filterwarnings('ignore')

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
# 2. Load data from public.features
# ---------------------------------------------------------------------
def load_features():
    query = "SELECT date, city, hpi_benchmark, rent_avg_city FROM public.features ORDER BY city, date;"
    df = pd.read_sql_query(query, engine)
    df['date'] = pd.to_datetime(df['date'])
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
# 4. Train ARIMA per city for both targets
# ---------------------------------------------------------------------
def train_arima_dual_target(df: pd.DataFrame):
    results = []
    metrics = []
    model_name = "arima_v1"

    for target, column in [("price", "hpi_benchmark"), ("rent", "rent_avg_city")]:
        print(f"\n[INFO] ===== Training target: {target.upper()} =====")

        for city, group in df.groupby('city'):
            group = group.sort_values('date')
            y = group[column].astype(float)

            if y.isna().all() or y.nunique() <= 1:
                print(f"[WARN] Skipping {city}/{target}: not enough variation.")
                continue

            # Split chronologically
            train_df = group[group['date'] <= '2020-12-01']
            valid_df = group[(group['date'] > '2020-12-01') & (group['date'] <= '2025-12-01')]

            try:
                # ---------------- TRAIN ----------------
                model = ARIMA(train_df[column], order=(1,1,1))
                fitted = model.fit()

                # ---------------- VALIDATION ----------------
                if not valid_df.empty:
                    forecast_val = fitted.forecast(steps=len(valid_df))
                    mae, mape = evaluate_performance(valid_df[column].values, forecast_val.values)
                    metrics.append({'target': target, 'city': city, 'mae': mae, 'mape': mape})
                    print(f"[VAL] {city}/{target}: MAE={mae:,.0f}, MAPE={mape:.2f}%")

                # ---------------- RETRAIN ON FULL DATA ----------------
                full_model = ARIMA(group[column], order=(1,1,1))
                fitted_full = full_model.fit()

                forecast_res = fitted_full.get_forecast(steps=120)  # 10 years (monthly)
                forecast = forecast_res.predicted_mean
                conf_int = forecast_res.conf_int(alpha=0.05)

                last_date = pd.to_datetime(group['date'].iloc[-1])

                for i in range(120):
                    predict_date = last_date + pd.DateOffset(months=i+1)
                    results.append({
                        'model_name': model_name,
                        'target': target,
                        'horizon_months': i+1,
                        'city': city,
                        'predict_date': predict_date,
                        'yhat': float(forecast.iloc[i]),
                        'yhat_lower': float(conf_int.iloc[i, 0]),
                        'yhat_upper': float(conf_int.iloc[i, 1]),
                        'features_version': 'features_build_etl_v9',
                        'model_artifact_uri': None,
                        'is_micro': False
                    })

                print(f"[OK] ARIMA trained for {city}/{target} ({len(group)} records, 120 forecasts)")

            except Exception as e:
                print(f"[ERROR] ARIMA failed for {city}/{target}: {e}")

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
        conn.execute(insert_sql, df_preds.to_dict(orient='records'))

    print(f"[OK] Inserted {len(df_preds):,} ARIMA predictions (both targets) into public.model_predictions")

# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
if __name__ == '__main__':
    start = datetime.now()
    print("[DEBUG] train_model_arima_v1 started ...")

    df_features = load_features()
    df_preds, df_metrics = train_arima_dual_target(df_features)
    write_predictions(df_preds)

    if not df_metrics.empty:
        print("\n[SUMMARY] Validation results (2020–2025):")
        print(df_metrics.sort_values('mape').to_string(index=False, formatters={'mape': '{:.2f}%'.format}))

    print(f"\n[DONE] train_model_arima_v1 completed in {datetime.now() - start}")
