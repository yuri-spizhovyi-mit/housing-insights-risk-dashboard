#!/usr/bin/env python3
"""
compare_models_v2.py
Automatically computes validation metrics (MAPE) for each model:
- prophet_v3
- arima_v4
- lightgbm_v3
- lstm_v1

Populates table: public.model_comparison
Exports JSON for dashboard: ./.debug/model_comparison.json
"""

import json
import numpy as np
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor

MODELS = [
    ("prophet_v3", "prophet"),
    ("arima_v4", "arima"),
    ("lightgbm_v3", "lightgbm"),
    ("lstm_v1", "lstm"),
]


def mape(y_true, y_pred):
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    return float(np.mean(np.abs((y_true - y_pred) / y_true)) * 100)


def fetch_predictions(conn, model_name):
    q = """
        SELECT predict_date, y_true, y_pred
        FROM public.model_predictions
        WHERE model_name = %s
        ORDER BY predict_date
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(q, (model_name,))
        return cur.fetchall()


def upsert_model_comparison(conn, model_name, family, mape_value):
    q = """
        INSERT INTO public.model_comparison(model_name, family, mape)
        VALUES (%s, %s, %s)
        ON CONFLICT (model_name)
        DO UPDATE SET mape = EXCLUDED.mape;
    """
    with conn.cursor() as cur:
        cur.execute(q, (model_name, family, mape_value))


def main():
    conn = psycopg2.connect(
        host="localhost", dbname="housing", user="postgres", password="postgres"
    )

    results = []

    for version, family in MODELS:
        rows = fetch_predictions(conn, version)
        if not rows:
            print(f"No data for {version}")
            continue

        df = pd.DataFrame(rows)
        score = mape(df["y_true"], df["y_pred"])

        upsert_model_comparison(conn, version, family, score)

        results.append(
            {"model_name": version, "family": family, "mape": round(score, 4)}
        )

    conn.commit()
    conn.close()

    Path("./.debug").mkdir(exist_ok=True)
    with open("./.debug/model_comparison.json", "w") as f:
        json.dump(results, f, indent=2)

    print("DONE: model_comparison updated & JSON exported.")


if __name__ == "__main__":
    main()
