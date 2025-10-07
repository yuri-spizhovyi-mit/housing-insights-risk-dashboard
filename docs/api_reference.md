# 🌐 API Reference (FastAPI)

The API is served via **FastAPI (Python)** and provides endpoints for forecasts, risk indicators, sentiment, and PDF reports.  
All endpoints return structured JSON (or PDF for reports).

## Base URLs

Local:

```http

http://localhost:8000
```

Production:

```http
https://housing-insights-risk-dashboard.vercel.app/docs#/
```

---

## 🔑 Common Query Parameters

| Param          | Type   | Example              | Notes                                           |
| -------------- | ------ | -------------------- | ----------------------------------------------- |
| `city`         | string | Toronto              | Required for `/forecast`, `/risk`, `/sentiment` |
| `target`       | string | `price` or `rent`    | Optional for `/forecast`                        |
| `horizon`      | string | `1y` `2y` `5y` `10y` | Forecast horizon                                |
| `propertyType` | string | Condo                | Optional filter                                 |
| `beds`         | number | 2                    | Optional                                        |
| `baths`        | number | 2                    | Optional                                        |
| `sqftMin`      | number | 800                  | Optional                                        |
| `sqftMax`      | number | 1200                 | Optional                                        |
| `yearBuiltMin` | number | 2000                 | Optional                                        |
| `yearBuiltMax` | number | 2025                 | Optional                                        |

---

## 📌 Endpoints

| Method | Endpoint             | Description                             |
| -----: | -------------------- | --------------------------------------- |
|    GET | `/cities`            | List cities and property types          |
|    GET | `/forecast`          | Forecast (prices or rents) with filters |
|    GET | `/risk`              | Risk indicators for a city              |
|    GET | `/sentiment`         | News sentiment & headlines              |
|    GET | `/report/{city}.pdf` | Download PDF report for a city          |
|    GET | `/anomalies`         | Market anomalies detection for a city   |

---

### Example Responses

#### /cities

```json
{
  "cities": {
    "Kelowna": ["Condo", "House"],
    "Toronto": ["Condo"]
  }
}
```

#### /forecast

```json
{
  "city": "Toronto",
  "target": "price",
  "horizon": 12,
  "data": [
    { "date": "2025-10-01", "value": 750000, "lower": 720000, "upper": 780000 }
  ]
}
```

#### /risk

```json
{
  "city": "Toronto",
  "date": "2025-09-21",
  "score": 62,
  "breakdown": [
    { "name": "Affordability", "status": "Tight" },
    { "name": "Price-to-Rent", "status": "Elevated" },
    { "name": "Inventory", "status": "Low" }
  ]
}
```

#### /sentiment

```json
{
  "city": "Toronto",
  "items": [
    {
      "date": "2025-08-29",
      "headline": "New supply targets announced",
      "sentiment": "NEU"
    }
  ]
}
```

#### /anomalies

```json
{
  "city": "Toronto",
  "anomalies": [
    { "date": "2025-08-01", "metric": "price", "value": 850000, "expected": 780000, "deviation": "+9%" }
  ]
}
```
#### /report/{city}.pdf

- Returns binary PDF
