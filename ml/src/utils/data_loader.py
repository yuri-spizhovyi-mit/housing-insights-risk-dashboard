# ml/src/utils/data_loader.py

import pandas as pd
from sqlalchemy import text


def load_timeseries(engine, target: str, city: str) -> pd.DataFrame:
    """
    Load a time series for a given target and city.
    Returns DataFrame with columns ['ds', 'y'] for Prophet and anomaly detection.

    Supported targets:
        - price                (mapped to features.hpi_benchmark)
        - rent                 (mapped to features.rent_avg_city)
        - rent_index           (public.rent_index)
        - house_price_index    (public.house_price_index)
        - features             (features.hpi_composite_sa)
        - any other metric name → public.metrics(metric, city)
    """

    with engine.connect() as conn:
        # --------------------------------------------------
        # 1. SPECIAL CASES FOR ANOMALIES: price / rent
        # --------------------------------------------------
        if target == "price":
            query = text("""
                SELECT date,  benchmark_price AS value
                FROM public.house_price_index
                WHERE city = :city AND property_type = 'All'
                ORDER BY date
            """)
            df = pd.read_sql(query, conn, params={"city": city})

        elif target == "rent":
            query = text("""
                SELECT date, rent_value  AS value
                FROM public.rent_index
                WHERE city = :city
                ORDER BY date
            """)
            df = pd.read_sql(query, conn, params={"city": city})

        # --------------------------------------------------
        # 2. RENT INDEX (CMHC ANNUAL/MONTHLY RENT SERIES)
        # --------------------------------------------------
        elif target == "rent_index":
            query = text("""
                SELECT date, index_value AS value
                FROM public.rent_index
                WHERE city = :city
                ORDER BY date
            """)
            df = pd.read_sql(query, conn, params={"city": city})

        # --------------------------------------------------
        # 3. HOUSE PRICE INDEX (CREA HPI)
        # --------------------------------------------------
        elif target == "house_price_index":
            query = text("""
                SELECT date, index_value AS value
                FROM public.house_price_index
                WHERE city = :city
                ORDER BY date
            """)
            df = pd.read_sql(query, conn, params={"city": city})

        # --------------------------------------------------
        # 4. GENERIC FEATURES TARGET (LEGACY)
        # --------------------------------------------------
        elif target == "features":
            query = text("""
                SELECT date, hpi_composite_sa AS value
                FROM public.features
                WHERE city = :city AND property_type = 'All'
                ORDER BY date
            """)
            df = pd.read_sql(query, conn, params={"city": city})

        # --------------------------------------------------
        # 5. DEFAULT: METRICS TABLE (macro-economic)
        # --------------------------------------------------
        else:
            query = text("""
                SELECT date, value
                FROM public.metrics
                WHERE metric = :metric AND city = :city
                ORDER BY date
            """)
            df = pd.read_sql(query, conn, params={"metric": target, "city": city})

    # --------------------------------------------------
    # FINAL CLEANUP AND LOGGING
    # --------------------------------------------------

    if df.empty:
        print(f"[WARN] No data found for target='{target}' city='{city}'")
        return pd.DataFrame(columns=["ds", "y"])

    # Prophet-compatible naming
    df = df.rename(columns={"date": "ds", "value": "y"})
    df = df.dropna(subset=["y"])

    print(f"[DEBUG] Loaded {len(df)} rows for target='{target}' city='{city}'")
    return df
