# Utils

This folder contains **shared utilities** for all modeling pipelines.

## Purpose
- Avoid duplication by providing **common helpers**.
- Handle database I/O, logging, evaluation, and configuration.

## Examples
- `data_loader.py` → load timeseries slices from Postgres.
- `db_writer.py` → insert predictions into `model_predictions`, `risk_predictions`, `anomaly_signals`.
- `metrics.py` → evaluation metrics (RMSE, MAPE, etc.).
- `logger.py` → shared logging config for pipelines.

## Usage
Every model (forecasting, risk, anomalies) should **import utilities from here**.

