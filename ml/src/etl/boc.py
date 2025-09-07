import pandas as pd
import requests
from .base import Context, write_df, put_raw_bytes


def _get_series(series: str, start: str = "2000-01-01") -> pd.DataFrame:
    url = f"https://www.bankofcanada.ca/valet/observations/{series}/json?start_date={start}"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    j = r.json()
    obs = j["observations"]
    records = []
    for o in obs:
        d = o["d"]
        v = o.get(series, {}).get("v")
        if v is not None:
            records.append({"date": d, "value": float(v)})
    return pd.DataFrame.from_records(records)


def run(ctx: Context):
    # Target for the overnight rate (policy rate)
    df = _get_series("V39079", "2000-01-01")  # monthly series
    put_raw_bytes(
        ctx,
        f"{ctx.s3_raw_prefix}/boc/{ctx.run_date.isoformat()}/V39079.json",
        df.to_json(orient="records").encode(),
        "application/json",
    )

    df["date"] = pd.to_datetime(df["date"]).dt.to_period("M").dt.to_timestamp()
    df = df.assign(city="Canada", metric="policy_rate_overnight", source="BoC")
    out = df[["city", "date", "metric", "value", "source"]]
    write_df(out, "metrics", ctx)
