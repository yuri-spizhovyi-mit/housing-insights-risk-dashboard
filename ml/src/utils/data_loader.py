# ml/src/utils/data_loader.py
import pandas as pd
from sqlalchemy import text

def load_timeseries(engine, target: str, city: str) -> pd.DataFrame:
    """
    Load a time series for the given metric/target and city.
    Returns DataFrame with columns ['ds', 'y'] for Prophet.
    """

    with engine.connect() as conn:
        if target == "rent_index":
            query = text("""
                SELECT date, index_value AS value
                FROM public.rent_index
                WHERE city = :city
                ORDER BY date
            """)
            df = pd.read_sql(query, conn, params={"city": city})

        elif target == "house_price_index":
            query = text("""
                SELECT date, index_value AS value
                FROM public.house_price_index
                WHERE city = :city
                ORDER BY date
            """)
            df = pd.read_sql(query, conn, params={"city": city})

        else:
            # Default for metrics table (BoC, StatCan, CMHC)
            query = text("""
                SELECT date, value
                FROM public.metrics
                WHERE metric = :metric AND city = :city
                ORDER BY date
            """)
            df = pd.read_sql(query, conn, params={"metric": target, "city": city})

    if df.empty:
        print(f"[WARN] No data found for {target} – {city}")
        return pd.DataFrame(columns=["ds", "y"])

    # Prophet requires these exact column names
    df = df.rename(columns={"date": "ds", "value": "y"})
    df = df.dropna(subset=["y"])

    print(f"[DEBUG] Loaded {len(df)} points for {target} – {city}")
    return df
