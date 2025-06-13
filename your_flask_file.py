from flask import Flask, request, jsonify
import pandas as pd
import mmh3
import os
import json

app = Flask(__name__)

# Constants
BUCKET_PATH = "customer_buckets"
FEATHER_FILENAME = "data.feather"
INDEX_DIR = "indexes"

# Compute bucket and split using MurmurHash
def get_bucket_split(customer_id):
    prefix = customer_id[:3]
    prefix_hash = hex(mmh3.hash(prefix, signed=False))
    bucket = prefix_hash[2]
    split = prefix_hash[2:5]
    return bucket, split

# Load data from a given bucket/split
def load_customer_data(bucket, split):
    file_path = os.path.join(BUCKET_PATH, bucket, split, FEATHER_FILENAME)
    if os.path.exists(file_path):
        return pd.read_feather(file_path)
    return pd.DataFrame()

@app.route('/customer', methods=['GET'])
def get_customer():
    query_params = request.args

    if not query_params:
        return jsonify({"error": "Please provide at least one query parameter"}), 400

    df = pd.DataFrame()

    # Fast path if customer_id is provided
    if 'customer_id' in query_params:
        customer_id = query_params.get('customer_id')
        bucket, split = get_bucket_split(customer_id)
        df = load_customer_data(bucket, split)
    else:
        # Try to use multiple index-based filters
        all_references = []
        for key, value in query_params.items():
            index_file = os.path.join(INDEX_DIR, key, f"{value.strip().lower()}.json")
            if os.path.exists(index_file):
                with open(index_file) as f:
                    refs = json.load(f)
                    ref_set = {(ref["bucket"], ref["split"]) for ref in refs}
                    all_references.append(ref_set)

        dfs = []

        if all_references:
            # Intersection across all index filter sets
            matched_refs = set.intersection(*all_references)
            for bucket, split in matched_refs:
                df_part = load_customer_data(bucket, split)
                if not df_part.empty:
                    dfs.append(df_part)
            if dfs:
                df = pd.concat(dfs, ignore_index=True)
        else:
            # No matching indexes — fallback to load all
            for bucket in os.listdir(BUCKET_PATH):
                bucket_path = os.path.join(BUCKET_PATH, bucket)
                if not os.path.isdir(bucket_path):
                    continue
                for split in os.listdir(bucket_path):
                    df_part = load_customer_data(bucket, split)
                    if not df_part.empty:
                        dfs.append(df_part)
            if dfs:
                df = pd.concat(dfs, ignore_index=True)

    # Final filtering on loaded data (for correctness)
    for key, value in query_params.items():
        if key in df.columns:
            df = df[df[key].astype(str).str.lower() == value.lower()]

    if df.empty:
        return jsonify({"message": "No customer found with given filters"}), 404

    return df.to_json(orient='records')

@app.route('/')
def index():
    return "Welcome to the Customer Lookup API! Use /customer?customer_id=cka2501"

if __name__ == '__main__':
    app.run(debug=True, port=5050)
