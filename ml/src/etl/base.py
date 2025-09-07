from dataclasses import dataclass
from datetime import date
from urllib.parse import quote_plus
import os, io, re, zipfile, json, pathlib
import pandas as pd
from sqlalchemy import create_engine
import boto3


@dataclass
class Context:
    run_date: date
    s3_endpoint: str = os.getenv("S3_ENDPOINT", "http://localhost:9000")
    s3_access: str = os.getenv("S3_ACCESS_KEY", "minioadmin")
    s3_secret: str = os.getenv("S3_SECRET_KEY", "minioadmin")
    s3_bucket_raw: str = os.getenv("S3_BUCKET_RAW", "hird-raw")
    s3_raw_prefix: str = os.getenv("S3_RAW_PREFIX", "raw")
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: str = os.getenv("DB_PORT", "5432")
    db_user: str = os.getenv("DB_USER", "postgres")
    db_pass: str = os.getenv("DB_PASS", "postgres")
    db_name: str = os.getenv("DB_NAME", "hird")

    @property
    def engine(self):
        pw = quote_plus(self.db_pass)
        url = f"postgresql+psycopg2://{self.db_user}:{pw}@{self.db_host}:{self.db_port}/{self.db_name}"
        return create_engine(url, future=True)

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


def write_df(df: pd.DataFrame, table: str, ctx: Context, if_exists="append"):
    df.columns = [c.lower() for c in df.columns]
    with ctx.engine.begin() as conn:
        df.to_sql(table, conn, if_exists=if_exists, index=False)


def month_floor(d: pd.Series) -> pd.Series:
    # convert to first day of month
    return pd.to_datetime(d.astype(str)).dt.to_period("M").dt.to_timestamp()
