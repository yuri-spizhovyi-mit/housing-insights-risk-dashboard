"""
Fetch building permits data from StatCan WDS and load into construction_permits table.
"""

import os
import uuid
import pandas as pd
from . import base, statcan_wds

SNAPSHOT_DIR = "./.debug/statcan_permits"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

# Example StatCan PID for Building Permits (replace with the correct one)
PERMITS_PID = "34100030"


def fetch_permits():
    df = statcan_wds.download_table_csv(PERMITS_PID)
    df.to_csv(f"{SNAPSHOT_DIR}/permits_raw.csv", index=False)
    return df


def run(ctx):
    df = fetch_permits()

    # TODO: adjust column names depending on StatCan CSV structure.
    tidy = pd.DataFrame(
        {
            # Generate a unique permit_id if not provided
            "permit_id": [str(uuid.uuid4()) for _ in range(len(df))],
            "city": df["GEO"],  # e.g., "Vancouver"
            "postal_code": None,  # StatCan usually doesn’t provide postal codes
            "units_approved": df["VALUE"],
            "date_approved": pd.to_datetime(df["REF_DATE"], errors="coerce"),
            "property_type": df.get("Type of structure"),  # or appropriate column
        }
    )

    tidy = tidy.dropna(subset=["date_approved"])
    tidy.to_csv(f"{SNAPSHOT_DIR}/permits_tidy.csv", index=False)

    tidy = tidy[
        [
            "permit_id",
            "city",
            "postal_code",
            "units_approved",
            "date_approved",
            "property_type",
        ]
    ]

    base.write_df(tidy, "construction_permits", ctx)
    return {"rows": len(tidy)}
