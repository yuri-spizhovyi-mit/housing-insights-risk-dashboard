from ml.src.etl.base import (
    Context,
    write_df,
    write_hpi_upsert,
    put_raw_bytes,
    month_floor,
)
import io
import re
import zipfile
import pandas as pd
import requests
from pathlib import Path

HPI_TOOL_URL = "https://www.crea.ca/housing-market-stats/mls-home-price-index/hpi-tool/"

# --------------------------------------------------------------------------------------
# Discovery
# --------------------------------------------------------------------------------------


def _latest_zip_url() -> str:
    html = requests.get(HPI_TOOL_URL, timeout=60).text
    m = re.search(
        r"https://www\.crea\.ca/files/mls-hpi-data/MLS_HPI_[A-Za-z]+_\d{4}\.zip", html
    )
    if not m:
        raise RuntimeError("CREA HPI ZIP link not found on tool page")
    return m.group(0)


def _has_city_col(df: pd.DataFrame) -> bool:
    cols_lower = {str(c).lower(): c for c in df.columns}
    return any(k in cols_lower for k in ("city", "cma", "region", "area"))


def _read_any_table_from_zip(zb: bytes) -> pd.DataFrame:
    """
    Prefer a CSV/XLSX sheet that contains a city-like column.
    Fallback to the first CSV/XLSX if none found (tidy() will provide a national fallback).
    """
    with zipfile.ZipFile(io.BytesIO(zb)) as z:
        names = z.namelist()

        # 1) Try CSVs with a city-like column
        for n in names:
            if n.lower().endswith(".csv"):
                try:
                    df = pd.read_csv(z.open(n))
                    if _has_city_col(df):
                        return df
                except Exception:
                    pass

        # 2) Try XLSX sheets with a city-like column
        xlsx_names = [n for n in names if n.lower().endswith((".xlsx", ".xls"))]
        for n in xlsx_names:
            try:
                with z.open(n) as f:
                    xl = pd.ExcelFile(f)
                    for s in xl.sheet_names:
                        try:
                            df = xl.parse(s, dtype=object)
                            if _has_city_col(df):
                                return df
                        except Exception:
                            continue
            except Exception:
                continue

        # 3) Fallback: first CSV or first XLSX sheet
        for n in names:
            if n.lower().endswith(".csv"):
                return pd.read_csv(z.open(n))
        if xlsx_names:
            with z.open(xlsx_names[0]) as f:
                xl = pd.ExcelFile(f)
                return xl.parse(xl.sheet_names[0])

    raise RuntimeError("No readable table found in CREA ZIP.")


# --------------------------------------------------------------------------------------
# Tidy
# --------------------------------------------------------------------------------------


def _detect_date_col(df: pd.DataFrame) -> str:
    cols_lower = {str(c).lower(): c for c in df.columns}
    date_col = next(
        (cols_lower[k] for k in ("date", "period", "ref_date") if k in cols_lower), None
    )
    if date_col:
        return date_col
    # fallback: if first column parses as datetime, use it
    if len(df.columns) > 0:
        c0 = df.columns[0]
        try:
            pd.to_datetime(df[c0], errors="raise")
            return c0
        except Exception:
            pass
    raise RuntimeError(f"CREA HPI date column not found. Columns: {list(df.columns)}")


