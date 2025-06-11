import os
import pandas as pd
import json
import re
import mmh3

FEATHER_FILE = "full_data.feather"
BUCKET_PATH = "customer_buckets"
INDEX_DIR = "indexes"

# Columns to index (excluding customer_id)
FILTER_COLUMNS = [
    "name", "surname", "age", "gender",
    "occupation", "dob", "experience"
]

# Ensure index directories exist
for col in FILTER_COLUMNS:
    os.makedirs(os.path.join(INDEX_DIR, col), exist_ok=True)

# Clean value to use as filename
def safe_filename(val):
    return re.sub(r"[^\w\-]", "_", str(val).strip().lower())

# Get bucket and split from customer_id
def get_bucket_split(customer_id):
    prefix = customer_id[:3]
    prefix_hash = hex(mmh3.hash(prefix, signed=False))
    bucket = prefix_hash[2]
    split = prefix_hash[2:5]
    return bucket, split

# Load full feather data
df = pd.read_feather(FEATHER_FILE)

# Add bucket and split columns
df["bucket"], df["split"] = zip(*df["customer_id"].map(get_bucket_split))

# Build index files
for col in FILTER_COLUMNS:
    if col not in df.columns:
        continue

    for val in df[col].dropna().unique():
        val_safe = safe_filename(val)
        index_path = os.path.join(INDEX_DIR, col, f"{val_safe}.json")

        # Get all bucket-split combinations where this value appears
        entries = df[df[col] == val][["bucket", "split"]].drop_duplicates().to_dict(orient="records")

        # Merge with existing index file if present
        if os.path.exists(index_path):
            with open(index_path) as f:
                existing = json.load(f)
        else:
            existing = []

        # Avoid duplicates
        seen_keys = {f"{e['bucket']}_{e['split']}" for e in existing}
        for entry in entries:
            key = f"{entry['bucket']}_{entry['split']}"
            if key not in seen_keys:
                existing.append(entry)
                seen_keys.add(key)

        with open(index_path, "w") as f:
            json.dump(existing, f, indent=2)

print("✅ Indexes generated successfully from full_data.feather")
