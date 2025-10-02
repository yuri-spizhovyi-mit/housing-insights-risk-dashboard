import pandas as pd
from statsmodels.tsa.arima.model import ARIMA


def run_arima(df: pd.DataFrame, city: str, target: str):
    """
    Forecast using ARIMA (1,1,1) as a baseline.
    Returns a list of dicts ready for insertion into model_predictions.
    """
    results = []
    series = df["value"]

    model = ARIMA(series, order=(1, 1, 1))
    fit = model.fit()
    forecast = fit.get_forecast(steps=12).summary_frame()

    for i, row in forecast.iterrows():
        results.append(
            {
                "model_name": "arima",
                "target": target,
                "horizon_months": i + 1,
                "city": city,
                "predict_date": row.name.date(),
                "yhat": float(row["mean"]),
                "yhat_lower": float(row["mean_ci_lower"]),
                "yhat_upper": float(row["mean_ci_upper"]),
                "features_version": "v1.0",
                "model_artifact_uri": "s3://models/arima_v1.pkl",
            }
        )
    return results
