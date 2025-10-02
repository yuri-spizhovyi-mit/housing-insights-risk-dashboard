from ..utils.data_loader import load_timeseries
from ..utils.db_writer import write_forecasts
from .prophet_model import run_prophet
from .arima_model import run_arima


def run_forecasting_pipeline(conn, city: str, target: str):
    df = load_timeseries(conn, target, city)

    results = []
    results.extend(run_prophet(df, city, target))
    results.extend(run_arima(df, city, target))

    write_forecasts(conn, results)
