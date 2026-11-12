# db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
from .database_url import normalize_database_url

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    raise RuntimeError(
        "❌ DATABASE_URL is not set. Check your .env or Vercel env settings."
    )

# Keep driver selection stable across SQLAlchemy default changes.
DB_URL = normalize_database_url(DB_URL)

engine = create_engine(
    DB_URL, connect_args={"sslmode": "require"} if "neon.tech" in (DB_URL.host or "") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
