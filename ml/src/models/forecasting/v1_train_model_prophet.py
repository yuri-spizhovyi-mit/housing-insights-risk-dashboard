"""
train_model_prophet.py
----------------------------------------------------------
Trains Facebook Prophet models per city using public.features data.
Forecasts 1, 2, 5, and 10-year horizons and writes predictions to
public.model_predictions in Neon database.
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
# 3. Train Prophet per city
# ---------------------------------------------------------------------
def train_prophet_per_city(df: pd.DataFrame):
    results = []
    model_name = "prophet_v1"

    for city, group in df.groupby("city"):
        group = group.sort_values("date")

        # Prophet expects ds, y columns
        prophet_df = group.rename(columns={"date": "ds", "hpi_benchmark": "y"})

        # Skip if target is flat or zero (avoid degenerate model)
        if prophet_df["y"].nunique() <= 1:
            print(f"[WARN] Skipping {city}: constant or zero HPI.")
            continue

        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            changepoint_prior_scale=0.05,
        )
        model.fit(prophet_df)

        future = model.make_future_dataframe(periods=120, freq="MS")  # up to 10 years
        forecast = model.predict(future)

        # Select future horizons
        for horizon, months in [(1, 12), (2, 24), (5, 60), (10, 120)]:
            target_date = prophet_df["ds"].max() + pd.DateOffset(months=months)
            row = forecast.loc[forecast["ds"] == target_date]

            if row.empty:
                continue

            yhat = float(row["yhat"].values[0])
            yhat_lower = float(row["yhat_lower"].values[0])
            yhat_upper = float(row["yhat_upper"].values[0])

            results.append(
                {
                    "model_name": model_name,
                    "target": "hpi_benchmark",
                    "horizon_months": months,
                    "city": city,
                    "predict_date": target_date,
                    "yhat": yhat,
                    "yhat_lower": yhat_lower,
                    "yhat_upper": yhat_upper,
                    "features_version": "features_build_etl_v9",
                    "model_artifact_uri": None,
                    "is_micro": False,
                }
            )

        print(f"[OK] Prophet trained for {city} ({len(prophet_df)} records)")

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
        f"[OK] Inserted {len(df_preds):,} Prophet predictions into public.model_predictions"
    )


# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
if __name__ == "__main__":
    start = datetime.now()
    print("[DEBUG] train_model_prophet started ...")

    df_features = load_features()
    df_preds = train_prophet_per_city(df_features)
    write_predictions(df_preds)

    print(f"[DONE] train_model_prophet completed in {datetime.now() - start}")
