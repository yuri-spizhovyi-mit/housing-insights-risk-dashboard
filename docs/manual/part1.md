[⬅ Back to TOC](./index.md)

# Part I. Foundations

## Chapter 1. Introduction: Why Housing Markets Are Complex

### 1.1 Housing as a Multi-Dimensional Asset
Housing is simultaneously a **consumption good** (we live in it) and an **investment asset** (we expect it to store or grow wealth). 
This dual role means buyers care about comfort, proximity, and neighborhood quality _and_ about interest rates, expected appreciation, and portfolio risk. 
As a result, demand in housing depends on **psychology, demographics, and finance** all at once—richer dynamics than in markets for standardized goods.

### 1.2 Heterogeneity of Housing Units
No two homes are identical. Even on the same street, modest differences in **lot size, view, build quality, or renovation history** can translate into large price differences. 
This heterogeneity violates the “identical goods” assumption of many simple models and motivates methods like **Hedonic Pricing Models** (decompose price into attributes) and **Repeat‑Sales Models** (track the same home over time).

### 1.3 Data Challenges
Housing data can be **messy, delayed, and fragmented**:
- **Transaction lag:** listings → offers → closings → official recording often takes months.  
- **Omitted variables:** interior condition, odors, neighbor behavior, or “feel” of a block are rarely recorded.  
- **Granularity:** some neighborhoods have many sales; others have few, creating sampling issues.  
- **Multiple sources:** official statistics, market platforms, and private datasets differ in definitions and release cadence.

### 1.4 Multiple Market Drivers
**Micro drivers:** school quality, crime, walkability, transit access, parks, neighborhood reputation.  
**Macro drivers:** interest rates, income/unemployment, demographics/migration, construction costs, credit availability, global capital flows.  
Because the **mix and intensity** of these drivers varies by city, markets such as Vancouver, Toronto, and Kelowna can move very differently at the same time.

### 1.5 Time Dynamics and Nonlinearity
Preferences and constraints shift over time:
- **Remote work** increased the value of space and home offices.  
- **Rate hikes** reduce affordability, often nonlinearly (a small rate move can push many buyers below qualification thresholds).  
- **Redevelopment** or new transit can change a neighborhood’s trajectory within years.  
Effects are **nonlinear** and **interaction‑heavy** (e.g., the value of an extra bedroom depends on location and household size).

### 1.6 Policy and Institutional Influence
Zoning, mortgage qualification rules, foreign‑buyer policies, rent control, taxes, and subsidies can **distort or redirect** supply and demand. 
These institutional forces create discontinuities that standard models may miss without explicit representation.

### 1.7 Deep Dive: Formal Characteristics of Housing Markets
Economists typically emphasize:  
1) **Heterogeneous goods** (unique attributes); 2) **Immobility** (location fixed); 3) **Durability** (long life, slow turnover);  
4) **High transaction costs** (legal fees, commissions, taxes); 5) **Slow supply response** (multi‑year build cycles); 6) **Dual role** (consumption + investment).  
These features help explain **boom‑bust cycles** and the need for specialized forecasting tools.

### 1.8 Key Takeaway
Housing markets mix **economic, social, financial, and policy** dimensions. Understanding this complexity motivates the blended toolbox (econometric + ML + risk) developed in the rest of the book.

---

## Chapter 2. Data Sources and Pipeline

### 2.1 Why Data Matters in Housing Forecasting
Models are only as good as their inputs. Housing outcomes reflect both **local attributes** and **macro conditions**, so we integrate **multiple sources** into a unified pipeline.

### 2.2 Core Data Sources
- **CREA (Canadian Real Estate Association):** MLS® transactions, listings, prices, regional breakdowns → foundation for resale indices.  
- **CMHC (Canada Mortgage and Housing Corporation):** starts, completions, vacancy rates, rent surveys → supply and rental dynamics.  
- **Statistics Canada (StatCan):** demographics, income, migration, CPI → fundamental demand drivers.  
- **Bank of Canada (BoC):** policy rates, bond yields, credit conditions → affordability and financing.  
- **Rental platforms (RentFaster, Rentals.ca, etc.):** real‑time asking rents and unit features → high‑frequency market tension.  
- **Local platforms (Craigslist, Castanet):** supplemental signals for smaller markets or validation.

