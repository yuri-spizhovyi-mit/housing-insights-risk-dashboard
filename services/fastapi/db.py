import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load .env if it exists (for local dev)
load_dotenv()

# Get DATABASE_URL
DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    raise RuntimeError(
        "❌ DATABASE_URL is not set. Check your .env or Vercel env settings."
    )


def query(sql, params=None):
    try:
        # Choose SSL mode depending on environment (Neon requires it)
        sslmode = "require" if "neon.tech" in DB_URL else "disable"

        conn = psycopg2.connect(DB_URL, sslmode=sslmode, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        cur.execute(sql, params or ())
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        print("❌ DB error:", e)
        raise
