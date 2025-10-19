# ================================================================
# train_lightgbm.py — v2 (compatible with all LightGBM versions)
# ================================================================

import pandas as pd
import lightgbm as lgb
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import numpy as np


def train_lightgbm(path: str = "data/historical_features.parquet"):
    df = pd.read_parquet(path)
    print(f"[INFO] Loaded {len(df)} rows for training")

    # Select features and target
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
    target_col = "target_hpi_12m_ahead"

    X = df[feature_cols].fillna(0)
    y = df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )

    train_data = lgb.Dataset(X_train, label=y_train)
    valid_data = lgb.Dataset(X_test, label=y_test)

    params = {
        "objective": "regression",
        "metric": "rmse",
        "learning_rate": 0.05,
        "num_leaves": 31,
        "feature_fraction": 0.9,
        "bagging_fraction": 0.8,
        "bagging_freq": 5,
    }

    # ✅ Compatible syntax for all LightGBM versions
    model = lgb.train(
        params,
        train_data,
        valid_sets=[valid_data],
        num_boost_round=500,
        callbacks=[lgb.early_stopping(stopping_rounds=50)],
    )

    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    print(f"[RESULT] RMSE = {rmse:.4f}")

    Path("models").mkdir(exist_ok=True)
    model.save_model("models/lightgbm_hpi.txt")
    print("[OK] Model saved → models/lightgbm_hpi.txt")


if __name__ == "__main__":
    train_lightgbm()
