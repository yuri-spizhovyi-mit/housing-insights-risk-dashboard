"""
train_model_lightgbm_v2.py
------------------------------------
Trains LightGBM forecasting models for each (city, property_type)
using model_features_v2.

Target: Next-month HPI benchmark (shifted).
Writes predictions into public.model_predictions.
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
from sqlalchemy import create_engine, text
from datetime import datetime, timezone
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(usecwd=True))
NEON_DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(NEON_DATABASE_URL, pool_pre_ping=True, future=True)


def load_model_features():
    query = """
        SELECT *
        FROM public.model_features
        ORDER BY date, city, property_type;
    """
    df = pd.read_sql_query(query, engine)
    df["date"] = pd.to_datetime(df["date"])
    print("[INFO] Loaded", len(df), "rows from model_features")
    return df


def make_target(df):
    df = df.sort_values(["city", "property_type", "date"])
    df["target"] = df.groupby(["city", "property_type"])["hpi_benchmark"].shift(-1)
    df = df.dropna(subset=["target"])
    return df


def train_lightgbm(df_group):
    feature_cols = [
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
    ]

    df_group = df_group.sort_values("date")
    n = len(df_group)
    split = int(n * 0.8)

    train = df_group.iloc[:split]
    test = df_group.iloc[split:]

    X_train = train[feature_cols]
    y_train = train["target"]

    X_test = test[feature_cols]
    y_test = test["target"]

    model = lgb.LGBMRegressor(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=-1,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="regression",
    )

    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    test = test.copy()
    test["prediction"] = preds

    return model, train, test


def write_predictions(df_pred):
    cols = ["date", "city", "property_type", "prediction", "model_name", "created_at"]
    sql = text(f"""
        INSERT INTO public.model_predictions ({", ".join(cols)})
        VALUES ({", ".join(":" + c for c in cols)})
        ON CONFLICT (date, city, property_type, model_name)
        DO UPDATE SET
            prediction = EXCLUDED.prediction,
            created_at = EXCLUDED.created_at;
    """)

    df_pred["created_at"] = datetime.now(timezone.utc)
    df_pred["model_name"] = "lightgbm_v2"

    records = df_pred[cols].to_dict(orient="records")

    with engine.begin() as conn:
        for batch_start in range(0, len(records), 2000):
            batch = records[batch_start : batch_start + 2000]
            conn.execute(sql, batch)

    print(f"[OK] Wrote {len(records)} LightGBM predictions")


def main():
    print("[DEBUG] Starting LightGBM v2 training...")
    df = load_model_features()
    df = make_target(df)

    all_predictions = []

    for (city, ptype), group in df.groupby(["city", "property_type"]):
        print(f"[TRAIN] {city} - {ptype}: {len(group)} rows")
        model, train, test = train_lightgbm(group)

        preds = test[["date", "city", "property_type", "prediction"]]
        all_predictions.append(preds)

    final_df = pd.concat(all_predictions, ignore_index=True)
    write_predictions(final_df)

    print("[DONE] LightGBM v2 training completed.")


if __name__ == "__main__":
    main()
