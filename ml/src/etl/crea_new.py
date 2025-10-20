from dotenv import find_dotenv, load_dotenv
import os
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

# Load environment
load_dotenv(find_dotenv(usecwd=True))
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")

if not NEON_DATABASE_URL:
    raise RuntimeError("❌ NEON_DATABASE_URL not found in .env")

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
# Load and transform CREA Excel workbook
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
        date_col = "Date" if "Date" in df.columns else "DATE"
        if date_col not in df.columns:
            print(f"[WARN] Missing Date column in {sheet}, skipping.")
            continue

        # Melt into long format
        measures = [c for c in df.columns if c != date_col]
        long_df = df.melt(
            id_vars=[date_col],
            value_vars=measures,
            var_name="measure",
            value_name="index_value",
        )
        long_df["city"] = city
        long_df["date"] = pd.to_datetime(long_df[date_col], errors="coerce")
        long_df["index_value"] = pd.to_numeric(long_df["index_value"], errors="coerce")
        long_df = long_df.dropna(subset=["date", "index_value"])

        all_rows.append(long_df[["city", "date", "measure", "index_value"]])
        print(f"[INFO] {city}: {len(long_df)} rows.")

    if not all_rows:
        raise RuntimeError("No valid data found in Excel workbook.")

    df = pd.concat(all_rows, ignore_index=True)
    print(f"[INFO] Combined total rows: {len(df)}")
    return df


# --------------------------------------------------------------------
# Bulk write to Neon (fast, safe)
# --------------------------------------------------------------------
def write_bulk(df: pd.DataFrame, table_name: str = "house_price_index"):
    if df.empty:
        print("[WARN] Nothing to write to database.")
        return

    engine = create_engine(NEON_DATABASE_URL, pool_pre_ping=True, future=True)
    print("[DEBUG] Connected to Neon successfully.")

    # Write in chunks of 2000 rows
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
    print("[DEBUG] CREA bulk Neon loader starting...")

    df = load_crea_xlsx()
    write_bulk(df)

    elapsed = datetime.now() - start
    print(f"[DONE] Bulk load completed in {elapsed}.")
