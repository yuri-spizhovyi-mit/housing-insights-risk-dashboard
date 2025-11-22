"""
features_build_etl_v10_full_rebuild_fixed2.py
----------------------------------------------------------
Adds numeric sanitization before database insertion to prevent BIGINT out-of-range errors.
Preserves all v10_full_rebuild_fixed logic.
"""

from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime, timezone
import pandas as pd
import numpy as np
import os

load_dotenv(find_dotenv(usecwd=True))
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL") or os.getenv("DATABASE_URL")
if not NEON_DATABASE_URL:
    raise RuntimeError("NEON_DATABASE_URL not found in .env")

engine = create_engine(NEON_DATABASE_URL, pool_pre_ping=True, future=True)
print("[DEBUG] Connected to Neon via .env")

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

    property_types = ["Apartment", "House", "Town House"]
    hpi = hpi[hpi['property_type'].isin(property_types)]

    print("[STEP] Pivoting metrics table...")
    metrics_pivot = metrics.pivot_table(index=['date', 'city'], columns='metric', values='value', aggfunc='mean').reset_index()
    metrics_pivot.columns.name = None

    all_months = pd.date_range(hpi['date'].min(), hpi['date'].max(), freq='MS')
    cities = sorted(hpi['city'].unique())
    base = pd.MultiIndex.from_product([all_months, cities, property_types], names=['date', 'city', 'property_type']).to_frame(index=False)

    df = base.merge(hpi, on=['date', 'city', 'property_type'], how='left')
    df = df.merge(rent, on=['date', 'city'], how='left')
    df = df.merge(metrics_pivot, on=['date', 'city'], how='left')
    df = df.merge(macro, on=['date', 'city'], how='left')
    df = df.merge(demo, on=['date', 'city'], how='left')

    if 'Canada' in metrics_pivot['city'].unique():
        nat = metrics_pivot[metrics_pivot['city'] == 'Canada'].set_index('date')
        for col in ['mortgage_rate', 'overnight_rate', 'unemployment_rate']:
            for city in cities:
                df_city = df[df['city'] == city]
                merged = df_city.merge(nat[[col]], left_on='date', right_index=True, how='left', suffixes=('', '_nat'))
                filled = merged[col].fillna(merged[col + '_nat'])
                df.loc[df['city'] == city, col] = filled.values

    df = fill_missing(df, ['hpi_benchmark', 'rent_avg_city'], ['city', 'property_type'])
    df['hpi_change_yoy'] = df.groupby(['city', 'property_type'])['hpi_benchmark'].transform(pct_change_yoy)
    df['rent_change_yoy'] = df.groupby(['city'])['rent_avg_city'].transform(pct_change_yoy)

    df = df.replace([np.inf, -np.inf], np.nan)
    df['source'] = 'features_build_etl_v10_full_rebuild_fixed2'
    df['created_at'] = datetime.now(timezone.utc)

    print(f"[INFO] Final dataset shape: {df.shape}")
    return df

def write_to_db(df: pd.DataFrame):
    print("[STEP] Writing to public.features ...")

    # --- Numeric sanitization ---
    df['population'] = pd.to_numeric(df['population'], errors='coerce').fillna(0).astype(np.int64)
    df['median_income'] = pd.to_numeric(df['median_income'], errors='coerce')
    df['migration_rate'] = pd.to_numeric(df['migration_rate'], errors='coerce')

    cols = [
        'date', 'city', 'property_type', 'hpi_benchmark', 'rent_avg_city', 'mortgage_rate', 'unemployment_rate',
        'overnight_rate', 'population', 'median_income', 'migration_rate', 'gdp_growth', 'cpi_yoy',
        'hpi_change_yoy', 'rent_change_yoy', 'source', 'created_at'
    ]

    insert_sql = text(f"""
        INSERT INTO public.features ({', '.join(cols)})
        VALUES ({', '.join([':' + c for c in cols])})
        ON CONFLICT (date, city, property_type)
        DO UPDATE SET
            hpi_benchmark = EXCLUDED.hpi_benchmark,
            rent_avg_city = EXCLUDED.rent_avg_city,
            hpi_change_yoy = EXCLUDED.hpi_change_yoy,
            rent_change_yoy = EXCLUDED.rent_change_yoy,
            source = EXCLUDED.source,
            created_at = EXCLUDED.created_at;
    """)

    with engine.begin() as conn:
        conn.exec_driver_sql("SELECT 1;")
        batch_size = 5000
        total = len(df)
        for i in range(0, total, batch_size):
            batch = df.iloc[i:i+batch_size]
            conn.execute(insert_sql, batch.to_dict(orient='records'))
            print(f"[WRITE] Batch {i // batch_size + 1} → {len(batch)} rows")

    print(f"[OK] Written {len(df):,} rows to public.features")

if __name__ == '__main__':
    start = datetime.now(timezone.utc)
    print("[DEBUG] features_build_etl_v10_full_rebuild_fixed2 started ...")
    df_features = build_features()
    write_to_db(df_features)
    print(f"\n[DONE] features_build_etl_v10_full_rebuild_fixed2 completed in {datetime.now(timezone.utc) - start}")
