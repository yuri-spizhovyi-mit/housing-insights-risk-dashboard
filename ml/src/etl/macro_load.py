# ================================================================
# macro_load.py — Load macroeconomic indicators from CSV into Postgres
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


def fetch_macro_data(path="data/macro_economic_data.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    df["city"] = df["city"].str.strip()
    return df


def write_macro(df: pd.DataFrame):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS public.macro_economic_data (
                date DATE NOT NULL,
                city VARCHAR(100) NOT NULL,
                unemployment_rate NUMERIC(5,2),
                gdp_growth_rate NUMERIC(5,2),
                prime_lending_rate NUMERIC(5,2),
                housing_starts INTEGER,
                created_at TIMESTAMP DEFAULT now(),
                PRIMARY KEY (date, city)
            );
        """)
        )

        records = df.to_dict(orient="records")
        conn.execute(
            text("""
            INSERT INTO public.macro_economic_data
                (date, city, unemployment_rate, gdp_growth_rate, prime_lending_rate, housing_starts)
            VALUES
                (:date, :city, :unemployment_rate, :gdp_growth_rate, :prime_lending_rate, :housing_starts)
            ON CONFLICT (date, city) DO UPDATE SET
                unemployment_rate = EXCLUDED.unemployment_rate,
                gdp_growth_rate = EXCLUDED.gdp_growth_rate,
                prime_lending_rate = EXCLUDED.prime_lending_rate,
                housing_starts = EXCLUDED.housing_starts;
        """),
            records,
        )
    print(f"[OK] Upserted {len(df)} rows into public.macro_economic_data")


if __name__ == "__main__":
    df = fetch_macro_data()
    write_macro(df)
