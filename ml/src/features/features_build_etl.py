"""
ETL: Build unified features table for housing models (v9)
----------------------------------------------------------
Adds automatic computation of hpi_change_yoy and rent_change_yoy,
fills NaN values with 0, and optimizes Neon DB write with warm-up + larger batch size.
"""

from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime
import pandas as pd
import os

# ---------------------------------------------------------------------
# 1. Environment setup
# ---------------------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL") or os.getenv("DATABASE_URL")
if not NEON_DATABASE_URL:
    raise RuntimeError("NEON_DATABASE_URL not found in .env")

engine = create_engine(
    NEON_DATABASE_URL,
    pool_pre_ping=True,
    future=True,
    connect_args={"options": "-c statement_timeout=60000"},
)
print("[DEBUG] Connected to Neon via .env")


# ---------------------------------------------------------------------
# 2. Helper to load tables
# ---------------------------------------------------------------------
def load_table(table_name: str, columns: str = "*") -> pd.DataFrame:
    query = f"SELECT {columns} FROM public.{table_name};"
    try:
        df = pd.read_sql_query(query, engine)
        print(f"[INFO] Loaded {len(df):,} rows from {table_name}")
        return df
    except Exception as e:
        print(f"[WARN] Failed to load {table_name}: {e}")
        return pd.DataFrame()


