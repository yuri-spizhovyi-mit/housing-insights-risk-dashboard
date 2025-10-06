import pandas as pd

# Forecasting libs
from prophet import Prophet
from statsmodels.tsa.arima.model import ARIMA

# Risk & anomaly detection
from sklearn.ensemble import IsolationForest


# -----------------------------
# Forecast Models
# -----------------------------
def run_forecasts(df: pd.DataFrame, city: str, target: str) -> pd.DataFrame:
    """
    Fit Prophet model and return forecast DataFrame ready for DB insertion.
    Expects df with columns ['ds', 'y'] (already renamed in data_loader).
    Returns DataFrame with all required metadata for model_predictions.
    """
    if df is None or df.empty:
        print(f"[WARN] Empty dataframe for {target} – {city}")
        return pd.DataFrame()

    try:
        m = Prophet(seasonality_mode="additive", yearly_seasonality=True)
        m.fit(df)

        # Predict 12 future months
        future = m.make_future_dataframe(periods=12, freq="MS")
        forecast = m.predict(future)

        # Keep only future horizon
        future_forecast = forecast.tail(12)[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
        future_forecast = future_forecast.rename(columns={"ds": "predict_date"})
        future_forecast["predict_date"] = pd.to_datetime(future_forecast["predict_date"])

        # Add metadata columns expected by model_predictions
        future_forecast["model_name"] = "Prophet"
        future_forecast["target"] = target
        future_forecast["horizon_months"] = list(range(1, len(future_forecast) + 1))
        future_forecast["city"] = city
        future_forecast["property_type"] = None
        future_forecast["beds"] = None
        future_forecast["baths"] = None
        future_forecast["sqft_min"] = None
        future_forecast["sqft_max"] = None
        future_forecast["year_built_min"] = None
        future_forecast["year_built_max"] = None
        future_forecast["features_version"] = "v1.0"
        future_forecast["model_artifact_uri"] = "ml/models/prophet_v1.pkl"

        print(f"[OK] Forecast generated for {target} – {city}: {len(future_forecast)} rows")
        return future_forecast

    except Exception as e:
        print(f"[ERROR] run_forecasts() failed for {target} – {city}: {e}")
        return pd.DataFrame()


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
        {
            "city": city,
            "risk_type": "affordability",
            "predict_date": df["date"].iloc[-1],
            "risk_value": affordability,
            "model_name": "calc",
        },
        {
            "city": city,
            "risk_type": "price_to_rent",
            "predict_date": df["date"].iloc[-1],
            "risk_value": price_to_rent,
            "model_name": "calc",
        },
        {
            "city": city,
            "risk_type": "inventory",
            "predict_date": df["date"].iloc[-1],
            "risk_value": inventory,
            "model_name": "calc",
        },
        {
            "city": city,
            "risk_type": "composite_index",
            "predict_date": df["date"].iloc[-1],
            "risk_value": composite,
            "model_name": "calc",
        },
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
        results.append(
            {
                "city": city,
                "target": target,
                "detect_date": row["date"],
                "anomaly_score": float(row["value"]),
                "is_anomaly": row["score"] == -1,
                "model_name": "isolation_forest",
            }
        )
    return results
