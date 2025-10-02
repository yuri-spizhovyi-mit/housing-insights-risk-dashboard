import pandas as pd


def calc_affordability(df: pd.DataFrame, city: str):
    """
    Calculate a simple affordability index.
    Normalized 0.0–1.0 (higher = less affordable).
    """
    latest_val = df["value"].iloc[-1]
    affordability = min(latest_val / 1_000_000, 1.0)  # fake normalization

    return {
        "city": city,
        "risk_type": "affordability",
        "predict_date": df["date"].iloc[-1],
        "risk_value": affordability,
        "model_name": "calc",
    }
