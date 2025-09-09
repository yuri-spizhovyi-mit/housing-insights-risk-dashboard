import io, re, zipfile
import pandas as pd
import requests

WDS = "https://www150.statcan.gc.ca/t1/wds/rest"

SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": "hird-etl/0.1 (+https://github.com/yuri-spizhovyi-mit/housing-insights-risk-dashboard)",
        "Accept": "application/json, */*",
    }
)


def _normalize_pid(pid_like: str) -> str:
    """
    Accepts forms like:
      - '34-10-0145-01'  -> '34100145'
      - '34100145'       -> '34100145'
      - '3410014501'     -> '34100145'  (drop trailing '01')
    Returns the 8-digit ProductId required by WDS and CSV endpoints.
    """
    digits = re.sub(r"\D", "", str(pid_like))
    if len(digits) >= 8:
        return digits[:8]
    raise ValueError(f"Invalid StatCan PID/table number: {pid_like}")


def download_table_csv(pid_like: str, lang: str = "en") -> pd.DataFrame:
    """
    Primary: WDS 'full table' endpoint returning the CSV ZIP URL.
    Fallback: direct CSV ZIP (…/n1/tbl/csv/{pid}-eng.zip) if WDS fails.
    """
    pid = _normalize_pid(pid_like)
    wds_url = f"{WDS}/getFullTableDownloadCSV/{pid}/{lang}"

    try:
        r = SESSION.get(wds_url, timeout=60)
        r.raise_for_status()
        zip_url = r.json()["object"]  # e.g. .../n1/tbl/csv/{pid}-eng.zip
    except Exception:
        suffix = "eng" if lang == "en" else "fra"
        zip_url = f"https://www150.statcan.gc.ca/n1/tbl/csv/{pid}-{suffix}.zip"

    r = SESSION.get(zip_url, timeout=180)
    r.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        name = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
        return pd.read_csv(zf.open(name))
