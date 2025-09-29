# ml/src/etl/construction_permits.py
import pandas as pd
from sqlalchemy import text
from ml.utils.db import get_engine


def fetch_permits():
    """Stub: Replace with CMHC / municipal permit API"""
    data = [
        {
            "permit_id": "P-2025-001",
            "city": "Kelowna",
            "postal_code": "V1Y2A3",
            "units_approved": 120,
            "date_approved": "2025-06-15",
            "property_type": "Apartment",
        }
    ]
    return pd.DataFrame(data)


def write_permits(df, ctx):
    engine = get_engine(ctx)
    with engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(
                text("""
                INSERT INTO construction_permits
                (permit_id, city, postal_code, units_approved,
                 date_approved, property_type)
                VALUES (:permit_id, :city, :postal_code, :units, :date, :ptype)
                ON CONFLICT (permit_id) DO UPDATE
                SET city=EXCLUDED.city,
                    postal_code=EXCLUDED.postal_code,
                    units_approved=EXCLUDED.units,
                    date_approved=EXCLUDED.date,
                    property_type=EXCLUDED.ptype
            """),
                {
                    "permit_id": row["permit_id"],
                    "city": row["city"],
                    "postal_code": row["postal_code"],
                    "units": row["units_approved"],
                    "date": row["date_approved"],
                    "ptype": row["property_type"],
                },
            )


def run(ctx):
    df = fetch_permits()
    write_permits(df, ctx)
