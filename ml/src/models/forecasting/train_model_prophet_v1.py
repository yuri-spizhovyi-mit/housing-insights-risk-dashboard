"""
train_model_prophet_v1.py
----------------------------------------------------------
CITY-LEVEL PROPHET FORECASTING (PHASE 2)

Targets:
- price (hpi_raw)
- rent  (rent_raw)

Regressors (Option A):
- macro_z
- demo_z

Forecast:
- 120 months ahead (2025 → 2035)
"""

import pandas as pd
import numpy as np
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from dotenv import load_dotenv, find_dotenv
import os
import warnings
from prophet import Prophet

warnings.filterwarnings("ignore")


# ---------------------------------------------------------
# ENVIRONMENT
# ---------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)


# ---------------------------------------------------------
# LOAD MODEL FEATURES (CITY-LEVEL)
# ---------------------------------------------------------
def load_city_features():
    q = """
        SELECT
            date,
            city,
            hpi_raw,
            rent_raw,
            macro_z,
            demo_z
        FROM public.model_features
        ORDER BY city, date;
    """
    df = pd.read_sql(q, engine)
    df["date"] = pd.to_datetime(df["date"])
    return df


# ---------------------------------------------------------
# TRAIN PROPHET FOR ONE CITY & TARGET
# ---------------------------------------------------------
def train_prophet_for_city(df, city, target_col, target_name):

    g = df[df.city == city].sort_values("date").copy()

    if len(g) < 50:
        print(f"[WARN] Too little data for {city}/{target_name}")
        return []

    # -------------------------------------------
    # PREPARE DATAFRAME IN PROPHET FORMAT
    # -------------------------------------------
    df_p = pd.DataFrame({
        "ds": g["date"],
        "y": g[target_col],
        "macro_z": g["macro_z"],
        "demo_z": g["demo_z"]
    })

    # -------------------------------------------
    # DEFINE PROPHET MODEL
    # -------------------------------------------
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        seasonality_mode="additive"
    )

    # add regressors
    model.add_regressor("macro_z")
    model.add_regressor("demo_z")

    # -------------------------------------------
    # FIT MODEL
    # -------------------------------------------
    model.fit(df_p)

    # -------------------------------------------
    # MAKE FUTURE DATAFRAME (120 MONTHS)
    # -------------------------------------------
    future = model.make_future_dataframe(periods=120, freq="MS")

    # merge regressors for future
    last_macro = g["macro_z"].iloc[-1]
    last_demo = g["demo_z"].iloc[-1]

    future["macro_z"] = last_macro
    future["demo_z"] = last_demo

    # -------------------------------------------
    # FORECAST
    # -------------------------------------------
    fc = model.predict(future)

    # -------------------------------------------
    # COLLECT ONLY FUTURE FORECASTS
    # -------------------------------------------
    fc_future = fc[fc["ds"] > g["date"].max()].reset_index(drop=True)

    rows = []

    for i, row in fc_future.iterrows():

        # clamp negative outputs
        y_raw = max(0.0, float(row["yhat"]))
        lo_raw = max(0.0, float(row["yhat_lower"]))
        hi_raw = max(0.0, float(row["yhat_upper"]))

        # round to dollars
        y = int(round(y_raw))
        lo = int(round(lo_raw))
        hi = int(round(hi_raw))

        rows.append({
            "run_id": str(uuid.uuid4()),
            "model_name": "prophet_v1",
            "target": target_name,
            "horizon_months": i + 1,

            "city": city,
            "property_type": None,
            "beds": None,
            "baths": None,
            "sqft_min": None,
            "sqft_max": None,
            "year_built_min": None,
            "year_built_max": None,

            "predict_date": row["ds"],
            "yhat": y,
            "yhat_lower": lo,
            "yhat_upper": hi,

            "features_version": "model_features_city_v1",
            "model_artifact_uri": None,
            "created_at": datetime.now(timezone.utc),

            "is_micro": False
        })

    print(f"[OK] Prophet forecast created for {city}/{target_name}")
    return rows


# ---------------------------------------------------------
# WRITE TO DATABASE
# ---------------------------------------------------------
def write_predictions(rows):
    if not rows:
        print("[WARN] No predictions to write.")
        return

    sql = text("""
        INSERT INTO public.model_predictions (
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

    print(f"[OK] Inserted {len(rows)} Prophet v1 predictions.")


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
def main():
    print("[DEBUG] Starting Prophet v1 training...")

    df = load_city_features()
    all_rows = []

    for city in df.city.unique():

        # price forecast
        rows_hpi = train_prophet_for_city(df, city, "hpi_raw", "price")
        all_rows.extend(rows_hpi)

        # rent forecast
        rows_rent = train_prophet_for_city(df, city, "rent_raw", "rent")
        all_rows.extend(rows_rent)

    write_predictions(all_rows)

    print("[DONE] Prophet v1 completed successfully.")


if __name__ == "__main__":
    main()
