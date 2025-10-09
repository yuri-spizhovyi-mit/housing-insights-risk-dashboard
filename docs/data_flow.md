# 🧩 Data Flow — Housing Insights + Risk Dashboard

This document provides a comprehensive overview of how data moves across the system — from external sources, through ETL and feature engineering, to machine learning models, APIs, and the React dashboard.

---

## 🧠 End-to-End Overview

```mermaid
graph TD
    subgraph ETL["ETL Layer (ml/src/etl)"]
        CREA[CREA HPI Adapter] --> HPI[(house_price_index)]
        CMHC[CMHC Adapter] --> METRICS[(metrics)]
        STATCAN[StatCan CPI Adapter] --> METRICS
        BOC[Bank of Canada Adapter] --> METRICS
        RENTALS[Rentals / RentFaster Adapter] --> RENT[(rent_index)]
        NEWS[News & Sentiment Adapter] --> SENT[(news_articles & news_sentiment)]
    end

    subgraph FEAT["Feature Engineering (ml/src/features/build_features.py)"]
        HPI --> FEATURES[(features)]
        METRICS --> FEATURES
        RENT --> FEATURES
    end

    subgraph ML["Modeling Layer (ml/src/models)"]
        FEATURES --> PROPHET[Prophet / ARIMA Forecasts]
        FEATURES --> RISK[Composite Risk Indices]
        FEATURES --> ISOF[Isolation Forest Anomalies]
        PROPHET --> MODEL_PRED[(model_predictions)]
        RISK --> RISK_PRED[(risk_predictions)]
        ISOF --> ANOMALY[(anomaly_signals)]
    end

    subgraph API["FastAPI Layer (ml/src/api)"]
        MODEL_PRED -->|GET /forecast| FASTAPI
        RISK_PRED -->|GET /risk| FASTAPI
        SENT -->|GET /sentiment| FASTAPI
        ANOMALY -->|GET /anomalies| FASTAPI
        FASTAPI --> REPORT[/report/{city}.pdf/]
    end

    subgraph UI["Frontend (React + TypeScript)"]
        FASTAPI --> UI_APP["HIRD Dashboard (Vite + Recharts)"]
    end

    UI_APP -->|Forecast charts| MODEL_PRED
    UI_APP -->|Risk Gauge| RISK_PRED
    UI_APP -->|Sentiment Feed| SENT
    UI_APP -->|PDF Report| REPORT
```

---

## 🔄 Stage-by-Stage Summary

| Stage | Layer | Description | Output Tables |
|-------|--------|--------------|----------------|
| **1. Data Extraction & Load (ETL)** | Python adapters in `ml/src/etl/` | Fetch from CREA, CMHC, StatCan, BoC, Rentals, and News APIs. Store in raw/aggregate tables. | `house_price_index`, `metrics`, `rent_index`, `news_articles`, `news_sentiment` |
| **2. Feature Engineering** | `ml/src/features/build_features.py` | Merge ETL outputs into unified macro-level `features` table with engineered fields like `price_to_rent`, `hpi_mom_pct`. | `features` |
| **3. Modeling** | `ml/src/models` | Train and generate forecasts (Prophet/ARIMA), risk indices, and anomaly scores. | `model_predictions`, `risk_predictions`, `anomaly_signals` |
| **4. Serving Layer (API)** | FastAPI | Serve endpoints `/forecast`, `/risk`, `/sentiment`, `/anomalies`, `/report/{city}.pdf`. | Reads from model & sentiment tables |
| **5. Presentation Layer (UI)** | React + TypeScript | Display live charts, risk gauges, and reports using Recharts and PDF viewer. | Calls FastAPI endpoints via React Query |

---

## 🏗 Database Schema Overview

| Category | Tables | Description |
|-----------|---------|--------------|
| **Raw & Aggregated Data** | `listings_raw`, `house_price_index`, `metrics`, `rent_index`, `demographics`, `macro_economic_data`, `news_articles`, `construction_permits` | Data directly from ETL adapters |
| **Feature-Engineered Data** | `listings_features`, `features` | `features` = macro-level (city/date); `listings_features` = micro-level (per listing) |
| **Model Outputs** | `model_predictions`, `risk_predictions`, `anomaly_signals` | Results consumed by UI & reports |
| **Reference & Auxiliary** | `news_sentiment` | NLP-derived sentiment scores per city/date |

---

## 🧱 File Responsibilities

| File | Role |
|------|------|
| `ml/src/etl/*.py` | Data ingestion adapters (BoC, StatCan, CREA, etc.) |
| `ml/src/features/build_features.py` | Merges ETL outputs → `public.features` |
| `ml/src/models/*.py` | Forecasting, risk, anomaly model training and prediction |
| `ml/src/reporting/report_generator.py` | Builds PDF reports for `/report/{city}.pdf` endpoint |
| `ml/src/api/*` | FastAPI routes serving forecasts, risks, sentiment, anomalies |
| `services/ui/` | React dashboard (charts, gauges, sentiment list, reports) |

---

## 🚀 Typical Workflow

1. Run ETL: `make etl` or individual source (e.g. `make etl-boc`)
2. Build features: `make features`
3. Train & forecast models: `python -m ml.src.models.pipeline`
4. Serve predictions through FastAPI
5. View results in the React dashboard (deployed via Netlify or Vercel)

---

## 📘 Related Docs

- [Architecture Overview](./architecture.md)
- [Data Sources](./data_sources.md)
- [API Reference](./api_reference.md)
- [Modeling Notes](./modeling.md)

