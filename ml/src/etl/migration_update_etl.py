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
# Province → City mapping
# --------------------------------------------------------------------
PROVINCE_TO_CITIES = {
    "British Columbia": ["Vancouver", "Victoria"],
    "Alberta": ["Calgary", "Edmonton"],
    "Manitoba": ["Winnipeg"],
    "Ontario": ["Toronto", "Ottawa"],
}


# --------------------------------------------------------------------
# Load, process, and extend migration data
# --------------------------------------------------------------------
def load_migration_csv(path="data/migration_17100040.csv") -> pd.DataFrame:
    print(f"[DEBUG] Reading {path} ...")
    df = pd.read_csv(path)

    # Detect geography column dynamically
    geo_col = next((c for c in df.columns if c.lower().startswith("geo")), None)
    if geo_col is None:
        raise RuntimeError(
            f"[ERROR] Could not find geography column in {df.columns.tolist()}"
        )

    # Clean and prepare
    df["year"] = df["REF_DATE"].astype(str).str[:4].astype(int)
    df[geo_col] = df[geo_col].str.strip()

    # Clean component column
    comp_col = next((c for c in df.columns if "Components" in c), None)
    if comp_col is None:
        raise RuntimeError(
            "[ERROR] Could not find 'Components of population growth' column."
        )

    # Target migration-related components
    target_components = [
        "Immigrants",
        "Emigrants",
        "Net interprovincial migration",
        "Net international migration",
        "Net migration",
    ]
    df = df[df[comp_col].isin(target_components)]

    # Aggregate signed migration values
    df["sign"] = 1
    df.loc[df[comp_col].str.contains("Emigrants", case=False, na=False), "sign"] = -1
    df["VALUE"] = df["VALUE"].astype(float) * df["sign"]

    # Group by province + year
    df_grouped = (
        df.groupby([geo_col, "year"], as_index=False)["VALUE"]
        .sum()
        .rename(columns={geo_col: "province", "VALUE": "net_migration"})
    )

    # Normalize province names
    df_grouped["province"] = (
        df_grouped["province"].str.replace(r" \(map\)", "", regex=True).str.strip()
    )
    print("[DEBUG] Province names found:", df_grouped["province"].unique().tolist())

    # Keep only relevant provinces
    df_grouped = df_grouped[df_grouped["province"].isin(PROVINCE_TO_CITIES.keys())]
    if df_grouped.empty:
        raise RuntimeError(
            "[ERROR] No matching provinces found after normalization. Check CSV format."
        )

    df_grouped["migration_rate"] = (
        df_grouped["net_migration"].astype(float) / 1000
    ).round(2)

    # Broadcast province → cities
    expanded_rows = []
    for _, row in df_grouped.iterrows():
        province, year, rate = row["province"], row["year"], row["migration_rate"]
        for city in PROVINCE_TO_CITIES[province]:
            expanded_rows.append({"city": city, "year": year, "migration_rate": rate})

    df_city = pd.DataFrame(expanded_rows)

    # Linear extrapolation to 2025
    target_year = 2025
    rows_extended = []
    for city, group in df_city.groupby("city"):
        group = group.sort_values("year")
        x, y = group["year"].values, group["migration_rate"].values
        if len(x) >= 3:
            slope, intercept = np.polyfit(x[-3:], y[-3:], 1)
            pred_2025 = intercept + slope * target_year
            print(f"[INFO] {city}: projected net migration {pred_2025:.2f} for 2025")
            group = pd.concat(
                [
                    group,
                    pd.DataFrame(
                        {
                            "city": [city],
                            "year": [target_year],
                            "migration_rate": [pred_2025],
                        }
                    ),
                ],
                ignore_index=True,
            )
        rows_extended.append(group)
    df_city = pd.concat(rows_extended, ignore_index=True)

    # Expand yearly → monthly
    monthly_rows = []
    for _, row in df_city.iterrows():
        for m in range(1, 13):
            monthly_rows.append(
                {
                    "date": datetime(int(row["year"]), m, 1),
                    "city": row["city"],
                    "migration_rate": float(row["migration_rate"]),
                }
            )
    df_monthly = pd.DataFrame(monthly_rows)

    # Limit to 2005‑01‑01 → 2025‑08‑01
    df_monthly = df_monthly[
        (df_monthly["date"] >= datetime(2005, 1, 1))
        & (df_monthly["date"] <= datetime(2025, 8, 1))
    ]
    df_monthly["created_at"] = pd.Timestamp.now()

    print(
        f"[INFO] Prepared {len(df_monthly)} monthly migration rows (2005‑01‑01 → 2025‑08‑01)."
    )
    return df_monthly


# --------------------------------------------------------------------
# Upsert migration data into demographics (Neon-safe)
# --------------------------------------------------------------------
def upsert_migration(df: pd.DataFrame):
    if df.empty:
        print("[WARN] No rows to upsert.")
        return

    print("[DEBUG] Pre-warming Neon connection ...")
    with engine.begin() as conn:
        conn.execute(text("SELECT 1;"))
    print("[DEBUG] Connection pre-warmed for Neon.")

    print("[DEBUG] Writing migration data into public.demographics ...")
    upsert_sql = text("""
        INSERT INTO public.demographics (date, city, migration_rate, created_at)
        VALUES (:date, :city, :migration_rate, :created_at)
        ON CONFLICT (date, city)
        DO UPDATE SET
            migration_rate = EXCLUDED.migration_rate,
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

    print(f"[OK] Upserted {len(df)} migration rows into demographics.")


# --------------------------------------------------------------------
# Entrypoint
# --------------------------------------------------------------------
if __name__ == "__main__":
    start = datetime.now()
    print("[DEBUG] Migration ETL started ...")

    df = load_migration_csv()
    upsert_migration(df)

    elapsed = datetime.now() - start
    print(f"[DONE] Migration ETL completed in {elapsed}.")
