# ml/src/etl/utils.py
import re
import unicodedata
from typing import Optional

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
    # drop province tail after comma
    s = re.sub(rf",\s*({_PROVINCES})\b", "", s)
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