def _tidy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Output columns: city, date (month-floor), index_value (float), measure, source='CREA'
    Strategy:
      1) Prefer city-level rows (long or matrix melted).
      2) If no city-level data exists, fall back to national/composite as city='Canada'.
    """
    # normalize headers
    df = df.rename(columns={c: str(c).strip() for c in df.columns})
    cols_lower = {str(c).lower(): c for c in df.columns}
    date_col = _detect_date_col(df)

    # detect long case (has a city-like column)
    city_col = next(
        (cols_lower[k] for k in ("city", "cma", "region", "area") if k in cols_lower),
        None,
    )
    value_col = next(
        (
            c
            for c in df.columns
            if "benchmark" in str(c).lower() and "price" in str(c).lower()
        ),
        None,
    )
    if not value_col:
        value_col = next(
            (c for c in df.columns if re.search(r"\bhpi\b", str(c).lower())), None
        )

    if city_col:
        if value_col:
            # Case A1: already long with single value column
            tidy = df.rename(
                columns={city_col: "city", date_col: "date", value_col: "index_value"}
            )
            tidy["measure"] = (
                "HPI" if "hpi" in str(value_col).lower() else "benchmark_price"
            )
            tidy["source"] = "CREA"
        else:
            # Case A2: long with multiple value columns → melt
            measure_cols = [c for c in df.columns if c not in (city_col, date_col)]
            long = df.melt(
                id_vars=[city_col, date_col],
                value_vars=measure_cols,
                var_name="measure",
                value_name="index_value",
            )
            tidy = long.rename(columns={city_col: "city", date_col: "date"})
            tidy["source"] = "CREA"
    else:
        # Case B: matrix (cities as columns) OR national-only sheet
        value_cols = [c for c in df.columns if c != date_col]
        non_city_regex = r"(composite|detached|single|two[_\s-]?storey|apartment|benchmark|hpi|sa|nsa)"
        likely_city_cols = [
            c for c in value_cols if not re.search(non_city_regex, str(c), flags=re.I)
        ]

        if likely_city_cols:
            # Melt matrix with city columns
            long = (
                df[[date_col] + likely_city_cols]
                .melt(id_vars=[date_col], var_name="city", value_name="index_value")
                .rename(columns={date_col: "date"})
            )
            long["measure"] = "HPI"
            long["source"] = "CREA"
            tidy = long[["city", "date", "index_value", "measure", "source"]]
        else:
            # No city columns at all → FALLBACK to national/composite as city='Canada'
            # Choose the best available composite column in order of preference
            candidates = [
                # Seasonally adjusted HPI first
                *[
                    c
                    for c in value_cols
                    if re.search(r"^Composite.*HPI.*SA$", str(c), re.I)
                ],
                *[
                    c
                    for c in value_cols
                    if re.search(r"^Composite.*HPI$", str(c), re.I)
                ],
                # Then benchmark price if no HPI
                *[
                    c
                    for c in value_cols
                    if re.search(r"^Composite.*Benchmark.*SA$", str(c), re.I)
                ],
                *[
                    c
                    for c in value_cols
                    if re.search(r"^Composite.*Benchmark", str(c), re.I)
                ],
            ]
            if not candidates:
                # Still nothing ⇒ produce empty; caller will still write_df (no-op)
                tidy = pd.DataFrame(
                    columns=["city", "date", "index_value", "measure", "source"]
                )
            else:
                best = candidates[0]
                measure = "HPI" if "hpi" in str(best).lower() else "benchmark_price"
                tidy = (
                    df[[date_col, best]]
                    .rename(columns={date_col: "date", best: "index_value"})
                    .assign(city="Canada", measure=measure, source="CREA")
                )

    # normalize date & numeric
    if not tidy.empty:
        tidy["date"] = month_floor(tidy["date"])
        tidy = tidy[pd.to_numeric(tidy["index_value"], errors="coerce").notna()]
        tidy["index_value"] = tidy["index_value"].astype(float)
        tidy["city"] = tidy["city"].astype("string").str.strip()
        tidy = tidy.dropna(subset=["city"])

    return tidy


# --------------------------------------------------------------------------------------
# Pipeline
# --------------------------------------------------------------------------------------


def run(ctx):
    print("[DEBUG] CREA ETL starting...")

    # Local ZIP fallback
    local_zip = (
        Path(__file__).resolve().parents[3] / "data" / "MLS_HPI_September_2025_EN.zip"
    )
    if local_zip.exists():
        print(f"[DEBUG] Using local CREA ZIP → {local_zip}")
        with open(local_zip, "rb") as f:
            resp_content = f.read()
    else:
        # fallback to web scraping if no local file found
        url = _latest_zip_url()
        resp = requests.get(url, timeout=180)
        resp.raise_for_status()
        resp_content = resp.content

    # Snapshot raw ZIP
    key = f"{ctx.s3_raw_prefix}/crea/{ctx.run_date.isoformat()}/MLS_HPI_September_2025_EN.zip"
    put_raw_bytes(ctx, key, resp_content, "application/zip")
    print("[DEBUG] Raw CREA ZIP snapshot saved to MinIO")

    # Extract and load the Seasonally Adjusted Monthly workbook
    with zipfile.ZipFile(io.BytesIO(resp_content)) as zf:
        xlsx_name = [n for n in zf.namelist() if "Seasonally Adjusted (M)" in n][0]
        print(f"[DEBUG] Found Excel file → {xlsx_name}")
        with zf.open(xlsx_name) as f:
            df = pd.read_excel(f)

    print("[DEBUG] Raw HPI sheet shape:", df.shape)
    print("[DEBUG] Columns:", list(df.columns)[:10])

    # --- normalize into long form ---
    # Expect columns: 'Date', 'Region', 'Benchmark Price', 'Composite', etc.
    df.columns = [c.strip() for c in df.columns]
    if "Region" in df.columns:
        df = df.rename(columns={"Region": "city", "Date": "date"})
    elif "City" in df.columns:
        df = df.rename(columns={"City": "city", "Date": "date"})
    else:
        # fallback for national-only dataset
        print("[DEBUG] No 'Region' column found — treating as Canada-wide series.")
        df["city"] = "Canada"
        df = df.rename(columns={"Date": "date"})

    ##############################

    # Convert to long format (one row per city/date/measure)
    value_cols = [c for c in df.columns if c not in ["date", "city"]]
    tidy = df.melt(
        id_vars=["city", "date"],
        value_vars=value_cols,
        var_name="measure",
        value_name="index_value",
    )

    # clean
    tidy["date"] = pd.to_datetime(tidy["date"], errors="coerce")
    tidy = tidy.dropna(subset=["date", "index_value"])
    tidy["source"] = "CREA_HPI"

    print("[DEBUG] Tidy shape:", tidy.shape)
    print(tidy.head(5))

    # Write to DB
    write_hpi_upsert(tidy, ctx)
    print("[DEBUG] CREA ETL complete — rows written:", len(tidy))

    return tidy


if __name__ == "__main__":
    from datetime import date
    from ml.src.etl import base  # ✅ add this import

    ctx = base.Context(run_date=date.today())
    run(ctx)
    print("[DEBUG] CREA ETL finished.")
