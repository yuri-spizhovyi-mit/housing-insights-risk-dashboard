"""
train_model_lightgbm_v1_property_types.py
---------------------------------------------------------
Final corrected version

✔ One unified timeseries per city (Option A)
✔ property_type_id used as input feature
✔ Predicts per property type (Apartment / House / Town House)
✔ Compatible with model_features v1-legacy table
✔ Writes predictions into model_predictions table
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import uuid
import os
from dotenv import load_dotenv, find_dotenv

# ----------------------------------------------------------
# DB
# ----------------------------------------------------------
load_dotenv(find_dotenv(usecwd=True))
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)

# ----------------------------------------------------------
# Property type maps
# ----------------------------------------------------------
PROPERTY_TYPE_MAP_REV = {
    0: "Apartment",
    1: "House",
    2: "Town House",
}

PROPERTY_TYPE_IDS = [0, 1, 2]

# ----------------------------------------------------------
# Features we feed into the model
# ----------------------------------------------------------
FEATURE_COLS = [
    "hpi_benchmark",
    "rent_avg_city",
    "mortgage_rate",
    "unemployment_rate",
    "overnight_rate",
    "population",
    "median_income",
    "migration_rate",
    "gdp_growth",
    "cpi_yoy",
    "hpi_change_yoy",
    "rent_change_yoy",
    "property_type_id",      # key feature
    "hpi_scaled",
    "rent_scaled",
    "macro_scaled",
    "demographics_scaled",
]

TARGETS = ["price", "rent"]

# ----------------------------------------------------------
# Load unified v1 features
# ----------------------------------------------------------
def load_features():
    query = """
        SELECT
            date,
            city,
            property_type_id,
            hpi_benchmark,
            rent_avg_city,
            mortgage_rate,
            unemployment_rate,
            overnight_rate,
            population,
            median_income,
            migration_rate,
            gdp_growth,
            cpi_yoy,
            hpi_change_yoy,
            rent_change_yoy,
            hpi_scaled,
            rent_scaled,
            macro_scaled,
            demographics_scaled,
            hpi_benchmark_scaled,
            rent_avg_city_scaled,
            mortgage_rate_scaled,
            unemployment_rate_scaled,
            overnight_rate_scaled,
            population_scaled,
            median_income_scaled,
            migration_rate_scaled,
            gdp_growth_scaled,
            cpi_yoy_scaled
        FROM public.model_features
        ORDER BY city, date;
    """
    df = pd.read_sql(query, engine)
    df["date"] = pd.to_datetime(df["date"])
    return df

# ----------------------------------------------------------
# Build training window for v1 methodology
# ----------------------------------------------------------
def split_train_val(df):
    train_df = df[df["date"] < "2020-01-01"]
    val_df   = df[(df["date"] >= "2020-01-01") & (df["date"] <= "2025-01-01")]
    final_start = df["date"].max()
    return train_df, val_df, final_start

# ----------------------------------------------------------
# Make LightGBM model
# ----------------------------------------------------------
def train_lgbm(train_df, val_df, target_col):
    X_train = train_df[FEATURE_COLS].astype(float)
    y_train = train_df[target_col].astype(float)

    X_val = val_df[FEATURE_COLS].astype(float)
    y_val = val_df[target_col].astype(float)

    train_set = lgb.Dataset(X_train, y_train)
    val_set   = lgb.Dataset(X_val, y_val, reference=train_set)

    params = {
        "objective": "regression",
        "metric": "rmse",
        "verbosity": -1,
        "learning_rate": 0.05,
        "num_leaves": 31,
        "feature_fraction": 0.9,
        "bagging_fraction": 0.8,
        "bagging_freq": 5,
        "min_data_in_leaf": 20,
    }

    callbacks = [
        lgb.early_stopping(stopping_rounds=80),
        lgb.log_evaluation(period=0)   # silence output
    ]

    model = lgb.train(
        params,
        train_set,
        valid_sets=[train_set, val_set],
        num_boost_round=800,
        callbacks=callbacks,
    )


    return model

# ----------------------------------------------------------
# Long-horizon recursive forecasting (2025 → 2035)
# ----------------------------------------------------------
def recursive_forecast(model, last_known_row, months_ahead=120):
    preds = []
    current = last_known_row.copy()
    current_date = last_known_row["date"]

    for _ in range(months_ahead):
        current_date += timedelta(days=30)  # approximate monthly step
        current["date"] = current_date

        X = current[FEATURE_COLS].astype(float).values.reshape(1, -1)
        yhat = float(model.predict(X)[0])

        preds.append((current_date, yhat))

        # Update autoregressive inputs
        if "price" in current:
            current["hpi_benchmark"] = yhat
            current["hpi_scaled"] = yhat  # approximate trend continuation

        if "rent" in current:
            current["rent_avg_city"] = yhat
            current["rent_scaled"] = yhat

    return preds

# ----------------------------------------------------------
# Save predictions
# ----------------------------------------------------------
def write_predictions(run_id, model_name, target, horizon_months, city, property_type, pred_list):
    rows = []
    for (pdate, yhat) in pred_list:
        rows.append({
            "run_id": str(uuid.uuid4()),
            "model_name": model_name,
            "target": target,
            "horizon_months": horizon_months,
            "city": city,
            "property_type": property_type,
            "predict_date": pdate,
            "yhat": yhat,
            "features_version": "v1_legacy_with_property_type",
            "created_at": datetime.utcnow(),
            "is_micro": False,
        })

    with engine.begin() as conn:
        sql = text("""
            INSERT INTO public.model_predictions (
                run_id, model_name, target, horizon_months, city,
                property_type, predict_date, yhat,
                features_version, created_at, is_micro
            )
            VALUES (
                :run_id, :model_name, :target, :horizon_months, :city,
                :property_type, :predict_date, :yhat,
                :features_version, :created_at, :is_micro
            )
        """)
        conn.execute(sql, rows)

# ----------------------------------------------------------
# Main training loop
# ----------------------------------------------------------
def main():
    print("[INFO] Loading features...")
    df = load_features()

    model_name = "lightgbm_v1"
    run_id = str(uuid.uuid4())

    # Loop over cities only (Option A)
    for city, group in df.groupby("city"):
        group = group.sort_values("date")

        print(f"\n====================")
        print(f"[TRAIN] CITY: {city}")
        print("====================")

        train_df, val_df, last_date = split_train_val(group)

        for target in TARGETS:
            target_col = "hpi_benchmark" if target == "price" else "rent_avg_city"

            print(f"[TARGET] {target}")

            model = train_lgbm(train_df, val_df, target_col)

            # Final known row for autoregression
            last_row = group[group["date"] == last_date].iloc[-1].copy()

            # Forecast per property type
            for ptype_id in PROPERTY_TYPE_IDS:
                ptype_txt = PROPERTY_TYPE_MAP_REV[ptype_id]

                print(f"  [FORECAST] {city} / {ptype_txt}")

                last_pt = last_row.copy()
                last_pt["property_type_id"] = ptype_id

                preds = recursive_forecast(
                    model,
                    last_pt,
                    months_ahead=120   # 10 years
                )

                write_predictions(
                    run_id,
                    model_name,
                    target,
                    horizon_months=120,
                    city=city,
                    property_type=ptype_txt,
                    pred_list=preds
                )

    print("\n[DONE] LightGBM v1 forecasting completed.")


if __name__ == "__main__":
    main()
