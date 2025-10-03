import pandas as pd
from prophet import Prophet


def run_prophet(df: pd.DataFrame, city: str, target: str):
    """
    Forecast using Facebook Prophet.
    Returns a list of dicts ready for insertion into model_predictions.
    """
    results = []
    prophet_df = df.rename(columns={"date": "ds", "value": "y"})
    m = Prophet()
    m.fit(prophet_df)

    future = m.make_future_dataframe(periods=12, freq="ME")
    forecast = m.predict(future)

    for i, row in forecast.tail(12).iterrows():
        results.append(
            {
                "model_name": "prophet",
                "target": target,
                "horizon_months": i + 1,
                "city": city,
                "predict_date": row["ds"].date(),
                "yhat": float(row["yhat"]),
                "yhat_lower": float(row["yhat_lower"]),
                "yhat_upper": float(row["yhat_upper"]),
                "features_version": "v1.0",
                "model_artifact_uri": "s3://models/prophet_v1.pkl",
            }
        )
    return results
