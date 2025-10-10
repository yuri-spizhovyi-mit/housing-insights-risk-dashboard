import pandas as pd
from lightgbm import LGBMRegressor


def run_micro_forecast(df: pd.DataFrame, city: str, params: dict):
    """
    Property-level forecast using LightGBM.
    Returns list[dict] formatted for model_predictions table.
    """
    results = []
    model = LGBMRegressor()

    # Train or load existing model (simplified for now)
    features = [
        "beds",
        "baths",
        "sqft_avg",
        "price_to_rent",
        "hpi_mom_pct",
        "rent_mom_pct",
    ]
    df = df.dropna(subset=features)
    X, y = df[features], df["hpi_composite_sa"]
    model.fit(X, y)

    # Predict horizon months ahead
    last_date = pd.to_datetime(df["date"]).max()
    horizon_months = params.get("horizon_months", 12)
    for i in range(horizon_months):
        predict_date = (last_date + pd.DateOffset(months=i + 1)).date()
        yhat = float(
            model.predict(
                [
                    [
                        params["beds"],
                        params["baths"],
                        params["sqft_avg"],
                        df["price_to_rent"].iloc[-1],
                        df["hpi_mom_pct"].iloc[-1],
                        df["rent_mom_pct"].iloc[-1],
                    ]
                ]
            )[0]
        )
        results.append(
            {
                "model_name": "lightgbm_micro",
                "target": "property_price",
                "horizon_months": i + 1,
                "city": city,
                "predict_date": predict_date,
                "yhat": yhat,
                "yhat_lower": yhat * 0.97,
                "yhat_upper": yhat * 1.03,
                "features_version": "v1.1",
                "model_artifact_uri": "s3://models/lgbm_micro_v1.pkl",
            }
        )
    return results
