import re
import unicodedata

CANON = {
    "kelowna": "Kelowna",
    "vancouver": "Vancouver",
    "toronto": "Toronto",
    "canada": "Canada",
}

SYNONYMS = {
    "greater toronto area": "toronto",
    "toronto cma": "toronto",
    "toronto (cma)": "toronto",
    "toronto, ontario": "toronto",
    "metro vancouver": "vancouver",
    "vancouver (cma)": "vancouver",
    "vancouver, british columbia": "vancouver",
    "vancouver, b.c.": "vancouver",
    "kelowna (cma)": "kelowna",
    "kelowna, british columbia": "kelowna",
}

PROVINCES = {
    "british columbia",
    "ontario",
    "alberta",
    "saskatchewan",
    "manitoba",
    "quebec",
    "nova scotia",
    "new brunswick",
    "newfoundland and labrador",
    "prince edward island",
    "yukon",
    "northwest territories",
    "nunavut",
}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode("ascii")
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    # remove common suffixes
    s = re.sub(r"\s*\((cma|ca)\)$", "", s)
    s = re.sub(r"\s*census (metropolitan area|agglomeration)$", "", s)
    # drop province tail after comma
    s = re.sub(
        r",\s*(british columbia|ontario|alberta|saskatchewan|manitoba|quebec|nova scotia|new brunswick|newfoundland and labrador|prince edward island|yukon|northwest territories|nunavut)\b",
        "",
        s,
    )
    s = s.strip()
    return s


def canonical_geo(
    geo: str, dguid: str | None = None, code_map: dict[str, str] | None = None
) -> str | None:
    # 1) prefer codes if provided
    if dguid and code_map and dguid in code_map:
        return code_map[dguid]

    g = _norm(geo)
    if g in SYNONYMS:
        g = SYNONYMS[g]
    if g in CANON:
        return CANON[g]  # Kelowna/Vancouver/Toronto/Canada
    if g in PROVINCES:
        return g.title()  # Keep provinces if you want them
    if "canada" in g:
        return "Canada"  # any variant including 'canada'
    return None  # not in our list
