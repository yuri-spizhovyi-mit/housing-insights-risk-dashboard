# run_rentals_once.py
from datetime import date
from ml.src.etl import rentals_ca, base


def main():
    ctx = base.Context(run_date=date(2025, 9, 12))
    ctx.params = {
        # pick ONE of these three:
        "rentals_ca_path": "ml/tests/data/rentals_sample.csv",  # local CSV sample
        # "rentals_ca_url": "https://…/rentals_2025-08.xlsx",   # direct CSV/XLSX
        # "rentals_ca_auto": True,                               # try auto-discovery
    }

    df = rentals_ca.run(ctx)
    print(df)


if __name__ == "__main__":
    main()
