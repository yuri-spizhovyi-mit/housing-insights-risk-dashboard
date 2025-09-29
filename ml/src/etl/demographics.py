# ml/src/etl/demographics.py
import pandas as pd
from sqlalchemy import text
from ml.src.etl.db import get_engine


def fetch_demo_data():
    """Stub: Replace with StatCan population tables"""
    data = [
        {
            "date": "2025-01-01",
            "city": "Kelowna",
            "population": 156000,
            "net_migration": 2300,
            "age_distribution_25_34_perc": 18.5,
            "avg_disposable_income": 54000,
        }
    ]
    return pd.DataFrame(data)


def write_demo(df, ctx):
    engine = get_engine(ctx)
    with engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(
                text("""
                INSERT INTO demographics
                (date, city, population, net_migration,
                 age_distribution_25_34_perc, avg_disposable_income)
                VALUES (:date, :city, :population, :net_migration, :age, :income)
                ON CONFLICT (date, city) DO UPDATE
                SET population=EXCLUDED.population,
                    net_migration=EXCLUDED.net_migration,
                    age_distribution_25_34_perc=EXCLUDED.age,
                    avg_disposable_income=EXCLUDED.income
            """),
                {
                    "date": row["date"],
                    "city": row["city"],
                    "population": row["population"],
                    "net_migration": row["net_migration"],
                    "age": row["age_distribution_25_34_perc"],
                    "income": row["avg_disposable_income"],
                },
            )


def run(ctx):
    df = fetch_demo_data()
    write_demo(df, ctx)
