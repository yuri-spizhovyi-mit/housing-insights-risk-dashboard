"""
Fetch building permits data from StatCan WDS and load into construction_permits.
"""

import os
import pandas as pd
from . import base, statcan_wds

SNAPSHOT_DIR = "./.debug/statcan_permits"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

PERMITS_PID = "34100030"  # Example: Building permits by type and region


def fetch_permits():
    df = statcan_wds.download_table_csv(PERMITS_PID)
    df.to_csv(f"{SNAPSHOT_DIR}/permits_raw.csv", index=False)
    return df


def run(ctx):
    df = fetch_permits()
    tidy = pd.DataFrame(
        {
            "permit_id": df.index.astype(str),
            "city": df["GEO"],
            "postal_code": None,  # Not in StatCan; keep null
            "units_approved": df["VALUE"],
            "date_approved": pd.to_datetime(df["REF_DATE"], errors="coerce"),
            "property_type": df["Type of structure"],
        }
    )
    base.write_df(tidy, "construction_permits", ctx)
    return {"rows": len(tidy)}
