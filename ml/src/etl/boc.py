# ml/src/etl/boc.py
from typing import Dict, Iterable, Optional
import os
import time

import pandas as pd
import requests

from . import base

DEFAULT_SOURCE = "BoC"
# Correct Valet endpoint base: /valet/observations/{seriesNames}/json
VALET_BASE = "https://www.bankofcanada.ca/valet/observations"


def _empty_tidy() -> pd.DataFrame:
    """Return an empty tidy frame with the expected columns."""
    return pd.DataFrame(columns=["city", "date", "metric", "value", "source"])


def fetch_series_valet(
    series_ids: Iterable[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    retries: int = 3,
    backoff: float = 1.5,
    timeout: int = 20,
) -> pd.DataFrame:
    """
    Fetch one or more BoC Valet series and return a tidy DataFrame with columns:
    [city, date, metric, value, source]

    - city is "Canada" for all macro series.
    - metric is the raw series id (aliasing applied later).
    """
    series_ids = list(series_ids or [])
    if not series_ids:
        return _empty_tidy()

    series_names = ",".join(series_ids)
    url = f"{VALET_BASE}/{series_names}/json"

    params: Dict[str, str] = {}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date

    last_exc: Optional[Exception] = None
    for attempt in range(retries):
        try:
            r = requests.get(
                url,
                params=params,
                headers={"Accept": "application/json"},
                timeout=timeout,
            )
            r.raise_for_status()
            payload = r.json()
            observations = payload.get("observations", [])

            rows = []
            for o in observations:
                d = o.get("d")
                if not d:
                    continue
                for sid in series_ids:
                    cell = o.get(sid)
                    if not cell:
                        continue
                    v = cell.get("v")
                    if v is None:
                        continue
                    try:
                        val = float(v)
                    except Exception:
                        continue
                    rows.append(
                        {
                            "city": "Canada",
                            "date": d,
                            "metric": sid,  # alias applied in load_boc_series
                            "value": val,
                            "source": DEFAULT_SOURCE,
                        }
                    )

            if not rows:
                return _empty_tidy()
            return pd.DataFrame(rows)

        except Exception as e:
            last_exc = e
            if attempt == retries - 1:
                raise
            time.sleep(backoff * (attempt + 1))

    # Should never reach here (we either returned or raised), but keep mypy happy
    if last_exc:
        raise last_exc
    return _empty_tidy()


def load_boc_series(
    series_ids: Iterable[str],
    engine,
    schema: str = "public",
    alias: Optional[Dict[str, str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    Fetch BoC series, apply aliasing, and UPSERT into public.metrics via write_metrics_upsert.
    Returns the tidy DataFrame that was written.
    """
    df = fetch_series_valet(series_ids, start_date=start_date, end_date=end_date)
    if df is None or df.empty:
        return _empty_tidy()

    # Apply alias mapping and default "BoC_<sid>" if alias missing
    if alias:
        df["metric"] = df["metric"].map(lambda sid: alias.get(sid, f"BoC_{sid}"))
    else:
        df["metric"] = df["metric"].map(lambda sid: f"BoC_{sid}")

    # Return tidy without writing; caller decides how to persist
    tidy = df[["city", "date", "metric", "value", "source"]].copy()
    return tidy


def run(ctx: base.Context):
    """
    Production run: fetch BoC Valet series and upsert into public.metrics via write_df.
    Uses optional START_DATE / END_DATE (YYYY-MM-DD) from env for backfills.
    """
    series_ids = ["V39079"]
    alias = {"V39079": "BoC_OvernightRate"}

    start_date = os.getenv("START_DATE")
    end_date = os.getenv("END_DATE")

    df = load_boc_series(
        series_ids=series_ids,
        engine=ctx.engine,
        schema="public",
        alias=alias,
        start_date=start_date,
        end_date=end_date,
    )

    # Write using generic writer so tests can intercept table "metrics"
    base.write_df(df, "metrics", ctx)
    # Optional snapshot to raw
    if df is not None and not df.empty:
        put = getattr(base, "put_raw_bytes", None)
        if callable(put):
            path = f"{ctx.s3_raw_prefix}/boc/{ctx.run_date.isoformat()}/V39079.tidy.csv"
            put(ctx, path, df.to_csv(index=False).encode("utf-8"), "text/csv")
    print(f"[DEBUG] Wrote {len(df)} rows to metrics from BoC")


if __name__ == "__main__":
    from datetime import date

    ctx = base.Context(run_date=date.today())
    run(ctx)
    print("[DEBUG] BoC ETL finished.")
