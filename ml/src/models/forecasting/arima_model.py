import pandas as pd
from statsmodels.tsa.arima.model import ARIMA


def run_arima(df: pd.DataFrame, city: str, target: str):
    results = []
    series = df["value"]

    model = ARIMA(series, order=(1, 1, 1))
    fit = model.fit()
    forecast = fit.get_forecast(steps=12)
    forecast_df = forecast.summary_frame()

    # forecast_df.index is usually RangeIndex → build real dates
    last_date = df["date"].iloc[-1]
    future_dates = pd.date_range(last_date, periods=12, freq="ME")

    for i, (date, row) in enumerate(zip(future_dates, forecast_df.itertuples())):
        results.append(
            {
                "model_name": "arima",
                "target": target,
                "horizon_months": i + 1,
                "city": city,
                "predict_date": date.date(),
                "yhat": float(row.mean),
                "yhat_lower": float(row.mean_ci_lower),
                "yhat_upper": float(row.mean_ci_upper),
                "features_version": "v1.0",
                "model_artifact_uri": "s3://models/arima_v1.pkl",
            }
        )
    return results
