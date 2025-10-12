# ================================================================
# 🚀 pipeline_micro_update.py — Testing Micro (Property-Level) Forecasts
# ================================================================

import os
import pandas as pd
from sqlalchemy import create_engine, text
from ml.src.utils.data_loader import load_timeseries
from ml.src.utils.db_writer import write_forecasts
from ml.src.models.run_models import run_forecasts
from ml.src.models.run_models_micro_update import run_micro_forecast

MIN_POINTS = 3  # Safety: need enough data for Prophet


# ---------------------------------------------------------------
# 🔌 DB Connection (reuse main pipeline logic)
# ---------------------------------------------------------------
def _get_engine():
    """Build SQLAlchemy engine from env (works locally & Neon)."""
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5433/hird",
    )
    print(f"[DEBUG] Connecting to DB → {db_url}")
    return create_engine(db_url, future=True)


# ---------------------------------------------------------------
# 🔁 Main Runner
# ---------------------------------------------------------------
def _run_one(engine, metric="features", city=None) -> None:
    df = load_timeseries(engine, metric, city)
    if df is None or df.empty or len(df.dropna()) < MIN_POINTS:
        print(f"[WARN] Skipping {metric} – {city}: insufficient data.")
        return

    # Forecast for multiple horizons
    horizons = {12: "1Y", 24: "2Y"}

    for horizon_months, label in horizons.items():
        try:
            # 1️⃣ Prophet forecast (macro)
            forecast_res, _ = run_forecasts(
                df, city, metric, horizon_months=horizon_months
            )
            if isinstance(forecast_res, pd.DataFrame) and not forecast_res.empty:
                forecast_res["model_name"] = "Prophet"
                forecast_res["target"] = metric
                forecast_res["horizon_months"] = horizon_months
                forecast_res["city"] = city
                forecast_res["features_version"] = "v1.0"
                forecast_res["model_artifact_uri"] = "ml/models/prophet"
                write_forecasts(engine, forecast_res)
                print(f"[OK] {label} Prophet forecast saved for {metric} – {city}")

            # 2️⃣ Micro (property-level) forecast
            micro_params = {
                "beds": 2,
                "baths": 1,
                "sqft_avg": 850,
                "property_type": "Condo",
            }
            micro_forecast = run_micro_forecast(
                df, city, micro_params, horizon_months=horizon_months
            )
            if isinstance(micro_forecast, pd.DataFrame) and not micro_forecast.empty:
                write_forecasts(engine, micro_forecast)
                print(f"[OK] {label} Micro forecast saved for {metric} – {city}")

        except Exception as e:
            print(f"[ERROR] Forecast failed for {metric} – {city} ({label}): {e}")

    print(f"[DONE] Completed all horizons for {metric} – {city}")


# ---------------------------------------------------------------
# 🧠 Orchestration
# ---------------------------------------------------------------
def run_pipeline_micro():
    """Run micro forecast pipeline for test cities."""
    engine = _get_engine()
    run_list = ["Vancouver", "Kelowna"]
    for city in run_list:
        print(f"[INFO] Running forecasts for {city}")
        _run_one(engine, metric="hpi_composite_sa", city=city)
    print("[DONE] Micro forecast pipeline completed.")


# ---------------------------------------------------------------
# 🚀 CLI Entrypoint
# ---------------------------------------------------------------
if __name__ == "__main__":
    run_pipeline_micro()
