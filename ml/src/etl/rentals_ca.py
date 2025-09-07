import io, re
import pandas as pd, requests
from bs4 import BeautifulSoup
from .base import Context, write_df, put_raw_bytes
from datetime import date

REPORT_URL = "https://rentals.ca/national-rent-report"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
}


def _find_city_table(html: str) -> pd.DataFrame | None:
    # Try pandas to parse all tables
    try:
        tables = pd.read_html(html)
    except ValueError:
        tables = []

    for t in tables:
        lower = [str(c).lower() for c in t.columns]
        has_city = any("city" in c for c in lower)
        # look for any numeric column that could be rent
        has_numeric = t.select_dtypes("number").shape[1] >= 1
        if has_city and has_numeric:
            return t
    return None


def run(ctx: Context):
    r = requests.get(REPORT_URL, headers=HEADERS, timeout=60)
    r.raise_for_status()
    html = r.text
    put_raw_bytes(
        ctx,
        f"{ctx.s3_raw_prefix}/rentals_ca/{ctx.run_date.isoformat()}/report.html",
        html.encode(),
        "text/html",
    )

    df = _find_city_table(html)
    if df is None:
        print(
            "[WARN] Rentals.ca table not found on report page; skipping rents load for now."
        )
        # Write an empty frame to keep the pipeline green
        empty = pd.DataFrame(
            columns=["city", "date", "bedroom_type", "median_rent", "source"]
        )
        write_df(empty, "rents", ctx)
        return

    # Identify columns
    cols = {str(c).lower(): c for c in df.columns}
    city_col = next((cols[k] for k in cols if "city" in k), None)

    # Pick a numeric rent column (prefer 'Overall' or 'Total' wording if present)
    num_cols = df.select_dtypes("number").columns.tolist()
    preferred = next(
        (
            c
            for c in df.columns
            if str(c).lower() in ("overall", "total", "average", "avg", "all")
        ),
        None,
    )
    rent_col = (
        preferred
        if preferred in df.columns and df[preferred].dtype.kind in "if"
        else (num_cols[0] if num_cols else None)
    )

    if not city_col or not rent_col:
        print(
            f"[WARN] Unexpected Rentals.ca columns: {list(df.columns)}; skipping rents load."
        )
        empty = pd.DataFrame(
            columns=["city", "date", "bedroom_type", "median_rent", "source"]
        )
        write_df(empty, "rents", ctx)
        return

    tidy = df.rename(columns={city_col: "city", rent_col: "median_rent"}).assign(
        date=pd.Timestamp(ctx.run_date).to_period("M").to_timestamp(),
        bedroom_type="overall",
        source="Rentals.ca",
    )
    tidy = tidy[tidy["city"].isin(["Kelowna", "Vancouver", "Toronto"])]

    # keep only rows with numeric rent
    tidy = tidy[pd.to_numeric(tidy["median_rent"], errors="coerce").notna()]
    tidy["median_rent"] = tidy["median_rent"].astype(float)

    write_df(
        tidy[["city", "date", "bedroom_type", "median_rent", "source"]], "rents", ctx
    )
