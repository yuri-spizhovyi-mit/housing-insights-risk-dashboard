# 🧮 Predictive Data Flow — Observation vs. Prediction Horizon

This document explains how **historical data transforms into future forecasts** across the Housing Insights + Risk Dashboard architecture.

---

## 🧭 Concept Overview

> **We don’t predict from today’s listings — we learn from the past to simulate the future.**

| Step | Concept | Description |
|------|----------|-------------|
| **1. Observation (Time t)** | Historical samples | Each record = `(date, city, features, target price)` from ETL + features tables. |
| **2. Learning** | Model training | Prophet/ARIMA learn temporal macro trends; LightGBM learns property-level price behaviour. |
| **3. Projection (Time t → t + h)** | Forecast macro drivers | Prophet/ARIMA extend features (HPI, rent, CPI…) → `features_future`. |
| **4. Simulation (Time t + h)** | Synthetic future rows | Combine predicted macro features with real property configurations → `prediction_grid`. |
| **5. Inference (Time t + h)** | Predict outcomes | Feed synthetic rows into trained model → `model_predictions` (future ŷ). |

---

## 🧩 End-to-End Diagram

```mermaid
graph TD

    %% === ETL ===
    subgraph ETL["1️⃣ ETL — Historical Observation"]
        CREA[CREA HPI]
        RENT[RentFaster / Rentals.ca]
        STATCAN[StatCan CPI / GDP / Population]
        BOC[Bank of Canada Rates]
    end
    CREA --> HPI[(house_price_index)]
    RENT --> RENT_IDX[(rent_index)]
    STATCAN --> DEMO[(demographics)]
    BOC --> METRICS[(metrics)]

    %% === FEATURE ENGINEERING ===
    subgraph FEAT["2️⃣ Feature Engineering — Historical Context"]
        FEATURES[(features<br>(macro-level time-series))]
        LISTINGS_RAW[(listings_raw)]
        LISTINGS_FEAT[(listings_features)]
    end
    HPI --> FEATURES
    RENT_IDX --> FEATURES
    DEMO --> FEATURES
    METRICS --> FEATURES
    LISTINGS_RAW --> LISTINGS_FEAT

    %% === MODEL TRAINING ===
    subgraph MODEL["3️⃣ Modeling — Learn Historical Patterns"]
        PROPHET[Prophet / ARIMA]
        LIGHTGBM[LightGBM / XGBoost]
    end
    FEATURES --> PROPHET
    FEATURES --> LIGHTGBM
    LISTINGS_FEAT --> LIGHTGBM

    %% === FORECASTING ===
    subgraph FORECAST["4️⃣ Forecast — Prediction Horizon"]
        FEATURES_FUTURE[(features_future<br>(forecasted macro context))]
        GRID[(prediction_grid<br>(synthetic combinations))]
        FUTURE_JOIN[(features_future × prediction_grid)]
    end
    PROPHET --> FEATURES_FUTURE
    LISTINGS_FEAT --> GRID
    FEATURES_FUTURE --> FUTURE_JOIN
    GRID --> FUTURE_JOIN
    FUTURE_JOIN --> LIGHTGBM

    %% === SERVING ===
    subgraph SERVE["5️⃣ Serving — UI / API Layer"]
        MODEL_PRED[(model_predictions)]
    end
    LIGHTGBM --> MODEL_PRED
```

---

## 🧠 Mapping Concept → Implementation

| Conceptual Step | Implementation Location | Output Table / Artifact | Description |
|-----------------|--------------------------|--------------------------|--------------|
| **1️⃣ Historical Samples** | `ml/src/features/build_features.py` | `public.features` | Merge macroeconomic data from HPI, rent, BoC, StatCan into monthly feature snapshots. |
| **2️⃣ Model Training** | `ml/src/models/pipeline.py` | model artifacts (.pkl / MLflow) | Prophet learns macro trends, LightGBM learns price behaviour. |
| **3️⃣ Forecast Macro Drivers** | `ml/src/models/forecasting/features_forecast.py` | `public.features_future` | Extend HPI, rent, CPI, GDP into future months. |
| **4️⃣ Generate Synthetic Future Rows** | `ml/src/models/predict_grid.py` | `prediction_grid` | Cross-join property configurations with future macro context. |
| **5️⃣ Predict Future Prices** | `ml/src/models/predict_future_prices.py` | `public.model_predictions` | Apply trained model to synthetic rows and output ŷ for UI. |

---

## ✅ Summary

| Phase | Description | Data Product |
|--------|--------------|---------------|
| **Observation** | ETL builds factual, historical data. | `features`, `listings_features` |
| **Learning** | Models trained on past patterns. | Trained Prophet/LightGBM artifacts |
| **Projection** | Forecast future macro trends. | `features_future` |
| **Simulation** | Create synthetic combinations. | `prediction_grid` |
| **Inference** | Predict and serve results. | `model_predictions` |

---

**Last Updated:** 2025‑10‑13
