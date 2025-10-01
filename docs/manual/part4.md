[⬅ Back to TOC](./index.md)

# Part IV. Risk and Uncertainty

## Chapter 11. Risk Indices and Confidence Intervals

### 11.1 Introduction
Forecasting is incomplete without understanding **uncertainty and risk**.  
Risk indices and confidence intervals quantify the robustness of predictions.

### 11.2 Risk Indices

A risk index aggregates multiple indicators (affordability, leverage, volatility) into one score.

General form:

$$
RiskIndex_t = w_1 \cdot Affordability_t + w_2 \cdot Leverage_t + w_3 \cdot Volatility_t
$$

where weights $w_i$ reflect importance.

- **Affordability** = Price-to-Income ratio.  
- **Leverage** = Debt-to-Income ratio.  
- **Volatility** = variance of returns.

### 11.3 Confidence Intervals

Confidence intervals quantify the range of likely outcomes.

General form (normal approximation):

$$
CI = \hat{y} \pm z_{\alpha/2} \cdot \frac{\sigma}{\sqrt{n}}
$$

- $\hat{y}$: forecasted value.  
- $z_{\alpha/2}$: critical value from normal distribution.  
- $\sigma$: standard deviation.  
- $n$: sample size.

Interpretation: a 95% CI means we expect the true value to lie within the interval 95% of the time.

### 11.4 Monte Carlo Simulation

Monte Carlo simulates many possible paths of future outcomes.

Algorithm:
1. Define model and uncertainty distributions.  
2. Generate $N$ random draws.  
3. Recompute forecast each draw.  
4. Summarize distribution of outcomes.

Mathematically:

$$
\hat{y}_t^{(m)} = f(X_t, \varepsilon^{(m)}), \quad m=1,\dots,M
$$

where $\varepsilon^{(m)}$ is a random draw. The final forecast distribution is aggregated over $M$ simulations.

### 11.5 Strengths and Weaknesses

| Method            | Strength | Weakness |
|-------------------|----------|----------|
| Risk Index        | Simple, interpretable | Choice of weights subjective |
| Confidence Interval | Clear communication of uncertainty | Assumes distributional form |
| Monte Carlo       | Flexible, nonlinear | Computationally expensive |

### 11.6 Key Takeaway
Risk indices and intervals are essential to communicate forecast uncertainty and prevent false confidence.

---

## Chapter 12. Scenario Analysis and Stress Testing

### 12.1 Introduction
Scenario analysis and stress testing go beyond statistical intervals by explicitly simulating shocks and alternative futures.

### 12.2 Scenario Analysis

Scenario analysis explores "what-if" cases.

Example: A 2% interest rate hike.

Impact on mortgage payment (annuity formula):

$$
M = P \cdot \frac{r(1+r)^n}{(1+r)^n - 1}
$$

where $M$ = monthly payment, $P$ = loan principal, $r$ = monthly rate, $n$ = number of months.

Scenario analysis adjusts $r$ and recomputes $M$.

### 12.3 Stress Testing

Stress tests push models to extremes, asking: **what if the worst happens?**

Example: A 30% house price drop.

Price under stress:

$$
P_{stress} = P_{current} \cdot (1 - 0.30)
$$

Banks and regulators use such tests to check resilience.

### 12.4 Techniques Used
- Historical scenarios (e.g., 2008 financial crisis).  
- Hypothetical shocks (large rate hike, pandemic).  
- Reverse stress tests (find conditions that break system).

### 12.5 Applications
- Central banks test financial system stability.  
- Developers assess housing affordability shocks.  
- Insurers evaluate catastrophe losses.

### 12.6 Strengths and Weaknesses

| Method          | Strength | Weakness |
|-----------------|----------|----------|
| Scenario Analysis | Intuitive, flexible | May understate extremes |
| Stress Testing  | Exposes vulnerabilities | Assumptions may be arbitrary |

### 12.7 Key Takeaway
Scenario analysis and stress testing reveal vulnerabilities hidden by averages and give decision-makers actionable insights.

---

## Part IV Summary
Forecasting housing markets is not only about predicting averages. It requires quantifying **risks and uncertainty**.  
- Risk indices summarize vulnerabilities.  
- Confidence intervals express uncertainty ranges.  
- Monte Carlo explores probabilistic outcomes.  
- Scenario analysis and stress tests prepare us for shocks.  

Together, these tools ensure forecasts are **robust, credible, and resilient**.

---

[⬅ Back to TOC](./index.md)
