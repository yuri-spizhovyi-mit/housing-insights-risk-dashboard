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
        # Each adapter normally calls write_df.
        # Instead, patch write_df to just return df.
        import ml.src.etl.base as base

        orig_write_df = base.write_df
        dfs = {}

        def fake_write_df(df: pd.DataFrame, table: str, ctx, if_exists="append"):
            dfs[table] = df

        base.write_df = fake_write_df
        fn(ctx)
        return dfs
    finally:
        base.write_df = orig_write_df


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
