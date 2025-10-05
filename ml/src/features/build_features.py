# ml/src/features/build_features.py
import pandas as pd
from ml.src.utils.data_loader import load_hpi, load_rents, load_macro


def build_city_features(city: str):
    hpi = load_hpi(city)
    rents = load_rents(city)
    macro = load_macro()
    df = (
        hpi.merge(rents, on="date", how="left")
        .merge(macro, on="date", how="left")
        .fillna(method="ffill")
    )
    return df
