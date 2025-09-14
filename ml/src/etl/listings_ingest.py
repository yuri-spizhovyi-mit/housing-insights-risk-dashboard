# listings_ingest.py
#!/usr/bin/env python3
import argparse, time
from db import get_pg_connection
from base import write_listings_upsert
from utils import save_snapshot
from listings_castanet import fetch_castanet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-pages", type=int, default=2)
    ap.add_argument("--sleep-sec", type=float, default=1.0)
    args = ap.parse_args()

    rows, blobs = fetch_castanet(max_pages=args.max_pages, sleep_sec=args.sleep_sec)

    # save snapshots
    for i, b in enumerate(blobs):
        save_snapshot(b, ".debug/castanet", f"page_{i}", "html")

    with get_pg_connection() as conn:
        n = write_listings_upsert(conn, rows)
        print(f"Castanet upsert attempted for {n} rows")

    # quick sanity
    print("Example row:", rows[0] if rows else "no rows parsed")


if __name__ == "__main__":
    main()
