"""
train_model_prophet_v2.py
----------------------------------------------------------
Trains Prophet models per city using public.features data.
Generates monthly forecasts for 10 years (120 months) ahead and writes results
into public.model_predictions in Neon database.
"""

from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime
from prophet import Prophet
import pandas as pd
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
# 2. Load data from public.features
# ---------------------------------------------------------------------
def load_features():
    query = "SELECT date, city, hpi_benchmark FROM public.features ORDER BY city, date;"
    df = pd.read_sql_query(query, engine)
    print(f"[INFO] Loaded {len(df):,} rows from public.features")
    return df

# ---------------------------------------------------------------------
# 3. Train Prophet per city and predict monthly for 10 years
# ---------------------------------------------------------------------
def train_prophet_per_city(df: pd.DataFrame):
    results = []
    model_name = "prophet_v2"

    for city, group in df.groupby("city"):
        group["date"] = pd.to_datetime(group["date"])
        group = group.sort_values("date")

        # Prophet expects columns 'ds' and 'y'
        prophet_df = group.rename(columns={"date": "ds", "hpi_benchmark": "y"})

        if prophet_df['y'].nunique() <= 1:
            print(f"[WARN] Skipping {city}: constant or zero HPI.")
            continue

        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            changepoint_prior_scale=0.05
        )

        model.fit(prophet_df)

        # Forecast 10 years (120 months) ahead
        future = model.make_future_dataframe(periods=120, freq='MS')
        forecast = model.predict(future)

        max_date = pd.to_datetime(prophet_df["ds"].max())
        forecast_future = forecast[forecast["ds"] > max_date]


        for _, row in forecast_future.iterrows():
            results.append({
                'model_name': model_name,
                'target': 'hpi_benchmark',
                'horizon_months': int((row['ds'] - prophet_df['ds'].max()).days / 30.4),
                'city': city,
                'predict_date': row['ds'],
                'yhat': float(row['yhat']),
                'yhat_lower': float(row['yhat_lower']),
                'yhat_upper': float(row['yhat_upper']),
                'features_version': 'features_build_etl_v9',
                'model_artifact_uri': None,
                'is_micro': False
            })

        print(f"[OK] Prophet trained for {city} ({len(forecast_future)} monthly forecasts)")

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
        conn.execute(insert_sql, df_preds.to_dict(orient='records'))

    print(f"[OK] Inserted {len(df_preds):,} Prophet monthly predictions into public.model_predictions")

# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
if __name__ == '__main__':
    start = datetime.now()
    print("[DEBUG] train_model_prophet_v2 started ...")

    df_features = load_features()
    df_preds = train_prophet_per_city(df_features)
    write_predictions(df_preds)

    print(f"[DONE] train_model_prophet_v2 completed in {datetime.now() - start}")
