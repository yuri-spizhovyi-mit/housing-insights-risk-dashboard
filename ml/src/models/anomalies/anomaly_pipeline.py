from ..utils.data_loader import load_timeseries
from ..utils.db_writer import write_anomalies
from .isolation_forest import detect_iforest


def run_anomaly_pipeline(conn, city: str, target: str):
    """
    Run anomaly detection for a given city + target
    and write results into anomaly_signals.
    """
    df = load_timeseries(conn, target, city)

    results = detect_iforest(df, city, target)

    write_anomalies(conn, results)
