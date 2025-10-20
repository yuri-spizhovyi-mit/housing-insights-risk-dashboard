import pandas as pd
from datetime import datetime
from sqlalchemy import text
from ml.src.etl.db import get_engine


# --------------------------------------------------------------------
# Rent Index ETL from StatCan / CMHC CSV (Final Stable Version)
# --------------------------------------------------------------------
def load_rent_csv(path="data/rent_index.csv"):
    """Load and preprocess CMHC/StatCan rent data from CSV."""
    df = pd.read_csv(path, low_memory=False)
    df.columns = [c.strip() for c in df.columns]

    # Expected columns: REF_DATE, GEO, Type of structure, Type of unit, VALUE
    df = df.rename(
        columns={
            "REF_DATE": "year",
            "GEO": "city",
            "Type of unit": "unit_type",
            "VALUE": "value",
        }
    )

    # Normalize GEO field -> remove province names, "CMA of", etc.
    df["city"] = (
        df["city"]
        .astype(str)
        .str.replace("CMA of ", "", regex=False)
        .str.replace(",.*", "", regex=True)   # remove everything after comma (province)
        .str.strip()
        .str.title()
    )

    # Filter to target cities
    target_cities = [
        "Vancouver", "Toronto", "Montréal", "Calgary", "Edmonton",
        "Ottawa", "Winnipeg", "Victoria", "Kelowna"
    ]
    df = df[df["city"].isin(target_cities)]

    if df.empty:
        print("[WARN] No matching cities found in rent_index.csv — please verify GEO names.")
        return pd.DataFrame()

    print(f"[DEBUG] Filtered cities: {sorted(df['city'].unique().tolist())}")

    # Convert year to datetime (use July 1st of that year)
    df["date"] = pd.to_datetime(df["year"].astype(str) + "-07-01")

    # Map unit types to our target columns
    mapping = {
        "Bachelor units": "median_rent_apartment_0br",
        "One bedroom units": "median_rent_apartment_1br",
        "Two bedroom units": "median_rent_apartment_2br",
        "Three bedroom units": "median_rent_apartment_3br",
    }
    df = df[df["unit_type"].isin(mapping.keys())]
    df["unit_col"] = df["unit_type"].map(mapping)

    # Aggregate duplicates by (city, date, unit_col)
    df = df.groupby(["city", "date", "unit_col"], as_index=False)["value"].mean()

    # Pivot to wide format
    wide = df.pivot(index=["city", "date"], columns="unit_col", values="value").reset_index()

    # Flatten multi-index columns
    wide.columns.name = None
    wide = wide.rename_axis(None, axis=1)

    # Ensure all needed columns exist
    for col in ["median_rent_apartment_1br", "median_rent_apartment_2br", "median_rent_apartment_3br"]:
        if col not in wide.columns:
            wide[col] = None

    # Compute index_value as mean across available bedrooms
    wide["index_value"] = wide[
        ["median_rent_apartment_1br",
         "median_rent_apartment_2br",
         "median_rent_apartment_3br"]
    ].mean(axis=1, skipna=True)

    print(f"[INFO] Loaded rent data for {wide['city'].nunique()} cities, {len(wide)} rows total.")
    return wide


# --------------------------------------------------------------------
# Write to Postgres
# --------------------------------------------------------------------
def write_rent_index(df: pd.DataFrame):
    """Upsert rent index data into public.rent_index."""
    if df.empty:
        print("[WARN] No rent index data to write.")
        return

    engine = get_engine()
    with engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(
                text("""
                INSERT INTO public.rent_index 
                (date, city, index_value,
                 median_rent_apartment_1br, median_rent_apartment_2br, median_rent_apartment_3br,
                 active_rental_count, avg_rental_days)
                VALUES (:date, :city, :index_value, :r1, :r2, :r3, NULL, NULL)
                ON CONFLICT (date, city) DO UPDATE
                SET index_value = EXCLUDED.index_value,
                    median_rent_apartment_1br = EXCLUDED.median_rent_apartment_1br,
                    median_rent_apartment_2br = EXCLUDED.median_rent_apartment_2br,
                    median_rent_apartment_3br = EXCLUDED.median_rent_apartment_3br;
                """),
                {
                    "date": row["date"],
                    "city": row["city"],
                    "index_value": float(row["index_value"]) if pd.notna(row["index_value"]) else None,
                    "r1": float(row.get("median_rent_apartment_1br", None)) if pd.notna(row.get("median_rent_apartment_1br", None)) else None,
                    "r2": float(row.get("median_rent_apartment_2br", None)) if pd.notna(row.get("median_rent_apartment_2br", None)) else None,
                    "r3": float(row.get("median_rent_apartment_3br", None)) if pd.notna(row.get("median_rent_apartment_3br", None)) else None,
                },
            )
    print(f"[OK] Inserted or updated {len(df)} rent_index rows.")


# --------------------------------------------------------------------
# Entrypoint
# --------------------------------------------------------------------
def run():
    df = load_rent_csv()
    write_rent_index(df)
    print("[DONE] rent_index ETL from CSV complete.")


if __name__ == "__main__":
    run()
