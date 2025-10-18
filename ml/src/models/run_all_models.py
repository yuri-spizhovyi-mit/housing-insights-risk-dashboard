# ================================================================
# run_all_models.py — Unified Runner for Macro + Micro Pipelines
# ================================================================

from ml.src.models.pipeline import run_pipeline as run_macro
from ml.src.models.run_models_micro_update import run_micro_forecast
from datetime import date
from ml.src.etl import base


def run_all_models():
    print(
        "\n=== STEP 1: Running Macro Forecasts (Prophet + ARIMA + IsolationForest) ==="
    )
    run_macro()

    print("\n=== STEP 2: Running Micro Forecast Scaling (Property-level ratios) ===")
    ctx = base.Context(run_date=date.today())
    run_micro_forecast(ctx, target="rent_index")

    print("\n✅ All pipelines completed successfully!\n")


if __name__ == "__main__":
    run_all_models()
