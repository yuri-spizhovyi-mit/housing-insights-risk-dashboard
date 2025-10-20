# ml/tests/trace_prophet.py
import pandas as pd
from sqlalchemy import create_engine, text
from prophet import Prophet
import numpy as np
import os

ENGINE = create_engine(
       os.environ.get("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5433/hird")
   )

CITY = "Vancouver"
TARGET = "rent_index"   # <- switch to 'house_price_index' to compare

def build_training_df(city, target):
    with ENGINE.begin() as conn:
        if target == "rent_index":
            # Adjust to match YOUR source of truth:
            # (A) rent_index table:
            q = text("""
                SELECT date AS ds, index_value AS y
                FROM public.rent_index
                WHERE city=:city
                ORDER BY date
            """)
            # (B) Or features table (uncomment if that's your source):
            # q = text("""
            #     SELECT date AS ds, rent_monthly_median AS y
            #     FROM public.features
            #     WHERE city=:city
            #     ORDER BY date
            # """)
        else:
            q = text("""
                SELECT date AS ds, index_value AS y
                FROM public.house_price_index
                WHERE city=:city AND measure='Composite'
                ORDER BY date
            """)
        df = pd.read_sql(q, conn, params={"city": city})
    return df

def main():
    df = build_training_df(CITY, TARGET)

    print("\n=== TRAIN DF HEAD ===")
    print(df.head(10))
    print("\n=== TRAIN DF TAIL ===")
    print(df.tail(10))
    print("\n=== TRAIN DF STATS ===")
    print(df["y"].describe())
    print("\nAny negatives in y?:", (df["y"] < 0).any())
    print("Any NaNs in y?:", df["y"].isna().any())

    # Optional: if you log-transform elsewhere, check here!
    # y_log = np.log1p(df["y"])
    # print("\nlog1p(y) stats:", y_log.describe())

    # Fit a tiny model to see immediate forecast scale (no writing to DB)
    m = Prophet(uncertainty_samples=0)  # matches your collapsed intervals
    m.fit(df.rename(columns={"ds":"ds", "y":"y"}))

    future = m.make_future_dataframe(periods=24, freq="MS")
    fcst = m.predict(future)[["ds","yhat","yhat_lower","yhat_upper"]]

    print("\n=== SAMPLE FORECAST (IN-MEMORY) ===")
    print(fcst.tail(12))
    print("\nMin yhat:", fcst["yhat"].min(), "Max yhat:", fcst["yhat"].max())

if __name__ == "__main__":
    main()
