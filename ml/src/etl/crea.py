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
        # heuristics: prefer CSVs first, else first XLSX sheet with "Benchmark"
        names = z.namelist()
        # try CSV
        csvs = [n for n in names if n.lower().endswith(".csv")]
        if csvs:
            df = pd.read_csv(z.open(csvs[0]))
        else:
            xlsx = next(n for n in names if n.lower().endswith((".xlsx", ".xls")))
            with z.open(xlsx) as f:
                xl = pd.ExcelFile(f)
                # pick sheet that likely holds benchmark prices
                sheet = next(
                    (
                        s
                        for s in xl.sheet_names
                        if "benchmark" in s.lower() or "composite" in s.lower()
                    ),
                    xl.sheet_names[0],
                )
                df = xl.parse(sheet)
    return df


def _tidy(df: pd.DataFrame) -> pd.DataFrame:
    cols = {c.strip(): c for c in df.columns}
    # loose mappings to common CREA column names
    mapping = {
        "City": next((c for c in cols if c.lower() == "city"), None),
        "Date": next(
            (c for c in cols if c.lower() in ("date", "period", "ref_date")), None
        ),
        "BenchmarkPrice": next(
            (c for c in cols if "benchmark" in c.lower() and "price" in c.lower()), None
        ),
        "Index": next(
            (c for c in cols if c.lower() in ("hpi", "index", "composite index")), None
        ),
    }
    if (
        not mapping["City"]
        or not mapping["Date"]
        or not (mapping["BenchmarkPrice"] or mapping["Index"])
    ):
        # Show columns to adjust quickly if CREA changes schema
        raise RuntimeError(
            f"CREA HPI columns changed. Columns seen: {list(df.columns)}"
        )

    if mapping["BenchmarkPrice"]:
        tidy = df.rename(
            columns={
                mapping["City"]: "city",
                mapping["Date"]: "date",
                mapping["BenchmarkPrice"]: "index_value",
            }
        )
        tidy["measure"] = "benchmark_price"
    else:
        tidy = df.rename(
            columns={
                mapping["City"]: "city",
                mapping["Date"]: "date",
                mapping["Index"]: "index_value",
            }
        )
        tidy["measure"] = "hpi_index"

    tidy["source"] = "CREA"
    tidy["date"] = month_floor(tidy["date"])
    tidy = tidy[["city", "date", "index_value", "measure", "source"]].dropna()
    # optional focus
    tidy = tidy[tidy["city"].isin(["Kelowna", "Vancouver", "Toronto"])]
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
