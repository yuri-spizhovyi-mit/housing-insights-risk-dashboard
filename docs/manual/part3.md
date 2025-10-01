[⬅ Back to TOC](./index.md)

# Part III. Machine Learning Models

## Chapter 7. Decision Trees and Random Forests

### 7.1 Introduction
Decision Trees are interpretable, rule-based models that split data into regions based on feature thresholds. Random Forests are ensembles of decision trees that improve accuracy and robustness by averaging many trees.

### 7.2 Decision Trees

#### 7.2.1 Concept
Decision Trees split nodes based on purity measures like **Entropy** and **Gini Index**.

Entropy:
$$
H(S) = - \sum_{i=1}^k p_i \log_2 p_i
$$

Gini Index:
$$
Gini(S) = 1 - \sum_{i=1}^k p_i^2
$$

Information Gain:
$$
IG(S, A) = H(S) - \sum_{v \in Values(A)} \frac{|S_v|}{|S|} H(S_v)
$$

#### 7.2.2 Strengths
- Interpretable (rules can be visualized).  
- Handles categorical and numerical data.  
- Nonlinear relationships captured.

#### 7.2.3 Weaknesses
- Overfitting with deep trees.  
- Unstable (small changes can shift splits).  
- Poor extrapolation beyond training range.

### 7.3 Random Forests

#### 7.3.1 Concept
Random Forests build **B** trees on bootstrapped samples and average their predictions.

Formula:
$$
\hat{f}(x) = \frac{1}{B} \sum_{b=1}^B T_b(x)
$$

where $T_b(x)$ is the prediction from tree $b$.

#### 7.3.2 Strengths
- Reduces overfitting.  
- More stable than single trees.  
- Provides feature importance.

#### 7.3.3 Weaknesses
- Less interpretable than single trees.  
- Slower inference with many trees.  

### 7.4 Comparison: Decision Trees vs Random Forests

| Aspect            | Decision Tree | Random Forest |
|-------------------|---------------|---------------|
| Interpretability  | High          | Medium        |
| Variance          | High          | Low           |
| Accuracy          | Moderate      | High          |
| Overfitting Risk  | High          | Low           |

### 7.5 Key Takeaway
Decision Trees explain structure; Random Forests deliver accuracy and stability.

---

## Chapter 8. Gradient Boosting Methods (XGBoost, LightGBM, CatBoost)

### 8.1 Introduction
Boosting builds models sequentially, where each new model corrects errors from the previous ones.

### 8.2 Gradient Boosting Concept

General update rule:
$$
F_m(x) = F_{m-1}(x) + \gamma_m h_m(x)
$$

where $h_m(x)$ is the weak learner (usually a shallow tree) and $\gamma_m$ is the step size.

### 8.3 Loss Minimization
We fit $h_m$ to the **negative gradient of the loss function**.

Example: For squared error loss,
$$
L(y, F(x)) = (y - F(x))^2
$$

The gradient is:
$$
r_{im} = - \frac{\partial L(y_i, F(x_i))}{\partial F(x_i)} = y_i - F_{m-1}(x_i)
$$

### 8.4 Popular Implementations
- **XGBoost**: regularization, fast implementation.  
- **LightGBM**: efficient histogram-based splits.  
- **CatBoost**: categorical feature handling.

### 8.5 Strengths and Weaknesses

| Aspect | Strength | Weakness |
|--------|----------|----------|
| Accuracy | High predictive power | Overfitting if not tuned |
| Flexibility | Handles nonlinearities | Sensitive to hyperparameters |
| Speed | Fast (optimized libs) | Training cost > RF |

### 8.6 Key Takeaway
Gradient Boosting methods are state-of-the-art for tabular housing data forecasting.

---

## Chapter 9. Neural Networks for Housing Forecasting

### 9.1 Introduction
Neural Networks are powerful universal function approximators capable of capturing highly nonlinear relationships.

### 9.2 Forward Propagation

For layer $l$:
$$
z^{[l]} = W^{[l]} a^{[l-1]} + b^{[l]}
$$

$$
a^{[l]} = f(z^{[l]})
$$

where $f$ is an activation function (ReLU, sigmoid, etc.).

### 9.3 Backpropagation
Weights are updated by gradient descent:

$$
W^{[l]} = W^{[l]} - \eta \frac{\partial L}{\partial W^{[l]}}
$$

where $\eta$ is the learning rate.

### 9.4 Types of Neural Networks
- **Feedforward (FNN):** standard dense layers.  
- **Convolutional (CNN):** good for spatial data (e.g., satellite images).  
- **Recurrent (RNN, LSTM):** good for time series.  

### 9.5 Comparison of NN Types

| Type  | Housing Application | Strength | Weakness |
|-------|---------------------|----------|----------|
| FNN   | Tabular features    | Flexible | Needs lots of data |
| CNN   | Images/maps         | Extracts spatial features | Compute-heavy |
| LSTM  | Price/rent series   | Captures temporal patterns | Training instability |

### 9.6 Key Takeaway
Neural networks add flexibility and power, especially when combined with rich feature sets.

---

## Chapter 10. Time Series ML Models (ARIMA, Prophet, LSTM)

### 10.1 Introduction
Dedicated time series models are crucial for forecasting housing prices and rents.

### 10.2 ARIMA

General form:
$$
\phi(B)(1-B)^d y_t = 	heta(B)\varepsilon_t
$$

- $\phi(B)$: autoregressive polynomial.  
- $(1-B)^d$: differencing for stationarity.  
- $	heta(B)$: moving average polynomial.  
- $\varepsilon_t$: error term.

### 10.3 Prophet

Additive model:
$$
y(t) = g(t) + s(t) + h(t) + \varepsilon_t
$$

- $g(t)$: trend.  
- $s(t)$: seasonality.  
- $h(t)$: holidays/events.  
- $\varepsilon_t$: noise.

### 10.4 LSTM

LSTM gates:

Forget gate:
$$
f_t = \sigma(W_f [h_{t-1}, x_t] + b_f)
$$

Input gate:
$$
i_t = \sigma(W_i [h_{t-1}, x_t] + b_i)
$$

Cell state:
$$
	ilde{C}_t = 	anh(W_c [h_{t-1}, x_t] + b_c)
$$

Update:
$$
C_t = f_t \cdot C_{t-1} + i_t \cdot 	ilde{C}_t
$$

Output gate:
$$
o_t = \sigma(W_o [h_{t-1}, x_t] + b_o)
$$

Hidden state:
$$
h_t = o_t \cdot 	anh(C_t)
$$

### 10.5 Comparison of Time Series Models

| Model   | Strength | Weakness |
|---------|----------|----------|
| ARIMA   | Well understood, interpretable | Assumes linearity |
| Prophet | Handles seasonality, easy to use | Simplistic for shocks |
| LSTM    | Captures nonlinear & long dependencies | Needs lots of data |

### 10.6 Key Takeaway
ARIMA, Prophet, and LSTM each play roles in housing forecasting, depending on data size, frequency, and complexity.

---

## Part III Summary
Machine Learning models excel at prediction:  
- **Trees & Forests:** interpretable structure + ensemble robustness.  
- **Boosting:** state-of-the-art tabular accuracy.  
- **Neural Networks:** powerful with rich features (images, sequences).  
- **Time Series ML:** ARIMA/Prophet/LSTM for temporal dynamics.  

They complement econometric models, trading interpretability for predictive power.

---

[⬅ Back to TOC](./index.md)
