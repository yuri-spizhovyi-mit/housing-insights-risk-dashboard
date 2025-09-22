# 📝 Task: Connect UI to FastAPI Endpoints

**Assignee:** Max  
**Status:** Open  
**Priority:** High

---

## 🎯 Goal

Replace all mock data in the HIRD dashboard with live data from FastAPI endpoints. Ensure every widget maps cleanly to its endpoint and response shape.

---

## 🔗 UI → API Mapping

### 1) City Selector (Dropdown)

- **API:** `GET /cities`
- **Use:** Populate City dropdown and (optionally) Property Type options per city
- **Response:**

```json
{
  "cities": {
    "Kelowna": ["Condo", "House"],
    "Toronto": ["Condo"],
    "Vancouver": ["Apartment", "Townhouse"]
  }
}
```

---

### 2) Home Price Forecast (Recharts Line)

- **API:** `GET /forecast`
- **Params:** from FilterContext → `city`, `target=price`, `horizon`, `propertyType`, `beds`, `baths`, `sqftMin`, `sqftMax`, `yearBuiltMin`, `yearBuiltMax`
- **Response:**

```json
{
  "city": "Kelowna",
  "target": "price",
  "horizon": 24,
  "data": [
    { "date": "2025-10-01", "value": 785000, "lower": 765000, "upper": 805000 }
  ]
}
```

- **Chart data expected by Recharts:**

```js
data.map((d) => ({
  date: d.date,
  value: d.value,
  lower: d.lower,
  upper: d.upper,
}));
```

---

### 3) Rent Forecast (Recharts Line)

- **API:** `GET /forecast`
- **Params:** same as above but `target=rent`
- **Response:** same structure, values are rent amounts

---

### 4) Risk Gauge

- **API:** `GET /risk?city={city}`
- **Response:**

```json
{
  "city": "Vancouver",
  "date": "2025-09-21",
  "score": 62,
  "breakdown": [
    { "name": "Affordability", "status": "Tight" },
    { "name": "Price-to-Rent", "status": "Elevated" },
    { "name": "Inventory", "status": "Low" }
  ]
}
```

- **Usage:**
  - `score` drives the gauge
  - `breakdown` shows side labels

---

### 5) Sentiment & News

- **API:** `GET /sentiment?city={city}`
- **Response:**

```json
{
  "city": "Kelowna",
  "items": [
    {
      "date": "2025-08-29",
      "headline": "New supply targets announced",
      "sentiment": "NEU"
    },
    {
      "date": "2025-08-14",
      "headline": "Rate cuts delayed; affordability worsens",
      "sentiment": "NEG"
    }
  ]
}
```

---

## 🔧 Implementation Snippets

### Build query string from FilterContext

```ts
const toParams = (f: {
  city: string;
  horizon: string;
  propertyType: string;
  beds: string;
  baths: string;
  sqftMin: number;
  sqftMax: number;
  yearBuilt: string;
}) => {
  const q: Record<string, string> = {
    city: f.city,
    horizon: f.horizon.toLowerCase(),
  };
  if (f.propertyType && f.propertyType !== "any")
    q.propertyType = f.propertyType;
  if (f.beds !== "any") q.beds = String(f.beds);
  if (f.baths !== "any") q.baths = String(f.baths);
  if (f.sqftMin) q.sqftMin = String(f.sqftMin);
  if (f.sqftMax) q.sqftMax = String(f.sqftMax);
  if (f.yearBuilt !== "any") {
    q.yearBuiltMin = f.yearBuilt;
    q.yearBuiltMax = f.yearBuilt;
  }
  return new URLSearchParams(q).toString();
};
```

### One-liner fetch (GET with all filters)

```ts
const res = await fetch(`/forecast?${toParams(filters)}`);
```

---

## ✅ Deliverable

- All UI widgets fetch from FastAPI using the shapes above
- Mock JSON fully removed
- Filters are passed as **query params**, not bodies
- Works on localhost and Netlify → FastAPI
