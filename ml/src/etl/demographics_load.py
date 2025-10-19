# ================================================================
# ml/src/etl/demographics_load.py — Load demographic data from CSV into DB
# ================================================================

import pandas as pd
from sqlalchemy import create_engine, text
import os


def get_engine():
    db_url = os.getenv(
        "DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5433/hird"
    )
    print(f"[DEBUG] Connecting to DB → {db_url}")
    return create_engine(db_url, future=True)


def fetch_demo_data(path="data/demographics.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    # normalize city names just in case
    df["city"] = df["city"].str.strip()
    return df


def write_demo(df: pd.DataFrame):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS public.demographics (
                date date NOT NULL,
                city varchar(100) NOT NULL,
                population integer,
                migration_rate integer,
                age_25_34_perc numeric(5,2),
                median_income numeric(12,2),
                created_at timestamp without time zone DEFAULT now(),
                PRIMARY KEY (date, city)
            )
        """)
        )
        records = []
        for _, r in df.iterrows():
            records.append(
                {
                    "date": r["date"],
                    "city": r["city"],
                    "population": int(r["population"]),
                    "migration_rate": int(round(float(r["migration_rate"]) * 1000))
                    if not pd.isna(r["migration_rate"])
                    else None,
                    "age_25_34_perc": float(r["age_25_34_perc"])
                    if not pd.isna(r["age_25_34_perc"])
                    else None,
                    "median_income": float(r["median_income"])
                    if not pd.isna(r["median_income"])
                    else None,
                }
            )
        conn.execute(
            text("""
            INSERT INTO public.demographics
                (date, city, population, migration_rate, age_25_34_perc, median_income)
            VALUES
                (:date, :city, :population, :migration_rate, :age_25_34_perc, :median_income)
            ON CONFLICT (date, city) DO UPDATE SET
                population = EXCLUDED.population,
                migration_rate = EXCLUDED.migration_rate,
                age_25_34_perc = EXCLUDED.age_25_34_perc,
                median_income = EXCLUDED.median_income
        """),
            records,
        )
    print(f"[OK] Upserted {len(df)} rows into public.demographics")


if __name__ == "__main__":
    df = fetch_demo_data()
    write_demo(df)
