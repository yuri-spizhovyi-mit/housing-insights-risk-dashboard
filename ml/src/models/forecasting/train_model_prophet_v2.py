"""
train_model_prophet_v2.py
-----------------------------------------
City-level Prophet forecasting (v2)
Targets:
- price
- rent
Forecast horizon: 1–60 months
"""

import pandas as pd
import uuid
import os
from datetime import datetime, timezone
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text
from prophet import Prophet

load_dotenv(find_dotenv(usecwd=True))
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)

REGRESSORS = [
    "mortgage_rate_z",
    "unemployment_rate_z",
    "cpi_yoy_z",
    "roll_3_z",
    "roll_6_z",
]


# ---------------------------------------------------------
# LOAD FEATURES
# ---------------------------------------------------------
def load_features():
    q = """
        SELECT
            date, city,
            hpi_benchmark, rent_avg_city,
            mortgage_rate_z, unemployment_rate_z, cpi_yoy_z,
            roll_3_z, roll_6_z
        FROM public.model_features
        ORDER BY city, date;
    """

    df = pd.read_sql(q, engine)
    df["date"] = pd.to_datetime(df["date"])
    return df


# ---------------------------------------------------------
# TRAIN PROPHET
# ---------------------------------------------------------
def forecast_city_target(df, city, target_col, target_name):
    g = df[df.city == city].sort_values("date").copy()
    if len(g) < 24:
        print(f"[WARN] Prophet: not enough history for {city}/{target_name}")
        return []

    dfp = g.rename(columns={"date": "ds", target_col: "y"})
    dfp["y"] = dfp["y"].astype(float)

    model = Prophet()
    for r in REGRESSORS:
        model.add_regressor(r)

    model.fit(dfp[["ds","y"] + REGRESSORS])

    # Create future dataframe for 60 months
    future = model.make_future_dataframe(periods=60, freq="MS")
    # Attach regressors for forecasting period → use last known values
    last_vals = g.iloc[-1][REGRESSORS]
    for r in REGRESSORS:
        future[r] = g[r].tolist() + [last_vals[r]] * 60

    fc = model.predict(future)

    rows = []
    hist_end = g["date"].max()

    forecast_df = fc[fc["ds"] > hist_end].copy().reset_index(drop=True)

    for i, row in forecast_df.iterrows():
        horizon = i + 1
        rows.append({
            "run_id": str(uuid.uuid4()),
            "model_name": "prophet_v2",
            "target": target_name,
            "horizon_months": horizon,
            "city": city,
            "property_type": None,
            "beds": None,
            "baths": None,
            "sqft_min": None,
            "sqft_max": None,
            "year_built_min": None,
            "year_built_max": None,
            "predict_date": row["ds"],
            "yhat": float(max(0.0, row["yhat"])),
            "yhat_lower": float(max(0.0, row["yhat_lower"])),
            "yhat_upper": float(max(0.0, row["yhat_upper"])),
            "features_version": "features_to_model_v1",
            "model_artifact_uri": None,
            "created_at": datetime.now(timezone.utc),
            "is_micro": False
        })

    print(f"[OK] Prophet v2 forecast: {city}/{target_name}")
    return rows


# ---------------------------------------------------------
# WRITE PREDICTIONS
# ---------------------------------------------------------
def write_predictions(rows):
    if not rows:
        return

    sql = text("""
        INSERT INTO public.model_predictions(
            run_id, model_name, target, horizon_months,
            city, property_type,
            beds, baths, sqft_min, sqft_max,
            year_built_min, year_built_max,
            predict_date, yhat, yhat_lower, yhat_upper,
            features_version, model_artifact_uri,
            created_at, is_micro
        )
        VALUES (
            :run_id, :model_name, :target, :horizon_months,
            :city, :property_type,
            :beds, :baths, :sqft_min, :sqft_max,
            :year_built_min, :year_built_max,
            :predict_date, :yhat, :yhat_lower, :yhat_upper,
            :features_version, :model_artifact_uri,
            :created_at, :is_micro
        );
    """)

    with engine.begin() as conn:
        conn.execute(sql, rows)

    print(f"[OK] Inserted {len(rows)} Prophet v2 predictions.")


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
def main():
    print("[DEBUG] Starting Prophet v2...")

    df = load_features()
    all_rows = []

    for city in df.city.unique():
        all_rows.extend(forecast_city_target(df, city, "hpi_benchmark", "price"))
        all_rows.extend(forecast_city_target(df, city, "rent_avg_city", "rent"))

    write_predictions(all_rows)
    print("[DONE] Prophet v2 complete.")


if __name__ == "__main__":
    main()
