import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Mapping, Optional
from urllib.parse import quote_plus

import boto3
import pandas as pd
from dotenv import find_dotenv, load_dotenv
from psycopg2 import connect as psycopg2_connect
from psycopg2.extras import execute_values
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Load .env starting from the current working directory upward (repo root)
load_dotenv(find_dotenv(usecwd=True))

LISTINGS_COLS = [
    "listing_id",
    "url",
    "date_posted",
    "city",
    "postal_code",
    "property_type",
    "listing_type",
    "price",
    "bedrooms",
    "bathrooms",
    "area_sqft",
    "year_built",
    "description",
]

_UPSERT_SQL = f"""
INSERT INTO public.listings_raw ({", ".join(LISTINGS_COLS)})
VALUES %s
ON CONFLICT (listing_id) DO UPDATE SET
  url = EXCLUDED.url,
  date_posted = GREATEST(public.listings_raw.date_posted, EXCLUDED.date_posted),
  city = EXCLUDED.city,
  postal_code = COALESCE(EXCLUDED.postal_code, public.listings_raw.postal_code),
  property_type = COALESCE(EXCLUDED.property_type, public.listings_raw.property_type),
  listing_type = COALESCE(EXCLUDED.listing_type, public.listings_raw.listing_type),
  price = COALESCE(EXCLUDED.price, public.listings_raw.price),
  bedrooms = COALESCE(EXCLUDED.bedrooms, public.listings_raw.bedrooms),
  bathrooms = COALESCE(EXCLUDED.bathrooms, public.listings_raw.bathrooms),
  area_sqft = COALESCE(EXCLUDED.area_sqft, public.listings_raw.area_sqft),
  year_built = COALESCE(EXCLUDED.year_built, public.listings_raw.year_built),
  description = COALESCE(EXCLUDED.description, public.listings_raw.description);
"""


def write_listings_upsert(conn, rows: Iterable[Mapping]) -> int:
    values = [tuple(r.get(k) for k in LISTINGS_COLS) for r in rows]
    if not values:
        return 0
    with conn.cursor() as cur:
        execute_values(cur, _UPSERT_SQL, values, page_size=1000)
    conn.commit()
    return len(values)


def _build_pg_url_from_env() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url

    host = os.getenv("DB_HOST", os.getenv("POSTGRES_HOST", "localhost"))
    port = os.getenv("DB_PORT", os.getenv("POSTGRES_PORT", "5433"))
    name = os.getenv("DB_NAME", os.getenv("POSTGRES_DB", "hird"))
    user = os.getenv("DB_USER", os.getenv("POSTGRES_USER", "postgres"))
    pwd = os.getenv("DB_PASS", os.getenv("POSTGRES_PASSWORD", "postgres"))
    return f"postgresql+psycopg2://{quote_plus(user)}:{quote_plus(pwd)}@{host}:{port}/{name}"


@dataclass
class Context:
    run_date: date
    s3_endpoint: str = os.getenv("S3_ENDPOINT", "http://localhost:9000")
    s3_access: str = os.getenv("S3_ACCESS_KEY", "minioadmin")
    s3_secret: str = os.getenv("S3_SECRET_KEY", "minioadmin")
    s3_bucket_raw: str = os.getenv("S3_BUCKET_RAW", "hird-raw")
    s3_raw_prefix: str = os.getenv("S3_RAW_PREFIX", "raw")

    @property
    def engine(self):
        pg_url = _build_pg_url_from_env()
        engine = create_engine(pg_url, pool_pre_ping=True, future=True)
        # optional sanity ping
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine

    @property
    def s3(self):
        return boto3.client(
            "s3",
            endpoint_url=self.s3_endpoint,
            aws_access_key_id=self.s3_access,
            aws_secret_access_key=self.s3_secret,
        )


def put_raw_bytes(
    ctx: Context, key: str, blob: bytes, content_type="application/octet-stream"
):
    ctx.s3.put_object(
        Bucket=ctx.s3_bucket_raw, Key=key, Body=blob, ContentType=content_type
    )
    return f"s3://{ctx.s3_bucket_raw}/{key}"


def write_df(
    df: pd.DataFrame,
    table: str,
    ctx: Context,
    if_exists: str = "append",
    **kwargs,
) -> int:
    if df is None or df.empty:
        print(f"[DEBUG] Skipping write: {table} DataFrame empty.")
        return 0

    df = df.copy()
    df.columns = [c.lower() for c in df.columns]

    engine = ctx.engine
    # Use connection.execute() without implicit transaction rollback
    with engine.connect() as conn:
        df.to_sql(
            table,
            conn,
            schema="public",
            if_exists=if_exists,
            index=False,
            method=kwargs.pop("method", "multi"),
            chunksize=kwargs.pop("chunksize", 500),
            **kwargs,
        )
        conn.commit()  # ✅ Explicit commit to persist data

        total = conn.execute(
            text(f'SELECT COUNT(*) FROM public."{table}"')
        ).scalar_one()
        print(f"[DEBUG] Total rows in {table} after write:", total)
        return int(total)


