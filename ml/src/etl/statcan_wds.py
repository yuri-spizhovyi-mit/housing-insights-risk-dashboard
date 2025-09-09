# ml/src/etl/statcan_wds.py
import io
import time
import zipfile

import pandas as pd
import requests

WDS = "https://www150.statcan.gc.ca/t1/wds/rest"

# 1) Use a Session with friendly headers (WDS/CloudFront can be picky)
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "hird-etl/0.1 (+https://github.com/yuri-spizhovyi-mit/housing-insights-risk-dashboard)",
    "Accept": "*/*",
    "Accept-Language": "en",
    "Connection": "keep-alive",
})

def _get_json_with_retry(url: str, tries: int = 3, backoff: float = 1.0):
    last = None
    for i in range(tries):
        r = SESSION.get(url, timeout=60)
        if r.status_code == 406:
            # sometimes 406 with strict accepts; tweak headers and retry
            SESSION.headers.update({"Accept": "application/json, text/plain, */*"})
        if r.ok:
            return r.json()
        last = r
        time.sleep(backoff * (2 ** i))
    last.raise_for_status()

def _get_bytes_with_retry(url: str, tries: int = 3, backoff: float = 1.0) -> bytes:
    last = None
    for i in range(tries):
        r = SESSION.get(url, timeout=300)
        if r.ok:
            return r.content
        last = r
        time.sleep(backoff * (2 ** i))
    last.raise_for_status()

def download_table_csv(pid: str, lang: str = "en") -> pd.DataFrame:
    """
    StatCan WDS 'full table download' flow:
      1) GET JSON descriptor -> { object: <zip_url> }
      2) GET the ZIP, read the CSV inside
    Handles intermittent 406s with retry + relaxed headers.
    """
    meta_url = f"{WDS}/getFullTableDownloadCSV/{pid}/{lang}"
    meta = _get_json_with_retry(meta_url)

    zip_url = meta["object"]
    content = _get_bytes_with_retry(zip_url)

    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        # pick the first CSV
        name = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
        return pd.read_csv(zf.open(name))
