# 🧩 Data Flow — Housing Insights + Risk Dashboard

This document provides a comprehensive overview of how data moves across the system — from external sources, through ETL and feature engineering, to machine learning models, APIs, and the React dashboard.

---

## 🧠 End-to-End Overview (v2 — with Craigslist Listings)

```mermaid
graph TD
    %% --- ETL LAYER ---
    subgraph ETL["ETL Layer (ml/src/etl)"]
        CREA[CREA HPI Adapter] --> HPI[(house_price_index)]
        BOC[Bank of Canada Adapter] --> METRICS[(metrics)]
        STATCAN[StatCan CPI Adapter] --> METRICS
        CMHC[CMHC Adapter] --> METRICS
        CL[Craigslist Adapter (crg_listing.py)] --> LRAW[(listings_raw)]
        LISTINGS_PROC[listings_features.py] --> LFEAT[(listings_features)]
        LRAW --> LISTINGS_PROC
        NEWS[News & Sentiment Adapter] --> SENT[(news_articles & news_sentiment)]
    end

    %% --- FEATURE ENGINEERING (MACRO) ---
    subgraph FEAT["Feature Engineering (ml/src/features/build_features.py)"]
        HPI --> FEATURES[(features)]
        METRICS --> FEATURES
        %% rent_index is optional/synthetic for now; if available, include it
        %% RENT --> FEATURES
    end

    %% --- MODELING LAYERS ---
    subgraph ML["Modeling Layer (ml/src/models & micro_forecasting)"]
        FEATURES --> PROPHET[Prophet / ARIMA]
        FEATURES --> RISK[Composite Risk / Affordability]
        FEATURES --> ISOF[Isolation Forest]
        LFEAT --> LGBM[LightGBM Property Model]
        FEATURES --> LGBM
        PROPHET --> MODEL_PRED[(model_predictions)]
        RISK --> RISK_PRED[(risk_predictions)]
        ISOF --> ANOM[(anomaly_signals)]
        LGBM --> PROP_PRED[(property_price_predictions)]
    end

    %% --- API LAYER ---
    subgraph API["FastAPI Layer (ml/src/api)"]
        MODEL_PRED -->|GET /forecast| FASTAPI
        RISK_PRED -->|GET /risk| FASTAPI
        ANOM -->|GET /anomalies| FASTAPI
        PROP_PRED -->|GET /property_price| FASTAPI
        SENT -->|GET /sentiment| FASTAPI
    end

    %% --- UI LAYER ---
    subgraph UI["React + TypeScript Dashboard"]
        FASTAPI --> HOMEPRICE["🏡 Home Price Forecast"]
        FASTAPI --> RENTPRICE["🏢 Rent Price Forecast"]
        FASTAPI --> RISKGAUGE["⚙️ Risk Gauge"]
        FASTAPI --> ANOMUI["📉 Market Anomalies"]
        FASTAPI --> SENTFEED["📰 Sentiment Feed"]
        FASTAPI --> ESTIMATOR["💰 Property Price Estimator"]
    end
```

---

## 🔄 Stage-by-Stage Summary

| Stage                               | Layer                                                 | Description                                                                                                                       | Output Tables                                                                                                 |
| ----------------------------------- | ----------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| **1. Data Extraction & Load (ETL)** | Python adapters in `ml/src/etl/`                      | Fetch from CREA, BoC, StatCan, CMHC, **Craigslist** (real listings), and News. Store in raw/aggregate tables.                     | `house_price_index`, `metrics`, `listings_raw`, `news_articles`, `news_sentiment` *(optional:* `rent_index`)* |
| **2. Macro Feature Engineering**    | `ml/src/features/build_features.py`                   | Merge macro sources into unified monthly **city-date** table with engineered fields (`price_to_rent`, `hpi_mom_pct`).             | `features`                                                                                                    |
| **3. Micro Feature Engineering**    | `ml/src/etl/listings_features.py`                     | Clean and encode **Craigslist** listings into ML-ready property-level features (`price_per_sqft`, `property_age`, one-hot types). | `listings_features`                                                                                           |
| **4. Modeling — Macro**             | `ml/src/models`                                       | Forecast city-level price & rent, risk, anomalies.                                                                                | `model_predictions`, `risk_predictions`, `anomaly_signals`                                                    |
| **5. Modeling — Micro**             | `ml/src/micro_forecasting/property_price_forecast.py` | Train LightGBM on `listings_features` + join with `features`; apply macro scaling for forward-looking estimates.                  | `property_price_predictions`                                                                                  |
| **6. Serving Layer (API)**          | FastAPI                                               | Endpoints `/forecast`, `/risk`, `/anomalies`, `/property_price`, `/sentiment`.                                                    | Reads from model tables                                                                                       |
| **7. Presentation Layer (UI)**      | React + TypeScript                                    | Charts, risk gauges, property estimator, sentiment/news.                                                                          | Calls FastAPI endpoints                                                                                       |

---

## 🏗 Database Schema Overview (updated)

| Category                    | Tables                                                                                     | Description                                                               |
| --------------------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------- |
| **Raw & Aggregated Data**   | `listings_raw`, `house_price_index`, `metrics`, *(optional)* `rent_index`, `news_articles` | Direct from ETL adapters (Craigslist now primary for listings)            |
| **Feature-Engineered Data** | `listings_features`, `features`                                                            | `features` = macro (city/date); `listings_features` = micro (per listing) |
| **Model Outputs**           | `model_predictions`, `risk_predictions`, `anomaly_signals`, `property_price_predictions`   | Served by FastAPI                                                         |
| **Reference & Auxiliary**   | `news_sentiment`                                                                           | NLP-derived sentiment scores per city/date                                |

---

## 🧱 File Responsibilities (key)

| File                                                  | Role                                                                      |
| ----------------------------------------------------- | ------------------------------------------------------------------------- |
| `ml/src/etl/crg_listing.py`                           | **Craigslist** scraper → writes `public.listings_raw`                     |
| `ml/src/etl/listings_features.py`                     | Cleans & encodes raw listings → `public.listings_features`                |
| `ml/src/features/build_features.py`                   | Builds macro `public.features` from CREA/BoC/StatCan/CMHC                 |
| `ml/src/micro_forecasting/property_price_forecast.py` | Trains LightGBM & predicts property prices → `property_price_predictions` |
| `ml/src/models/*`                                     | Macro forecasting (Prophet/ARIMA), risk, anomalies                        |
| `ml/src/api/*`                                        | FastAPI routes                                                            |
| `services/ui/*`                                       | React dashboard components                                                |

---

## 🚀 Typical Workflow (updated)

1. Run Craigslist ETL: `python ml/src/etl/crg_listing.py`
2. Build listings features: `python ml/src/etl/listings_features.py`
3. Build macro features: `make features`
4. Train macro models (Prophet/ARIMA) & risk/anomaly pipelines
5. Train micro model: `python ml/src/micro_forecasting/property_price_forecast.py`
6. Serve via FastAPI → visualize in UI

---

## 📘 Related Docs

* [Architecture Overview](./architecture.md)
* [Data Sources](./data_sources.md)
* [API Reference](./api_reference.md)
* [Modeling Notes](./modeling.md)
* [Architecture V2 – Micro Forecasting](./architecture_v2_micro_forecasting.md)
