# ML & Data Pipelines

This folder contains all Python code for:

- ETL from CREA, CMHC, StatCan, BoC, Rentals.ca, News RSS
- Feature engineering
- Models (Prophet/LightGBM forecasting, risk classifier, anomalies, sentiment)
- PDF report generation

## Structure

- `src/` → library code
- `pipelines/` → orchestration scripts
- `notebooks/` → exploratory notebooks
- `reports/` → templates + sample PDFs
- `tests/` → pytest unit and integration tests

```mermaid
flowchart LR
    A[Raw Data Sources\n(CREA, CMHC, RentFaster,\nStatCan, BoC)] --> B[Listings Raw\n(listings_raw, macro_data)]
    B --> C[Feature Engineering\n(cleaning, price_per_sqft,\none-hot encoding, etc.)]
    C --> D[Listings Features\n(ML-ready tables)]
    D --> E[Model Training\n(batch/offline)]
    E --> F[Predictions Table\n(model_predictions,\nrisks, sentiment)]
    F --> G[API / Gateway Layer\n(fast queries)]
    G --> H[Customer UI\n(charts, risks, forecasts)]

    D --> E
    E --> F
```
