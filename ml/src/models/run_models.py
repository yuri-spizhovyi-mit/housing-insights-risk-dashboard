import pandas as pd

# Forecasting libs
from prophet import Prophet
from statsmodels.tsa.arima.model import ARIMA

# Risk & anomaly detection
from sklearn.ensemble import IsolationForest


# -----------------------------
# Forecast Models
# -----------------------------
def run_forecasts(
    df: pd.DataFrame, city: str, target: str, horizon_months: int = 12
) -> pd.DataFrame:
    """
    Fit Prophet model and return forecast DataFrame ready for DB insertion.
    Expects df with columns ['ds', 'y'] (renamed in data_loader).
    Returns DataFrame with all required columns for model_predictions.
    """
    if df is None or df.empty:
        print(f"[WARN] Empty dataframe for {target} – {city}")
        return pd.DataFrame()

    try:
        model = Prophet(
            seasonality_mode="additive",
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
        )
        model.fit(df)

        # Predict for dynamic horizon (months)
        future = model.make_future_dataframe(periods=horizon_months, freq="MS")
        forecast = model.predict(future)

        # Keep only future horizon
        future_forecast = forecast.tail(horizon_months)[
            ["ds", "yhat", "yhat_lower", "yhat_upper"]
        ].copy()
        future_forecast = future_forecast.rename(columns={"ds": "predict_date"})
        future_forecast["predict_date"] = pd.to_datetime(
            future_forecast["predict_date"]
        )

        # Add metadata columns expected by model_predictions
        future_forecast["model_name"] = "Prophet"
        future_forecast["target"] = target
        future_forecast["horizon_months"] = horizon_months
        future_forecast["city"] = city
        future_forecast["property_type"] = None
        future_forecast["beds"] = None
        future_forecast["baths"] = None
        future_forecast["sqft_min"] = None
        future_forecast["sqft_max"] = None
        future_forecast["year_built_min"] = None
        future_forecast["year_built_max"] = None
        future_forecast["features_version"] = "v1.0"
        future_forecast["model_artifact_uri"] = (
            f"ml/models/prophet_{horizon_months}m.pkl"
        )

        print(
            f"[OK] Forecast generated for {target} – {city} ({horizon_months}m): {len(future_forecast)} rows"
        )
        return future_forecast, model

    except Exception as e:
        print(f"[ERROR] run_forecasts() failed for {target} – {city}: {e}")
        return pd.DataFrame()


# -----------------------------
# Risk Indices
# -----------------------------
from statsmodels.tsa.arima.model import ARIMA
import pandas as pd


def calc_risk_indices(forecast_df, city, target):
    """Compute forecasted risk index (volatility) from Prophet yhat predictions."""
    if forecast_df is None or forecast_df.empty:
        return pd.DataFrame()

    try:
        series = forecast_df["yhat"].dropna()
        model = ARIMA(series, order=(1, 0, 0))
        fitted = model.fit()
        resid = fitted.resid

        risk = resid.rolling(window=3).std().dropna()

        risk_df = pd.DataFrame(
            {
                "city": city,
                "risk_type": target,
                "predict_date": forecast_df.loc[risk.index, "predict_date"].values,
                "risk_value": risk.values,
                "model_name": "ARIMA",
            }
        )
        print(f"[OK] ARIMA produced {len(risk_df)} forecasted risk points for {city}")
        return risk_df

    except Exception as e:
        print(f"[ERROR] calc_risk_indices() failed for {city}: {e}")
        return pd.DataFrame()


# -----------------------------
# Anomaly Detection
# -----------------------------
from sklearn.ensemble import IsolationForest
import pandas as pd
import numpy as np


def detect_anomalies(forecast_df, city, target):
    """Detect anomalies within the Prophet forecast horizon using yhat values."""
    if forecast_df is None or forecast_df.empty:
        return pd.DataFrame()

    try:
        X = forecast_df[["yhat"]].dropna().values
        model = IsolationForest(contamination=0.05, random_state=42)
        model.fit(X)
        scores = model.decision_function(X)
        labels = model.predict(X)  # -1 = anomaly

        anomalies_df = pd.DataFrame(
            {
                "city": city,
                "target": target,
                "detect_date": forecast_df["predict_date"].iloc[-len(X) :].values,
                "anomaly_score": scores,
                "is_anomaly": labels == -1,
                "model_name": "IsolationForest",
            }
        )
        print(
            f"[OK] IsolationForest processed {len(anomalies_df)} forecasted points for {city}"
        )
        return anomalies_df

    except Exception as e:
        print(f"[ERROR] detect_anomalies() failed for {city}: {e}")
        return pd.DataFrame()
