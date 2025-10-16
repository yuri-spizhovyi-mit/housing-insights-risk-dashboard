import pandas as pd
from datetime import datetime
from sqlalchemy import text
from ml.src.etl.db import get_engine


# --------------------------------------------------------------------
# 1. Helper functions
# --------------------------------------------------------------------
def safe_int(val):
    """Convert to int or return None if NaN/invalid."""
    if pd.isna(val):
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def safe_float(val):
    """Convert to float or return None if NaN/invalid."""
    if pd.isna(val):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


# --------------------------------------------------------------------
# 2. Load raw listings
# --------------------------------------------------------------------
def fetch_rent_data(ctx):
    """Fetch rental listings for all cities from listings_raw."""
    engine = get_engine()
    query = """
        SELECT date_posted, city, price, bedrooms
        FROM public.listings_raw
        WHERE listing_type ILIKE 'rent%'   -- handles 'Rental' or 'Rent'
          AND price IS NOT NULL
          AND price > 100
    """

    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

    if df.empty:
        print("[WARN] No rental listings found.")
        return df

    # Normalize city names (remove province, unify case)
    df["city"] = (
        df["city"]
        .astype(str)
        .str.replace(",.*", "", regex=True)
        .str.strip()
        .str.title()
    )
    return df


# --------------------------------------------------------------------
# 3. Aggregate monthly medians per city
# --------------------------------------------------------------------
def transform_rent_index(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate monthly rent metrics for all cities."""
    if df.empty:
        return df

    df["month"] = pd.to_datetime(df["date_posted"]).dt.to_period("M").dt.to_timestamp()

    def agg_func(g):
        return pd.Series(
            {
                "median_rent_apartment_1br": g.loc[
                    g["bedrooms"] == 1, "price"
                ].median(),
                "median_rent_apartment_2br": g.loc[
                    g["bedrooms"] == 2, "price"
                ].median(),
                "median_rent_apartment_3br": g.loc[
                    g["bedrooms"] == 3, "price"
                ].median(),
                "active_rental_count": len(g),
                "avg_rental_days": None,  # placeholder for scraped data
                "index_value": g["price"].median(),
            }
        )

    # Silence Pandas FutureWarning by excluding group columns explicitly
    agg = (
        df.groupby(["city", "month"], group_keys=False)
        .apply(agg_func, include_groups=False)  # ✅ removes warning
        .reset_index()
    )

    agg.rename(columns={"month": "date"}, inplace=True)
    print(f"[INFO] Aggregated {len(agg)} monthly city rent records.")
    return agg


# --------------------------------------------------------------------
# 4. Write to public.rent_index
# --------------------------------------------------------------------
def write_rent_index(df: pd.DataFrame, ctx):
    """Upsert aggregated rent data into public.rent_index."""
    if df.empty:
        print("[WARN] Nothing to write to rent_index.")
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
                VALUES (:date, :city, :index_value, :r1, :r2, :r3, :count, :days)
                ON CONFLICT (date, city) DO UPDATE
                SET index_value = EXCLUDED.index_value,
                    median_rent_apartment_1br = EXCLUDED.median_rent_apartment_1br,
                    median_rent_apartment_2br = EXCLUDED.median_rent_apartment_2br,
                    median_rent_apartment_3br = EXCLUDED.median_rent_apartment_3br,
                    active_rental_count = EXCLUDED.active_rental_count,
                    avg_rental_days = EXCLUDED.avg_rental_days;
                """),
                {
                    "date": row["date"],
                    "city": row["city"],
                    "index_value": safe_float(row["index_value"]),
                    "r1": safe_float(row["median_rent_apartment_1br"]),
                    "r2": safe_float(row["median_rent_apartment_2br"]),
                    "r3": safe_float(row["median_rent_apartment_3br"]),
                    "count": safe_int(row["active_rental_count"]),
                    "days": safe_int(row["avg_rental_days"]),
                },
            )
    print(f"[OK] Inserted/updated {len(df)} rows → rent_index.")


# --------------------------------------------------------------------
# 5. Entrypoint
# --------------------------------------------------------------------
def run(ctx):
    df = fetch_rent_data(ctx)
    agg = transform_rent_index(df)
    write_rent_index(agg, ctx)
    print("[DONE] rent_index ETL complete.")


# --------------------------------------------------------------------
# 6. CLI Entrypoint
# --------------------------------------------------------------------
if __name__ == "__main__":
    from datetime import date
    from ml.src.etl import base

    ctx = base.Context(run_date=date.today())
    run(ctx)
