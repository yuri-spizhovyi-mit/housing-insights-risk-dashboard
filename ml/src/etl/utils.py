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


def canonical_geo(raw: str) -> str | None:
    if not raw:
        return None
    s = str(raw).lower().strip()
    s = s.replace("cma", "").replace("ca", "")
    s = s.replace(", british columbia", "").replace(", ontario", "")
    s = s.replace(" census metropolitan area", "").replace(" census agglomeration", "")
    s = s.strip()

    if "kelowna" in s:
        return "Kelowna"
    if "vancouver" in s:
        return "Vancouver"
    if "toronto" in s:
        return "Toronto"
    if "canada" in s:
        return "Canada"
    return None


# not in our list
