
"""
features_build_etl_v10_full_patched.py
----------------------------------------
Final stable ETL:
- v10 logic preserved
- Correct demographics broadcasting (city-year → monthly)
- No row inflation
- mortgage_rate, unemployment_rate, overnight_rate preserved
- National fallback enabled
"""

from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime, timezone
import pandas as pd
import numpy as np
import os

load_dotenv(find_dotenv(usecwd=True))
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")
if not NEON_DATABASE_URL:
    raise RuntimeError("DATABASE_URL not found in .env")

engine = create_engine(NEON_DATABASE_URL, pool_pre_ping=True, future=True)
print("[DEBUG] Connected to Neon")

def load_table(name: str, columns: str):
    query = f"SELECT {columns} FROM public.{name} ORDER BY date, city;"
    df = pd.read_sql_query(query, engine)
    df['date'] = pd.to_datetime(df['date'])
    print(f"[STEP] Loaded {len(df):,} rows from {name}")
    return df

def fill_missing(df, cols, group_cols):
    df = df.sort_values(group_cols + ['date'])
    for c in cols:
        df[c] = df.groupby(group_cols)[c].ffill().bfill()
    return df

def pct_change_yoy(series):
    return series.pct_change(periods=12) * 100

def build_features():
    print("[STEP] Loading source tables...")
    hpi = load_table("house_price_index", "date, city, property_type, benchmark_price AS hpi_benchmark")
    rent = load_table("rent_index", "date, city, rent_value AS rent_avg_city")
    metrics = load_table("metrics", "date, city, metric, value")
    macro = load_table("macro_economic_data", "date, city, gdp_growth, cpi_yoy")
    demo = load_table("demographics", "date, city, population, migration_rate, median_income")

    # ---------------------------------------------------------
    # FIX: Correct broadcasting of demographics
    # ---------------------------------------------------------
    if not demo.empty:
        demo["year"] = demo["date"].dt.year

        demo_yearly = (
            demo.sort_values(["city", "date"])
                .groupby(["city", "year"])
                .first()
                .reset_index()
        )

        expanded = []
        for _, row in demo_yearly.iterrows():
            for month in range(1, 13):
                expanded.append({
                    "date": pd.Timestamp(row["year"], month, 1),
                    "city": row["city"],
                    "population": row["population"],
                    "migration_rate": row["migration_rate"],
                    "median_income": row["median_income"],
                })

        demo = pd.DataFrame(expanded).sort_values(["city", "date"])
        print(f"[STEP] Broadcasted demographics → {len(demo):,} rows")

    # ---------------------------------------------------------
    property_types = ["Apartment", "House", "Town House"]
    hpi = hpi[hpi['property_type'].isin(property_types)]

    print("[STEP] Pivoting metrics table...")
    metrics_pivot = metrics.pivot_table(
        index=['date', 'city'], 
        columns='metric', 
        values='value', 
        aggfunc='mean'
    ).reset_index()
    metrics_pivot.columns.name = None

    # Metrics already use snake_case
    # Ensure required columns exist
    for col in ["mortgage_rate", "overnight_rate", "unemployment_rate"]:
        if col not in metrics_pivot.columns:
            metrics_pivot[col] = None

    all_months = pd.date_range(hpi['date'].min(), hpi['date'].max(), freq='MS')
    cities = sorted(hpi['city'].unique())

    base = pd.MultiIndex.from_product(
        [all_months, cities, property_types],
        names=['date', 'city', 'property_type']
    ).to_frame(index=False)

    df = base.merge(hpi, on=['date', 'city', 'property_type'], how='left')
    df = df.merge(rent, on=['date', 'city'], how='left')
    df = df.merge(metrics_pivot, on=['date', 'city'], how='left')
    df = df.merge(macro, on=['date', 'city'], how='left')
    df = df.merge(demo, on=['date', 'city'], how='left')

    # National fallback (Option A)
    if 'Canada' in metrics_pivot['city'].unique():
        nat = metrics_pivot[metrics_pivot['city'] == 'Canada'].set_index('date')

        for col in ['mortgage_rate', 'overnight_rate', 'unemployment_rate']:
            df_city = df.merge(nat[[col]], left_on='date', right_index=True, how='left', suffixes=('', '_nat'))
            df[col] = df_city[col].fillna(df_city[col + "_nat"])

    df = fill_missing(df, ['hpi_benchmark', 'rent_avg_city'], ['city', 'property_type'])

    df['hpi_change_yoy'] = df.groupby(['city', 'property_type'])['hpi_benchmark'].transform(pct_change_yoy)
    df['rent_change_yoy'] = df.groupby(['city'])['rent_avg_city'].transform(pct_change_yoy)

    df = df.replace([np.inf, -np.inf], np.nan)
    df['source'] = 'features_build_etl_v10_full_patched'
    df['created_at'] = datetime.now(timezone.utc)

    print(f"[INFO] Final dataset shape: {df.shape}")
    return df

def write_to_db(df: pd.DataFrame):
    print("[STEP] Writing to public.features ...")

    df['population'] = pd.to_numeric(df['population'], errors='coerce').fillna(0).astype(np.int64)
    df['median_income'] = pd.to_numeric(df['median_income'], errors='coerce')
    df['migration_rate'] = pd.to_numeric(df['migration_rate'], errors='coerce')

    cols = [
        'date', 'city', 'property_type',
        'hpi_benchmark', 'rent_avg_city',
        'mortgage_rate', 'unemployment_rate', 'overnight_rate',
        'population', 'median_income', 'migration_rate',
        'gdp_growth', 'cpi_yoy',
        'hpi_change_yoy', 'rent_change_yoy',
        'source', 'created_at'
    ]

    sql = text(f"""
        INSERT INTO public.features ({', '.join(cols)})
        VALUES ({', '.join(':'+c for c in cols)})
        ON CONFLICT (date, city, property_type)
        DO UPDATE SET
            hpi_benchmark = EXCLUDED.hpi_benchmark,
            rent_avg_city = EXCLUDED.rent_avg_city,
            mortgage_rate = EXCLUDED.mortgage_rate,
            unemployment_rate = EXCLUDED.unemployment_rate,
            overnight_rate = EXCLUDED.overnight_rate,
            hpi_change_yoy = EXCLUDED.hpi_change_yoy,
            rent_change_yoy = EXCLUDED.rent_change_yoy,
            source = EXCLUDED.source,
            created_at = EXCLUDED.created_at;
    """)

    with engine.begin() as conn:
        conn.exec_driver_sql("SELECT 1;")
        batch_size = 3000
        total = len(df)
        for i in range(0, total, batch_size):
            batch = df.iloc[i:i+batch_size]
            conn.execute(sql, batch.to_dict(orient='records'))
            print(f"[WRITE] Batch {i//batch_size + 1} → {len(batch)} rows")

    print(f"[OK] Written {len(df):,} rows to public.features")


if __name__ == "__main__":
    start = datetime.now(timezone.utc)
    print("[DEBUG] features_build_etl_v10_full_patched started ...")

    df_features = build_features()
    write_to_db(df_features)

    print(f"[DONE] Completed in {datetime.now(timezone.utc) - start}")
