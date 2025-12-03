"""
train_model_lightgbm_v3.py
----------------------------------------------------------
Trains LightGBM regression models per city using scaled features and time-based backtesting.
- Training: 2005–2020
- Validation: 2020–2025 (evaluate MAPE & MAE)
- Production forecast: 2025–2035 (120 monthly steps, iterative prediction)
Writes results into public.model_predictions and logs validation metrics.
"""

from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime
import pandas as pd
import lightgbm as lgb
import numpy as np
import os

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
# 2. Load model_features
# ---------------------------------------------------------------------
def load_model_features():
    query = "SELECT * FROM public.model_features ORDER BY city, date;"
    df = pd.read_sql_query(query, engine)
    df['date'] = pd.to_datetime(df['date'])
    print(f"[INFO] Loaded {len(df):,} rows from public.model_features")
    return df

# ---------------------------------------------------------------------
# 3. Evaluation metrics
# ---------------------------------------------------------------------
def evaluate_performance(y_true, y_pred):
    mae = np.mean(np.abs(y_true - y_pred))
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    return mae, mape

# ---------------------------------------------------------------------
# 4. Train and forecast per city
# ---------------------------------------------------------------------
def train_lightgbm_per_city(df: pd.DataFrame):
    results = []
    metrics = []
    model_name = "lightgbm_v3"

    feature_cols = [
        'hpi_benchmark_scaled', 'rent_avg_city_scaled', 'mortgage_rate_scaled',
        'unemployment_rate_scaled', 'overnight_rate_scaled', 'population_scaled',
        'median_income_scaled', 'migration_rate_scaled', 'gdp_growth_scaled', 'cpi_yoy_scaled'
    ]

    for city, group in df.groupby('city'):
        group = group.sort_values('date')

        X = group[feature_cols]
        y = group['hpi_benchmark']

        # ---------------- Time-based split ----------------
        train_mask = group['date'] <= '2020-12-01'
        valid_mask = (group['date'] > '2020-12-01') & (group['date'] <= '2025-12-01')

        X_train, y_train = X[train_mask], y[train_mask]
        X_valid, y_valid = X[valid_mask], y[valid_mask]

        train_data = lgb.Dataset(X_train, label=y_train)
        valid_data = lgb.Dataset(X_valid, label=y_valid, reference=train_data)

        params = {
            'objective': 'regression',
            'metric': 'mae',
            'learning_rate': 0.05,
            'num_leaves': 31,
            'verbose': -1
        }

        model = lgb.train(
            params,
            train_data,
            num_boost_round=500,
            valid_sets=[train_data, valid_data],
            callbacks=[lgb.early_stopping(stopping_rounds=50), lgb.log_evaluation(period=0)]
        )

        # ---------------- Validation ----------------
        if not X_valid.empty:
            y_pred_val = model.predict(X_valid)
            mae, mape = evaluate_performance(y_valid.values, y_pred_val)
            metrics.append({'city': city, 'mae': mae, 'mape': mape})
            print(f"[VAL] {city}: MAE={mae:,.0f}, MAPE={mape:.2f}%")

        # ---------------- Retrain on full data ----------------
        full_data = lgb.Dataset(X, label=y)
        final_model = lgb.train(params, full_data, num_boost_round=int(model.best_iteration or 300))

        # ---------------- Forecast monthly for 10 years ----------------
        last_row = group.iloc[-1].copy()
        last_date = last_row['date']

        for i in range(120):
            next_date = last_date + pd.DateOffset(months=i+1)
            # For simplicity, use last known scaled features (static forecast)
            X_next = last_row[feature_cols].values.reshape(1, -1)
            yhat = float(final_model.predict(X_next)[0])
            yhat_lower, yhat_upper = yhat * 0.95, yhat * 1.05

            results.append({
                'model_name': model_name,
                'target': 'hpi_benchmark',
                'horizon_months': i+1,
                'city': city,
                'predict_date': next_date,
                'yhat': yhat,
                'yhat_lower': yhat_lower,
                'yhat_upper': yhat_upper,
                'features_version': 'features_to_model_etl_v1',
                'model_artifact_uri': None,
                'is_micro': False
            })

        print(f"[OK] LightGBM trained for {city} ({len(group)} records, 120 forecasts)")

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

    print(f"[OK] Inserted {len(df_preds):,} LightGBM monthly predictions into public.model_predictions")

# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
if __name__ == '__main__':
    start = datetime.now()
    print("[DEBUG] train_model_lightgbm_v3 started ...")

    df_features = load_model_features()
    df_preds, df_metrics = train_lightgbm_per_city(df_features)
    write_predictions(df_preds)

    if not df_metrics.empty:
        print("\n[SUMMARY] Validation results (2020–2025):")
        print(df_metrics.sort_values('mape').to_string(index=False, formatters={'mape': '{:.2f}%'.format}))

    print(f"\n[DONE] train_model_lightgbm_v3 completed in {datetime.now() - start}")
