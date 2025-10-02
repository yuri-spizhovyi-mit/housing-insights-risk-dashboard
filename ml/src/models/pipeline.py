import psycopg2
from forecasting.forecast_pipeline import run_forecasting_pipeline
from risk.risk_pipeline import run_risk_pipeline
from anomalies.anomaly_pipeline import run_anomaly_pipeline

def run_pipeline():
    conn = psycopg2.connect("dbname=hird user=postgres password=postgres host=localhost port=5433")

    cities = ["Kelowna", "Toronto", "Vancouver"]
    metrics = ["rent_index", "house_price_index"]

    for city in cities:
        for metric in metrics:
            # Forecasts
            run_forecasting_pipeline(conn, city, metric)

            # Risk
            run_risk_pipeline(conn, city, metric)

            # Anomalies
            run_anomaly_pipeline(conn, city, metric)

    conn.close()

if __name__ == "__main__":
    run_pipeline()
