# 🏡 Housing Insights + Risk Dashboard

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3.x-green?logo=springboot&logoColor=white)
![Java](https://img.shields.io/badge/Java-21-red?logo=openjdk&logoColor=white)
![React](https://img.shields.io/badge/React-18-blue?logo=react&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?logo=typescript&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?logo=postgresql&logoColor=white)
![MinIO](https://img.shields.io/badge/MinIO-Storage-orange?logo=minio&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker&logoColor=white)

### 🌐 **Live Demo**  
➡️ https://hird.netlify.app/

Forecasting housing market dynamics remains one of the most challenging and important problems in applied economics and data science.  
This project provides a transparent, data-driven framework developed as a 3-month MVP to explore whether modern machine-learning and econometric approaches can improve the interpretability and predictive stability of housing indicators across Canadian cities.

---

## 📌 Project Overview

The **Housing Insights + Risk Dashboard** integrates data engineering, time-series forecasting, and economic modeling into a single analytical platform.

1. **Short-Term Housing Insights** → AI/ML forecasts of home prices and rental indices (1–10 years ahead)  
   - Models: **Prophet**, **ARIMA**, **LSTM**  
   - Outputs: rent index and price forecasts for Vancouver, Toronto, Calgary, Edmonton, Ottawa, and others  

2. **Long-Term Housing Risk Dashboard** → macro indicators and risk classification  
   - Metrics: affordability, price-to-rent, debt-to-GDP, interest rates, and other structural measures  
   - *Planned:* crisis-similarity classifier (e.g., “today’s market resembles 2008 conditions by 80 %”)

---

## 🧠 Forecasting Framework

The forecasting module integrates **statistical**, **deep learning**, and **macro-economic** modeling.

| Model | Level | Purpose |
|--------|--------|----------|
| **Prophet** | Macro | Captures long-term trend/seasonality in price and rent indices |
| **ARIMA** | Macro | Robust statistical baseline; complements Prophet |
| **LSTM** | Deep Learning | Learns sequential nonlinear patterns in housing dynamics |

At the current stage, **Prophet**, **ARIMA**, and **LSTM** produce multi-horizon forecasts (1–60 months) for each city and target variable.  
All predictions are stored in the `public.model_predictions` table and visualized in the React dashboard.

Future enhancements will introduce hybrid modeling combining LSTM outputs with macro features and rental-listing signals for improved stability.

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
- **ML Layer:** Prophet, ARIMA, LSTM forecasting; anomaly detection  
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
| **I. MVP Implementation (Completed)** | Sept – Oct 2025 | ETL pipelines, Prophet/ARIMA forecasting, and database integration |
| **II. System Integration (In Progress)** | Oct – Dec 2025 | LightGBM model training, API Gateway (Spring Boot), and UI enhancements |
| **III. Risk Modeling (Next Phase)** | Dec 2025 – Feb 2026 | Crisis-similarity classifier and composite housing risk index |

📈 For detailed milestones, see the [Project Roadmap](https://github.com/users/yuri-spizhovyi-mit/projects/2/views/4).

---