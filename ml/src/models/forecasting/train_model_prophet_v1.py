"""
train_model_prophet_v1.py
----------------------------------------------------------
Dual-target Prophet forecasting:

Targets:
- Home price  (target="price") → hpi_benchmark
- Rent price  (target="rent")  → rent_avg_city

For each (city, property_type):
- Train: 2005–2020
- Validate: 2020–2025
- Forecast: 2025–2035 (120 months)

Writes predictions to public.model_predictions with correct schema.
"""

import pandas as pd
import numpy as np
import uuid
from datetime import datetime, timezone
from prophet import Prophet
from sqlalchemy import create_engine, text
from dotenv import load_dotenv, find_dotenv
import warnings
import os

warnings.filterwarnings("ignore")

# ----------------------------------------------------------
# ENVIRONMENT
# ----------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)


# ----------------------------------------------------------
# LOAD model_features (NOT public.features)
# ----------------------------------------------------------
def load_model_features():
    q = """
        SELECT
            date,
            city,
            property_type,
            hpi_benchmark,
            rent_avg_city,
            hpi_z,
            rent_z,
            macro_composite_z,
            demographics_composite_z,
            hpi_change_yoy,
            rent_change_yoy,
            lag_1,
            lag_3,
            lag_6,
            lag_12,
            roll_3,
            roll_6,
            roll_12
        FROM public.model_features
        ORDER BY city, property_type, date;
    """
    df = pd.read_sql(q, engine)
    df["date"] = pd.to_datetime(df["date"])
    print(f"[INFO] Loaded {len(df)} rows from model_features")
    return df


# ----------------------------------------------------------
# VALIDATION METRICS
# ----------------------------------------------------------
def mae(y_true, y_pred):
    return float(np.mean(np.abs(y_true - y_pred)))


def mape(y_true, y_pred):
    return float(np.mean(np.abs((y_true - y_pred) / y_true))) * 100


# ----------------------------------------------------------
# Prophet model builder (with regressors)
# ----------------------------------------------------------
def build_prophet_model():
    model = Prophet(
        yearly_seasonality=True,
        changepoint_prior_scale=0.08,
        interval_width=0.90,
    )
    return model


# ----------------------------------------------------------
# Add regressors to Prophet
# ----------------------------------------------------------
REGRESSOR_COLS = [
    "hpi_z",
    "rent_z",
    "macro_composite_z",
    "demographics_composite_z",
    "hpi_change_yoy",
    "rent_change_yoy",
    "lag_1",
    "lag_3",
    "lag_6",
    "lag_12",
    "roll_3",
    "roll_6",
    "roll_12",
]


# ----------------------------------------------------------
# Training logic per (city, property_type, target)
# ----------------------------------------------------------
def train_prophet_for_group(df, city, ptype, target_name, col_name):

    g = df[(df.city == city) & (df.property_type == ptype)].sort_values("date")

    # Prepare Prophet input
    p_df = g.rename(columns={"date": "ds", col_name: "y"})

    # Train/validation split
    train = p_df[p_df.ds <= "2020-12-01"]
    valid = p_df[(p_df.ds > "2020-12-01") & (p_df.ds <= "2025-12-01")]

    # ------------------------- MODEL BUILD -------------------------
    model = build_prophet_model()

    # Add regressors
    for col in REGRESSOR_COLS:
        model.add_regressor(col)

    # Train
    model.fit(train[["ds", "y"] + REGRESSOR_COLS])

    # ------------------------- VALIDATION -------------------------
    if not valid.empty:
        fc_valid = model.predict(valid[["ds"] + REGRESSOR_COLS])
        v_mae = mae(valid["y"], fc_valid["yhat"])
        v_mape = mape(valid["y"], fc_valid["yhat"])
        print(f"[VAL] {city}/{ptype}/{target_name}: MAE={v_mae:,.0f}, MAPE={v_mape:.2f}%")

    # ------------------------- RETRAIN ON FULL DATA -------------------------
    full_model = build_prophet_model()
    for col in REGRESSOR_COLS:
        full_model.add_regressor(col)

    full_model.fit(p_df[["ds", "y"] + REGRESSOR_COLS])

    # ------------------------- FORECAST 120 MONTHS -------------------------
    future = full_model.make_future_dataframe(periods=120, freq="MS")

    # Merge regressors (extend with last known values)
    last_vals = g.iloc[-1:][REGRESSOR_COLS].to_dict(orient="records")[0]
    future_reg = pd.DataFrame([last_vals] * len(future))

    future_fc = full_model.predict(pd.concat([future, future_reg], axis=1))

    last_date = g["date"].max()

    rows = []

    for i in range(120):
        pred_row = future_fc.iloc[len(p_df) + i]

        forecast_date = last_date + pd.DateOffset(months=i + 1)

        rows.append(
            {
                "run_id": str(uuid.uuid4()),
                "model_name": "prophet_v1",
                "target": target_name,
                "horizon_months": i + 1,
                "city": city,
                "property_type": ptype,
                "beds": None,
                "baths": None,
                "sqft_min": None,
                "sqft_max": None,
                "year_built_min": None,
                "year_built_max": None,
                "predict_date": forecast_date,
                "yhat": float(pred_row["yhat"]),
                "yhat_lower": float(pred_row["yhat_lower"]),
                "yhat_upper": float(pred_row["yhat_upper"]),
                "features_version": "model_features_v1",
                "model_artifact_uri": None,
                "created_at": datetime.now(timezone.utc),
                "is_micro": False,
            }
        )

    print(f"[OK] Prophet forecast for {city}/{ptype}/{target_name} (120 months)")
    return rows


# ----------------------------------------------------------
# INSERT INTO model_predictions
# ----------------------------------------------------------
def write_predictions(rows):
    if not rows:
        print("[WARN] No rows to insert.")
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

    print(f"[OK] Inserted {len(rows)} Prophet predictions.")


# ----------------------------------------------------------
# Entrypoint
# ----------------------------------------------------------
def main():
    print("[DEBUG] Starting Prophet v1...")

    df = load_model_features()

    all_rows = []

    for (city, ptype), _ in df.groupby(["city", "property_type"]):

        # Home Price
        rows_price = train_prophet_for_group(df, city, ptype, "price", "hpi_benchmark")
        all_rows.extend(rows_price)

        # Rent Price
        rows_rent = train_prophet_for_group(df, city, ptype, "rent", "rent_avg_city")
        all_rows.extend(rows_rent)

    write_predictions(all_rows)

    print("[DONE] Prophet v1 completed.")


if __name__ == "__main__":
    main()
