import io
import zipfile
import requests
import pandas as pd

WDS = "https://www150.statcan.gc.ca/t1/wds/rest"
CODR = "https://proxy-apicast.statcan.gc.ca/odc-tbl/api/v1"


def _wds_full_table_url(pid: str, lang: str = "en") -> str:
    """Ask WDS for a one-time ZIP URL of the full table CSV."""
    r = requests.get(
        f"{WDS}/getFullTableDownloadCSV/{pid}/{lang}",
        headers={"Accept": "application/json"},
        timeout=60,
    )
    r.raise_for_status()
    j = r.json()
    if not j or "object" not in j:
        raise RuntimeError(f"WDS response missing object for pid={pid}: {j}")
    return j["object"]


def _download_wds_csv_zip(url: str) -> pd.DataFrame:
    z = requests.get(url, timeout=300)
    z.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(z.content)) as zf:
        name = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
        return pd.read_csv(zf.open(name))


def _download_codr_csv(pid: str, lang: str = "en") -> pd.DataFrame:
    # CODR CSV stream (no ZIP). contentType=CSV ensures CSV body.
    # Example: /odc-tbl/api/v1/en/1810000401?contentType=CSV
    url = f"{CODR}/{lang}/{pid}?contentType=CSV"
    r = requests.get(url, headers={"Accept": "text/csv"}, timeout=120)
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.text))


def download_table_csv(pid: str, lang: str = "en") -> pd.DataFrame:
    """Try WDS (ZIP CSV). If 406/other issues, fall back to CODR (CSV)."""
    try:
        url = _wds_full_table_url(pid, lang)
        return _download_wds_csv_zip(url)
    except requests.HTTPError as e:
        # Common: 406 Not Acceptable -> fall back to CODR
        if e.response is not None and e.response.status_code == 406:
            return _download_codr_csv(pid, lang)
        raise
    except Exception:
        # Any unexpected failure -> try CODR as a fallback
        return _download_codr_csv(pid, lang)
