import datetime as dt
import pandas as pd
import pytest

from ml.src.etl import crea, cmhc, statcan, boc, rentals_ca
from ml.src.etl.base import Context


@pytest.fixture(scope="module")
def ctx():
    # Test context with fake Postgres/MinIO creds (not used in dry-run)
    return Context(run_date=dt.date.today())


def _safe_run(fn, ctx):
    """Run adapter, return DataFrame if possible."""
    try:
        # Each adapter normally calls write_df or write_hpi_upsert.
        # Instead, patch these to just return df.
        import ml.src.etl.base as base
        import ml.src.etl.crea as crea

        orig_write_df = base.write_df
        orig_write_hpi_upsert = base.write_hpi_upsert
        orig_crea_write_hpi_upsert = crea.write_hpi_upsert
        dfs = {}

        def fake_write_df(df: pd.DataFrame, table: str, ctx, if_exists="append"):
            dfs[table] = df

        def fake_write_hpi_upsert(df: pd.DataFrame, ctx):
            dfs["house_price_index"] = df

        base.write_df = fake_write_df
        base.write_hpi_upsert = fake_write_hpi_upsert
        crea.write_hpi_upsert = fake_write_hpi_upsert
        fn(ctx)
        return dfs
    finally:
        base.write_df = orig_write_df
        base.write_hpi_upsert = orig_write_hpi_upsert
        crea.write_hpi_upsert = orig_crea_write_hpi_upsert


def test_crea(ctx):
    dfs = _safe_run(crea.run, ctx)
    assert "house_price_index" in dfs
    assert not dfs["house_price_index"].empty


def test_cmhc(ctx):
    dfs = _safe_run(cmhc.run, ctx)
    assert "metrics" in dfs
    assert not dfs["metrics"].empty


def test_statcan(ctx):
    dfs = _safe_run(statcan.run, ctx)
    assert "metrics" in dfs
    assert not dfs["metrics"].empty


def test_boc(ctx):
    dfs = _safe_run(boc.run, ctx)
    assert "metrics" in dfs
    assert not dfs["metrics"].empty


def test_rentals(ctx):
    dfs = _safe_run(rentals_ca.run, ctx)
    assert "rents" in dfs
    assert not dfs["rents"].empty
