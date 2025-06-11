from flask import Flask, request, jsonify
import pandas as pd
import mmh3
import os
import json

app = Flask(__name__)

# Constants
BUCKET_PATH = "customer_buckets"
FEATHER_FILENAME = "data.feather"

def get_bucket_split(customer_id):
    prefix = customer_id[:3]
    prefix_hash = hex(mmh3.hash(prefix, signed=False))
    bucket_name = prefix_hash[2]
    split_name = prefix_hash[2:5]
    return bucket_name, split_name

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

    # Fast path for customer_id
    if 'customer_id' in query_params:
        customer_id = query_params.get('customer_id')
        bucket, split = get_bucket_split(customer_id)
        df = load_customer_data(bucket, split)

    else:
        # Try to use index-based optimization
        found_index = False
        for key, value in query_params.items():
            index_file = os.path.join("indexes", key, f"{value.strip().lower()}.json")
            if os.path.exists(index_file):
                with open(index_file) as f:
                    references = json.load(f)
                dfs = []
                for ref in references:
                    df_part = load_customer_data(ref["bucket"], ref["split"])
                    if not df_part.empty:
                        dfs.append(df_part)
                if dfs:
                    df = pd.concat(dfs, ignore_index=True)
                    found_index = True
                    break  # Use only the first matching index

        # If no index matched, fallback to loading all
        if not found_index:
            dfs = []
            for bucket in os.listdir(BUCKET_PATH):
                for split in os.listdir(os.path.join(BUCKET_PATH, bucket)):
                    df_part = load_customer_data(bucket, split)
                    if not df_part.empty:
                        dfs.append(df_part)
            if dfs:
                df = pd.concat(dfs, ignore_index=True)

    # Apply any additional filters directly
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