def month_floor(d: pd.Series) -> pd.Series:
    # convert to first day of month
    return pd.to_datetime(d.astype(str)).dt.to_period("M").dt.to_timestamp()


def _resolve_engine(ctx):
    eng_attr = getattr(ctx, "engine")
    return eng_attr() if callable(eng_attr) else eng_attr


def write_metrics_upsert(df: pd.DataFrame, ctx: "Context") -> None:
    if df is None or df.empty:
        return
    needed = {"metric", "city", "date", "value", "source"}
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(f"metrics upsert missing columns: {missing}")

    df = df.dropna(subset=["metric", "city", "date"]).drop_duplicates(
        subset=["metric", "city", "date"], keep="last"
    )

    sql = text("""
        INSERT INTO public.metrics (metric, value, city, "date", source)
        VALUES (:metric, :value, :city, :date, :source)
        ON CONFLICT ("date", metric, city)
        DO UPDATE SET
            value  = EXCLUDED.value,
            source = EXCLUDED.source
    """)

    rows = df.to_dict(orient="records")
    eng = _resolve_engine(ctx)  # << fix here
    with eng.begin() as cx:
        cx.execute(sql, rows)


def write_hpi_upsert(df: pd.DataFrame, ctx: "Context") -> None:
    if df is None or df.empty:
        return
    needed = {"city", "date", "index_value", "measure", "source"}
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(f"HPI upsert missing columns: {missing}")

    df = df.dropna(subset=["city", "date", "measure"]).drop_duplicates(
        subset=["city", "date", "measure"], keep="last"
    )

    sql = text("""
        INSERT INTO public.house_price_index (city, "date", index_value, measure, source)
        VALUES (:city, :date, :index_value, :measure, :source)
        ON CONFLICT (city, "date", measure)
        DO UPDATE SET
            index_value = EXCLUDED.index_value,
            source      = EXCLUDED.source
    """)

    rows = df.to_dict(orient="records")
    eng = _resolve_engine(ctx)  # << fix here too
    with eng.begin() as cx:
        cx.execute(sql, rows)


def write_rents_upsert(
    df: pd.DataFrame, ctx_or_engine, schema: Optional[str] = "public"
) -> None:
    """
    Upsert into rents(city, "date", bedroom_type, median_rent, source)
    Primary key: (city, "date", bedroom_type)

    Accepts either a 'median_rent' column OR a legacy 'value' column
    and writes to 'median_rent' in the DB.
    """
    if df is None or df.empty:
        return

    df = df.copy()

    # Accept legacy 'value' and map to 'median_rent' if needed
    if "median_rent" not in df.columns:
        if "value" in df.columns:
            df["median_rent"] = pd.to_numeric(df["value"], errors="coerce")
        else:
            raise ValueError("rents upsert: expected 'median_rent' or 'value' column")

    required = {"city", "date", "bedroom_type", "median_rent", "source"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"rents upsert: missing columns: {missing}")

    # Normalize types for safety
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date.astype(str)
    df["median_rent"] = pd.to_numeric(df["median_rent"], errors="coerce")

    # Drop rows that don't have a date or rent
    df = df.dropna(subset=["date", "median_rent"])

    rows = df[["city", "date", "bedroom_type", "median_rent", "source"]].to_dict(
        "records"
    )

    # Note: "date" is quoted in your DDL; keep it quoted here too
    sql = text(f"""
        INSERT INTO {schema}.rents (city, "date", bedroom_type, median_rent, source)
        VALUES (:city, :date, :bedroom_type, :median_rent, :source)
        ON CONFLICT (city, "date", bedroom_type)
        DO UPDATE SET
            median_rent = EXCLUDED.median_rent,
            source = EXCLUDED.source
    """)

    eng = _resolve_engine(ctx_or_engine)  # accepts Context or Engine
    with eng.begin() as conn:
        conn.execute(sql, rows)


def get_session(ctx: Optional[Context] = None):
    """Return a basic HTTP session. Extend here if you need proxies/headers."""
    import requests

    return requests.Session()


def get_neon_engine() -> Engine:
    """
    Return a SQLAlchemy engine for Neon cloud database.
    """
    neon_url = os.getenv("NEON_DATABASE_URL")
    if not neon_url:
        raise RuntimeError("NEON_DATABASE_URL not set in .env")
    eng = create_engine(neon_url, pool_pre_ping=True, future=True)
    # optional ping
    with eng.connect() as conn:
        conn.execute(text("SELECT 1"))
    return eng
