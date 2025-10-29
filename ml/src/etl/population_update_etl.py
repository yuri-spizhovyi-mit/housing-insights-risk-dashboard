from dotenv import find_dotenv, load_dotenv
import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from datetime import datetime

# --------------------------------------------------------------------
# Load environment variables
# --------------------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
NEON_DATABASE_URL = os.getenv("DATABASE_URL")

if not NEON_DATABASE_URL:
    raise RuntimeError("NEON_DATABASE_URL not found in .env")

engine = create_engine(NEON_DATABASE_URL, pool_pre_ping=True, future=True)
print("[DEBUG] Connected to Neon via .env")

# --------------------------------------------------------------------
# City mapping
# --------------------------------------------------------------------
CITY_MAP = {
    "Victoria (CMA), British Columbia (map)": "Victoria",
    "Vancouver (CMA), British Columbia (map)": "Vancouver",
    "Calgary (CMA), Alberta (map)": "Calgary",
    "Edmonton (CMA), Alberta (map)": "Edmonton",
    "Winnipeg (CMA), Manitoba (map)": "Winnipeg",
    "Ottawa - Gatineau (CMA), Ontario/Quebec (map)": "Ottawa",
    "Toronto (CMA), Ontario (map)": "Toronto",
}


# --------------------------------------------------------------------
# Load, reshape, and extend population data
# --------------------------------------------------------------------
def load_population_csv(path="data/population.csv") -> pd.DataFrame:
    print(f"[DEBUG] Reading {path} ...")
    df = pd.read_csv(path, header=0)
    df.columns = df.columns.str.strip()
    df.rename(columns={df.columns[0]: "Geography"}, inplace=True)

    # Detect year columns dynamically
    year_cols = [c for c in df.columns if str(c).isdigit()]
    if not year_cols:
        raise ValueError("No numeric year columns found in CSV.")

    df = df[df["Geography"].isin(CITY_MAP.keys())].copy()
    df["city"] = df["Geography"].map(CITY_MAP)

    # Melt wide → long
    df_long = df.melt(
        id_vars=["city"], value_vars=year_cols, var_name="year", value_name="population"
    )
    df_long["year"] = pd.to_numeric(df_long["year"], errors="coerce").astype(int)
    df_long["population"] = (
        df_long["population"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .astype(float)
        .round(0)
    )

    # ----------------------------------------------------------------
    # Linear regression extrapolation to 2025
    # ----------------------------------------------------------------
    rows_extended = []
    target_year = 2025

    for city, group in df_long.groupby("city"):
        group = group.sort_values("year")
        x = group["year"].values
        y = group["population"].values

        if len(x) >= 3:
            coeffs = np.polyfit(x[-3:], y[-3:], 1)
            slope, intercept = coeffs
            predicted_2025 = intercept + slope * target_year
            print(f"[INFO] {city}: Linear projection → {predicted_2025:,.0f} for 2025")
            group = pd.concat(
                [
                    group,
                    pd.DataFrame(
                        {
                            "city": [city],
                            "year": [target_year],
                            "population": [predicted_2025],
                        }
                    ),
                ],
                ignore_index=True,
            )
        else:
            print(
                f"[WARN] {city}: Not enough years to project, skipping extrapolation."
            )

        rows_extended.append(group)

    df_long = pd.concat(rows_extended, ignore_index=True)

    # Expand to monthly
    monthly = []
    for _, row in df_long.iterrows():
        for m in range(1, 13):
            monthly.append(
                {
                    "date": datetime(int(row["year"]), m, 1),
                    "city": row["city"],
                    "population": int(round(row["population"])),
                }
            )

    df_monthly = pd.DataFrame(monthly)
    df_monthly["created_at"] = pd.Timestamp.now()

    # Limit to full range 2005‑01‑01 → 2025‑08‑01
    df_monthly = df_monthly[
        (df_monthly["date"] >= datetime(2005, 1, 1))
        & (df_monthly["date"] <= datetime(2025, 8, 1))
    ]

    print(
        f"[INFO] Prepared {len(df_monthly)} monthly population rows (2005‑01‑01 → 2025‑08‑01)."
    )
    return df_monthly


# --------------------------------------------------------------------
# Upsert population into demographics (Neon-safe)
# --------------------------------------------------------------------
def upsert_population(df: pd.DataFrame):
    if df.empty:
        print("[WARN] No rows to upsert.")
        return

    print("[DEBUG] Pre-warming Neon connection ...")
    with engine.begin() as conn:
        conn.execute(text("SELECT 1;"))
    print("[DEBUG] Connection pre-warmed for Neon.")

    print("[DEBUG] Writing population data into public.demographics ...")
    upsert_sql = text("""
        INSERT INTO public.demographics (date, city, population, created_at)
        VALUES (:date, :city, :population, :created_at)
        ON CONFLICT (date, city)
        DO UPDATE SET
            population = EXCLUDED.population,
            created_at = NOW();
    """)

    # Chunked upserts to avoid Neon timeouts
    records = df.to_dict(orient="records")
    batch_size = 2000

    total = 0
    with engine.begin() as conn:
        for i in range(0, len(records), batch_size):
            chunk = records[i : i + batch_size]
            conn.execute(upsert_sql, chunk)
            total += len(chunk)
            print(f"[OK] {total}/{len(records)} rows inserted ...")

    print(f"[OK] Upserted {len(df)} population rows into demographics.")


# --------------------------------------------------------------------
# Entrypoint
# --------------------------------------------------------------------
if __name__ == "__main__":
    start = datetime.now()
    print("[DEBUG] Population ETL started ...")

    df = load_population_csv()
    upsert_population(df)

    elapsed = datetime.now() - start
    print(f"[DONE] Population ETL completed in {elapsed}.")
