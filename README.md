# 🏡 Housing Insights + Risk Dashboard

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3.x-green?logo=springboot&logoColor=white)
![Java](https://img.shields.io/badge/Java-17-red?logo=openjdk&logoColor=white)
![React](https://img.shields.io/badge/React-18-blue?logo=react&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?logo=typescript&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?logo=postgresql&logoColor=white)
![MinIO](https://img.shields.io/badge/MinIO-Storage-orange?logo=minio&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker&logoColor=white)

Predicting the housing market has been attempted many times — and most models have failed.  
This project takes another step forward, leveraging **modern AI/ML technologies** with a clear and pragmatic design, built in just three months as an MVP.  
We approach it with both scientific rigor and a hopeful outlook for success.

---

## 📌 Project Overview

The **Housing Insights + Risk Dashboard** is a 3-month MVP (Sept–Nov 2025) that combines:

1. **Short-term Housing Insights** → AI/ML forecasts (1–2 years) of home prices & rents  
   - Models: Prophet, LightGBM  
   - Deliverables: forecasts for Kelowna, Vancouver, Toronto  

2. **Long-term Housing Risk Dashboard** → Macro indicators and risk classification  
   - Metrics: affordability, price-to-rent, debt-to-GDP, interest rates  
   - Crisis-similarity classifier (e.g., “Today looks 80 % like 2008”)  

---

## 🧠 Theoretical Foundation

The project is grounded in both **economic theory** and **machine learning methodology**, outlined in  
[docs/manual/index.md](./docs/manual/index.md).  

Key theoretical pillars include:

- **Hedonic Pricing Theory** — housing prices reflect the sum of the implicit value of their attributes  
- **Market Efficiency vs. Behavioral Biases** — exploring why prices deviate from fundamentals  
- **Risk Modeling and Early-Warning Indicators** — inspired by financial stability research  
- **AI/ML Forecasting Framework** — using time-series and ensemble models to capture trend, seasonality, and anomaly signals  

Together, these provide the conceptual bridge between economic insight and data-driven forecasting.

---

## 🏗 Architecture

### **Phase 1 – MVP (Current)**  
- **Data Layer:** PostgreSQL (+PostGIS), MinIO for raw snapshots and artifacts  
- **ML Layer (Python):** Forecasting, risk indices, anomaly detection, sentiment analysis (DistilBERT)  
- **Orchestration:** Docker Compose for Postgres, MinIO, and ETL pipelines  
- **Frontend (React/TypeScript):** Interactive dashboard (in progress)  

### **Phase 2 – Planned Integration (Dec 2025 – Feb 2026)**  
- **API Gateway (Java + Spring Boot):** Will serve ML forecasts and risk indicators from Postgres to frontend clients  
- **Authentication & Role-Based Access:** Planned implementation for secure API endpoints  

📖 See [docs/architecture.md](./docs/architecture.md) for technical details.

---

## 🚀 Deliverables

- 📊 AI-driven forecasts (Kelowna, Vancouver, Toronto)  
- ⚙️ End-to-end ETL pipelines (CREA, CMHC, BoC, StatCan)  
- 🤖 ML models: forecasting, risk index, anomaly detection, sentiment NLP  
- 📑 Automated 2-page PDF reports per city  
- 🌐 Planned REST API gateway (Spring Boot + Java 17)  

---

## 👥 Team

- **Yuri** → Data Engineering, ML Models, Reports  
- **Max** → Frontend (React/TypeScript) and upcoming Spring Boot API integration  

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

- **Phase 1 (MVP):** Sept 1 – Nov 20 2025  
- **Phase 2 (Integration):** Dec 2025 – Feb 2026  
- See [Project Roadmap](https://github.com/users/yuri-spizhovyi-mit/projects/2/views/4)  

---
