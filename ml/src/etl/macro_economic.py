# ml/src/etl/macro_economic.py
import pandas as pd
from sqlalchemy import text
from ml.src.etl.db import get_engine


def fetch_macro_data():
    """Stub: Replace with StatCan / BoC API calls"""
    data = [
        {
            "date": "2025-08-01",
            "province": "BC",
            "unemployment_rate": 5.6,
            "gdp_growth_rate": 1.2,
            "prime_lending_rate": 6.0,
            "housing_starts": 2100,
        }
    ]
    return pd.DataFrame(data)


def write_macro(df, ctx):
    engine = get_engine(ctx)
    with engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(
                text("""
                INSERT INTO macro_economic_data
                (date, province, unemployment_rate, gdp_growth_rate,
                 prime_lending_rate, housing_starts)
                VALUES (:date, :province, :u, :g, :p, :h)
                ON CONFLICT (date, province) DO UPDATE
                SET unemployment_rate=EXCLUDED.unemployment_rate,
                    gdp_growth_rate=EXCLUDED.gdp_growth_rate,
                    prime_lending_rate=EXCLUDED.prime_lending_rate,
                    housing_starts=EXCLUDED.housing_starts
            """),
                dict(row),
            )


def run(ctx):
    df = fetch_macro_data()
    write_macro(df, ctx)
