import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text

# --------------------------------------------------------------------
# Direct Neon DB URL (bypasses .env)
# --------------------------------------------------------------------
NEON_DATABASE_URL = "postgresql+psycopg2://neondb_owner:npg_nNJqVB2lAKc5@ep-green-queen-adrdjlhp-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# --------------------------------------------------------------------
# Load and preprocess rent data
# --------------------------------------------------------------------
def load_rent_csv(path="data/rent_index.csv"):
    df = pd.read_csv(path, low_memory=False)
    df.columns = [c.strip() for c in df.columns]

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
        .str.replace(",.*", "", regex=True)
        .str.strip()
        .str.title()
    )

    # Filter to major cities
    target_cities = [
        "Vancouver", "Toronto", "Montréal", "Calgary", "Edmonton",
        "Ottawa", "Winnipeg", "Victoria", "Kelowna"
    ]
    df = df[df["city"].isin(target_cities)]

    if df.empty:
        print("[WARN] No matching cities found — check GEO normalization.")
        return pd.DataFrame()

    print(f"[DEBUG] Filtered cities: {sorted(df['city'].unique().tolist())}")

    df["date"] = pd.to_datetime(df["year"].astype(str) + "-07-01")

    mapping = {
        "Bachelor units": "median_rent_apartment_0br",
        "One bedroom units": "median_rent_apartment_1br",
        "Two bedroom units": "median_rent_apartment_2br",
        "Three bedroom units": "median_rent_apartment_3br",
    }
    df = df[df["unit_type"].isin(mapping.keys())]
    df["unit_col"] = df["unit_type"].map(mapping)

    df = df.groupby(["city", "date", "unit_col"], as_index=False)["value"].mean()

    wide = df.pivot(index=["city", "date"], columns="unit_col", values="value").reset_index()
    wide.columns.name = None
    wide = wide.rename_axis(None, axis=1)

    for col in ["median_rent_apartment_1br", "median_rent_apartment_2br", "median_rent_apartment_3br"]:
        if col not in wide.columns:
            wide[col] = None

    wide["index_value"] = wide[
        ["median_rent_apartment_1br", "median_rent_apartment_2br", "median_rent_apartment_3br"]
    ].mean(axis=1, skipna=True)

    print(f"[INFO] Loaded rent data for {wide['city'].nunique()} cities, {len(wide)} rows total.")
    return wide


# --------------------------------------------------------------------
# Write directly to Neon
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
    print(f"[OK] Inserted or updated {len(df)} rows to Neon rent_index.")


# --------------------------------------------------------------------
# Entrypoint
# --------------------------------------------------------------------
if __name__ == "__main__":
    df = load_rent_csv()
    write_to_neon(df)
    print("[DONE] rent_index data successfully synced to Neon.")
