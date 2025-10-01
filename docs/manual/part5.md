[⬅ Back to TOC](./index.md)

# Part V. Integration & Application

## Chapter 13. Building Housing Forecast Dashboards (ETL + API + Frontend)

### 13.1 Introduction
Modern housing forecasting is not just about models but about **integrated systems** that deliver insights to users in real time.  
This requires combining **data pipelines (ETL)**, **APIs**, and **frontend dashboards**.

### 13.2 ETL: Extract–Transform–Load

Steps:
1. **Extract**: fetch data from CREA, CMHC, StatCan, BoC, RentFaster.  
2. **Transform**: clean, normalize, compute aggregates.  
3. **Load**: insert into PostgreSQL with schemas like `metrics`, `house_price_index`, `rents`.

Example ETL flow:
- RentFaster scraper → `rent_listings_raw` → monthly medians → `rents` table.

### 13.3 Backend: API Layer

FastAPI (Python) or Spring Boot (Java) can serve forecast results.

General API structure:
- `/forecast/home-prices` → returns predicted price index.  
- `/forecast/rents` → returns predicted rents.  
- `/risk` → returns risk indices, confidence bands.  
- `/scenario` → scenario analysis endpoints.

Benefits:
- Standardized data delivery.  
- Scalable microservice design.  
- Secure via authentication (JWT).

### 13.4 Frontend: Visualization

React + TypeScript dashboards allow interactive exploration.

Components:
- Line charts (Recharts, D3).  
- Filters (city, property type, bedrooms).  
- Tables with forecast summaries.  
- Risk dials (affordability index).

### 13.5 Integration Pipeline

Flow:
ETL → Database → API → Frontend Dashboard.

This integration ensures forecasts move from theory → data → actionable insights.

### 13.6 Challenges and Solutions

| Challenge | Solution |
|-----------|----------|
| Data lags | Integrate real-time listings with official data |
| API scaling | Use caching, pagination |
| User trust | Show confidence intervals and assumptions |

### 13.7 Key Takeaway
Dashboards transform forecasts into decisions, bridging data science with real-world policy and investment.

---

## Chapter 14. Case Studies: Canadian Housing Market

### 14.1 Introduction
Case studies illustrate how methods apply across scales: national, regional, and city.

### 14.2 National-Level Case: Canada
- Use CMHC, CREA, BoC macro data.  
- Hybrid econometric + ML forecasts national affordability.  
- Risk index highlights overvaluation in hot markets.

### 14.3 City Case: Vancouver
- High price-to-income, international demand.  
- Forecasts integrate migration, supply constraints.  
- Scenario: 2% interest rate hike → affordability crisis.

### 14.4 City Case: Toronto
- Rapid growth, pre-construction condo dominance.  
- Stress test: oversupply + rate hike → potential corrections.  
- Risk index shows leverage risk.

### 14.5 Regional Case: Kelowna
- Smaller sample size → need ML with rental listings.  
- Forecasts integrate seasonal rental demand.  
- Monte Carlo: high uncertainty due to tourism dependence.

### 14.6 Lessons from Case Studies
- Different markets respond to different drivers.  
- One-size-fits-all forecasting fails.  
- Integration of local + national drivers essential.

### 14.7 Key Takeaway
Case studies prove the need for flexible, hybrid models adapted to local context.

---

## Chapter 15. Conclusion & Future Directions

### 15.1 Recap of the Journey
We covered:
- **Foundations**: why housing is complex.  
- **Econometrics**: HPM, RSM, hybrids.  
- **Machine Learning**: Trees, Boosting, Neural Nets, Time Series.  
- **Risk**: indices, intervals, scenarios, stress tests.  
- **Integration**: dashboards and applications.

### 15.2 Core Insights
1. Housing is both consumption and investment.  
2. Data pipelines are foundational.  
3. Econometrics = interpretability. ML = accuracy.  
4. Risk quantification builds trust.  
5. Dashboards deliver impact.

### 15.3 Future Directions

#### 15.3.1 Alternative Data
- Satellite imagery for urban growth.  
- Social media for sentiment.  
- IoT sensors for smart housing.

#### 15.3.2 Advances in ML
- Transformer-based time series models.  
- Explainable AI (XAI) with Shapley values.  
- Automated ML pipelines.

#### 15.3.3 Policy Implications
- Transparency in forecasts.  
- Balance affordability vs. investment.  
- Crisis resilience planning.

### 15.4 Closing Thought
Forecasting housing is at the intersection of **economics, data science, and policy**.  
By blending econometric rigor, ML accuracy, and risk management, we can build systems that are **credible, transparent, and impactful**.

---

[⬅ Back to TOC](./index.md)
