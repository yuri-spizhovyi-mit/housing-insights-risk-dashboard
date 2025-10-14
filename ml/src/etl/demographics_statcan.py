"""
etl/demographics_snapshot.py — Hybrid Demographics ETL (StatCan + WPR)
----------------------------------------------------------------------
Fetches demographic indicators (population, migration) for major
Canadian cities using WorldPopulationReview and StatCan fallback for Canada.
Outputs a tidy snapshot into public.demographics.
"""

import os
from datetime import datetime, timezone
import pandas as pd
import requests
from bs4 import BeautifulSoup

from . import base, statcan_wds

SNAPSHOT_DIR = "./.debug/demographics_snapshot"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

# --- Constants --------------------------------------------------------

TARGET_CITIES = [
    "Vancouver",
    "Kelowna",
    "Toronto",
    "Victoria",
    "Calgary",
    "Edmonton",
    "Montreal",
    "Ottawa",
    "Winnipeg",
    "Canada",
]

# Approximate migration rates by province (index around 1.0 baseline)
MIGRATION_INDEX = {
    "British Columbia": 1.00,
    "Alberta": 0.95,
    "Ontario": 1.05,
    "Quebec": 0.83,
    "Manitoba": 0.78,
}

CITY_PROVINCE_MAP = {
    "Vancouver": "British Columbia",
    "Kelowna": "British Columbia",
    "Victoria": "British Columbia",
    "Calgary": "Alberta",
    "Edmonton": "Alberta",
    "Toronto": "Ontario",
    "Ottawa": "Ontario",
    "Montreal": "Quebec",
    "Winnipeg": "Manitoba",
}

# --- Data Fetchers ----------------------------------------------------


def fetch_statcan_canada():
    """Fetch national-level population and migration from StatCan (17100005, 17100008)."""
    print("[DEBUG] Fetching StatCan national population and migration...")
    try:
        pop_df = statcan_wds.download_table_csv("17100005")
        mig_df = statcan_wds.download_table_csv("17100008")
    except Exception as e:
        print("[WARN] StatCan download failed:", e)
        return pd.DataFrame(
            [{"city": "Canada", "population": None, "migration_rate": None}]
        )

    # detect numeric column
    def valcol(df):
        for c in df.columns:
            if c.upper().startswith("VALUE") or "OBS_VALUE" in c.upper():
                return c
        return None

    pop_col = valcol(pop_df)
    pop_df = pop_df[pop_df["GEO"].str.lower().str.contains("canada", na=False)]
    pop_df["population"] = pd.to_numeric(pop_df[pop_col], errors="coerce")
    pop_df = pop_df.sort_values("REF_DATE").tail(1)

    mig_col = valcol(mig_df)
    mig_df = mig_df[mig_df["GEO"].str.lower().str.contains("canada", na=False)]
    mig_df = mig_df[
        mig_df["Components of population growth"]
        .astype(str)
        .str.contains("Net", case=False, na=False)
    ]
    mig_df["migration_rate"] = pd.to_numeric(mig_df[mig_col], errors="coerce")
    mig_df = mig_df.sort_values("REF_DATE").tail(1)

    merged = {
        "city": "Canada",
        "population": pop_df["population"].iloc[0] if not pop_df.empty else None,
        "migration_rate": 1.00,  # normalized baseline
    }
    return pd.DataFrame([merged])


def fetch_wpr_cities():
    """Scrape WorldPopulationReview.com for Canadian city populations."""
    print("[DEBUG] Fetching city populations from WorldPopulationReview...")
    url = "https://worldpopulationreview.com/cities/canada"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    table = soup.find("table")
    if not table:
        raise RuntimeError("Could not find city table on WPR page")

    rows = []
    for tr in table.find_all("tr")[1:]:
        cols = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cols) >= 2:
            city_name = cols[0].split(",")[0].strip()
            pop_str = cols[1].replace(",", "").strip()
            try:
                pop_val = int(float(pop_str))
            except ValueError:
                continue
            if city_name in TARGET_CITIES:
                rows.append({"city": city_name, "population": pop_val})
    df = pd.DataFrame(rows)
    print(f"[INFO] Retrieved {len(df)} city rows from WPR.")
    return df


# --- ETL Assembly -----------------------------------------------------


def build_snapshot():
    print("[DEBUG] Building hybrid demographics snapshot...")
    statcan_df = fetch_statcan_canada()
    wpr_df = fetch_wpr_cities()

    # Merge both
    tidy = pd.concat([wpr_df, statcan_df], ignore_index=True)
    tidy["date"] = pd.Timestamp(datetime.now().date())
    tidy["migration_rate"] = tidy["city"].apply(
        lambda c: MIGRATION_INDEX.get(CITY_PROVINCE_MAP.get(c, ""), 1.0)
        if c != "Canada"
        else 1.0
    )
    tidy["age_25_34_perc"] = None
    tidy["median_income"] = None
    tidy["created_at"] = datetime.now(timezone.utc)

    tidy = tidy.sort_values("city").reset_index(drop=True)
    tidy.to_csv(f"{SNAPSHOT_DIR}/demographics_tidy_snapshot.csv", index=False)

    print(f"[INFO] Cleaned demographics snapshot rows: {len(tidy)}")
    print("[DEBUG] Cities included:", ", ".join(tidy["city"].unique()))
    return tidy


def write_demographics_upsert(df: pd.DataFrame, ctx: base.Context):
    """Upsert snapshot into public.demographics safely."""
    if df.empty:
        print("[WARN] No demographics data to write.")
        return

    sql = """
        INSERT INTO public.demographics
            (city, date, population, migration_rate, age_25_34_perc, median_income, created_at)
        VALUES (:city, :date, :population, :migration_rate, :age_25_34_perc, :median_income, :created_at)
        ON CONFLICT (city, date)
        DO UPDATE SET
            population = EXCLUDED.population,
            migration_rate = EXCLUDED.migration_rate,
            age_25_34_perc = EXCLUDED.age_25_34_perc,
            median_income = EXCLUDED.median_income,
            created_at = EXCLUDED.created_at;
    """
    eng = base._resolve_engine(ctx)
    rows = df.to_dict(orient="records")
    with eng.begin() as conn:
        conn.execute(base.text(sql), rows)
    print(f"[INFO] ✅ Upserted {len(df)} rows into public.demographics.")


def run(ctx):
    print("[DEBUG] Starting hybrid demographics ETL (StatCan + WPR)...")
    df = build_snapshot()
    write_demographics_upsert(df, ctx)
    print("[INFO] ✅ Demographics snapshot successfully written to public.demographics")


if __name__ == "__main__":
    from datetime import date

    ctx = base.Context(run_date=date.today())
    run(ctx)
    print("[DEBUG] Demographics snapshot ETL finished.")
