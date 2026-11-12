"""Select the PostgreSQL driver installed by the API requirements."""
from sqlalchemy.engine import make_url

def normalize_database_url(value):
    url = make_url(value)
    if url.drivername in {"postgres", "postgresql", "postgresql+psycopg"}:
        url = url.set(drivername="postgresql+psycopg2")
    return url
