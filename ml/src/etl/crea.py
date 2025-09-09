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


def run(ctx: Context):
    # 1) discover & download latest CREA ZIP
    url = _latest_zip_url()
    resp = requests.get(url, timeout=180)
    resp.raise_for_status()

    # 2) snapshot raw ZIP to MinIO
    key = (
        f"{ctx.s3_raw_prefix}/crea/{ctx.run_date.isoformat()}/{url.rsplit('/', 1)[-1]}"
    )
    put_raw_bytes(ctx, key, resp.content, "application/zip")

    # 3) parse + tidy (with fallback to Canada)
    raw_df = _read_any_table_from_zip(resp.content)
    tidy = _tidy(raw_df)

    # 4) write to Postgres (even if empty, so tests capture the intent)
    write_hpi_upsert(tidy, ctx)
