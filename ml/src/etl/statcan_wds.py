"""StatCan Web Data Service (WDS) data extraction utilities."""

import io
import zipfile
import requests
import pandas as pd

WDS = "https://www150.statcan.gc.ca/t1/wds/rest"


def download_table_csv(pid: str) -> pd.DataFrame:
    """Download and extract CSV data from StatCan WDS by product ID.

    Args:
        pid: StatCan product identifier

    Returns:
        DataFrame containing the extracted CSV data
    """
    # 1) ask WDS for a one-time ZIP URL
    r = requests.get(f"{WDS}/getFullTableDownloadCSV/{pid}/en", timeout=60)
    r.raise_for_status()
    url = r.json()["object"]
    # 2) download the ZIP
    z = requests.get(url, timeout=300)
    z.raise_for_status()
    # 3) read the single CSV inside
    with zipfile.ZipFile(io.BytesIO(z.content)) as zf:
        name = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
        df = pd.read_csv(zf.open(name))
    return df
