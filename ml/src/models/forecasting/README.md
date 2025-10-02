# Forecasting Models

## Purpose
Generate **time series forecasts** for housing metrics such as:
- Rent index
- House price index

## Current Models
- **Prophet** (`prophet_model.py`) → interpretable, seasonality-aware.
- **ARIMA** (`arima_model.py`) → statistical baseline.
- LightGBM (planned) → feature-rich machine learning approach.

## Pipeline
- `forecast_pipeline.py` → runs multiple models per city + target.
- Results written into **`model_predictions`**.

## Example Usage
