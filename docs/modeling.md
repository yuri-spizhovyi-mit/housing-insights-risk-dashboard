# Modeling

This chapter describes the forecasting and risk-detection models that power the Housing Insights & Risk Dashboard.  
The system uses a combination of statistical, machine-learning, and deep-learning approaches to model price trends, rental dynamics, and structural market anomalies.

---

## 1. Forecasting Models

The platform provides multi-horizon forecasts for both **home prices** and **median rent**.  
Three model families are used:

### **1.1 ARIMA (AutoRegressive Integrated Moving Average)**

**Purpose:**  
Short-term forecasting and modeling linear temporal dependencies.

**Why ARIMA:**  
- Performs well when recent history strongly predicts the near future  
- Suitable for stable markets or short forecast windows  
- Fast and interpretable  

**Characteristics:**  
- Assumes stationarity (uses differencing to enforce it)  
- Captures autoregressive and moving-average structure  
- Works best for **1–12 month horizons**

---

### **1.2 Prophet**

**Purpose:**  
Medium- and long-range forecasting while capturing trend, seasonality, and holiday effects.

**Why Prophet:**  
- Designed for business time series  
- Handles missing data and outliers  
- Automatically decomposes growth + yearly/weekly seasonality  
- Useful for **1–120 month horizons**

**Characteristics:**  
- Additive model: trend + seasonality + holidays  
- Robust to irregular market cycles  
- Generates confidence intervals (lower/upper bounds)

---

### **1.3 LSTM (Long Short-Term Memory Networks)**

**Purpose:**  
Deep learning model for complex non-linear temporal patterns.

**Why LSTM:**  
- Learns long-term dependencies in price and rent data  
- Handles non-stationary dynamics  
- Captures patterns that ARIMA/Prophet cannot model (lagged interactions, volatility)  

**Characteristics:**  
- Sequence-to-sequence neural network  
- Works well with long historical windows  
- Best for difficult long-range behavior (5–10 years)

---

## 2. Forecasting Targets and Horizons

Forecasts are generated for:

- **Home Price Index (HPI)**  
- **Median Rent**

Horizons supported:

- **1 year (12 months)**  
- **2 years (24 months)**  
- **5 years (60 months)**  
- **10 years (120 months)**  

The dashboard automatically **samples** long-horizon predictions for clean visualization.

---

## 3. Model Comparison Framework

The system evaluates each model using backtests.  
Recorded metrics include:

- **MAE** – Mean Absolute Error  
- **RMSE** – Root Mean Squared Error  
- **MAPE** – Percentage error  
- **R²** – Coefficient of determination  

These results power the **Model Comparison** chart in the dashboard, allowing users to quickly identify which models perform best for a given city and target.

---

## 4. Risk & Anomaly Detection Model

### **4.1 Isolation Forest**

**Purpose:**  
Identify abnormal market conditions such as rapid price spikes, unusual rent changes, structural imbalances, or other market shocks.

**Why Isolation Forest:**  
- Works well for irregular, high-dimensional behavior  
- Detects anomalies without labeled data  
- Each anomaly is scored and assigned a binary flag (`is_anomaly`)  

**Inputs used include:**  
- Price and rent growth rates  
- Inventory ratios  
- Affordability indicators  
- Price-to-rent deviations  
- Macroeconomic factors (depending on city coverage)

**Outputs:**  
- `anomaly_score`  
- `is_anomaly` (Boolean)  
- `detect_date`  
- `target` (price or rent)

These signals appear in the **Anomalies chart** and in the **PDF report**.

---

## 5. Combined Architecture

Together, the forecasting and anomaly models form a complete analytics pipeline:

- Forecast **future values** (ARIMA, Prophet, LSTM)  
- Compare **model performance** (MAE, RMSE, etc.)  
- Detect **abnormal events** (Isolation Forest)  
- Produce **risk indices** and **city-level summaries**  

This combination allows the dashboard to provide both **predictive insights** and **market-stability diagnostics**.

---

## 6. Summary

| Component          | Models Used                       | Purpose                                 |
|-------------------|-----------------------------------|-----------------------------------------|
| Price Forecasting | ARIMA, Prophet, LSTM              | Predict home price index                |
| Rent Forecasting  | ARIMA, Prophet, LSTM              | Predict median rent                     |
| Risk Prediction   | Isolation Forest                  | Detect anomalies & structural imbalance |
| Model Evaluation  | Backtesting (MAE, RMSE, MAPE, R²) | Compare predictive performance          |

The modeling layer is designed to be modular, allowing new models or features to be added without disrupting the existing architecture.

---

