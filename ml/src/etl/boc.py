# boc.py
from typing import Dict, Iterable, Optional
import pandas as pd
import requests

from . import base

DEFAULT_SOURCE = "BoC"

VALET_URL = "https://www.bankofcanada.ca/valet/series/observations"


def fetch_series_valet(
    series: Iterable[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    fmt: str = "json",
) -> Dict[str, pd.DataFrame]:
    """
    Fetch one or more BoC series via Valet API.
    series: e.g., ["V39079", "V122515"] (policy rate, CPI, etc.)
    Dates: 'YYYY-MM-DD' (optional; Valet supports filters)
    Returns dict series_id -> DataFrame(date, value)
    """
    joined = ",".join(series)
    params = {"series": joined}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date

    # Request JSON for robust parsing
    r = requests.get(VALET_URL, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    # JSON shape: {"observations": [{"d":"YYYY-MM-DD","V39079":"5.00", ...}, ...]}
    obs = data.get("observations", [])
    frames = {}
    for sid in series:
        rows = []
        for row in obs:
            d = row.get("d")
            v = row.get(sid)
            if d is None or v is None:  # some dates may not have all series
                continue
            try:
                val = float(v)
            except (TypeError, ValueError):
                continue
            rows.append({"date": pd.to_datetime(d).date(), "value": val})
        frames[sid] = pd.DataFrame(rows)
    return frames


def load_boc_series(
    series_ids: Iterable[str],
    engine,
    schema: str = "public",
    alias: Optional[Dict[str, str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    Fetch BoC Valet series, normalize to metrics, and UPSERT.
    alias maps raw id -> metric label (else 'BoC_<id>').
    """
    frames = fetch_series_valet(series_ids, start_date, end_date)
    out_frames = []
    for sid, df in frames.items():
        if df.empty:
            continue
        metric = (alias or {}).get(sid, f"BoC_{sid}")
        tidy = pd.DataFrame(
            {
                "metric": metric,
                "city": "Canada",
                "date": df["date"],
                "value": df["value"],
                "source": DEFAULT_SOURCE,
            }
        )
        base.write_metrics_upsert(tidy, engine, schema=schema)
        out_frames.append(tidy)
    return pd.concat(out_frames, ignore_index=True) if out_frames else pd.DataFrame()


def run(ctx):
    """
    Production run: fetch BoC Valet series and upsert into public.metrics.
    Uses optional START_DATE / END_DATE (YYYY-MM-DD) from env for backfills.
    """
    import os

    series_ids = ["V39079"]
    alias = {"V39079": "BoC_OvernightRate"}

    # Optional backfill window via env
    start_date = os.getenv("START_DATE")  # e.g., "2010-01-01"
    end_date = os.getenv("END_DATE")  # e.g., "2025-09-01"

    df = load_boc_series(
        series_ids=series_ids,
        engine=ctx.engine,  # uses your SQLAlchemy engine property
        schema="public",
        alias=alias,
        start_date=start_date,
        end_date=end_date,
    )

    # Optional: snapshot the tidy frame to raw/ for auditing (CSV)
    if df is not None and not df.empty:
        path = f"{ctx.s3_raw_prefix}/boc/{ctx.run_date.isoformat()}/V39079.tidy.csv"
        put = getattr(base, "put_raw_bytes", None)
        if callable(put):
            put(ctx, path, df.to_csv(index=False).encode("utf-8"), "text/csv")

    return df
