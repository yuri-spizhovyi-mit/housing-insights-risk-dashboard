"""
run_models_micro_update.py
--------------------------
Scales macro forecasts from model_predictions into
property-level (beds/baths/property_type) micro forecasts.

Reads:
  - public.listings_raw         → to compute rent ratios
  - public.model_predictions    → city-level forecasts

Writes:
  - public.model_predictions    (with micro columns filled)
"""

import pandas as pd
from sqlalchemy import text
from datetime import datetime
from ml.src.etl.db import get_engine
from ml.src.utils.db_writer import write_forecasts


# ---------------------------------------------------------------------
# Helper: normalize city names
# ---------------------------------------------------------------------
def _normalize_city(name: str) -> str:
    """Normalize city name capitalization and remove commas/extra spaces."""
    if not isinstance(name, str):
        return name
    return (
        name.replace(",", " ")
        .strip()
        .title()  # kelowna → Kelowna, VANCOUVER → Vancouver
    )


# ---------------------------------------------------------------------
# 1. Compute rent ratios from listings_raw
# ---------------------------------------------------------------------
def _compute_rent_ratios(engine, lookback_months: int = 6) -> pd.DataFrame:
    """
    Compute median rent ratios per (city,beds,baths,property_type)
    relative to the citywide median over last N months.
    Returns tidy DataFrame: city, beds, baths, property_type, rent_ratio.
    """
    print(
        f"\n[INFO] 🔍 Computing rent ratios from listings_raw (lookback={lookback_months}m)..."
    )

    with engine.connect() as conn:
        query = f"""
            SELECT city,
                   date_trunc('month', date_posted)::date AS month,
                   price,
                   bedrooms AS beds,
                   bathrooms AS baths,
                   property_type
            FROM public.listings_raw
            WHERE listing_type = 'rent'
              AND price IS NOT NULL
              AND date_posted > (CURRENT_DATE - interval '{lookback_months} month')
        """
        df = pd.read_sql(query, conn)

    if df.empty:
        print("[WARN] ⚠️ No listings_raw data found for ratio computation.")
        return pd.DataFrame()

    # Normalize & clean
    df["city"] = df["city"].apply(_normalize_city)
    df = df.dropna(subset=["price", "beds", "baths", "city", "property_type"])
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df[df["price"] > 100]

    # Median rents
    med_city = df.groupby(["city", "month"])["price"].median().rename("city_median")
    med_cfg = (
        df.groupby(["city", "month", "beds", "baths", "property_type"])["price"]
        .median()
        .rename("cfg_median")
    )
    merged = med_cfg.reset_index().merge(
        med_city.reset_index(), on=["city", "month"], how="left"
    )
    merged["ratio"] = merged["cfg_median"] / merged["city_median"]

    ratios = (
        merged.groupby(["city", "beds", "baths", "property_type"])["ratio"]
        .median()
        .reset_index()
        .rename(columns={"ratio": "rent_ratio"})
    )

    print(f"[INFO] ✅ Computed {len(ratios)} rent ratio rows.")
    return ratios


# ---------------------------------------------------------------------
# 2. Scale macro forecasts into micro-level forecasts
# ---------------------------------------------------------------------
def _scale_forecasts(ctx, target: str, horizon: int, ratios: pd.DataFrame):
    engine = get_engine()

    with engine.connect() as conn:
        macro_df = pd.read_sql(
            text("""
                SELECT city, target, horizon_months, predict_date,
                       yhat, yhat_lower, yhat_upper,
                       model_name, features_version
                FROM public.model_predictions
                WHERE target = :target
                  AND horizon_months = :horizon
                  AND property_type IS NULL
                  AND beds IS NULL
                  AND baths IS NULL
            """),
            conn,
            params={"target": target, "horizon": horizon},
        )

    if macro_df.empty:
        print(
            f"[WARN] ⚠️ No macro forecasts found for {target} horizon={horizon}. Skipping."
        )
        return

    # Normalize city names before join
    macro_df["city"] = macro_df["city"].apply(_normalize_city)
    ratios["city"] = ratios["city"].apply(_normalize_city)

    joined = macro_df.merge(ratios, on="city", how="inner")
    if joined.empty:
        print(f"[WARN] ⚠️ No matching city data for horizon={horizon}.")
        return

    print(
        f"[INFO] Scaling {len(macro_df)} macro rows → micro forecasts (horizon={horizon})..."
    )

    joined["yhat"] = joined["yhat"] * joined["rent_ratio"]
    joined["yhat_lower"] = joined["yhat_lower"] * joined["rent_ratio"]
    joined["yhat_upper"] = joined["yhat_upper"] * joined["rent_ratio"]

    out_cols = [
        "model_name",
        "target",
        "horizon_months",
        "city",
        "property_type",
        "beds",
        "baths",
        "predict_date",
        "yhat",
        "yhat_lower",
        "yhat_upper",
        "features_version",
    ]
    df_out = joined[out_cols].copy()
    df_out["created_at"] = datetime.now().astimezone()

    print(f"[INFO] 💾 Writing {len(df_out)} micro forecast rows...")
    write_forecasts(ctx, df_out)
    print(f"[INFO] ✅ Completed horizon={horizon} ({target})")


# ---------------------------------------------------------------------
# 3. Orchestrator
# ---------------------------------------------------------------------
def run_micro_forecast(ctx, target: str = "rent_index"):
    """Run micro forecast updates for multiple horizons (3,6,12,24 months)."""
    engine = get_engine()
    horizons = [12, 24, 60, 120]

    print(f"\n🚀 Starting micro forecast pipeline for target={target}")
    ratios = _compute_rent_ratios(engine, lookback_months=6)
    if ratios.empty:
        print("[WARN] ⚠️ Aborting micro forecast: no rent ratios available.")
        return

    for horizon in horizons:
        _scale_forecasts(ctx, target, horizon, ratios)

    print(f"\n🏁 All horizons processed successfully for target={target}")


# ---------------------------------------------------------------------
# 4. CLI Entrypoint
# ---------------------------------------------------------------------
if __name__ == "__main__":
    from datetime import date
    from ml.src.etl import base

    ctx = base.Context(run_date=date.today())
    run_micro_forecast(ctx, target="rent_index")
