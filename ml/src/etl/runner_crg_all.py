# ml/src/etl/runner_crg_all.py
import argparse
import time
from ml.src.etl.v2_crg_listing import (
    CITY_TO_BASE_URL,
    scrape_craigslist_to_listings_raw,
)


def run_all(
    categories=("rent", "sale"),
    cities=None,
    max_pages=3,
    sleep_sec=1.2,
    start_city=None,
):
    if cities is None:
        cities = list(CITY_TO_BASE_URL.keys())

    if start_city:
        # skip everything before start_city
        start_index = cities.index(start_city.lower())
        cities = cities[start_index:]

    total_rows = 0
    for city in cities:
        for category in categories:
            print(f"\n[RUNNER] Starting scrape for city={city}, category={category}")
            try:
                rows = scrape_craigslist_to_listings_raw(
                    base_url=CITY_TO_BASE_URL[city],
                    category=category,
                    query=None,
                    city=city,
                    max_pages=max_pages,
                    sleep_sec=sleep_sec,
                )
                print(f"[RUNNER] Finished {city}/{category}, wrote {rows} rows")
                total_rows += rows
            except Exception as e:
                print(f"[RUNNER][ERROR] {city}/{category} failed → {e}")
            time.sleep(2)

    print(f"\n[RUNNER] ✅ Done. Total rows written: {total_rows}")
    return total_rows


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument(
        "--start-city",
        choices=list(CITY_TO_BASE_URL.keys()),
        help="Resume from this city",
    )
    p.add_argument("--max-pages", type=int, default=3)
    p.add_argument("--sleep-sec", type=float, default=1.2)
    args = p.parse_args()

    run_all(
        categories=("rent", "sale"),
        max_pages=args.max_pages,
        sleep_sec=args.sleep_sec,
        start_city=args.start_city,
    )
