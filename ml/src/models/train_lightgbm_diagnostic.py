# ================================================================
# train_lightgbm_diagnostic.py — adds feature diagnostics & importance
# ================================================================

import pandas as pd
import lightgbm as lgb
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import numpy as np
import matplotlib.pyplot as plt


def train_lightgbm(path: str = "data/historical_features.parquet"):
    df = pd.read_parquet(path)
    print(f"[INFO] Loaded {len(df)} rows for training")

    # Select all numeric features except targets and meta columns
    feature_cols = [
        c
        for c in df.columns
        if c
        not in [
            "target_hpi_12m_ahead",
            "target_hpi_24m_ahead",
            "target_hpi_5y_ahead",
            "target_hpi_10y_ahead",
            "city",
            "date",
            "property_type",
            "created_at",
        ]
    ]

    # Filter to numeric only
    df = df.copy()
    X = df[feature_cols].select_dtypes(include=[np.number]).fillna(0)
    y = df["target_hpi_12m_ahead"]

    # Diagnostic: print feature stats
    print("\n=== Feature Diagnostics ===")
    print(f"Total candidate features: {len(feature_cols)}")
    print(f"Numeric usable features: {X.shape[1]}")
    print("Constant columns:", [c for c in X.columns if X[c].nunique() <= 1])
    print("Top 10 variances:")
    print(X.var().sort_values(ascending=False).head(10))
    print("============================\n")

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

    model = lgb.train(
        params,
        train_data,
        valid_sets=[valid_data],
        num_boost_round=500,
        callbacks=[lgb.early_stopping(stopping_rounds=50)],
    )

    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    print(f"[RESULT] RMSE = {rmse:.4f}\n")

    # Feature importance
    importance = pd.DataFrame(
        {"feature": model.feature_name(), "importance": model.feature_importance()}
    ).sort_values(by="importance", ascending=False)
    print("Top 10 feature importances:")
    print(importance.head(10))

    plt.figure(figsize=(8, 5))
    plt.barh(
        importance.head(10)["feature"],
        importance.head(10)["importance"],
        color="skyblue",
    )
    plt.gca().invert_yaxis()
    plt.title("Top 10 Feature Importances")
    plt.xlabel("Importance")
    plt.tight_layout()
    Path("models").mkdir(exist_ok=True)
    plt.savefig("models/lightgbm_feature_importance.png")
    print(
        "[OK] Saved feature importance chart → models/lightgbm_feature_importance.png"
    )

    Path("models").mkdir(exist_ok=True)
    model.save_model("models/lightgbm_hpi.txt")
    print("[OK] Model saved → models/lightgbm_hpi.txt")


if __name__ == "__main__":
    train_lightgbm()
