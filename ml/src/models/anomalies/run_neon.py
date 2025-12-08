import os
from sqlalchemy import create_engine
from .anomaly_pipeline import run_all_anomalies
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(usecwd=True))

# Load Neon DB URL from environment (.env or Vercel)
NEON_DB = os.getenv("NEON_DATABASE_URL")

if not NEON_DB:
    raise ValueError("NEON_DATABASE_URL is not set. Add it to your .env file.")

# Create Neon SQLAlchemy engine
engine = create_engine(NEON_DB, pool_pre_ping=True, future=True)

if __name__ == "__main__":
    print("Running anomaly detection on Neon database...")
    run_all_anomalies(engine)
    print("Completed anomaly detection on Neon!")
