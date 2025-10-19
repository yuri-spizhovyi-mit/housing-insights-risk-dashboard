# ================================================================
# predict_lightgbm.py — Use trained LightGBM model to forecast future HPI
# and write results into `public.model_predictions`
# ================================================================

import pandas as pd
import lightgbm as lgb
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import os


# ---------------------------------------------------------------
# 🔌 Database connection
# ---------------------------------------------------------------
def get_engine():
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5433/hird",
    )
    print(f"[DEBUG] Connecting to DB → {db_url}")
    return create_engine(db_url, future=True)


# ---------------------------------------------------------------
# ⚙️ Predict future HPI using trained model
# ---------------------------------------------------------------
def predict_lightgbm(model_path="models/lightgbm_hpi.txt", horizon_months=12):
    print(f"[INFO] Loading LightGBM model from {model_path}")
    model = lgb.Booster(model_file=model_path)

    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql("SELECT * FROM public.features", conn)

    # Prepare features
    feature_cols = [
        c
        for c in df.columns
        if c.startswith(
            (
                "price_",
                "rent_",
                "bedrooms_",
                "bathrooms_",
                "sqft_",
                "hpi_",
                "gdp_",
                "unemployment_",
                "prime_",
                "population",
            )
        )
    ]
    df = df.sort_values(["city", "date"])

    latest = df.groupby("city").tail(1).copy()
    latest["predict_date"] = pd.to_datetime(latest["date"]) + timedelta(
        days=30 * horizon_months
    )
    X = latest[feature_cols].fillna(0)

    # Predict
    y_pred = model.predict(X)
    latest["yhat"] = y_pred
    latest["yhat_lower"] = latest["yhat"] * 0.95
    latest["yhat_upper"] = latest["yhat"] * 1.05

    # Prepare final DataFrame for DB
    out = latest[["city", "predict_date", "yhat", "yhat_lower", "yhat_upper"]].copy()
    out["model_name"] = "LightGBM"
    out["target"] = "house_price_index"
    out["horizon_months"] = horizon_months
    out["property_type"] = None
    out["beds"] = None
    out["baths"] = None
    out["sqft_min"] = None
    out["sqft_max"] = None
    out["year_built_min"] = None
    out["year_built_max"] = None
    out["features_version"] = "v2.0"
    out["model_artifact_uri"] = model_path
    out["created_at"] = datetime.now().astimezone()

    print(f"[INFO] Writing {len(out)} LightGBM forecast rows to model_predictions...")

    # Write to database
    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO public.model_predictions (
                model_name, target, horizon_months, city, property_type,
                beds, baths, sqft_min, sqft_max, year_built_min, year_built_max,
                predict_date, yhat, yhat_lower, yhat_upper,
                features_version, model_artifact_uri, created_at
            )
            VALUES (
                :model_name, :target, :horizon_months, :city, :property_type,
                :beds, :baths, :sqft_min, :sqft_max, :year_built_min, :year_built_max,
                :predict_date, :yhat, :yhat_lower, :yhat_upper,
                :features_version, :model_artifact_uri, :created_at
            )
        """),
            out.to_dict(orient="records"),
        )

    print("[OK] ✅ LightGBM forecasts successfully written to database.")


# ---------------------------------------------------------------
# 🚀 CLI Entrypoint
# ---------------------------------------------------------------
if __name__ == "__main__":
    predict_lightgbm(model_path="models/lightgbm_hpi.txt", horizon_months=12)
