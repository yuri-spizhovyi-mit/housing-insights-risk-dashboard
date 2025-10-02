import pandas as pd
import psycopg2


def load_timeseries(conn, target: str, city: str) -> pd.DataFrame:
    """
    Load a time series (e.g., rent_index, house_price_index) for a given city.
    Returns a DataFrame with columns: date, value
    """
    query = """
        SELECT date, value
        FROM metrics
        WHERE metric = %s AND city = %s
        ORDER BY date
    """
    return pd.read_sql(query, conn, params=(target, city))
