# Modeling Layer — Housing Insights & Risk Dashboard

This folder contains all forecasting and machine learning components of the Housing Insights + Risk Dashboard.

## Structure Overview

| File | Description |
|------|--------------|
| **pipeline.py** | Main macro forecasting pipeline — runs Prophet (time-series), ARIMA (risk indices), and IsolationForest (anomaly detection) for `house_price_index`, `rent_index`, and `metrics`. |
| **run_models_micro_update.py** | Scales macro forecasts into property-level micro forecasts using rent ratios derived from recent listings (`listings_raw`). |
| **run_all_models.py** | 🧩 Unified runner that executes both macro and micro pipelines sequentially for complete forecast refresh. |
| **build_historical_dataset.py** | 🧱 Builds a supervised dataset for machine learning (LightGBM) by joining historical HPI, rent index, demographics, and macroeconomic indicators. Produces `data/historical_features.parquet`. |
| **train_lightgbm.py** | ⚡ Trains and evaluates a LightGBM regression model on the historical dataset to predict future HPI trends. Saves trained model under `models/lightgbm_hpi.txt`. |

## Typical Execution Flow

```bash
# 1️⃣ Run full forecasting stack (Prophet + Micro)
python ml/src/models/run_all_models.py

# 2️⃣ Build training dataset for LightGBM
python ml/src/models/build_historical_dataset.py

# 3️⃣ Train and evaluate LightGBM model
python ml/src/models/train_lightgbm.py
