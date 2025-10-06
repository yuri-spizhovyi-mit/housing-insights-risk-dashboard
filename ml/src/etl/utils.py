# ml/src/etl/utils.py
import re
import unicodedata
from typing import Optional
from pathlib import Path
from datetime import datetime, timezone


def save_snapshot(text: str, out_dir: str, basename: str, ext: str = "html") -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    p = Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)
    path = p / f"{basename}.{ts}.{ext}"
    path.write_text(text, encoding="utf-8")
    return str(path)


def is_kelowna_city(name: str | None) -> bool:
    if not name:
        return False
    n = name.strip().lower()
    return n in {"kelowna", "city of kelowna"}


_CANON = {
    "kelowna": "Kelowna",
    "vancouver": "Vancouver",
    "toronto": "Toronto",
    "canada": "Canada",
}

_PROVINCES = (
    "british columbia|ontario|alberta|saskatchewan|manitoba|quebec|nova scotia|"
    "new brunswick|newfoundland and labrador|prince edward island|yukon|"
    "northwest territories|nunavut"
)

_SUFFIXES = r"(cma|ca|census metropolitan area|census agglomeration)"


def _strip_accents(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")


def _clean(s: str) -> str:
    s = _strip_accents(str(s)).lower().strip()
    s = re.sub(r"\s+", " ", s)
    # drop common suffixes like " (CMA)" / " census metropolitan area"
    s = re.sub(rf"\s*\(({_SUFFIXES})\)$", "", s)
    s = re.sub(rf"\s*({_SUFFIXES})$", "", s)
    # drop province tail after comma (full names)
    s = re.sub(rf",\s*({_PROVINCES})\b", "", s)
    # NEW: drop short province abbreviations (BC, Ont, Alb, etc.)
    s = re.sub(r",\s*\b(bc|ont|ab|mb|qc|ns|nb|nl|pe|yt|nt|nu|c\-b)\b\.?", "", s)
    return s.strip()


def canonical_geo(raw: Optional[str]) -> Optional[str]:
    """
    Map messy StatCan/CMHC GEO labels into {Kelowna, Vancouver, Toronto, Canada}.
    Returns None if not one of the target geographies (you can extend later).
    """
    if raw is None:
        return None
    s = _clean(raw)

    # direct canonical
    if s in _CANON:
        return _CANON[s]

    # synonyms / contained forms
    if "kelowna" in s:
        return "Kelowna"
    if "vancouver" in s or "metro vancouver" in s:
        return "Vancouver"
    if "toronto" in s or "greater toronto" in s:
        return "Toronto"
    if "canada" in s:
        return "Canada"

    # optionally keep provinces; for now return None so we focus on CMAs + Canada
    return None
