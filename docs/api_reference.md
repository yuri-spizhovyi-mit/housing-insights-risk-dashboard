# 🌐 API Reference

The API is served via **Spring Boot (Java)** and provides endpoints for forecasts, risk indicators, anomalies, sentiment, and PDF reports.  
All endpoints return structured JSON (or PDF for reports).

Base URL (local):

```http
http://localhost:8080/v1
```

Base URL (production):

```http
https://housing-insights-risk-dashboard.vercel.app/
```

---

## 📌 Endpoints

| Method | Endpoint             | Description                         |
| ------ | -------------------- | ----------------------------------- |
| GET    | `/cities`            | List supported cities               |
| GET    | `/forecast/{city}`   | Forecast (prices or rents) for city |
| GET    | `/risk/{city}`       | Risk indicators for a city          |
| GET    | `/sentiment/{city}`  | News sentiment index for a city     |
| GET    | `/report/{city}.pdf` | Download PDF report for a city      |

---

## 📝 Example Requests & Responses

### 1. `/v1/cities`

**Request:**

```http
GET /v1/cities
```

**Response:**

```json
{
  "cities": ["Kelowna", "Vancouver", "Toronto"]
}
```

---

### 2. `/v1/metrics/{city}`

**Request:**

```http
GET /v1/metrics/Toronto
```

**Response:**

```json
{
  "city": "Toronto",
  "metrics": {
    "median_price": 865000,
    "median_rent": 2450,
    "population": 2809000,
    "gdp_per_capita": 68200
  },
  "last_updated": "2025-09-24"
}
```

---

### 3. `/v1/forecast/{city}`

**Request:**

```http
GET /v1/forecast/Kelowna
```

**Response:**

```json
{
  "city": "Kelowna",
  "horizon_months": 24,
  "last_updated": "2025-09-24",
  "forecasts": [
    {
      "date": "2025-10-01",
      "price": 785000,
      "rent": 2150,
      "yhat_lower": 765000,
      "yhat_upper": 805000
    },
    {
      "date": "2025-11-01",
      "price": 790000,
      "rent": 2170,
      "yhat_lower": 770000,
      "yhat_upper": 812000
    }
  ]
}
```

---

### 4. `/v1/risk/{city}`

**Request:**

```http
GET /v1/risk/Vancouver
```

**Response:**

```json
{
  "city": "Vancouver",
  "risk_index": 0.78,
  "level": "High",
  "crisis_similarity": { "2008": 0.82, "1990": 0.64 },
  "indicators": {
    "affordability": 0.81,
    "price_to_rent": 32.5,
    "debt_to_gdp": 92.1,
    "interest_rate": 5.25
  },
  "last_updated": "2025-09-25"
}
```

---

### 5. `/v1/anomalies/{city}`

**Request:**

```http
GET /v1/anomalies/Toronto
```

**Response:**

```json
{
  "city": "Toronto",
  "anomalies": [
    {
      "date": "2025-08-15",
      "series": "rent",
      "value": 2300,
      "expected": 2450,
      "z_score": -2.1
    },
    {
      "date": "2025-08-20",
      "series": "price",
      "value": 810000,
      "expected": 850000,
      "z_score": -3.0
    }
  ],
  "last_updated": "2025-09-25"
}
```

---

### 6. `/v1/sentiment/{city}`

**Request:**

```http
GET /v1/sentiment/Vancouver
```

**Response:**

```json
{
  "city": "Vancouver",
  "sentiment_index": 0.42,
  "label": "Negative",
  "trend_30d": [0.55, 0.51, 0.47, 0.42],
  "top_headlines": [
    "Rising mortgage rates dampen housing market",
    "Rents stabilize after summer surge"
  ],
  "last_updated": "2025-09-25"
}
```

---

### 7. `/v1/report/{city}.pdf`

**Request:**

```http
GET /v1/report/Kelowna.pdf
```

**Response:**

- Content-Type: `application/pdf`
- Binary PDF stream (2-page forecast + risk report)

---

## ⚙️ Notes

- All endpoints return structured JSON on success.
- Error responses use standard HTTP codes:
  - `400` Bad Request (invalid city, parameters)
  - `404` Not Found (no data for city/date)
  - `500` Internal Server Error
- Timestamps are in `YYYY-MM-DD` format (UTC).
- Reports are versioned by city + month in MinIO.
