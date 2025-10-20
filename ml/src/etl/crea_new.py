import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# --------------------------------------------------------------------
# Direct Neon DB URL
# --------------------------------------------------------------------
NEON_DATABASE_URL = "postgresql+psycopg2://neondb_owner:npg_nNJqVB2lAKc5@ep-green-queen-adrdjlhp-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
#NEON_DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5433/hird"
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
    "GREATER_TORONTO": "Toronto"
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

        # Clean and normalize columns
        df.columns = [c.strip().replace(" ", "_") for c in df.columns]
        if "Date" not in df.columns and "DATE" not in df.columns:
            print(f"[WARN] No 'Date' column in {sheet}, skipping.")
            continue

        date_col = "Date" if "Date" in df.columns else "DATE"

        # Melt into long format
        measures = [c for c in df.columns if c != date_col]
        long_df = df.melt(id_vars=[date_col], value_vars=measures,
                          var_name="measure", value_name="index_value")
        long_df["city"] = city

        # Clean data
        long_df = long_df.dropna(subset=["index_value"])
        long_df["date"] = pd.to_datetime(long_df[date_col], errors="coerce")
        long_df = long_df.dropna(subset=["date"])
        long_df["index_value"] = pd.to_numeric(long_df["index_value"], errors="coerce")
        long_df = long_df.dropna(subset=["index_value"])

        all_rows.append(long_df[["city", "date", "measure", "index_value"]])

        print(f"[INFO] Processed {city}: {len(long_df)} rows.")

    if not all_rows:
        print("[WARN] No data collected from any sheets.")
        return pd.DataFrame()

    result = pd.concat(all_rows, ignore_index=True)
    result["source"] = "CREA_XLSX"
    print(f"[INFO] Combined total rows: {len(result)}")
    return result


# --------------------------------------------------------------------
# Write to Neon database
# --------------------------------------------------------------------
def write_to_neon(df: pd.DataFrame):
    if df.empty:
        print("[WARN] Nothing to write to Neon.")
        return

    engine = create_engine(NEON_DATABASE_URL, pool_pre_ping=True, future=True)
    with engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(
                text("""
                INSERT INTO public.house_price_index
                (date, city, measure, index_value)
                VALUES (:date, :city, :measure, :index_value)
                ON CONFLICT (date, city, measure) DO UPDATE
                SET index_value = EXCLUDED.index_value;
                """),
                {
                    "date": row["date"],
                    "city": row["city"],
                    "measure": row["measure"],
                    "index_value": float(row["index_value"]),
                },
            )
    print(f"[OK] Inserted or updated {len(df)} rows in Neon house_price_index.")


# --------------------------------------------------------------------
# Entrypoint
# --------------------------------------------------------------------
if __name__ == "__main__":
    print("[DEBUG] CREA Excel loader starting...")
    df = load_crea_xlsx()
    write_to_neon(df)
    print("[DONE] CREA Excel data successfully loaded into Neon.")
