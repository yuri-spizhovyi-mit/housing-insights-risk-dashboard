"""
Fetch demographic data (population, migration, age distribution, income)
from StatCan and load into demographics table.
"""

import os
import pandas as pd
from . import base, statcan_wds

SNAPSHOT_DIR = "./.debug/statcan_demographics"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

# Example StatCan PIDs (replace with the right ones for your project)
POP_PID = "17100005"  # Population estimates
MIG_PID = "17100008"  # Net migration
AGE_PID = "17100009"  # Age distribution
INC_PID = "36100434"  # Disposable income


def fetch_demographics():
    dfs = {}
    for name, pid in [
        ("population", POP_PID),
        ("migration", MIG_PID),
        ("age", AGE_PID),
        ("income", INC_PID),
    ]:
        df = statcan_wds.download_table_csv(pid)
        df.to_csv(f"{SNAPSHOT_DIR}/{name}_raw.csv", index=False)
        dfs[name] = df
    return dfs


def run(ctx):
    dfs = fetch_demographics()

    # TODO: parse StatCan CSVs properly. For now, stub with demo rows:
    tidy = pd.DataFrame(
        {
            "date": pd.to_datetime(dfs["population"]["REF_DATE"], errors="coerce"),
            "city": dfs["population"]["GEO"],  # or filter for "Vancouver"
            "population": dfs["population"]["VALUE"],
            "net_migration": dfs["migration"]["VALUE"],
            "age_distribution_25_34_perc": dfs["age"]["VALUE"],
            "avg_disposable_income": dfs["income"]["VALUE"],
        }
    )

    tidy = tidy.dropna(subset=["date"])
    tidy.to_csv(f"{SNAPSHOT_DIR}/demographics_tidy.csv", index=False)

    # Only keep the schema columns
    tidy = tidy[
        [
            "date",
            "city",
            "population",
            "net_migration",
            "age_distribution_25_34_perc",
            "avg_disposable_income",
        ]
    ]

    base.write_df(tidy, "demographics", ctx)
    return {"rows": len(tidy)}
