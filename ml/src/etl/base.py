from typing import Optional
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import quote_plus
import os
from sqlalchemy import text

import boto3
import pandas as pd
from dotenv import find_dotenv, load_dotenv
from psycopg2.extras import (
    execute_values,
)  # requires psycopg2-binary in requirements.txt
from sqlalchemy import create_engine, text

# Load .env starting from the current working directory upward (repo root)
load_dotenv(find_dotenv(usecwd=True))


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
    df: pd.DataFrame, table: str, ctx: Context, if_exists: str = "append"
) -> int:
    """
    Generic loader: appends DataFrame rows into `public.{table}`.
    Returns the total row count in the table after the write.
    """
    if df is None or df.empty:
        return 0

    # normalize column names (you already did this—kept for safety)
    df = df.copy()
    df.columns = [c.lower() for c in df.columns]

    with ctx.engine.begin() as conn:
        # write rows
        df.to_sql(
            table,
            conn,
            schema="public",
            if_exists=if_exists,
            index=False,
            method="multi",
        )
        # return current table size for quick verification
        total = conn.execute(
            text(f'SELECT COUNT(*) FROM public."{table}"')
        ).scalar_one()
        return int(total)


# def write_hpi_upsert(df: pd.DataFrame, ctx: Context) -> int:
#     """
#     Idempotent upsert for house_price_index matching your V1 schema:

#     Columns expected:
#       city TEXT, date DATE, index_value DOUBLE PRECISION, measure TEXT, source TEXT

#     PK / grain: (city, date, measure)
#     """
#     if df is None or df.empty:
#         return 0

#     # Ensure required columns exist and normalized
#     needed = {"city", "date", "index_value", "measure", "source"}
#     miss = needed - set(map(str.lower, df.columns))
#     if miss:
#         raise ValueError(f"write_hpi_upsert: missing columns: {sorted(miss)}")

#     # Normalize column names + types
#     dfn = df.copy()
#     dfn.columns = [c.lower() for c in dfn.columns]
#     # Ensure Python date objects (or date-like) for 'date'
#     dfn["date"] = pd.to_datetime(dfn["date"]).dt.date
#     # Force float for index_value
#     dfn["index_value"] = dfn["index_value"].astype(float)

#     # Build tuples for execute_values
#     rows = [
#         (r.city, r.date, float(r.index_value), r.measure, r.source)
#         for r in dfn.itertuples(index=False)
#     ]

#     upsert_sql = """
#     INSERT INTO public.house_price_index (city, "date", index_value, measure, source)
#     VALUES %s
#     ON CONFLICT (city, "date", measure) DO UPDATE
#       SET index_value = EXCLUDED.index_value,
#           source      = EXCLUDED.source
#     """

#     with ctx.engine.begin() as conn:
#         raw = conn.connection  # psycopg2 connection under the SQLAlchemy hood
#         with raw.cursor() as cur:
#             execute_values(cur, upsert_sql, rows)
#         total = conn.execute(
#             text('SELECT COUNT(*) FROM public."house_price_index"')
#         ).scalar_one()
#         return int(total)


def month_floor(d: pd.Series) -> pd.Series:
    # convert to first day of month
    return pd.to_datetime(d.astype(str)).dt.to_period("M").dt.to_timestamp()


# def write_metrics_upsert(df: pd.DataFrame, ctx: "Context") -> None:
#     if df is None or df.empty:
#         return
#     needed = {"metric", "city", "date", "value", "source"}
#     missing = needed - set(df.columns)
#     if missing:
#         raise ValueError(f"metrics upsert missing columns: {missing}")

#     df = df.dropna(subset=["metric", "city", "date"]).drop_duplicates(
#         subset=["metric", "city", "date"], keep="last"
#     )

#     sql = text("""
#         INSERT INTO public.metrics (metric, value, city, "date", source)
#         VALUES (:metric, :value, :city, :date, :source)
#         ON CONFLICT ("date", metric, city)
#         DO UPDATE SET
#             value  = EXCLUDED.value,
#             source = EXCLUDED.source
#     """)
#     rows = df.to_dict(orient="records")
#     eng = ctx.engine()
#     with eng.begin() as cx:
#         cx.execute(sql, rows)

# ml/src/etl/base.py


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
    df: pd.DataFrame, engine: Engine, schema: Optional[str] = "public"
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

    with engine.begin() as conn:
        conn.execute(sql, rows)
