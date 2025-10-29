"""
ETL: CPI YoY by Province → City Broadcast
Source: Statistics Canada Table 18-10-0004-01 (Consumer Price Index)
Input : data/raw/cpi_18100004.zip
Output: public.macro_economic_data (columns: date, city, cpi_yoy)
"""

from zipfile import ZipFile
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime
import pandas as pd
import os

# ---------------------------------------------------------------------
# 1. Load environment
# ---------------------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")
if not NEON_DATABASE_URL:
    raise RuntimeError("NEON_DATABASE_URL not found in .env")

engine = create_engine(NEON_DATABASE_URL, pool_pre_ping=True, future=True)
print("[DEBUG] Connected to Neon via .env")


# ---------------------------------------------------------------------
# 2. Read CPI file from ZIP
# ---------------------------------------------------------------------
def load_cpi_zip(path="data/raw/cpi_18100004.zip") -> pd.DataFrame:
    with ZipFile(path, "r") as z:
        csv_name = next((n for n in z.namelist() if n.endswith(".csv")), None)
        if not csv_name:
            raise FileNotFoundError("No CSV file found in CPI ZIP archive")
        with z.open(csv_name) as f:
            df = pd.read_csv(f)

    print(f"[INFO] Loaded {len(df):,} raw CPI rows")

    # Keep only All-items and provinces
    provinces = [
        "British Columbia",
        "Alberta",
        "Manitoba",
        "Ontario",
        "Quebec",
    ]
    df = df[
        (df["Products and product groups"] == "All-items") & (df["GEO"].isin(provinces))
    ].copy()

    df["date"] = pd.to_datetime(df["REF_DATE"], errors="coerce")
    df = df.rename(columns={"GEO": "province", "VALUE": "cpi_index"})
    df = df[["date", "province", "cpi_index"]]
    df["cpi_index"] = pd.to_numeric(df["cpi_index"], errors="coerce")
    df = df.dropna(subset=["date", "cpi_index"])
    return df


# ---------------------------------------------------------------------
# 3. Transform → monthly 2005-01-01 … 2025-08-01 + CPI YoY + FFill
# ---------------------------------------------------------------------
def transform_cpi(df: pd.DataFrame) -> pd.DataFrame:
    all_months = pd.date_range("2004-01-01", "2025-08-01", freq="MS")
    frames = []

    for prov, g in df.groupby("province"):
        g = g.sort_values("date").set_index("date")

        # Reindex to full range and forward-fill missing CPI
        g = (
            g.reindex(all_months)
            .ffill()
            .reset_index()
            .rename(columns={"index": "date"})
        )
        g["province"] = prov

        # Compute YoY (%)
        g["cpi_yoy"] = g["cpi_index"].pct_change(12) * 100

        # Mark imputed rows (after last real value)
        last_real = df[df["province"] == prov]["date"].max()
        g["source"] = "StatCan_18-10-0004-01"
        g.loc[g["date"] > last_real, "source"] += "_FF"

        frames.append(g)

    df = pd.concat(frames, ignore_index=True)
    print(f"[INFO] Computed CPI YoY for {df['province'].nunique()} provinces")
    return df.dropna(subset=["cpi_yoy"])


# ---------------------------------------------------------------------
# 4. Broadcast provinces → cities
# ---------------------------------------------------------------------
def broadcast_to_cities(df: pd.DataFrame) -> pd.DataFrame:
    province_to_cities = {
        "British Columbia": ["Victoria", "Vancouver"],
        "Alberta": ["Calgary", "Edmonton"],
        "Manitoba": ["Winnipeg"],
        "Ontario": ["Ottawa", "Toronto"],
        "Quebec": ["Montreal"],
    }

    rows = []
    for _, row in df.iterrows():
        for city in province_to_cities.get(row["province"], []):
            rows.append(
                {
                    "date": row["date"],
                    "city": city,
                    "cpi_yoy": round(row["cpi_yoy"], 2),
                    "source": row["source"],
                }
            )

    df_cities = pd.DataFrame(rows)
    print(
        f"[INFO] Broadcasted to {df_cities['city'].nunique()} cities, {len(df_cities):,} rows total"
    )
    return df_cities


# ---------------------------------------------------------------------
# 5. Write to database
# ---------------------------------------------------------------------
def upsert_cpi(df: pd.DataFrame):
    upsert_sql = text("""
        INSERT INTO public.macro_economic_data (date, city, cpi_yoy, source, created_at)
        VALUES (:date, :city, :cpi_yoy, :source, NOW())
        ON CONFLICT (date, city)
        DO UPDATE SET
            cpi_yoy = EXCLUDED.cpi_yoy,
            source = EXCLUDED.source,
            created_at = NOW();
    """)

    with engine.begin() as conn:
        conn.execute(upsert_sql, df.to_dict(orient="records"))

    print(f"[OK] Upserted {len(df)} CPI YoY rows into macro_economic_data")


# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
if __name__ == "__main__":
    start = datetime.now()
    print("[DEBUG] CPI ETL started ...")
    df = load_cpi_zip()
    df = transform_cpi(df)
    df = broadcast_to_cities(df)
    upsert_cpi(df)
    print(f"[DONE] CPI ETL completed in {datetime.now() - start}")
