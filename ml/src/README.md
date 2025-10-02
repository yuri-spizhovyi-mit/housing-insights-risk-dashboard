# Modeling Layer

This folder contains the **core modeling components** of the Housing Insights & Risk Dashboard.

## Purpose
- Convert processed ETL data into **predictions, risk indices, and anomaly signals**.
- Provide a unified interface for **forecasting**, **risk analysis**, and **anomaly detection**.

## Submodules
- **forecasting/** → time series forecasting models (Prophet, ARIMA, LightGBM).
- **risk/** → affordability indices, price-to-rent, inventory stress, composite risk.
- **anomalies/** → anomaly detection (Isolation Forest, changepoints, statistical methods).
- **reporting/** → reporting helpers (PDF generation, evaluation summaries).

## Data Flow
1. ETL layer ingests and stores metrics into Postgres.
2. Models in this folder generate **predictions** or **indices**.
3. Results are written back into:
   - `model_predictions`
   - `risk_predictions`
   - `anomaly_signals`

## Status
✅ **Active** — forecasting, risk, and anomalies pipelines are connected to the API.
