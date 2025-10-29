"""
ETL: Monthly GDP Growth (derived from StatCan Table 36-10-0434-01)
Source: data/raw/gdp_36100434.zip
Computes YoY growth (%) and broadcasts to all dashboard cities.
"""

from zipfile import ZipFile
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime
import pandas as pd
import os

# ---------------------------------------------------------------------
# 1. Load environment and DB
# ---------------------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
NEON_DATABASE_URL = os.getenv("DATABASE_URL")
if not NEON_DATABASE_URL:
    raise RuntimeError("NEON_DATABASE_URL not found in .env")

engine = create_engine(NEON_DATABASE_URL, pool_pre_ping=True, future=True)
print("[DEBUG] Connected to Neon via .env")

# ---------------------------------------------------------------------
# 2. Load GDP ZIP file
# ---------------------------------------------------------------------
def load_gdp_zip(path="data/raw/gdp_36100434.zip") -> pd.DataFrame:
    with ZipFile(path, "r") as z:
        fname = next((n for n in z.namelist() if n.endswith((".csv", ".xlsx"))), None)
        if not fname:
            raise FileNotFoundError("No CSV/XLSX file found in GDP ZIP archive")
        print(f"[DEBUG] Reading {fname} ...")

        if fname.endswith(".csv"):
            with z.open(fname) as f:
                df = pd.read_csv(f, low_memory=False)
        else:
            with z.open(fname) as f:
                df = pd.read_excel(f, engine="openpyxl")

    print(f"[INFO] Loaded {len(df):,} raw GDP rows")

    # Filter for national, seasonally adjusted, real GDP
    df = df[
        (df["GEO"] == "Canada")
        & (df["Seasonal adjustment"] == "Seasonally adjusted at annual rates")
        & (df["Prices"] == "Chained (2017) dollars")
        & (df["North American Industry Classification System (NAICS)"].str.contains("All industries"))
    ].copy()

    # Parse and clean
    df["date"] = pd.to_datetime(df["REF_DATE"], errors="coerce")
    df["gdp_level"] = pd.to_numeric(df["VALUE"], errors="coerce")
    df = df.dropna(subset=["date", "gdp_level"])

    # Deduplicate any monthly duplicates
    df = df.groupby("date", as_index=False)["gdp_level"].mean()

    print(f"[INFO] Filtered {len(df)} monthly GDP points (All industries, real chained 2017 dollars)")
    return df


# ---------------------------------------------------------------------
# 3. Compute YoY growth (%)
# ---------------------------------------------------------------------
def transform_gdp(df: pd.DataFrame) -> pd.DataFrame:
    all_months = pd.date_range("2004-01-01", "2025-08-01", freq="MS")
    df = df.set_index("date").reindex(all_months).rename_axis("date").reset_index()
    df["gdp_level"] = df["gdp_level"].ffill()

    # Compute year-over-year GDP growth %
    df["gdp_growth"] = (df["gdp_level"] / df["gdp_level"].shift(12) - 1) * 100
    df["source"] = "StatCan_36-10-0434-01"
    df = df.dropna(subset=["gdp_growth"])
    print(f"[INFO] Computed GDP YoY from {df['date'].min().date()} → {df['date'].max().date()}")
    return df


# ---------------------------------------------------------------------
# 4. Broadcast to cities
# ---------------------------------------------------------------------
def broadcast_to_cities(df: pd.DataFrame) -> pd.DataFrame:
    cities = ["Victoria", "Vancouver", "Calgary", "Edmonton", "Winnipeg", "Ottawa", "Toronto", "Montreal"]
    rows = []
    for _, row in df.iterrows():
        for city in cities:
            rows.append({
                "date": row["date"],
                "city": city,
                "gdp_growth": round(row["gdp_growth"], 3),
                "source": row["source"],
            })
    df_cities = pd.DataFrame(rows)
    print(f"[INFO] Broadcasted to {len(cities)} cities, total {len(df_cities):,} rows")
    return df_cities


# ---------------------------------------------------------------------
# 5. Upsert into database
# ---------------------------------------------------------------------
def upsert_gdp(df: pd.DataFrame, batch_size: int = 500):
    upsert_sql = text("""
        INSERT INTO public.macro_economic_data (date, city, gdp_growth, source, created_at)
        VALUES (:date, :city, :gdp_growth, :source, NOW())
        ON CONFLICT (date, city)
        DO UPDATE SET
            gdp_growth = EXCLUDED.gdp_growth,
            source = EXCLUDED.source,
            created_at = NOW();
    """)

    total = len(df)
    with engine.begin() as conn:
        for start in range(0, total, batch_size):
            end = start + batch_size
            chunk = df.iloc[start:end]
            conn.execute(upsert_sql, chunk.to_dict(orient="records"))
            print(f"[DEBUG] Upserted {min(end, total)}/{total} rows...")

    print(f"[OK] Upserted {total:,} GDP rows in batches of {batch_size}")



# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
if __name__ == "__main__":
    start = datetime.now()
    print("[DEBUG] GDP ETL started ...")
    df = load_gdp_zip()
    df = transform_gdp(df)
    df = broadcast_to_cities(df)
    upsert_gdp(df)
    print(f"[DONE] GDP ETL completed in {datetime.now() - start}")
