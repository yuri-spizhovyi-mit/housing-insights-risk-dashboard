import pandas as pd
from sklearn.ensemble import IsolationForest


def detect_iforest(df: pd.DataFrame, city: str, target: str):
    """
    Detect anomalies using IsolationForest.
    Returns list of dicts for anomaly_signals.
    """
    iso = IsolationForest(contamination=0.1, random_state=42)
    df = df.copy()
    df["flag"] = iso.fit_predict(df[["value"]])

    results = []
    for _, row in df.iterrows():
        results.append(
            {
                "city": city,
                "target": target,
                "detect_date": row["date"],
                "anomaly_score": float(row["value"]),
                "is_anomaly": row["flag"] == -1,
                "model_name": "isolation_forest",
            }
        )
    return results
