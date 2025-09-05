import argparse
import datetime as dt
from src.etl.base import Context
from src.etl import crea, cmhc, statcan, boc


def main():
    p = argparse.ArgumentParser(description="Daily ETL entry point")
    p.add_argument(
        "--source", required=True, choices=["crea", "cmhc", "statcan", "boc", "all"]
    )
    p.add_argument("--date", default="today")
    args = p.parse_args()

    run_date = (
        dt.date.today() if args.date == "today" else dt.date.fromisoformat(args.date)
    )
    ctx = Context(run_date=run_date)

    if args.source == "all":
        for fn in (crea.run, cmhc.run, statcan.run, boc.run):
            fn(ctx)
    elif args.source == "crea":
        crea.run(ctx)
    elif args.source == "cmhc":
        cmhc.run(ctx)
    elif args.source == "statcan":
        statcan.run(ctx)
    elif args.source == "boc":
        boc.run(ctx)


if __name__ == "__main__":
    main()
