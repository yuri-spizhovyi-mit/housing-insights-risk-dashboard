import pandas as pd
from ml.src.models.forecasting.prophet_model import run_prophet
from ml.src.models.forecasting.arima_model import run_arima

def sample_df():
    dates = pd.date_range("2020-01-01", periods=24, freq="M")
    values = [100 + i*5 for i in range(24)]  # simple trend
    return pd.DataFrame({"date": dates, "value": values})

def test_prophet_forecast():
    df = sample_df()
    results = run_prophet(df, "Kelowna", "price")
    assert len(results) == 12
    assert all("yhat" in r for r in results)

def test_arima_forecast():
    df = sample_df()
    results = run_arima(df, "Kelowna", "price")
    assert len(results) == 12
    assert all("yhat" in r for r in results)
