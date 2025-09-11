import argparse
import datetime as dt
import os
from src.etl.base import Context
from src.etl import crea, cmhc, statcan, boc, rentals_ca


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--source",
        required=True,
        choices=["crea", "cmhc", "statcan", "boc", "rentals", "all"],
    )
    p.add_argument(
        "--date", default="today", help="Run date (YYYY-MM-DD) for snapshots"
    )
    p.add_argument("--start-date", help="Optional backfill start (YYYY-MM-DD)")
    p.add_argument("--end-date", help="Optional backfill end (YYYY-MM-DD)")
    p.add_argument("--rentals-file", help="Optional Rentals.ca CSV or JSON path")
    args = p.parse_args()

    # run_date for snapshot paths
    run_date = (
        dt.date.today() if args.date == "today" else dt.date.fromisoformat(args.date)
    )
    ctx = Context(run_date=run_date)

    # Expose backfill window to adapters via env (BoC uses these in run)
    if args.start_date:
        os.environ["START_DATE"] = args.start_date
    if args.end_date:
        os.environ["END_DATE"] = args.end_date

    def run_all():
        # Order: CREA → CMHC → StatCan → BoC → Rentals
        crea.run(ctx)
        cmhc.run(ctx)
        statcan.run(ctx)
        boc.run(ctx)
        if args.rentals_file:
            rentals_ca.run_file(ctx, path=args.rentals_file)
        else:
            rentals_ca.run_endpoint(ctx)

    if args.source == "all":
        run_all()
    elif args.source == "crea":
        crea.run(ctx)
    elif args.source == "cmhc":
        cmhc.run(ctx)
    elif args.source == "statcan":
        statcan.run(ctx)
    elif args.source == "boc":
        boc.run(ctx)
    elif args.source == "rentals":
        if args.rentals_file:
            rentals_ca.run_file(ctx, path=args.rentals_file)
        else:
            rentals_ca.run_endpoint(ctx)


if __name__ == "__main__":
    main()
