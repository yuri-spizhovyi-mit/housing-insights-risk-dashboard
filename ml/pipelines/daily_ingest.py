import argparse
import datetime as dt
from src.etl.base import Context
from src.etl import crea, cmhc, statcan, boc, rentals_ca


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--source",
        required=True,
        choices=["crea", "cmhc", "statcan", "boc", "rentals", "all"],
    )
    p.add_argument("--date", default="today")
    args = p.parse_args()

    run_date = (
        dt.date.today() if args.date == "today" else dt.date.fromisoformat(args.date)
    )
    ctx = Context(run_date=run_date)

    if args.source == "all":
        for fn in (crea.run, cmhc.run, statcan.run, boc.run, rentals_ca.run):
            fn(ctx)
    elif args.source == "crea":
        crea.run(ctx)
    elif args.source == "cmhc":
        cmhc.run(ctx)
    elif args.source == "statcan":
        statcan.run(ctx)
    elif args.source == "boc":
        boc.run(ctx)
    elif args.source == "rentals":
        rentals_ca.run(ctx)


if __name__ == "__main__":
    main()
