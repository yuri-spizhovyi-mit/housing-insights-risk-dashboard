import pandas as pd

df = pd.read_csv("data/rent_index.csv", low_memory=False)
print("Unique GEO values (first 30):")
print(df["GEO"].unique()[:30])
