# ml/src/models/pipeline.py

import os
import pandas as pd   
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from ml.src.utils.data_loader import load_timeseries
from ml.src.models.run_models import run_forecasts, calc_risk_indices, detect_anomalies
from ml.src.utils.db_writer import write_forecasts, write_risks, write_anomalies

MIN_POINTS = 3  # Prophet needs >= 2, we use 3 for safety


def _get_engine() -> Engine:
    """Build SQLAlchemy engine from env (works locally & Neon)."""
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5433/hird",
    )
    print(f"[DEBUG] Connecting to DB → {db_url}")
    return create_engine(db_url, future=True)


def _discover_targets(engine: Engine):
    """Discover available (metric, city) pairs safely."""
    targets = []

    with engine.connect() as cx:
        # 🔹 Try rent_index first
        try:
            rent_cities = cx.execute(
                text('SELECT DISTINCT city FROM public.rent_index ORDER BY city')
            ).scalars().all()
            for c in rent_cities:
                targets.append(("rent_index", c))
            print(f"[DEBUG] rent_index cities: {rent_cities}")
        except Exception as e:
            print(f"[WARN] rent_index table not found or empty: {e}")

        # 🔹 Then try house_price_index (CREA)
        try:
            hpi_cities = cx.execute(
                text('SELECT DISTINCT city FROM public.house_price_index ORDER BY city')
            ).scalars().all()
            for c in hpi_cities:
                targets.append(("house_price_index", c))
            print(f"[DEBUG] house_price_index cities: {hpi_cities}")
        except Exception as e:
            print(f"[WARN] house_price_index table not found or empty: {e}")

        # 🔹 Optionally include metrics table for macro data (BoC, StatCan)
        try:
            metrics_cities = cx.execute(
                text('SELECT DISTINCT city FROM public.metrics ORDER BY city')
            ).scalars().all()
            for c in metrics_cities:
                targets.append(("metrics", c))
            print(f"[DEBUG] metrics cities: {metrics_cities}")
        except Exception as e:
            print(f"[WARN] metrics table not found or empty: {e}")

    print(f"[DEBUG] Total discovered targets ({len(targets)}): {targets}")
    return targets


def _has_enough_points(df) -> bool:
    """Return True if DF has enough rows after dropping NaNs."""
    try:
        return len(df.dropna()) >= MIN_POINTS
    except Exception:
        return False


def _run_one(engine, metric: str, city: str) -> None:
    df = load_timeseries(engine, metric, city)
    if df is None or df.empty or len(df.dropna()) < 3:
        print(f"[WARN] Skipping {metric} – {city}: insufficient data.")
        return

    try:
        forecast_res = run_forecasts(df, city, metric)

        # ✅ explicit DataFrame check
        if isinstance(forecast_res, pd.DataFrame) and not forecast_res.empty:
            forecast_res["model_name"] = "Prophet"
            forecast_res["target"] = metric
            forecast_res["horizon_months"] = 12
            forecast_res["city"] = city
            forecast_res["features_version"] = "v1.0"
            forecast_res["model_artifact_uri"] = "ml/models/prophet"

            write_forecasts(engine, forecast_res)
            print(f"[OK] Forecast saved to model_predictions for {metric} – {city}")
        else:
            print(f"[WARN] Forecast result invalid or empty for {metric} – {city}")

    except Exception as e:
        print(f"[ERROR] Forecast step failed for {metric} – {city}: {e}")




def run_pipeline():
    """Main orchestration for ML runs."""
    engine = _get_engine()
    targets = _discover_targets(engine)
    if not targets:
        print("[WARN] No valid targets found. Did you run the ETL first?")
        return

    for metric, city in targets:
        print(f"[DEBUG] Running pipeline for {metric} – {city}")
        _run_one(engine, metric, city)

    print("[DONE] ML pipeline complete.")


if __name__ == "__main__":
    run_pipeline()