# ---------------------------------------------------------------------
# 3. Transform and merge
# ---------------------------------------------------------------------
def build_features():
    # Load source tables
    hpi = load_table("house_price_index", "date, city, benchmark_price")
    rent = load_table("rent_index", "date, city, rent_value")
    metrics = load_table("metrics", "date, city, metric, value")
    demo = load_table(
        "demographics", "date, city, population, migration_rate, median_income"
    )
    macro = load_table("macro_economic_data", "date, city, gdp_growth, cpi_yoy")

    # Rename columns
    if not hpi.empty:
        hpi.rename(columns={"benchmark_price": "hpi_benchmark"}, inplace=True)
    if not rent.empty:
        rent.rename(columns={"rent_value": "rent_avg_city"}, inplace=True)

    # City reference list
    cities = [
        "Victoria",
        "Vancouver",
        "Calgary",
        "Edmonton",
        "Winnipeg",
        "Ottawa",
        "Toronto",
        "Montreal",
    ]

    # -----------------------------------------------------------------
    # Broadcast national ("Canada") rows to all cities
    # -----------------------------------------------------------------
    def broadcast_national(df: pd.DataFrame, label: str):
        if df.empty or "city" not in df.columns:
            return df
        national = df[df["city"].str.lower() == "canada"]
        if national.empty:
            print(f"[INFO] No national rows to broadcast for {label}")
            return df
        expanded = pd.concat(
            [national.assign(city=c) for c in cities], ignore_index=True
        )
        df = pd.concat([df, expanded], ignore_index=True)
        print(
            f"[INFO] Broadcasted {len(national)} national {label} rows to {len(cities)} cities."
        )
        return df

    metrics = broadcast_national(metrics, "metrics")
    macro = broadcast_national(macro, "macro_economic_data")

    # Pivot metrics (metric → columns)
    if not metrics.empty:
        metrics_wide = metrics.pivot_table(
            index=["date", "city"], columns="metric", values="value", aggfunc="first"
        ).reset_index()
        metrics_wide.columns.name = None
        metrics = metrics_wide
        print(f"[INFO] Pivoted metrics into {len(metrics.columns) - 2} columns.")
    else:
        metrics = pd.DataFrame(columns=["date", "city"])

    # Normalize date & city
    for df in [hpi, rent, metrics, demo, macro]:
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df["city"] = df["city"].astype(str)

    # Build monthly date-city grid
    all_months = pd.date_range("2005-01-01", "2025-08-01", freq="MS")
    base = pd.MultiIndex.from_product(
        [all_months, cities], names=["date", "city"]
    ).to_frame(index=False)
    print(f"[INFO] Base grid created: {len(base):,} rows (months × cities)")

    # Merge all datasets
    df = base.copy()
    sources = {
        "hpi": hpi,
        "rent": rent,
        "metrics": metrics,
        "demo": demo,
        "macro": macro,
    }
    for name, src in sources.items():
        if not src.empty and all(col in src.columns for col in ["date", "city"]):
            df = df.merge(src, on=["date", "city"], how="left")
            print(f"[INFO] Merged {name} ({len(src)} rows)")
        else:
            print(f"[WARN] Skipped {name} — empty or missing date/city.")

    # Sanitize numeric columns
    for col in ["population", "median_income", "migration_rate", "hpi_benchmark"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    if "population" in df.columns:
        df["population"] = df["population"].astype("Int64")

    # -----------------------------------------------------------------
    # Derived metrics (year-over-year % change)
    # -----------------------------------------------------------------
    if "hpi_benchmark" in df.columns:
        df["hpi_change_yoy"] = (
            df.groupby("city")["hpi_benchmark"]
            .apply(lambda s: s.pct_change(12, fill_method=None) * 100)
            .reset_index(level=0, drop=True)
            .fillna(0)
        )

    if "rent_avg_city" in df.columns:
        df["rent_change_yoy"] = (
            df.groupby("city")["rent_avg_city"]
            .apply(lambda s: s.pct_change(12) * 100)
            .reset_index(level=0, drop=True)
            .fillna(0)
        )

    df["source"] = "features_build_etl_v9"
    print(f"[INFO] Final merged features DataFrame: {len(df):,} rows")
    return df


# ---------------------------------------------------------------------
# 4. Upsert (optimized for Neon DB)
# ---------------------------------------------------------------------
def upsert_features(df: pd.DataFrame, batch_size: int = 500):
    if df.empty:
        print("[WARN] No data to upsert — skipping database write.")
        return

    expected_cols = [
        "date",
        "city",
        "hpi_benchmark",
        "rent_avg_city",
        "hpi_change_yoy",
        "rent_change_yoy",
        "mortgage_rate",
        "unemployment_rate",
        "overnight_rate",
        "population",
        "migration_rate",
        "median_income",
        "gdp_growth",
        "cpi_yoy",
        "source",
    ]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = None
    df = df.where(pd.notnull(df), None)

    upsert_sql = text("""
        INSERT INTO public.features (
            date, city,
            hpi_benchmark, rent_avg_city,
            hpi_change_yoy, rent_change_yoy,
            mortgage_rate, unemployment_rate, overnight_rate,
            population, migration_rate, median_income,
            gdp_growth, cpi_yoy,
            source, created_at
        )
        VALUES (
            :date, :city,
            :hpi_benchmark, :rent_avg_city,
            :hpi_change_yoy, :rent_change_yoy,
            :mortgage_rate, :unemployment_rate, :overnight_rate,
            :population, :migration_rate, :median_income,
            :gdp_growth, :cpi_yoy,
            :source, NOW()
        )
        ON CONFLICT (date, city)
        DO UPDATE SET
            hpi_benchmark = EXCLUDED.hpi_benchmark,
            rent_avg_city = EXCLUDED.rent_avg_city,
            hpi_change_yoy = EXCLUDED.hpi_change_yoy,
            rent_change_yoy = EXCLUDED.rent_change_yoy,
            mortgage_rate = EXCLUDED.mortgage_rate,
            unemployment_rate = EXCLUDED.unemployment_rate,
            overnight_rate = EXCLUDED.overnight_rate,
            population = EXCLUDED.population,
            migration_rate = EXCLUDED.migration_rate,
            median_income = EXCLUDED.median_income,
            gdp_growth = EXCLUDED.gdp_growth,
            cpi_yoy = EXCLUDED.cpi_yoy,
            source = EXCLUDED.source,
            created_at = NOW();
    """)

    total = len(df)
    with engine.begin() as conn:
        # Warm-up query to activate Neon compute
        conn.exec_driver_sql("SELECT 1;")
        print("[DEBUG] Neon warmed up, starting upserts...")

        for start in range(0, total, batch_size):
            end = start + batch_size
            chunk = df.iloc[start:end]
            conn.execute(upsert_sql, chunk.to_dict(orient="records"))
            print(f"[DEBUG] Upserted {min(end, total)}/{total} rows...")

    print(f"[OK] Upserted {total:,} rows into public.features")


# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
if __name__ == "__main__":
    start = datetime.now()
    print("[DEBUG] Features build ETL started ...")
    df_features = build_features()
    upsert_features(df_features)
    print(f"[DONE] Features build ETL completed in {datetime.now() - start}")
