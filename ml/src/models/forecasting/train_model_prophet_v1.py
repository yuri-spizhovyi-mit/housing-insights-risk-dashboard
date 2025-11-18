"""
train_model_prophet_v1.py
----------------------------------------------------------
Unified dual-target Prophet model training script.
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
from prophet import Prophet
import pandas as pd
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
# 2. Load data from public.features
# ---------------------------------------------------------------------
def load_features():
    query = "SELECT date, city, hpi_benchmark, rent_avg_city FROM public.features ORDER BY city, date;"
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
# 4. Train Prophet per city for both targets
# ---------------------------------------------------------------------
def train_prophet_dual_target(df: pd.DataFrame):
    results = []
    metrics = []
    model_name = "prophet_v1"

    for target, column in [("price", "hpi_benchmark"), ("rent", "rent_avg_city")]:
        print(f"\n[INFO] ===== Training target: {target.upper()} =====")

        for city, group in df.groupby("city"):
            group = group.sort_values("date")

            prophet_df = group.rename(columns={column: "y", "date": "ds"})[["ds", "y"]]

            if prophet_df["y"].isna().all() or prophet_df["y"].nunique() <= 1:
                print(f"[WARN] Skipping {city}/{target}: not enough variation.")
                continue

            # Split chronologically
            train_df = prophet_df[prophet_df["ds"] <= "2020-12-01"]
            valid_df = prophet_df[
                (prophet_df["ds"] > "2020-12-01") & (prophet_df["ds"] <= "2025-12-01")
            ]

            # ---------------- TRAIN ----------------
            model = Prophet(yearly_seasonality=True, changepoint_prior_scale=0.05)
            model.fit(train_df)

            # ---------------- VALIDATION ----------------
            if not valid_df.empty:
                forecast_val = model.predict(valid_df[["ds"]])
                mae, mape = evaluate_performance(
                    valid_df["y"].values, forecast_val["yhat"].values
                )
                metrics.append(
                    {"target": target, "city": city, "mae": mae, "mape": mape}
                )
                print(f"[VAL] {city}/{target}: MAE={mae:,.0f}, MAPE={mape:.2f}%")

            # ---------------- RETRAIN ON FULL DATA ----------------
            full_model = Prophet(yearly_seasonality=True, changepoint_prior_scale=0.05)
            full_model.fit(prophet_df)

            # Forecast 10 years ahead (120 months)
            future = full_model.make_future_dataframe(periods=120, freq="MS")
            forecast = full_model.predict(future)
            forecast_future = forecast[forecast["ds"] > prophet_df["ds"].max()]

            for _, row in forecast_future.iterrows():
                results.append(
                    {
                        "model_name": model_name,
                        "target": target,
                        "horizon_months": int(
                            (row["ds"] - prophet_df["ds"].max()).days / 30.4
                        ),
                        "city": city,
                        "predict_date": row["ds"],
                        "yhat": float(row["yhat"]),
                        "yhat_lower": float(row["yhat_lower"]),
                        "yhat_upper": float(row["yhat_upper"]),
                        "features_version": "features_build_etl_v9",
                        "model_artifact_uri": None,
                        "is_micro": False,
                    }
                )

            print(
                f"[OK] Prophet trained for {city}/{target} ({len(forecast_future)} monthly forecasts)"
            )

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
        f"[OK] Inserted {len(df_preds):,} Prophet predictions (both targets) into public.model_predictions"
    )


# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
if __name__ == "__main__":
    start = datetime.now()
    print("[DEBUG] train_model_prophet_v1 started ...")

    df_features = load_features()
    df_preds, df_metrics = train_prophet_dual_target(df_features)
    write_predictions(df_preds)

    if not df_metrics.empty:
        print("\n[SUMMARY] Validation results (2020–2025):")
        print(
            df_metrics.sort_values("mape").to_string(
                index=False, formatters={"mape": "{:.2f}%".format}
            )
        )

    print(f"\n[DONE] train_model_prophet_v1 completed in {datetime.now() - start}")
