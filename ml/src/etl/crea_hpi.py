from dotenv import find_dotenv, load_dotenv
import os
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

# --------------------------------------------------------------------
# Load environment variables
# --------------------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")

if not NEON_DATABASE_URL:
    raise RuntimeError("DATABASE_URL not found in .env")

engine = create_engine(NEON_DATABASE_URL, pool_pre_ping=True, future=True)
print("[DEBUG] Connected to Neon via .env")

# --------------------------------------------------------------------
# City sheet mapping (sheet name → city name)
# --------------------------------------------------------------------
CITY_SHEETS = {
    "VICTORIA": "Victoria",
    "GREATER_VANCOUVER": "Vancouver",
    "CALGARY": "Calgary",
    "EDMONTON": "Edmonton",
    "WINNIPEG": "Winnipeg",
    "OTTAWA": "Ottawa",
    "GREATER_TORONTO": "Toronto",
}

# --------------------------------------------------------------------
# Property type mapping (CREA column → canonical property_type)
# --------------------------------------------------------------------
PROP_MAP = {
    "Single_Family_Benchmark": "House",
    "Townhouse_Benchmark": "Town House",
    "Apartment_Benchmark": "Apartment",
    "Composite_Benchmark": "All",
}

BENCHMARK_COLS = list(PROP_MAP.keys())


# --------------------------------------------------------------------
# Load, transform, and validate CREA workbook
# --------------------------------------------------------------------
def load_crea_xlsx(path="data/house_price_index.xlsx"):
    all_rows = []

    for sheet, city in CITY_SHEETS.items():
        try:
            df = pd.read_excel(path, sheet_name=sheet)
        except Exception as e:
            print(f"[WARN] Cannot read sheet {sheet}: {e}")
            continue

        df.columns = [c.strip().replace(" ", "_") for c in df.columns]
        if "Date" not in df.columns:
            print(f"[WARN] Missing Date column in {sheet}, skipping.")
            continue

        # Parse date to canonical YYYY-MM-01
        df["date"] = pd.to_datetime(df["Date"], format="%b %Y", errors="coerce")
        df = df.dropna(subset=["date"])

        # Melt benchmark columns to long format
        measures = [c for c in df.columns if c in BENCHMARK_COLS]
        long_df = df.melt(
            id_vars=["date"],
            value_vars=measures,
            var_name="orig_col",
            value_name="benchmark_price",
        )

        # Map property type and clean data
        long_df["property_type"] = long_df["orig_col"].map(PROP_MAP)
        long_df["city"] = city
        long_df["benchmark_price"] = pd.to_numeric(
            long_df["benchmark_price"], errors="coerce"
        ).round(0)
        long_df = long_df.dropna(subset=["benchmark_price"])
        long_df = long_df.query("benchmark_price > 0 and benchmark_price < 2_000_000")

        # Add metadata
        long_df["source"] = "CREA_HPI_v2025"
        long_df["created_at"] = pd.Timestamp.now()

        # Select final columns
        all_rows.append(
            long_df[
                [
                    "date",
                    "city",
                    "property_type",
                    "benchmark_price",
                    "source",
                    "created_at",
                ]
            ]
        )
        print(f"[INFO] {city}: {len(long_df)} rows processed.")

    if not all_rows:
        raise RuntimeError("No valid data found in Excel workbook.")

    df = pd.concat(all_rows, ignore_index=True)
    validate_hpi(df)
    print(f"[INFO] Combined total rows: {len(df)}")
    return df


# --------------------------------------------------------------------
# Validation checks according to Data_ETL spec (1.6)
# --------------------------------------------------------------------
def validate_hpi(df: pd.DataFrame):
    if df.duplicated(subset=["date", "city", "property_type"]).any():
        raise ValueError("Duplicate (date, city, property_type) rows found.")

    if (df["benchmark_price"] <= 0).any():
        raise ValueError("Found non-positive benchmark_price values.")

    if (df["benchmark_price"] >= 2_000_000).any():
        raise ValueError("Found unrealistic benchmark_price values (>2M).")

    print("[OK] Validation checks passed.")


# --------------------------------------------------------------------
# Write to database
# --------------------------------------------------------------------
def write_bulk(df: pd.DataFrame, table_name: str = "house_price_index"):
    if df.empty:
        print("[WARN] Nothing to write to database.")
        return

    print("[DEBUG] Writing to database...")
    df.to_sql(
        table_name,
        con=engine,
        schema="public",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=2000,
    )
    print(f"[OK] Bulk inserted {len(df)} rows into {table_name}.")


# --------------------------------------------------------------------
# Entrypoint
# --------------------------------------------------------------------
if __name__ == "__main__":
    start = datetime.now()
    print("[DEBUG] CREA HPI ETL started...")

    df = load_crea_xlsx()
    write_bulk(df)

    elapsed = datetime.now() - start
    print(f"[DONE] CREA HPI ETL completed in {elapsed}.")
