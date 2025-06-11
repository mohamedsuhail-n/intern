import pandas as pd

# Step 1: Load CSV and convert to a single feather file
csv_path = "customer_data.csv"
feather_path = "full_data.feather"

df = pd.read_csv(csv_path)
df.to_feather(feather_path)

print(f"Feather file saved at: {feather_path}")
