# 🏗 System Architecture (FastAPI-first)

The Housing Insights + Risk Dashboard MVP is composed of five main layers:

---

## 1) Frontend (React / TypeScript)

- Owner: Max
- Built with React + TypeScript + Vite
- Features:
  - Filters: City, Horizon, Property Type, Beds, Baths, Sqft range, Year Built
  - Charts: Home Price Forecast (Recharts), Rent Forecast (Recharts)
  - Risk Gauge (Recharts), Sentiment feed
  - Report download (PDF)

---

## 2) API Layer (FastAPI / Python)

— **Current**

- Owner: Max & Yuri
- Responsibilities: serve forecasts, risk indicators, sentiment, reports
- Endpoints:
  - `/cities`
  - `/forecast` (query params for filters)
  - `/risk`
  - `/sentiment`
  - `/report/{city}.pdf`
- Features:
  - CORS for `localhost:5173` and `hird.netlify.app`
  - OpenAPI schema via FastAPI
  - Ready for React Query integration

---

## 3) Model Layer (Python)

- Forecasting (Prophet / LightGBM)
- Risk logic (composite indices)
- Sentiment (NLP pipeline)
- Artifacts stored in object storage (e.g., MinIO/S3)

---

## 4) Reporting Layer (Python)

- Jinja2 → HTML → PDF
- Exposed as `/report/{city}.pdf`

---

## 5) Data Layer

- PostgreSQL (Neon) for:
  - `model_predictions` (serving cache)
  - Aggregates (house_price_index, rent_index, demographics, macro, news_sentiment)
- Object storage (MinIO/S3) for raw snapshots & artifacts

---

## 🔭 Future: Java API Gateway (Spring Boot)

- Purpose: Authentication, rate limiting, tenant routing, observability
- Mode: Reverse proxy → forwards `/cities`, `/forecast`, `/risk`, `/sentiment`, `/report` to FastAPI
- Contract: JSON shapes remain the same; only base URL changes

---

## 📊 Diagram

![System Architecture](../docs/img/architecture-diagram.png)

---

## Principles

- API-first contracts (stable JSON shapes)
- Separation of concerns (UI ↔ API ↔ ML)
- Reproducibility & versioning
- Simple local & cloud deploys
