import os
from functools import lru_cache
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from psycopg2 import connect


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    url = os.getenv("DATABASE_URL")
    if not url:
        user = os.getenv("POSTGRES_USER", "hird")
        pwd = os.getenv("POSTGRES_PASSWORD", "hirdpw")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "hird")
        url = f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"
    engine = create_engine(url, pool_pre_ping=True, future=True)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return engine


def get_conn():
    """Get a raw psycopg2 connection for scripts that need direct database access."""
    url = os.getenv("DATABASE_URL")
    if not url:
        user = os.getenv("POSTGRES_USER", "hird")
        pwd = os.getenv("POSTGRES_PASSWORD", "hirdpw")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "hird")
        url = f"postgresql://{user}:{pwd}@{host}:{port}/{db}"
    else:
        # Convert SQLAlchemy URL to psycopg2 URL format
        url = url.replace("postgresql+psycopg2://", "postgresql://")

    return connect(url)
