# 📝 Task: Connect UI to FastAPI Endpoints

**Assignee:** Max  
**Status:** Open  
**Priority:** High

---

## 🎯 Goal

Replace all mock data in the HIRD dashboard (`hird.netlify.app`) with live data from FastAPI endpoints.  
Ensure every UI widget correctly maps to its backend data source.

---

## 🔗 UI → API Mapping

### 1. City Selector (Dropdown)

- **Element:** Dropdown at top (City: Kelowna, Vancouver, Toronto)
- **API:** `GET /cities`
- **Data:**

  ```json
  ["Kelowna", "Vancouver", "Toronto"]
  ```

---

### 2. Forecast Charts (Home Price Forecast / Rent Forecast)

- **Element:** Line charts (top-left, bottom-left)
- **API:** `GET /forecast/{city}`

#### Data Source

From **`model_predictions`** table:

- `city` → Kelowna / Vancouver / Toronto
- `predict_date` → forecast date
- `yhat` → main prediction (→ `p50`)
- `yhat_lower` → lower bound (→ `p80`)
- `yhat_upper` → upper bound (→ `p95`)

#### Example Response

```json
[
  { "date": "2025-08-01", "p50": 1865, "p80": 1770, "p95": 1960 },
  { "date": "2025-09-01", "p50": 1878, "p80": 1784, "p95": 1975 },
  { "date": "2025-10-01", "p50": 2400, "p80": 2300, "p95": 2500 }
]
```

#### Notes

- Use `p50` for the main chart line.
- Shade the area between `p80` and `p95` as confidence bands.
- Filters (Beds, Baths, Sqft, Year Built) remain **UI-only for now**.

---

### 3. Risk Gauge (macro + local)

- **Element:** Gauge widget (top-right)
- **API:** `GET /risk/{city}`
- **Data:**

  ```json
  {
    "city": "Vancouver",
    "risk_index": 0.45,
    "level": "Moderate",
    "indicators": {
      "affordability": 0.6,
      "price_to_rent": 28.5,
      "inventory": "Low"
    }
  }
  ```

- **Notes:**

  - `risk_index` (0–1) drives gauge needle.
  - `level` (“Low”, “Moderate”, “High”) shows as label.
  - Indicators displayed as secondary labels.

---

### 4. Sentiment & News (Panel)

- **Element:** News list with sentiment labels (bottom-right)
- **API:** `GET /sentiment/{city}`
- **Data:**

  ```json
  {
    "city": "Kelowna",
    "sentiment_index": 0.42,
    "label": "Negative",
    "trend_30d": [0.55, 0.51, 0.47, 0.42],
    "top_headlines": [
      "Kelowna rental demand rises",
      "Rate cuts delayed; affordability worsens",
      "New supply targets announced"
    ],
    "last_updated": "2025-09-25"
  }
  ```

- **Notes:**
  - Show `top_headlines` as clickable list.
  - Use `label` + `sentiment_index` for sentiment badge.
  - Optionally plot `trend_30d` as sparkline.

---

### 5. PDF Download (Button)

- **Element:** “Download PDF” button (top-right)
- **API:** `GET /report/{city}.pdf`
- **Response:** Binary stream → triggers download (`city_report.pdf`).
- **Notes:**
  - Currently returns stub PDF.
  - Later: full report generation.

---

## ✅ Deliverable

- All 5 UI widgets wired to FastAPI.
- Mock JSON fully removed.
- Forecast chart directly powered from **`model_predictions`** table.
- Confirm working in **Netlify frontend** with live API calls.
