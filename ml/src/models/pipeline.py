import psycopg2
from data_loader import load_timeseries
from run_models import run_forecasts, calc_risk_indices, detect_anomalies
from db_writer import write_forecasts, write_risks, write_anomalies


def run_pipeline():
    conn = psycopg2.connect(
        "dbname=hird user=postgres password=postgres host=localhost port=5433"
    )

    cities = ["Kelowna", "Toronto", "Vancouver"]
    metrics = ["rent_index", "house_price_index"]

    for city in cities:
        for metric in metrics:
            df = load_timeseries(conn, metric, city)

            # Forecast models
            forecast_res = run_forecasts(df, city, metric)
            write_forecasts(conn, forecast_res)

            # Risk indices
            risk_res = calc_risk_indices(df, city, metric)
            write_risks(conn, risk_res)

            # Anomaly detection
            anomaly_res = detect_anomalies(df, city, metric)
            write_anomalies(conn, anomaly_res)

    conn.close()


if __name__ == "__main__":
    run_pipeline()
