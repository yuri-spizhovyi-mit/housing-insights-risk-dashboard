"""
Micro-forecast updater
----------------------
Scales macro forecasts from model_predictions down to (beds,baths,property_type)
using ratios computed from recent listings_raw data.
"""

import pandas as pd
from sqlalchemy import text
from datetime import datetime, timedelta

from ml.src.utils.data_loader import get_engine
from ml.src.utils.db_writer import write_forecasts


def _compute_rent_ratios(engine, lookback_months: int = 6) -> pd.DataFrame:
    """
    Compute median rent ratios per (city,beds,baths,property_type)
    over the last N months relative to city median.
    Returns tidy DataFrame with columns:
      city, beds, baths, property_type, rent_ratio
    """
    print(f"[INFO] Computing rent ratios from listings_raw (lookback={lookback_months}m)...")
    with engine.connect() as conn:
        df = pd.read_sql(
            """
            SELECT city,
                   date_trunc('month', date_posted)::date AS month,
                   price,
                   bedrooms AS beds,
                   bathrooms AS baths,
                   property_type
            FROM public.listings_raw
            WHERE listing_type = 'rent'
              AND price IS NOT NULL
              AND date_posted > (CURRENT_DATE - interval '%s month')
            """,
            conn,
            params=[lookback_months],
        )

    if df.empty:
        print("[WARN] No listings_raw data found for ratio computation.")
        return pd.DataFrame()

    # clean
    df = df.dropna(subset=["price", "beds", "baths", "city", "property_type"])
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df[df["price"] > 100]

    # median rents
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

    # average ratio across months
    ratios = (
        merged.groupby(["city", "beds", "baths", "property_type"])["ratio"]
        .median()
        .reset_index()
        .rename(columns={"ratio": "rent_ratio"})
    )

    print(f"[DEBUG] Computed {len(ratios)} rent ratio rows.")
    return ratios


def run_micro_forecast(ctx, target: str = "rent_index", horizon: int = 12):
    """
    1. Load city-level forecasts from model_predictions for the given target/horizon.
    2. Compute rent ratios from recent listings.
    3. Multiply city forecasts by ratios to produce property-level forecasts.
    4. Write results into public.model_predictions (same schema).
    """
    engine = get_engine()
    ratios = _compute_rent_ratios(engine, lookback_months=6)
    if ratios.empty:
        print("[WARN] Skipping micro forecast: no ratios available.")
        return

    with engine.connect() as conn:
        macro_df = pd.read_sql(
            text("""
                SELECT city, target, horizon_months, predict_date,
                       yhat, yhat_lower, yhat_upper, model_name, features_version
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
        print(f"[WARN] No macro forecasts found for {target} horizon={horizon}.")
        return

    print(f"[INFO] Scaling {len(macro_df)} macro forecast rows into micro forecasts...")

    # cross join ratios
    joined = macro_df.merge(ratios, on="city", how="inner")
    joined["yhat"] = joined["yhat"] * joined["rent_ratio"]
    joined["yhat_lower"] = joined["yhat_lower"] * joined["rent_ratio"]
    joined["yhat_upper"] = joined["yhat_upper"] * joined["rent_ratio"]

    # select / rename for DB writer
    out_cols = [
        "model_name", "target", "horizon_months", "city",
        "property_type", "beds", "baths",
        "predict_date", "yhat", "yhat_lower", "yhat_upper", "features_version"
    ]
    df_out = joined[out_cols].copy()
    df_out["created_at"] = datetime.utcnow()

    print(f"[INFO] Writing {len(df_out)} micro forecast rows to public.model_predictions...")
    write_forecasts(df_out, ctx)
    print("[INFO] ✅ Micro forecasts successfully written.")


if __name__ == "__main__":
    from datetime import date
    from ml.src.etl import base
    ctx = base.Context(run_date=date.today())
    run_micro_forecast(ctx, target="rent_index", horizon=12)
