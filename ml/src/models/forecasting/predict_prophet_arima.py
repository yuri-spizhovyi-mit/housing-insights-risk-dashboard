# ================================================================
# predict_prophet_arima.py — Forecasting Orchestrator
# ------------------------------------------------
# - Uses .env for secure DB connection
# - Calls forecast_pipeline.run_forecasting_pipeline() for each city
# - Writes Prophet + ARIMA predictions into public.model_predictions
# ================================================================

import os
from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime

from ml.src.models.forecasting.forecast_pipeline import run_forecasting_pipeline

# --------------------------------------------------------------------
# 🔌 Load environment & connect to DB
# --------------------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL not found in .env")

engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)
print(
    f"[DEBUG] Connected to DB via .env at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)


# --------------------------------------------------------------------
# 🧭 Helper: fetch all available cities
# --------------------------------------------------------------------
def get_cities(conn):
    result = conn.execute(
        text("""
        SELECT DISTINCT city
        FROM public.house_price_index
        WHERE measure = 'Composite_Benchmark'
        ORDER BY city;
    """)
    )
    cities = [r[0] for r in result]
    print(f"[INFO] Found {len(cities)} cities → {cities}")
    return cities


# --------------------------------------------------------------------
# 🚀 Main Orchestration
# --------------------------------------------------------------------
def main():
    cities = []
    with engine.begin() as conn:
        cities = get_cities(conn)

    for city in cities:
        print(f"\n[INFO] Running forecasting pipeline for {city} ...")
        try:
            run_forecasting_pipeline(engine, city=city, target="price_benchmark")
            print(f"[OK] Forecasts saved for {city}.")
        except Exception as e:
            print(f"[ERROR] {city}: {e}")
            continue

    print(f"\n[DONE] ✅ All forecasts generated and stored in model_predictions.")


if __name__ == "__main__":
    main()
