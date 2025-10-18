# 🏡 Housing Insights + Risk Dashboard

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3.x-green?logo=springboot&logoColor=white)
![Java](https://img.shields.io/badge/Java-21-red?logo=openjdk&logoColor=white)
![React](https://img.shields.io/badge/React-18-blue?logo=react&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?logo=typescript&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?logo=postgresql&logoColor=white)
![MinIO](https://img.shields.io/badge/MinIO-Storage-orange?logo=minio&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker&logoColor=white)

Forecasting housing market dynamics remains one of the most challenging and important problems in applied economics and data science.  
This project provides a transparent, data-driven framework developed as a 3-month MVP to explore whether modern machine-learning and econometric approaches can improve the interpretability and predictive stability of housing indicators across Canadian cities.

---

## 📌 Project Overview

The **Housing Insights + Risk Dashboard** integrates data engineering, time-series forecasting, and economic modeling into a single analytical platform.

1. **Short-Term Housing Insights** → AI/ML forecasts of home prices and rental indices (1–10 years ahead)  
   - Models: **Prophet**, **ARIMA**, **LightGBM (planned for micro-forecasts)**  
   - Outputs: rent index and price forecasts for Vancouver and Toronto  

2. **Long-Term Housing Risk Dashboard** → macro indicators and risk classification  
   - Metrics: affordability, price-to-rent, debt-to-GDP, interest rates, and other structural measures  
   - *Planned:* crisis-similarity classifier (e.g., “today’s market resembles 2008 conditions by 80 %”)

---

## 🧠 Forecasting Framework

The forecasting module integrates **statistical**, **machine-learning**, and **macro-economic** perspectives.

| Model | Level | Purpose |
|--------|--------|----------|
| **Prophet** | Macro | Captures trend and seasonality in rent and price indices |
| **ARIMA** | Macro | Serves as a statistical baseline for Prophet comparison |
| **LightGBM** | Micro | Learns feature-based relationships between rent index, listings data, and macro indicators to forecast city- and property-level prices |

At the current stage, **Prophet** and **ARIMA** produce multi-horizon forecasts (1, 2, 5, 10 years) for each city and target variable.  
All predictions are stored in the `public.model_predictions` table and visualized in the React dashboard.

The upcoming **LightGBM** layer will introduce supervised learning trained on a historical dataset built from:
- `house_price_index` (target variable → future HPI)
- `rent_index`
- macro indicators from the Bank of Canada and StatCan
- aggregated listing features (price, rent-to-price, square footage, bedrooms)

This will enable **hybrid forecasting** that links macroeconomic trends with micro-market signals, generating property-type-specific predictions (e.g., *“Vancouver – 2 bed Condo → $478 K ± 5 % in 12 months”*).

---

## 🧩 Database Schema Overview

The project’s PostgreSQL database integrates multiple layers of data — from raw listings to model forecasts — to ensure full traceability and reproducibility.

| Table | Purpose | Example Columns |
|--------|----------|----------------|
| `rent_listings_raw` | Raw rental listings scraped from RentFaster, Castanet, etc. | `city`, `price`, `bedrooms`, `sqft`, `url` |
| `rents` | Monthly median rent aggregates per city and bedroom type | `city`, `date`, `bedroom_type`, `median_rent`, `source` |
| `house_price_index` | Composite and property-type price indices (CREA, CMHC) | `city`, `date`, `hpi_composite_sa`, `mom_pct` |
| `metrics` | Macro-economic indicators (BoC, StatCan, CMHC) | `date`, `interest_rate`, `cpi`, `gdp_growth`, `unemployment_rate` |
| `features` | Combined macro + micro features for model training | `city`, `date`, `rent_index`, `price_index`, `debt_gdp_ratio` |
| `model_predictions` | Multi-horizon forecasts from Prophet, ARIMA, LightGBM | `city`, `target`, `predict_date`, `yhat`, `yhat_lower`, `yhat_upper` |
| `risk_predictions` | Risk index outputs from ARIMA or LightGBM | `city`, `predict_date`, `risk_score` |
| `anomaly_signals` | Detected anomalies via IsolationForest | `city`, `predict_date`, `is_anomaly`, `score` |

---

## 🏗 Architecture

### **Phase 1 – MVP (Current)**
- **Data Layer:** PostgreSQL (+ PostGIS), MinIO for snapshots and model artifacts  
- **ETL Layer:** Automated pipelines for CREA, CMHC, BoC, and StatCan  
- **ML Layer:** Prophet and ARIMA forecasts, anomaly detection, sentiment analysis (DistilBERT)  
- **Orchestration:** Docker Compose for Postgres, MinIO, and Python ETL containers  
- **Frontend:** React + TypeScript dashboard (in progress)  

### **Phase 2 – Planned Integration (Dec 2025 – Feb 2026)**
- **API Gateway:** Java + Spring Boot service to expose ML forecasts and risk metrics  
- **LightGBM Training Module:** Supervised micro-forecasting integration  
- **Authentication & Access Control:** Secure API endpoints for research use  

📖 See [docs/architecture.md](./docs/architecture.md) for technical details.

---

## 🚀 Deliverables

- 📊 Forecasts for rent and price indices (Prophet + ARIMA)  
- ⚙️ End-to-end ETL pipelines (CREA, CMHC, BoC, StatCan)  
- 🤖 ML modules: forecasting, risk indices, anomaly detection, sentiment NLP  
- 📑 Automated two-page PDF summaries per city  
- 🌐 Planned Spring Boot API integration with React dashboard  

---

## 👥 Team

- **Yuri Spizhovyi** — Data Engineering, ML Modeling, Reporting  
- **Max Spizhovyi** — Frontend Development (React/TypeScript) and Spring Boot API Integration  

---

## 📂 Documentation

See the [docs](./docs) folder for:  
- [Architecture](./docs/architecture.md)  
- [Data Sources](./docs/data_sources.md)  
- [Modeling](./docs/modeling.md)  
- [Reports](./docs/reports.md)  
- [Presentations](./docs/presentations)  

---

## 🗓 Timeline

| Phase | Period | Focus |
|--------|---------|--------|
| **I. MVP Implementation** | Sept – Nov 2025 | ETL pipelines, Prophet/ARIMA forecasting, database integration |
| **II. System Integration** | Dec 2025 – Feb 2026 | API Gateway, LightGBM training, UI enhancements |
| **III. Risk Modeling (optional)** | Mar – Apr 2026 | Crisis-similarity classifier and composite risk index |

📈 For detailed milestones, see the [Project Roadmap](https://github.com/users/yuri-spizhovyi-mit/projects/2/views/4).

---

### ✅ Summary of Updates

| Topic | Status |
|-------|--------|
| Rephrased introduction | ✅ Now objective and research-focused |
| Added ARIMA to models | ✅ Included in Forecasting Framework |
| Expanded forecasting description | ✅ Reflects Prophet + ARIMA current and LightGBM planned |
| Crisis-similarity classifier | ⚙️ Not implemented yet – planned for Phase III |
