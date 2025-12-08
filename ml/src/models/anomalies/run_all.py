# ml/src/models/anomalies/run_all.py

from ...etl.db import get_engine
from .anomaly_pipeline import run_all_anomalies


if __name__ == "__main__":
    engine = get_engine()
    run_all_anomalies(engine)
