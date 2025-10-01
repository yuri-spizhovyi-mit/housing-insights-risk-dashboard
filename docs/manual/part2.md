[⬅ Back to TOC](./index.md)

# Part II. Econometric Models

## Chapter 4. Hedonic Pricing Models (HPMs)

### 4.1 Core Concept
The **Hedonic Pricing Model (HPM)** decomposes the observed market price of a property into the implicit value of its attributes (size, location, amenities, etc.).  
Formally, the price is modeled as a function of characteristics, allowing us to estimate the **marginal willingness to pay** for each feature.

### 4.2 Interpretation of Model Components (α, β, ε)
The general HPM equation:  

\[
P_i = \alpha + \beta_1 X_{i1} + \beta_2 X_{i2} + \dots + \beta_k X_{ik} + \varepsilon_i
\]

- **P_i**: observed price of house *i*.  
- **α (alpha)**: intercept → baseline value of a hypothetical “zero-feature” house (not realistic, but anchors the regression).  
- **β_j (betas)**: coefficients → marginal contribution of each attribute *X_j* to price.  
- **X_{ij}**: attribute *j* of house *i* (e.g., square footage, bedrooms, neighborhood quality).  
- **ε_i**: error term → unobserved influences (noise, omitted features, buyer-seller negotiation).  

**Example:** If β₁ (for square footage) = 250, then each extra square foot adds about $250 to the house price, holding other factors constant.

### 4.3 Data Requirements
- **Rich micro-level data** with many attributes.  
- Large sample sizes to disentangle correlated features.  
- Consistency across listings or transaction records.  
- Control for location and time (e.g., fixed effects, spatial coordinates).

### 4.4 Strengths of HPM
- **Attribute valuation:** reveals the implicit price of features (e.g., lake view premium, proximity to schools).  
- **Policy use:** quantify benefits of infrastructure (e.g., new transit line).  
- **Detailed:** works well with heterogeneous housing stock.

### 4.5 Weaknesses of HPM
- **Data-hungry:** requires detailed, consistent feature data.  
- **Omitted variable bias:** missing attributes distort β estimates.  
- **Multicollinearity:** correlated features (e.g., size and bedrooms) make estimates unstable.  
- **Market instability:** preferences change over time, requiring re-estimation.

### 4.6 Top Features in HPM
| Category          | Typical Feature Examples                           | Expected Effect on Price |
|-------------------|---------------------------------------------------|--------------------------|
| Structural        | Square footage, lot size, bedrooms, bathrooms     | Larger = higher price |
| Locational        | Distance to CBD, schools, transit, amenities      | Closer/better = higher |
| Neighborhood      | Crime rate, income level, walkability             | Better = higher |
| Temporal          | Sale year/quarter, interest rates                 | Captures market cycle |
| Special features  | Lake view, pool, fireplace                        | Positive premium |

### 4.7 Forecasting Role
- HPMs are not always the most accurate forecasters but are invaluable for **interpretation**.  
- They can be embedded in dashboards to explain why prices differ across regions or property types.  
- Useful in **policy analysis** (e.g., how much a new transit station raises nearby house values).

### 4.8 Applications
- Real estate appraisal.  
- Infrastructure cost-benefit analysis.  
- Environmental valuation (e.g., noise reduction, pollution exposure).  
- Housing affordability studies.

### 4.9 Key Takeaway
HPMs excel at **explaining housing price formation** by attributes but must be combined with other models for forecasting and risk assessment.

---

## Chapter 5. Repeat-Sales Models (RSMs)

### 5.1 Core Concept
The **Repeat-Sales Model (RSM)** isolates pure price appreciation by comparing sales of the same property over time.  
By differencing prices of identical homes across transactions, RSM removes the need to observe all attributes.

### 5.2 Mathematical Formulation
\[
\ln(P_{i,t_2}) - \ln(P_{i,t_1}) = \sum_{j} \beta_j D_{j} + \varepsilon_i
\]

- **ln(P_{i,t₂}) - ln(P_{i,t₁})**: log price change of house *i* between sale at *t₁* and resale at *t₂*.  
- **D_j**: dummy variables for time periods.  
- **β_j**: estimated average appreciation/depreciation in each period.  
- **ε_i**: error term (house-specific shocks).  

This structure produces a **house price index** across time.

### 5.3 Strengths of RSM
- Controls for **unobserved features** (same house = same structure).  
- Produces clean **price indices**.  
- Useful for long-run market tracking.

### 5.4 Weaknesses of RSM
- Relies on properties that sell multiple times (sample bias: not all houses resell).  
- May not capture renovations/condition changes.  
- Limited cross-sectional insight (cannot value attributes).

### 5.5 RSM vs. HPM
- **HPM:** good for attribute-level analysis, but sensitive to omitted data.  
- **RSM:** robust for pure time-series indices, but blind to feature values.  
- Together, they provide complementary views.

### 5.6 Forecasting Role
RSM-derived indices feed into broader forecasting models (econometric or ML) as benchmarks for **market-wide appreciation trends**.

### 5.7 Case Example: Teranet–National Bank HPI
Canada’s Teranet–National Bank House Price Index is based on repeat-sales methodology.  
It tracks long-term trends across major cities and is widely used by policymakers and banks.

### 5.8 Key Takeaway
RSM is the **workhorse for house price indices**, less detailed than HPM but more stable for time-series analysis.

---

## Chapter 6. Hybrid Econometric Models (Panel Data, VAR, ECM)

### 6.1 Why Hybrid Models?
HPM and RSM capture partial aspects of housing markets. Hybrid econometric models integrate more dimensions: cross-sectional, temporal, and macroeconomic linkages.

### 6.2 Panel Data Models
- Combine cross-sectional (different houses/regions) and time-series dimensions.  
- Control for **fixed effects** (unobserved heterogeneity).  
- Example: Price_it = α + βX_it + μ_i + γ_t + ε_it.

### 6.3 Vector Autoregression (VAR)
- Treats multiple time series (e.g., prices, rents, interest rates, income) as endogenous.  
- Each variable is regressed on its own lags and lags of others.  
- Captures **dynamic feedback** (e.g., rates affect prices, which affect starts, which affect rents).

### 6.4 Error-Correction Models (ECM)
- Recognize that housing markets have long-run equilibria (income-to-price ratios, rent-price parity).  
- Short-run deviations corrected gradually via adjustment terms.  
- Example: ΔPrice_t = α(Price* - Price_t-1) + βΔX_t + ε_t.

### 6.5 Comparison of Hybrid Models
| Model | Strength | Weakness |
|-------|----------|----------|
| Panel | Handles heterogeneity, large datasets | Requires long panels |
| VAR   | Captures feedback loops | Data-hungry, hard to interpret |
| ECM   | Enforces long-run relationships | Sensitive to cointegration tests |

### 6.6 Key Takeaway
Hybrid models combine structure and dynamics, bridging micro-level pricing (HPM/RSM) with macro linkages. They often underpin central bank and policy forecasts.

---

## Part II Summary
Econometric models provide **interpretability and theory-based structure**:  
- **HPM:** explains how attributes map into price.  
- **RSM:** produces stable price indices.  
- **Hybrid models:** integrate micro + macro + dynamics.  

They remain the backbone of housing economics, though often complemented with machine learning for predictive accuracy.

---

[⬅ Back to TOC](./index.md)
