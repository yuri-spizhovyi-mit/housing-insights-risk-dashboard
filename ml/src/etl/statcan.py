from .base import Context, write_df, month_floor, put_raw_bytes
from .statcan_wds import download_table_csv

PID_CPI = "1810000401"  # 18-10-0004-01

CMA_WHITELIST = {
    "Kelowna (CMA)",
    "Vancouver (CMA)",
    "Toronto (CMA)",
}


def run(ctx: Context):
    df = download_table_csv(PID_CPI)
    put_raw_bytes(
        ctx,
        f"{ctx.s3_raw_prefix}/statcan/{ctx.run_date.isoformat()}/{PID_CPI}.csv",
        df.to_csv(index=False).encode(),
        "text/csv",
    )

    # Common columns: REF_DATE, GEO, DGUID, UOM, UOM_ID, SCALAR_ID, VECTOR, COORDINATE, VALUE, STATUS, SYMBOL, DECIMALS
    # Filter to All-items only, CMAs of interest
    # There is usually a 'Products and product groups' dimension; the 'All-items' selection varies—look for a column named 'Products and product groups' or 'Products'
    prod_col = next((c for c in df.columns if "product" in c.lower()), None)
    geo_col = "GEO"
    value_col = "VALUE"

    sel = df
    if prod_col:
        sel = sel[sel[prod_col].str.contains("All-items", case=False, na=False)]

    sel = sel[sel[geo_col].isin(CMA_WHITELIST)]
    sel = sel.rename(
        columns={"REF_DATE": "date", geo_col: "city", value_col: "value"}
    ).assign(metric="cpi_all_items", source="StatCan")
    sel["date"] = month_floor(sel["date"])
    out = sel[["city", "date", "metric", "value", "source"]].dropna(subset=["value"])
    write_df(out, "metrics", ctx)
