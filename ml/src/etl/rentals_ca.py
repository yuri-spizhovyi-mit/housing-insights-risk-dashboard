import pandas as pd
import requests
from bs4 import BeautifulSoup
from .base import Context, write_df, put_raw_bytes

REPORT_URL = "https://rentals.ca/national-rent-report"

def run(ctx: Context):
    html = requests.get(REPORT_URL, timeout=60).text
    put_raw_bytes(ctx, f"{ctx.s3_raw_prefix}/rentals_ca/{ctx.run_date.isoformat()}/report.html",
                  html.encode(), "text/html")
    soup = BeautifulSoup(html, "html.parser")
    # find the first table with city averages
    table = soup.find("table")
    if table is None:
        raise RuntimeError("Rentals.ca table not found on report page")
    df = pd.read_html(str(table))[0]
    # Try common headers
    # Expected columns often include City / Total (or Overall) / 1B / 2B...
    cols = {c.lower(): c for c in df.columns}
    city_col = next((cols[k] for k in cols if "city" in k), None)
    overall_col = next((cols[k] for k in cols if k in ("total","overall","avg","average")), None)
    if not city_col or not overall_col:
        raise RuntimeError(f"Unexpected Rentals.ca columns: {list(df.columns)}")

    tidy = (df.rename(columns={city_col:"city", overall_col:"median_rent"})
              .assign(date=pd.Timestamp(ctx.run_date).to_period("M").to_timestamp(),
                      bedroom_type="overall", source="Rentals.ca"))
    tidy = tidy[tidy["city"].isin(["Kelowna","Vancouver","Toronto"])]
    out = tidy[["city","date","bedroom_type","median_rent","source"]]
    write_df(out.rename(columns={"median_rent":"median_rent"}), "rents", ctx)
