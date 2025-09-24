"""
Fetch population / migration data from StatCan WDS and load into demographics.
"""

import os
import pandas as pd
from .. import base, statcan_wds

SNAPSHOT_DIR = "./.debug/statcan_demographics"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

# Example StatCan PID for population estimates
POP_PID = "17100005"  # Adjust to your chosen table
MIG_PID = "17100008"  # Adjust for migration flows


def fetch_demographics():
    # Population
    pop_df = statcan_wds.download_table_csv(POP_PID)
    pop_df.to_csv(f"{SNAPSHOT_DIR}/population_raw.csv", index=False)

    # Migration
    mig_df = statcan_wds.download_table_csv(MIG_PID)
    mig_df.to_csv(f"{SNAPSHOT_DIR}/migration_raw.csv", index=False)

    # TODO: tidy into schema (date, city, population, net_migration, etc.)
    # For now, return concatenated placeholder
    return pop_df, mig_df


def run(ctx):
    pop_df, mig_df = fetch_demographics()
    # Transform to your demographics schema
    tidy = pd.DataFrame(
        {
            "date": pd.to_datetime(pop_df["REF_DATE"], errors="coerce"),
            "city": "Vancouver",  # or from GEO column
            "population": pop_df["VALUE"],
            "net_migration": None,
        }
    )
    base.write_df(tidy, "demographics", ctx)
    return {"rows": len(tidy)}
