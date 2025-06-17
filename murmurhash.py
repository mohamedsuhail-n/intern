import os
import pandas as pd
import mmh3

# Step 1: Load data
df = pd.read_csv("customer_data.csv")

# Step 2: Extract fields
df['prefix'] = df['customer_id'].str[:3]
df['prefix_hash'] = df['prefix'].apply(lambda x: hex(mmh3.hash(x, signed=False)))
df['bucket_name'] = df['prefix_hash'].str[2]
df['split_name'] = df['prefix_hash'].str[2:5]

# Step 3: Base path to store
ROOT = "customer_buckets"

# Step 4: Group by (bucket_name, split_name)
for (bucket, split), group in df.groupby(['bucket_name', 'split_name']):
    folder_path = os.path.join(ROOT, bucket, split)
    os.makedirs(folder_path, exist_ok=True)
    
    # File path inside the split folder
    file_path = os.path.join(folder_path, "data.feather")
    
    # Write to Feather
    group.reset_index(drop=True).to_feather(file_path)

print("All customer data saved to respective split folders.")
