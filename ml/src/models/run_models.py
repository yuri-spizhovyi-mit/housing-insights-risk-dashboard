import pandas as pd

# Forecasting libs
from prophet import Prophet
from statsmodels.tsa.arima.model import ARIMA
# Risk & anomaly detection
from sklearn.ensemble import IsolationForest

# -----------------------------
# Forecast Models
# -----------------------------
def run_forecasts(df: pd.DataFrame, city: str, target: str):
    results = []

    # Prophet
    prophet_df = df.rename(columns={"date": "ds", "value": "y"})
    m = Prophet()
    m.fit(prophet_df)
    future = m.make_future_dataframe(periods=12, freq="M")
    forecast = m.predict(future)

    for step, row in forecast.tail(12).iterrows():
        results.append({
            "model_name": "prophet",
            "target": target,
            "horizon_months": step + 1,
            "city": city,
            "predict_date": row["ds"].date(),
            "yhat": float(row["yhat"]),
            "yhat_lower": float(row["yhat_lower"]),
            "yhat_upper": float(row["yhat_upper"]),
            "features_version": "v1.0",
            "model_artifact_uri": "s3://models/prophet_v1.pkl"
        })

    # TODO: Add ARIMA, LightGBM models here as needed

    return results


# -----------------------------
# Risk Indices
# -----------------------------
def calc_risk_indices(df: pd.DataFrame, city: str, target: str):
    """
    Simple example:
    - affordability = last_value / baseline_income
    - price_to_rent = house_price_index / rent_index
    - inventory = stub (0.0–1.0)
    """
    latest_val = df["value"].iloc[-1]
    affordability = min(latest_val / 1_000_000, 1.0)  # fake normalization
    price_to_rent = min(latest_val / 500_000, 1.0)
    inventory = 0.4  # TODO: compute from permits table

    composite = (affordability + price_to_rent + (1 - inventory)) / 3

    return [
        {"city": city, "risk_type": "affordability", "predict_date": df["date"].iloc[-1], "risk_value": affordability, "model_name": "calc"},
        {"city": city, "risk_type": "price_to_rent", "predict_date": df["date"].iloc[-1], "risk_value": price_to_rent, "model_name": "calc"},
        {"city": city, "risk_type": "inventory", "predict_date": df["date"].iloc[-1], "risk_value": inventory, "model_name": "calc"},
        {"city": city, "risk_type": "composite_index", "predict_date": df["date"].iloc[-1], "risk_value": composite, "model_name": "calc"},
    ]


# -----------------------------
# Anomaly Detection
# -----------------------------
def detect_anomalies(df: pd.DataFrame, city: str, target: str):
    """
    IsolationForest example: detect spikes/drops
    """
    iso = IsolationForest(contamination=0.1, random_state=42)
    df = df.copy()
    df["score"] = iso.fit_predict(df[["value"]])

    results = []
    for _, row in df.iterrows():
        results.append({
            "city": city,
            "target": target,
            "detect_date": row["date"],
            "anomaly_score": float(row["value"]),
            "is_anomaly": row["score"] == -1,
            "model_name": "isolation_forest"
        })
    return results
