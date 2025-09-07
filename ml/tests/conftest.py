# ml/tests/conftest.py
import pytest
import pandas as pd


@pytest.fixture(autouse=True)
def patch_io(monkeypatch):
    # no-op for S3 snapshots (MinIO)
    def fake_put_raw_bytes(ctx, key, blob, content_type="application/octet-stream"):
        return f"s3://fake/{key}"

    # capture writes instead of hitting Postgres
    captured = {}

    def fake_write_df(df: pd.DataFrame, table: str, ctx, if_exists="append"):
        captured[table] = df

    import ml.src.etl.base as base

    monkeypatch.setattr(base, "put_raw_bytes", fake_put_raw_bytes)
    monkeypatch.setattr(base, "write_df", fake_write_df)

    return captured
