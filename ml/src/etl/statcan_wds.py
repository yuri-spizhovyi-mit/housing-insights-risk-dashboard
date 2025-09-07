import io
import zipfile
import requests
import pandas as pd

WDS = "https://www150.statcan.gc.ca/t1/wds/rest"


def download_table_csv(pid: str, lang: str = "en") -> pd.DataFrame:
    # Ask WDS for a one-time ZIP URL (set headers to avoid 406)
    r = requests.get(
        f"{WDS}/getFullTableDownloadCSV/{pid}/{lang}",
        headers={"Accept": "application/json", "User-Agent": "hird-etl/0.1"},
        timeout=60,
    )
    r.raise_for_status()
    url = r.json()["object"]

    # Download the ZIP and read the CSV
    z = requests.get(url, timeout=300, headers={"User-Agent": "hird-etl/0.1"})
    z.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(z.content)) as zf:
        name = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
        return pd.read_csv(zf.open(name))
