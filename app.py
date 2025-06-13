import streamlit as st
import requests
import time

API_BASE = "http://127.0.0.1:5050"

st.set_page_config(page_title="Customer Lookup", layout="centered")
st.title("🧾 Dynamic Customer Data Lookup")

ALL_FILTERS = ["customer_id", "name", "surname", "age", "gender", "dob", "occupation", "experience"]
# Track which filters are active
if "active_filters" not in st.session_state:
    st.session_state.active_filters = []

if "filter_values" not in st.session_state:
    st.session_state.filter_values = {}

# Display buttons to add filters
st.subheader("➕ Add Filters")
cols = st.columns(4)
for i, f in enumerate(ALL_FILTERS):
    if f not in st.session_state.active_filters:
        if cols[i % 4].button(f"+ {f}"):
            st.session_state.active_filters.append(f)
            st.session_state.filter_values[f] = ""

st.divider()

# Display active filters and input boxes
if st.session_state.active_filters:
    st.subheader("🔍 Enter Filter Values")
    for f in st.session_state.active_filters:
        val = st.text_input(f"Enter {f}", key=f)
        st.session_state.filter_values[f] = val

    # Option to remove filters
    remove_col = st.columns(len(st.session_state.active_filters))
    for i, f in enumerate(st.session_state.active_filters):
        if remove_col[i].button(f"❌ Remove {f}", key=f"remove_{f}"):
            st.session_state.active_filters.remove(f)
            st.session_state.filter_values.pop(f, None)
            st.rerun()

# Prepare filters for query
query_params = {
    key: val for key, val in st.session_state.filter_values.items()
    if val.strip()
}

# Submit search
if st.button("🔎 Search Customers"):
    if not query_params:
        st.warning("⚠️ Please add and enter at least one filter.")
    else:
        start = time.time()
        response = requests.get(f"{API_BASE}/customer", params=query_params)
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
            st.error("❌ No matching customer found.")
