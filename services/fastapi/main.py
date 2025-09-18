from fastapi import FastAPI
import psycopg2, os
from psycopg2.extras import RealDictCursor

app = FastAPI()

DB_URL = os.getenv("DATABASE_URL")


def query(sql, params=None):
    conn = psycopg2.connect(DB_URL, sslmode="require", cursor_factory=RealDictCursor)
    cur = conn.cursor()
    cur.execute(sql, params or ())
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


@app.get("/")
def root():
    return {"status": "ok", "service": "fastapi"}


@app.get("/forecast/{city}")
def get_forecast(city: str):
    sql = """
        SELECT forecast_date, p50, p80, p95, risk_index
        FROM model_predictions
        WHERE city = %s
        ORDER BY forecast_date
    """
    return query(sql, (city,))
