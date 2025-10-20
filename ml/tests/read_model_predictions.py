import pandas as pd

df = pd.read_csv("ml/tests/mp.csv")

# Show where forecasts are negative
negatives = df[(df["yhat"] < 0) | (df["yhat_lower"] < 0) | (df["yhat_upper"] < 0)]
print(negatives[["city", "target", "model_name", "yhat", "yhat_lower", "yhat_upper"]].head(20))

# Stats summary
print(df.groupby("target")["yhat"].describe())
