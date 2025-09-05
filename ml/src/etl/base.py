from dataclasses import dataclass
from datetime import date
import os
import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus


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


def write_df(df: pd.DataFrame, table: str, ctx: Context, if_exists: str = "append"):
    df.columns = [c.lower() for c in df.columns]
    with ctx.engine.begin() as conn:
        df.to_sql(table, conn, if_exists=if_exists, index=False)
