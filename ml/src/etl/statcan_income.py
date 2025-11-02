from dotenv import find_dotenv, load_dotenv
import os
import pandas as pd
from zipfile import ZipFile
from datetime import datetime
from sqlalchemy import create_engine, text

# --------------------------------------------------------------------
# Load environment variables
# --------------------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")

if not NEON_DATABASE_URL:
    raise RuntimeError("NEON_DATABASE_URL not found in .env")

engine = create_engine(NEON_DATABASE_URL, pool_pre_ping=True, future=True)
print("[DEBUG] Connected to Neon via .env")

# --------------------------------------------------------------------
# City mapping
# --------------------------------------------------------------------
CITY_MAP = {
    "Victoria, British Columbia": "Victoria",
    "Vancouver, British Columbia": "Vancouver",
    "Calgary, Alberta": "Calgary",
    "Edmonton, Alberta": "Edmonton",
    "Winnipeg, Manitoba": "Winnipeg",
    "Ottawa-Gatineau, Ontario/Quebec": "Ottawa",
    "Toronto, Ontario": "Toronto",
}


# --------------------------------------------------------------------
# Load and transform StatCan Income dataset
# --------------------------------------------------------------------
def load_statcan_income(zip_path="data/raw/income_11100239.zip") -> pd.DataFrame:
    print(f"[DEBUG] Loading {zip_path} ...")

    # --- 1. Extract data from ZIP ---
    with ZipFile(zip_path, "r") as z:
        files = z.namelist()
        excel_name = next((n for n in files if n.endswith((".xlsx", ".xls"))), None)
        csv_name = next((n for n in files if n.endswith(".csv")), None)

        if excel_name:
            with z.open(excel_name) as f:
                df = pd.read_excel(f)
        elif csv_name:
            with z.open(csv_name) as f:
                df = pd.read_csv(f)
        else:
            raise FileNotFoundError(
                f"No .xlsx or .csv found in {zip_path}. Found: {files}"
            )

    # --- 2. Normalize GEO ---
    df["GEO"] = (
        df["GEO"]
        .astype(str)
        .str.replace(r" \(map\)", "", regex=True)  # remove “(map)”
        .str.replace("–", "-", regex=False)  # replace en-dash with hyphen
        .str.strip()
    )

    # --- 3. Filter relevant rows ---
    df = df[
        (df["Age group"] == "15 years and over")
        & (df["Sex"] == "Both sexes")
        & (df["Income source"] == "Total income")
        & (df["Statistics"] == "Median income (excluding zeros)")
        & (df["REF_DATE"].between(2005, 2025))
        & (df["GEO"].isin(CITY_MAP.keys()))
    ]

    print("[DEBUG] Cities included:", df["GEO"].unique().tolist())

    if df.empty:
        raise RuntimeError(
            "[ERROR] No data found after filtering. Check GEO names or file format."
        )

    # --- 4. Normalize and rename ---
    df = df.rename(
        columns={"REF_DATE": "year", "GEO": "city", "VALUE": "median_income"}
    )
    df["median_income"] = pd.to_numeric(df["median_income"], errors="coerce").round(2)
    df = df.dropna(subset=["median_income"])
    df["city"] = df["city"].map(CITY_MAP)

    # --- Fill missing cities with median of other cities ---
    available_cities = df["city"].unique().tolist()
    missing_cities = [c for c in CITY_MAP.values() if c not in available_cities]

    if missing_cities:
        print(
            f"[WARN] Missing data for: {missing_cities}. Filling with median of available cities."
        )
        filler_rows = []
        for year, group in df.groupby("year"):
            mean_income = group["median_income"].mean()
            for city in missing_cities:
                filler_rows.append(
                    {"year": year, "city": city, "median_income": round(mean_income, 2)}
                )
        df = pd.concat([df, pd.DataFrame(filler_rows)], ignore_index=True)

    # --- 5. Expand from annual → monthly ---
    monthly = []
    for _, row in df.iterrows():
        for month in range(1, 13):
            monthly.append(
                {
                    "date": datetime(int(row["year"]), month, 1),
                    "city": row["city"],
                    "median_income": row["median_income"],
                }
            )

    df_monthly = pd.DataFrame(monthly)

    # --- 6. Broadcast last available year → 2025‑08‑01 ---
    cutoff = datetime(2025, 8, 1)
    last_rows = []
    for city, group in df_monthly.groupby("city"):
        last_val = group.sort_values("date")["median_income"].iloc[-1]
        last_date = group["date"].max()
        current = datetime(last_date.year + 1, 1, 1)
        while current <= cutoff:
            last_rows.append({"date": current, "city": city, "median_income": last_val})
            next_month = current.month + 1
            next_year = current.year + (next_month - 1) // 12
            next_month = (next_month - 1) % 12 + 1
            current = datetime(next_year, next_month, 1)

    if last_rows:
        df_monthly = pd.concat([df_monthly, pd.DataFrame(last_rows)], ignore_index=True)

    df_monthly = (
        df_monthly[
            (df_monthly["date"] >= datetime(2005, 1, 1))
            & (df_monthly["date"] <= datetime(2025, 8, 1))
        ]
        .sort_values(["city", "date"])
        .reset_index(drop=True)
    )

    df_monthly["created_at"] = pd.Timestamp.now()
    print(
        f"[INFO] Prepared {len(df_monthly)} monthly income rows (2005‑01‑01 → 2025‑08‑01)."
    )
    return df_monthly


# --------------------------------------------------------------------
# Upsert into PostgreSQL (Neon-safe)
# --------------------------------------------------------------------
def upsert_income(df: pd.DataFrame):
    if df.empty:
        print("[WARN] No rows to upsert.")
        return

    print("[DEBUG] Pre-warming Neon connection ...")
    with engine.begin() as conn:
        conn.execute(text("SELECT 1;"))
    print("[DEBUG] Connection pre-warmed for Neon.")

    print("[DEBUG] Writing income data into public.demographics ...")
    upsert_sql = text("""
        INSERT INTO public.demographics (date, city, median_income, created_at)
        VALUES (:date, :city, :median_income, :created_at)
        ON CONFLICT (date, city)
        DO UPDATE SET
            median_income = EXCLUDED.median_income,
            created_at = NOW();
    """)

    records = df.to_dict(orient="records")
    batch_size = 2000
    total = 0

    with engine.begin() as conn:
        for i in range(0, len(records), batch_size):
            chunk = records[i : i + batch_size]
            conn.execute(upsert_sql, chunk)
            total += len(chunk)
            print(f"[OK] {total}/{len(records)} rows inserted ...")

    print(f"[OK] Upserted {len(df)} income rows into demographics.")


# --------------------------------------------------------------------
# Entrypoint
# --------------------------------------------------------------------
if __name__ == "__main__":
    start = datetime.now()
    print("[DEBUG] StatCan Median Income ETL started ...")

    df = load_statcan_income()
    upsert_income(df)

    elapsed = datetime.now() - start
    print(f"[DONE] StatCan ETL completed in {elapsed}.")
