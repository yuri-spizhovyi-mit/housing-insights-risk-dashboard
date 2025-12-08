# ml/src/models/anomalies/anomaly_pipeline.py

import pandas as pd
from ml.src.utils.data_loader import load_timeseries
from ml.src.utils.db_writer import write_anomalies
from .isolation_forest import detect_iforest

# -------------------------------------------
# Cities and targets to run anomaly detection
# -------------------------------------------

TARGET_CITIES = [
    "Victoria",
    "Vancouver",
    "Calgary",
    "Edmonton",
    "Winnipeg",
    "Ottawa",
    "Toronto",
]

TARGETS = ["price", "rent"]


# -------------------------------------------------------
# Main function that runs anomaly detection for 1 city+target
# -------------------------------------------------------


def run_anomaly_pipeline(conn, city: str, target: str):
    """
    Load a time series for the given city+target,
    run IsolationForest detection,
    and write results to anomaly_signals.
    """

    print(f"[INFO] Loading time series for {city}, {target}...")

    df = load_timeseries(conn, target, city)

    if df.empty:
        print(f"[WARN] No data found for {city}, {target}. Skipping.")
        return

    print(f"[INFO] Running IsolationForest for {city}, {target}...")
    results = detect_iforest(df, city, target)

    print(f"[INFO] Writing {len(results)} anomalies -> anomaly_signals table...")
    write_anomalies(conn, results)

    print(f"[DONE] Finished {city}, {target}")


# -------------------------------------------------------
# Run pipeline for ALL cities + BOTH targets
# -------------------------------------------------------


def run_all_anomalies(conn):
    """
    Run anomaly detection for:
      - all cities in TARGET_CITIES
      - both price and rent targets
    """

    print("\n========== Running anomaly pipeline for ALL CITIES ==========\n")

    for city in TARGET_CITIES:
        for target in TARGETS:
            print(f"\n=== Start: {city} — {target} ===")
            try:
                run_anomaly_pipeline(conn, city, target)
                print(f"✓ Completed: {city}, {target}")
            except Exception as e:
                print(f"✗ FAILED: {city}, {target} — {e}")

    print("\n========== ALL ANOMALIES PROCESSED ==========\n")
