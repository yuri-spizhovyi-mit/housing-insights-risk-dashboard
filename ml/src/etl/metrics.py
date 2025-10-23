# ml/src/etl/metrics.py
"""
ETL script: metrics.py
---------------------------------------
Purpose:
Load cleaned macroeconomic indicators (BoC + StatCan) into the public.metrics table.

Expected CSV files:
- data/interest_rate_5y_mortgage.csv
- data/overnight_rate.csv
- data/unemployment_rate.csv

Schema reference — public.metrics
---------------------------------------
date        DATE           Month start (YYYY-MM-01)
city        TEXT           'Canada' for national series
metric      TEXT           Metric name (e.g., mortgage_rate, overnight_rate)
value       NUMERIC        Metric numeric value
source      TEXT           Data source reference (e.g., BoC_V39079, StatsCan_14-10-0287)
created_at  TIMESTAMPTZ    Ingestion timestamp
Primary key (date, city, metric)
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv, find_dotenv

# -----------------------------------------------------------------------------
# Load environment and DB connection
# -----------------------------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")

if not NEON_DATABASE_URL:
    raise RuntimeError("NEON_DATABASE_URL not found in .env")

engine = create_engine(NEON_DATABASE_URL, pool_pre_ping=True, future=True)
print("[DEBUG] Connected to Neon database.")


# -----------------------------------------------------------------------------
# Utility functions
# -----------------------------------------------------------------------------
def load_metric_csv(path: str, metric_name: str, source: str) -> pd.DataFrame:
    """Load a cleaned CSV with columns [Date, Value] into standard tidy format."""
    df = pd.read_csv(path)
    if "Date" not in df.columns or "Value" not in df.columns:
        raise ValueError(f"{path} must contain 'Date' and 'Value' columns")
    df = df.rename(columns={"Date": "date", "Value": "value"})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["city"] = "Canada"
    df["metric"] = metric_name
    df["source"] = source
    df = df[["date", "city", "metric", "value", "source"]].dropna()
    print(f"[INFO] Loaded {len(df)} rows from {path}")
    return df


def recreate_metrics_table(engine):
    """Recreate the public.metrics table according to Data_ETL specification."""
    ddl = """
    DROP TABLE IF EXISTS public.metrics CASCADE;
    CREATE TABLE public.metrics (
        date DATE NOT NULL,
        city TEXT NOT NULL,
        metric TEXT NOT NULL,
        value NUMERIC,
        source TEXT DEFAULT 'unknown',
        created_at TIMESTAMPTZ DEFAULT now(),
        PRIMARY KEY (date, city, metric)
    );
    COMMENT ON TABLE public.metrics IS
        'Stores monthly economic indicators (mortgage rate, overnight rate, unemployment, etc.)';
    """
    with engine.begin() as conn:
        for statement in ddl.strip().split(";"):
            if statement.strip():
                conn.execute(text(statement))


def write_metrics(df: pd.DataFrame, engine):
    if df.empty:
        print("[WARN] Nothing to insert into metrics.")
        return
    df.to_sql(
        "metrics",
        con=engine,
        schema="public",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )
    print(f"[OK] Inserted {len(df)} rows into public.metrics.")


# -----------------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    recreate_metrics_table(engine)

    base_path = "data"
    dfs = []
    try:
        dfs.append(
            load_metric_csv(
                os.path.join(base_path, "interest_rate_5y_mortgage.csv"),
                "mortgage_rate",
                "BoC_V80691335",
            )
        )
    except Exception as e:
        print(f"[WARN] Skipped mortgage_rate: {e}")

    try:
        dfs.append(
            load_metric_csv(
                os.path.join(base_path, "overnight_rate.csv"),
                "overnight_rate",
                "BoC_V39079",
            )
        )
    except Exception as e:
        print(f"[WARN] Skipped overnight_rate: {e}")

    try:
        dfs.append(
            load_metric_csv(
                os.path.join(base_path, "unemployment_rate.csv"),
                "unemployment_rate",
                "StatsCan_14-10-0287",
            )
        )
    except Exception as e:
        print(f"[WARN] Skipped unemployment_rate: {e}")

    if dfs:
        df_all = pd.concat(dfs, ignore_index=True)
        write_metrics(df_all, engine)
    else:
        print("[WARN] No metric datasets found.")
