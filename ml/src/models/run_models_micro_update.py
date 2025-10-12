# -----------------------------
# Micro (Property-Level) Forecast
# -----------------------------
from lightgbm import LGBMRegressor
import numpy as np
import pandas as pd


def run_micro_forecast(
    df: pd.DataFrame, city: str, params: dict, horizon_months: int = 12
):
    """
    Run LightGBM-based property-level (micro) forecast.
    Returns a DataFrame consistent with Prophet output.
    """
    if df is None or df.empty:
        print(f"[WARN] Empty dataframe for {city} – micro forecast skipped.")
        return pd.DataFrame()

    try:
        # --- 1️⃣ Prepare training data
        features = [
            "beds",
            "baths",
            "sqft_avg",
            "price_to_rent",
            "hpi_mom_pct",
            "rent_mom_pct",
        ]
        for f in features:
            if f not in df.columns:
                df[f] = np.nan
        df = df.dropna(subset=["hpi_composite_sa", "price_to_rent"]).fillna(
            method="ffill"
        )

        X = df[features]
        y = df["hpi_composite_sa"]

        # --- 2️⃣ Train LightGBM regressor
        model = LGBMRegressor(
            n_estimators=300, learning_rate=0.05, max_depth=6, random_state=42
        )
        model.fit(X, y)

        # --- 3️⃣ Build future inputs using latest record as baseline
        last_row = df.iloc[-1]
        last_date = pd.to_datetime(last_row["date"])

        future_X = pd.DataFrame(
            [
                {
                    "beds": params.get("beds", last_row.get("beds", 2)),
                    "baths": params.get("baths", last_row.get("baths", 1)),
                    "sqft_avg": params.get("sqft_avg", last_row.get("sqft_avg", 900)),
                    "price_to_rent": last_row["price_to_rent"],
                    "hpi_mom_pct": last_row["hpi_mom_pct"],
                    "rent_mom_pct": last_row["rent_mom_pct"],
                }
            ]
            * horizon_months
        )

        # --- 4️⃣ Predict forward
        preds = model.predict(future_X)
        forecast_dates = [
            last_date + pd.DateOffset(months=i + 1) for i in range(horizon_months)
        ]

        # --- 5️⃣ Construct result DataFrame
        forecast_df = pd.DataFrame(
            {
                "predict_date": forecast_dates,
                "yhat": preds,
                "yhat_lower": preds * 0.97,
                "yhat_upper": preds * 1.03,
                "model_name": "LightGBM_Micro",
                "target": "property_price",
                "city": city,
                "horizon_months": horizon_months,
                "features_version": "v1.1",
                "property_type": params.get("property_type"),
                "beds": params.get("beds"),
                "baths": params.get("baths"),
                "sqft_avg": params.get("sqft_avg"),
                "model_artifact_uri": "ml/models/lgbm_micro_v1.pkl",
            }
        )

        print(
            f"[OK] Micro forecast generated for {city} ({horizon_months}m): {len(forecast_df)} rows"
        )
        return forecast_df

    except Exception as e:
        print(f"[ERROR] run_micro_forecast() failed for {city}: {e}")
        return pd.DataFrame()
