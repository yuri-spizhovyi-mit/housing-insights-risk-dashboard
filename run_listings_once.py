from datetime import date
from ml.src.etl import market_listings, base

def main():
    ctx = base.Context(run_date=date(2025, 9, 12))
    # Optional: configure params (enable/disable sources)
    ctx.params = {
        "enable_rentfaster": True,   # we’ll add adapter for RentFaster
        "max_pages": 1              # to keep it light on first run
    }
    df = market_listings.run(ctx)
    print(df)

if __name__ == "__main__":
    main()
