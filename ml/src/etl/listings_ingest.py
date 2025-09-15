# listings_ingest.py
#!/usr/bin/env python3
import argparse
import time
from datetime import date
from .base import Context, write_listings_upsert
from .utils import save_snapshot
from .listings_castanet import fetch_castanet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-pages", type=int, default=2)
    ap.add_argument("--sleep-sec", type=float, default=1.0)
    args = ap.parse_args()

    rows, blobs = fetch_castanet(max_pages=args.max_pages, sleep_sec=args.sleep_sec)

    # save snapshots
    for i, b in enumerate(blobs):
        save_snapshot(b, ".debug/castanet", f"page_{i}", "html")

    # Use Context for database connection
    ctx = Context(run_date=date.today())

    # Convert rows to the format expected by write_listings_upsert
    # Since write_listings_upsert expects a psycopg2 Connection, we need to use the engine directly
    from psycopg2 import connect
    from .base import _build_pg_url_from_env

    pg_url = _build_pg_url_from_env()
    # Convert SQLAlchemy URL to psycopg2 URL format
    pg_url_psycopg2 = pg_url.replace("postgresql+psycopg2://", "postgresql://")

    with connect(pg_url_psycopg2) as conn:
        n = write_listings_upsert(conn, rows)
        print(f"Castanet upsert attempted for {n} rows")

    # quick sanity
    print("Example row:", rows[0] if rows else "no rows parsed")


if __name__ == "__main__":
    main()
