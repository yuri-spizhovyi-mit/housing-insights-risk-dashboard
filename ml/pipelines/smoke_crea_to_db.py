from datetime import date
import pandas as pd
import sys
from pathlib import Path
import os

# Force IPv4 connection to avoid IPv6 authentication issues
os.environ["DB_HOST"] = "127.0.0.1"
# Override DATABASE_URL to use IPv4
os.environ["DATABASE_URL"] = (
    "postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/hird"
)

from ml.src.etl.base import _build_pg_url_from_env, Context, write_hpi_upsert
from dotenv import load_dotenv, find_dotenv

sys.path.append(str(Path(__file__).parent.parent))
# Load .env starting from the current working directory upward (repo root)
load_dotenv(find_dotenv(usecwd=True))

print("DB_HOST env var:", os.getenv("DB_HOST"))
print("DATABASE_URL env var:", os.getenv("DATABASE_URL"))
print("PG URL (from env):", _build_pg_url_from_env())


def main():
    # Override the Context to use 127.0.0.1 directly
    ctx = Context(run_date=date.today())
    # Manually set the database host to force IPv4
    ctx.db_host = "127.0.0.1"
    df = pd.DataFrame(
        [
            {
                "city": "Kelowna",
                "date": date(2024, 12, 1),
                "index_value": 365.4,
                "measure": "HPI",
                "source": "CREA",
            },
            {
                "city": "Vancouver",
                "date": date(2024, 12, 1),
                "index_value": 487.2,
                "measure": "HPI",
                "source": "CREA",
            },
            {
                "city": "Toronto",
                "date": date(2024, 12, 1),
                "index_value": 456.1,
                "measure": "HPI",
                "source": "CREA",
            },
        ]
    )
    total = write_hpi_upsert(df, ctx)
    print(f"house_price_index total rows: {total}")


if __name__ == "__main__":
    main()
