import os
import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = os.getenv("DATABASE_URL")


def query(sql, params=None):
    try:
        conn = psycopg2.connect(
            DB_URL, sslmode="disable", cursor_factory=RealDictCursor
        )
        cur = conn.cursor()
        cur.execute(sql, params or ())
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        print("❌ DB error:", e)  # debug log
        raise