### 2.3 Data Pipeline (ETL Architecture)
We implement a modular **ETL (Extract–Transform–Load)** pipeline:
1. **Extract:** pull via APIs (CREA/CMHC/StatCan/BoC) or scrape dynamic sites for rental listings (store HTML snapshots for reproducibility).  
2. **Transform:** normalize geographies, deduplicate listings, standardize bedroom categories, impute/flag missing data, and aggregate (e.g., monthly medians).  
3. **Load:** write to a relational store (e.g., PostgreSQL) using **staging → curated** layers for traceability and audits.

### 2.4 Database Schema (Simplified)
- `metrics` — cross‑source macro indicators (rates, CPI, employment).  
- `house_price_index` — CREA + repeat‑sales indices by city/type.  
- `rents` — monthly median asking rents by city/bed count/source.  
- `demographics` — population, migration, income.  
- `macro_economic_data` — BoC rates, bond yields, spreads.  
- `construction_permits` — starts/completions permits.  
- `rent_listings_raw` — raw scraped rental ads (for provenance/debug).

### 2.5 Example ETL Flow (RentFaster Adapter)
- Fetch HTML → store in `.debug/rentfaster/` (optional).  
- Parse to extract city, price, bedrooms, features.  
- Write to `rent_listings_raw`; derive monthly medians; push to `rents` with `source='ListingsMedian'`.  
This pattern repeats for other adapters to build a **unified data lake** feeding models and dashboards.

### 2.6 Challenges in Data Integration
- **Client‑rendered pages:** need headless browsers for scraping.  
- **Granularity mismatches:** city vs. CMA vs. province; we reconcile with mapping tables.  
- **Timeliness trade‑offs:** official series (quality, lagged) vs. listings (noisy, fresh).  
- **Cleaning complexity:** inconsistent unit labels (e.g., “Bachelor” vs “Studio”), outliers, duplicate listings.

### 2.7 Key Takeaway
A **reliable ETL and schema** are prerequisites for credible forecasts, enabling validation, reproducibility, and rapid iteration across models.

---

## Chapter 3. Forecasting Approaches (Econometric vs. Machine Learning)

### 3.1 Why We Forecast Housing
Stakeholders need **forward‑looking** views:  
- **Households** (buy vs. rent timing, budgeting).  
- **Policymakers** (affordability, systemic risk).  
- **Banks/Investors** (credit exposure, returns, capital planning).

### 3.2 Econometric Models
**Idea:** marry **economic theory** with statistical estimation.  
- **Hedonic Pricing Models (HPMs):** decompose price into attribute premiums (size, location, view).  
- **Repeat‑Sales Models (RSMs):** index pure price movement by tracking the same property over time.  
- **Hybrid models (Panel/VAR/ECM):** control for fixed effects, capture macro feedback, and enforce long‑run equilibria.  
**Strengths:** interpretability, policy evaluation, causal structure (with caveats).  
**Limitations:** strong assumptions; sensitive to missing variables; slower to adapt to shocks.

### 3.3 Machine Learning Models
**Idea:** learn patterns directly from data with minimal functional assumptions.  
- **Trees & Forests:** nonlinear splits, robust baselines, feature importance.  
- **Boosting (XGBoost/LightGBM/CatBoost):** sequential error‑correction, state‑of‑the‑art for tabular data.  
- **Neural Networks:** FNN for tabular, CNN for images, LSTM for time series.  
- **Dedicated time series ML:** ARIMA/Prophet/LSTM for trend + seasonality + nonlinear cycles.  
**Strengths:** predictive power, interactions, scalability.  
**Limitations:** interpretability, data appetite, overfitting risk.

### 3.4 Complementarity of Approaches
Rather than rivals, they are **complements**:  
- **Econometrics explains** (mechanisms, policy levers).  
- **ML predicts** (short‑ to medium‑term accuracy).  
Integrating both yields systems that are **trustworthy (explainable)** and **useful (accurate)**.

### 3.5 Case Example: Kelowna (Sketch)
- **ETL:** assemble CREA transactions, listings medians, CMHC vacancy, BoC rates.  
- **Econometrics:** HPM quantifies lake‑view premium; RSM constructs a local price index.  
- **ML:** LightGBM forecasts next‑year median; LSTM models seasonal rent patterns.  
- **Risk:** index flags affordability stress + overbuilding risk; scenario tool shows –10% outcome under rate shock.  
- **Dashboard:** combines drivers (econometrics), predictions (ML), and uncertainty (risk bands).

### 3.6 Key Takeaway
Use a **toolbox**, not a single hammer. Blend econometric structure with ML flexibility and explicit risk quantification for credible, actionable housing forecasts.

---

[⬅ Back to TOC](./index.md)
