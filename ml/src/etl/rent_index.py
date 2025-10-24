# ml/src/etl/rent_index.py
"""
ETL: Rent Index — simplified macro version (city-level average rents)
----------------------------------------------------------
Purpose:
Load CMHC annual rent data, compute city-level mean rent per year, expand
to monthly rows (2005-01–2025-08), and insert into public.rent_index.

Table schema
-------------
public.rent_index (
    date DATE NOT NULL,           -- YYYY-MM-01
    city TEXT NOT NULL,           -- City name
    rent_value NUMERIC(10,2),     -- Average monthly rent (CAD)
    data_flag TEXT,               -- ORIG_ANNUAL | DERIVED_ANNUAL | LOCF_FROM_2024
    source TEXT DEFAULT 'CMHC_Rental_Market_Survey',
    last_seen TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (date, city)
)
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv, find_dotenv

TARGET_CITIES = [
    "Victoria",
    "Vancouver",
    "Calgary",
    "Edmonton",
    "Winnipeg",
    "Ottawa",
    "Toronto",
]

# -----------------------------------------------------------------------------
# DB Connection
# -----------------------------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")
if not NEON_DATABASE_URL:
    raise RuntimeError("❌ NEON_DATABASE_URL not found in .env")
engine = create_engine(NEON_DATABASE_URL, pool_pre_ping=True, future=True)
print("[DEBUG] Connected to Neon database.")


# -----------------------------------------------------------------------------
# Recreate Table
# -----------------------------------------------------------------------------
def recreate_rent_index_table(engine):
    ddl = """
    DROP TABLE IF EXISTS public.rent_index CASCADE;
    CREATE TABLE public.rent_index (
        date DATE NOT NULL,
        city TEXT NOT NULL,
        rent_value NUMERIC(10,2),
        data_flag TEXT,
        source TEXT DEFAULT 'CMHC_Rental_Market_Survey',
        last_seen TIMESTAMPTZ DEFAULT now(),
        PRIMARY KEY (date, city)
    );
    COMMENT ON TABLE public.rent_index IS
        'City-level monthly apartment rent averages derived from CMHC annual survey data.';
    """
    with engine.begin() as conn:
        for stmt in ddl.strip().split(";"):
            s = stmt.strip()
            if s:
                conn.execute(text(s))
    print("[DEBUG] Recreated table public.rent_index")


# -----------------------------------------------------------------------------
# Load + Transform Annual CSV
# -----------------------------------------------------------------------------
def load_annual_csv(path="data/rent_index.csv") -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    df.columns = [c.strip() for c in df.columns]

    # Identify expected columns
    ref = next(
        (c for c in df.columns if "REF" in c.upper() or "YEAR" in c.upper()), None
    )
    geo = next(
        (c for c in df.columns if c.upper() in ["GEO", "GEOGRAPHY", "CITY"]), None
    )
    unit = next((c for c in df.columns if "UNIT" in c.upper()), None)
    val = next((c for c in df.columns if "VALUE" in c.upper()), None)

    if not all([ref, geo, unit, val]):
        raise ValueError("Missing required columns REF_DATE/GEO/Type of unit/VALUE")

    df = df[[ref, geo, unit, val]].rename(
        columns={ref: "year", geo: "city", unit: "unit_type", val: "rent_value"}
    )

    # Clean city
    df["city"] = (
        df["city"]
        .astype(str)
        .str.replace("CMA of ", "", regex=False)
        .str.replace(",.*", "", regex=True)
        .str.strip()
        .str.title()
    )
    df = df[df["city"].isin(TARGET_CITIES)]

    # Year to date
    df["year"] = df["year"].astype(str).str.extract(r"(\d{4})")[0]
    df["date"] = pd.to_datetime(df["year"] + "-01-01", errors="coerce")

    # Numeric values
    df["rent_value"] = pd.to_numeric(df["rent_value"], errors="coerce")
    df = df.dropna(subset=["rent_value", "date"])
    df = df[(df["rent_value"] > 0) & (df["rent_value"] < 10000)]

    # Average across unit types → one value per city/year
    agg = df.groupby(["city", "date"], as_index=False)["rent_value"].mean()
    agg["data_flag"] = "ORIG_ANNUAL"
    agg["source"] = "CMHC_Rental_Market_Survey_" + agg["date"].dt.year.astype(str)
    agg["last_seen"] = pd.Timestamp.now()

    print(
        f"[INFO] Annual city-level rows: {len(agg)} | Cities: {agg['city'].nunique()}"
    )
    return agg


# -----------------------------------------------------------------------------
# Expand Annual → Monthly
# -----------------------------------------------------------------------------
def expand_to_monthly(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    months = pd.date_range("2005-01-01", "2025-08-01", freq="MS")
    out_frames = []

    for city, sub in df.groupby("city"):
        sub = sub.sort_values("date")
        year_map = {d.year: v for d, v in zip(sub["date"], sub["rent_value"])}

        mf = pd.DataFrame({"date": months})
        mf["city"] = city
        mf["rent_value"] = mf["date"].dt.year.map(year_map)
        mf["rent_value"] = mf["rent_value"].ffill()

        # Flags
        mf["data_flag"] = "DERIVED_ANNUAL"
        mf["source"] = "CMHC_Rental_Market_Survey"
        mf["last_seen"] = pd.Timestamp.now()

        # LOCF for 2025
        mask_2025 = (mf["date"] >= "2025-01-01") & (mf["date"] <= "2025-08-01")
        mf.loc[mask_2025, "data_flag"] = "LOCF_FROM_2024"

        out_frames.append(mf)

    monthly = pd.concat(out_frames, ignore_index=True)
    monthly = monthly[
        (monthly["date"] >= "2005-01-01") & (monthly["date"] <= "2025-08-01")
    ]
    print(f"[INFO] Expanded monthly rows: {len(monthly)}")
    return monthly


# -----------------------------------------------------------------------------
# Write to DB
# -----------------------------------------------------------------------------
def write_rent_index(df: pd.DataFrame, engine):
    if df.empty:
        print("[WARN] No rent data to write.")
        return

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["rent_value"] = pd.to_numeric(df["rent_value"], errors="coerce")

    chunk = 200
    total = len(df)
    print(f"[DEBUG] Writing {total} rows to public.rent_index in chunks of {chunk}...")
    start = 0
    with engine.begin() as conn:
        while start < total:
            batch = df.iloc[start : start + chunk]
            batch.to_sql(
                "rent_index",
                con=conn,
                schema="public",
                if_exists="append",
                index=False,
                method="multi",
                chunksize=None,
            )
            print(f"  ↳ Inserted rows {start}..{start + len(batch) - 1}")
            start += len(batch)

    print(f"[OK] Inserted all {total} rows into public.rent_index.")


# -----------------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    recreate_rent_index_table(engine)
    annual = load_annual_csv("data/rent_index.csv")
    monthly = expand_to_monthly(annual)
    write_rent_index(monthly, engine)
    print("[DONE] rent_index ETL completed.")
