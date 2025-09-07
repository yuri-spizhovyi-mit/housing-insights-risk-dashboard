import io, re, zipfile, datetime as dt
import pandas as pd, requests
from .base import Context, write_df, put_raw_bytes, month_floor

HPI_TOOL_URL = "https://www.crea.ca/housing-market-stats/mls-home-price-index/hpi-tool/"


def _latest_zip_url() -> str:
    html = requests.get(HPI_TOOL_URL, timeout=60).text
    m = re.search(
        r"https://www\.crea\.ca/files/mls-hpi-data/MLS_HPI_[A-Za-z]+_\d{4}\.zip", html
    )
    if not m:
        raise RuntimeError("CREA HPI ZIP link not found on tool page")
    return m.group(0)


def _read_any_table_from_zip(zb: bytes) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(zb)) as z:
        names = z.namelist()
        # prefer CSV; else first xlsx
        csvs = [n for n in names if n.lower().endswith(".csv")]
        if csvs:
            return pd.read_csv(z.open(csvs[0]))
        xlsx = next(n for n in names if n.lower().endswith((".xlsx", ".xls")))
        with z.open(xlsx) as f:
            xl = pd.ExcelFile(f)
            # try to find a likely sheet; else first
            sheet = next(
                (
                    s
                    for s in xl.sheet_names
                    if "benchmark" in s.lower()
                    or "composite" in s.lower()
                    or "hpi" in s.lower()
                ),
                xl.sheet_names[0],
            )
            return xl.parse(sheet)


def _tidy(df: pd.DataFrame) -> pd.DataFrame:
    # Normalize column names (strip spaces)
    df = df.rename(columns={c: c.strip() for c in df.columns})
    cols_lower = {c.lower(): c for c in df.columns}

    # Identify the date column
    date_col = next(
        (cols_lower[k] for k in cols_lower if k in ("date", "period", "ref_date")), None
    )
    if date_col is None:
        raise RuntimeError(
            f"CREA HPI date column not found. Columns seen: {list(df.columns)}"
        )

    # Case A: long/tidy already (has City column + value column)
    city_col = next(
        (cols_lower[k] for k in cols_lower if k in ("city", "cma", "region", "area")),
        None,
    )
    price_col = next(
        (c for c in df.columns if "benchmark" in c.lower() and "price" in c.lower()),
        None,
    )
    hpi_single_col = next(
        (
            c
            for c in df.columns
            if re.search(r"\bhpi\b", c.lower()) and "composite" in c.lower()
        ),
        None,
    )

    if city_col and (price_col or hpi_single_col):
        # already has a single value column
        if price_col:
            tidy = df.rename(
                columns={city_col: "city", date_col: "date", price_col: "index_value"}
            ).assign(measure="benchmark_price", source="CREA")
        else:
            tidy = df.rename(
                columns={
                    city_col: "city",
                    date_col: "date",
                    hpi_single_col: "index_value",
                }
            ).assign(measure="hpi_index", source="CREA")

    else:
        # Case B: wide format like: Date, Composite_HPI_SA, Detached_HPI_SA, ...
        # Melt non-date columns into long form
        value_cols = [c for c in df.columns if c != date_col]
        long = df.melt(
            id_vars=[date_col],
            value_vars=value_cols,
            var_name="series",
            value_name="index_value",
        )
        long = long.rename(columns={date_col: "date"})
        # There is no per-city in this wide set; it's usually a given geography (Composite).
        # We’ll set city=None or "Canada" only if explicitly national; prefer None.
        long["city"] = None

        # Map measure based on series name
        def _measure_from_series(s: str) -> str:
            s = s.lower()
            if "benchmark" in s and "price" in s:
                return "benchmark_price"
            if "hpi" in s:
                return "hpi_index"
            return "value"

        long["measure"] = long["series"].apply(_measure_from_series)
        long["source"] = "CREA"
        tidy = long[["city", "date", "index_value", "measure", "source"]]

    # Normalize date to month start
    tidy["date"] = month_floor(tidy["date"])
    # If we have city names, filter to focus cities (optional)
    if "city" in tidy.columns and tidy["city"].notna().any():
        tidy = tidy[
            tidy["city"].isin(["Kelowna", "Vancouver", "Toronto"]) | tidy["city"].isna()
        ]

    # Keep only rows with a numeric index_value
    tidy = tidy[pd.to_numeric(tidy["index_value"], errors="coerce").notna()]
    tidy["index_value"] = tidy["index_value"].astype(float)
    return tidy


def run(ctx: Context):
    url = _latest_zip_url()
    resp = requests.get(url, timeout=180)
    resp.raise_for_status()
    key = (
        f"{ctx.s3_raw_prefix}/crea/{ctx.run_date.isoformat()}/{url.rsplit('/', 1)[-1]}"
    )
    put_raw_bytes(ctx, key, resp.content, "application/zip")
    raw_df = _read_any_table_from_zip(resp.content)
    tidy = _tidy(raw_df)
    write_df(tidy, "house_price_index", ctx)
