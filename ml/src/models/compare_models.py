"""
compare_models.py
----------------------------------------------------------
Compares forecasting models (LightGBM, Prophet, ARIMA) by city and horizon.
Computes MAE, MAPE, RMSE, ranks models, and writes summary results to
public.model_comparison. Also displays a grouped bar chart (MAPE % by city).
"""

from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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
# 2. Load predictions and actuals
# ---------------------------------------------------------------------
def load_data():
    preds = pd.read_sql_query(
        "SELECT model_name, city, horizon_months, predict_date, yhat FROM public.model_predictions;",
        engine,
    )
    actuals = pd.read_sql_query(
        "SELECT city, date AS predict_date, hpi_benchmark AS actual FROM public.features;",
        engine,
    )
    print(f"[INFO] Loaded {len(preds):,} predictions and {len(actuals):,} actuals.")

    df = preds.merge(actuals, on=["city", "predict_date"], how="inner")
    print(f"[INFO] Merged dataset: {len(df):,} matched rows.")
    return df


# ---------------------------------------------------------------------
# 3. Compute metrics
# ---------------------------------------------------------------------
def compute_metrics(df: pd.DataFrame):
    results = []
    for (city, horizon, model), g in df.groupby(
        ["city", "horizon_months", "model_name"]
    ):
        y_true, y_pred = g["actual"].values, g["yhat"].values
        if len(y_true) == 0 or np.all(y_true == 0):
            continue

        mae = np.mean(np.abs(y_true - y_pred))
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))

        results.append(
            {
                "city": city,
                "horizon_months": horizon,
                "model_name": model,
                "mae": mae,
                "mape": mape,
                "rmse": rmse,
            }
        )

    df_metrics = pd.DataFrame(results)

    # Rank and find best model per city & horizon
    df_metrics["rank"] = df_metrics.groupby(["city", "horizon_months"])["mape"].rank(
        method="dense"
    )
    df_metrics["best_model"] = df_metrics["rank"] == 1

    print(f"[INFO] Computed metrics for {len(df_metrics)} model-city-horizon combos.")
    return df_metrics


# ---------------------------------------------------------------------
# 4. Write results to public.model_comparison
# ---------------------------------------------------------------------
def write_to_db(df: pd.DataFrame):
    if df.empty:
        print("[WARN] No metrics to insert.")
        return

    insert_sql = text("""
        INSERT INTO public.model_comparison (
            city, horizon_months, model_name, mae, mape, rmse, rank, best_model, evaluated_at
        ) VALUES (
            :city, :horizon_months, :model_name, :mae, :mape, :rmse, :rank, :best_model, NOW()
        )
        ON CONFLICT (city, horizon_months, model_name)
        DO UPDATE SET
            mae = EXCLUDED.mae,
            mape = EXCLUDED.mape,
            rmse = EXCLUDED.rmse,
            rank = EXCLUDED.rank,
            best_model = EXCLUDED.best_model,
            evaluated_at = NOW();
    """)

    with engine.begin() as conn:
        conn.exec_driver_sql("SELECT 1;")
        conn.execute(insert_sql, df.to_dict(orient="records"))

    print(f"[OK] Wrote {len(df):,} rows into public.model_comparison")


# ---------------------------------------------------------------------
# 5. Visualization
# ---------------------------------------------------------------------
def plot_comparison(df: pd.DataFrame):
    df_latest = df[df["horizon_months"] == 12]  # plot 1-year horizon by default
    pivot_df = df_latest.pivot(index="city", columns="model_name", values="mape")

    pivot_df.plot(kind="bar", figsize=(10, 5))
    plt.ylabel("MAPE (%)")
    plt.title("Forecasting Model Comparison by City (MAPE %, lower is better)")
    plt.xticks(rotation=45, ha="right")
    plt.legend(title="Model")
    plt.tight_layout()
    plt.show()


# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
if __name__ == "__main__":
    start = datetime.now()
    print("[DEBUG] compare_models started ...")

    df = load_data()
    df_metrics = compute_metrics(df)
    write_to_db(df_metrics)
    plot_comparison(df_metrics)

    print(f"[DONE] compare_models completed in {datetime.now() - start}")
