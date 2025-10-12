"""
Build per-listing engineered features for micro-level ML models (LightGBM, etc.)
Source: public.listings_raw
Target: public.listings_features
"""

import os
import datetime as dt
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# ----------------------------------------------------------------------
# 1. Environment setup
# ----------------------------------------------------------------------
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise EnvironmentError("DATABASE_URL not found in .env file")

engine = create_engine(DATABASE_URL)


# ----------------------------------------------------------------------
# 2. Helpers
# ----------------------------------------------------------------------
def log(msg: str):
    print(f"[build_listings_features] {msg}")


def _one_hot_property_type(df: pd.DataFrame) -> pd.DataFrame:
    """Create one-hot encoded flags for property_type"""
    df["property_type"] = df["property_type"].astype(str).str.lower().fillna("unknown")

    for t in ["house", "condo", "apartment", "townhouse"]:
        df[f"property_type_{t}"] = (
            df["property_type"].str.contains(t, regex=False).astype(bool)
        )

    return df


# ----------------------------------------------------------------------
# 3. Main build function
# ----------------------------------------------------------------------
def build_listings_features():
    log("📥 Loading listings_raw ...")
    with engine.begin() as conn:
        df = pd.read_sql("SELECT * FROM public.listings_raw", conn)

    log(f"Loaded {len(df)} rows from listings_raw")

    if df.empty:
        log("⚠️ No data found in listings_raw. Exiting.")
        return

    # ------------------------------------------------------------------
    # Feature engineering
    # ------------------------------------------------------------------
    log("🧮 Engineering numeric features...")

    # Handle divisions safely
    df["price_per_sqft"] = df.apply(
        lambda r: r["price"] / r["area_sqft"]
        if r["area_sqft"] not in [0, None]
        else None,
        axis=1,
    )

    current_year = dt.date.today().year
    df["property_age"] = df["year_built"].apply(
        lambda y: current_year - y if pd.notnull(y) and y > 1800 else None
    )

    df = _one_hot_property_type(df)

    # Keep only columns required by listings_features schema
    expected_cols = [
        "listing_id",
        "price_per_sqft",
        "property_age",
        "bedrooms",
        "bathrooms",
        "area_sqft",
        "year_built",
        "postal_code",
        "property_type_house",
        "property_type_condo",
        "property_type_apartment",
        "property_type_townhouse",
    ]

    df = df.reindex(columns=expected_cols)
    df = df.fillna(0)

    log(f"✅ Prepared DataFrame: {df.shape[0]} rows × {df.shape[1]} cols")

    # ------------------------------------------------------------------
    # Write to DB
    # ------------------------------------------------------------------
    log("📝 Writing into public.listings_features ...")
    with engine.begin() as conn:
        # Truncate table before full rebuild
        conn.execute(text("TRUNCATE TABLE public.listings_features RESTART IDENTITY;"))
        df.to_sql(
            "listings_features",
            con=conn,
            schema="public",
            if_exists="append",
            index=False,
        )

    log(f"✅ Wrote {len(df)} rows into listings_features.")


# ----------------------------------------------------------------------
# 4. CLI entrypoint
# ----------------------------------------------------------------------
if __name__ == "__main__":
    build_listings_features()
