# 🏡 Housing Insights + Risk Dashboard

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3.x-green?logo=springboot&logoColor=white)
![Java](https://img.shields.io/badge/Java-17-red?logo=openjdk&logoColor=white)
![React](https://img.shields.io/badge/React-18-blue?logo=react&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?logo=typescript&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?logo=postgresql&logoColor=white)
![MinIO](https://img.shields.io/badge/MinIO-Storage-orange?logo=minio&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker&logoColor=white)

> _“In theory, theory and practice are the same. In practice, they are not.”_  
> — Albert Einstein

Predicting the housing market has been attempted many times — and most models have failed.  
This project takes another step forward, leveraging **up-to-date AI/ML technologies** with a clear and pragmatic design, built in just three months as an MVP.  
We approach it with both scientific rigor and a hopeful outlook for success.

---

## 📌 Project Overview

The **Housing Insights + Risk Dashboard** is a 3-month MVP (Sept–Nov 2025) that combines:

1. **Short-term Housing Insights** → AI/ML forecasts (1–2 years) of home prices & rents

   - Models: Prophet, LightGBM
   - Deliverables: forecasts for Kelowna, Vancouver, Toronto

2. **Long-term Housing Risk Dashboard** → Macro indicators and risk classification
   - Metrics: affordability, price-to-rent, debt-to-GDP, interest rates
   - Crisis-similarity classifier (e.g., “Today looks 80% like 2008”)

---

## 🏗 Architecture

- **Data Layer:** PostgreSQL (+PostGIS), MinIO for raw snapshots and artifacts
- **ML Models (Python):** Forecasting, risk, anomalies, sentiment (HuggingFace DistilBERT)
- **API Layer (Java):** Spring Boot REST API serving ML outputs from Postgres
- **Frontend (TypeScript):** React dashboard with charts, risk gauge, and PDF download
- **Reports:** 2-page PDF (Forecast + Risk) per city

📖 See [docs/architecture.md](./docs/architecture.md) for details.

---

## 🚀 Deliverables

- 📊 Interactive React dashboard (3 cities)
- ⚙️ REST API (Spring Boot, PostgreSQL, MinIO)
- 🤖 ML models: forecasting, risk index, anomaly detection, sentiment NLP
- 📑 2-page PDF reports (Kelowna, Vancouver, Toronto)

---

## 👥 Team

- **Yuri** → Data engineering, ML models, reports
- **Max** → API layer (Spring Boot) + Frontend (React/TS)

---

## 📂 Documentation

See the [docs](./docs) folder for:

- [Architecture](./docs/architecture.md)
- [Data Sources](./docs/data_sources.md)
- [Modeling](./docs/modeling.md)
- [API Reference](./docs/api_reference.md)
- [Reports](./docs/reports.md)
- [Presentations](./docs/presentations)

---

## 🗓 Timeline

- Start: **Sept 1, 2025**
- End: **Nov 20, 2025**
- See [Project Roadmap](./docs/architecture.md#-project-roadmap-sept-1--nov-20-2025)

---
