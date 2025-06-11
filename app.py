import streamlit as st
import requests
import time

API_BASE = "http://127.0.0.1:5050"

st.title("🧾 Dynamic Customer Data Lookup")

# Select filter type
filter_field = st.selectbox("Filter By", ["customer_id", "name", "surname", "age", "gender", "dob", "occupation", "experience"])
filter_value = st.text_input(f"Enter {filter_field}")

if st.button("🔍 Search"):
    if filter_value.strip():
        start = time.time()
        response = requests.get(f"{API_BASE}/customer", params={filter_field: filter_value})
        duration = time.time() - start

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 1:
                st.success(f"✅ {len(data)} Customers Found in {duration:.4f} seconds")
                st.dataframe(data)
            else:
                st.success(f"✅ Customer Found in {duration:.4f} seconds")
                st.json(data)
        else:
            st.error("❌ No matching customer found")
    else:
        st.warning(f"⚠️ Please enter a value for {filter_field}.")
