from datetime import date
import logging
from ml.src.etl import market_listings, base

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def main():
    ctx = base.Context(run_date=date(2025, 9, 12))
    # Optional: configure params (enable/disable sources)
    ctx.params = {
        "enable_rentfaster": True,   # we'll add adapter for RentFaster
        "max_pages": 1              # to keep it light on first run
    }
    print(f"Context params: {ctx.params}")
    df = market_listings.run(ctx)
    print(f"Result DataFrame shape: {df.shape}")
    print(df)

if __name__ == "__main__":
    main()
