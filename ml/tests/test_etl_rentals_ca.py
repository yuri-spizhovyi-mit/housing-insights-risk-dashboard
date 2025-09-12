from datetime import date
from ml.src.etl import rentals_ca, base

def test_rentals_upsert(tmp_path):
    ctx = base.Context(
        run_date=date(2025, 9, 12),
        params={"rentals_ca_path": "tests/data/rentals_sample.csv"}
    )
    df = rentals_ca.run(ctx)
    assert not df.empty
    assert set(df.columns) == {"city","date","bedroom_type","median_rent","source"}

    # optional: query back from DB
    conn = base.get_engine(ctx).connect()
    rows = conn.execute("select * from public.rents where source='Rentals.ca'").fetchall()
    assert rows
