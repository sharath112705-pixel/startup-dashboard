import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Startup Funding Dashboard")

uploaded_file = st.file_uploader("Upload your CSV dataset", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    st.subheader("Column Names in Your CSV")
    st.write(list(df.columns))  # 🔥 Shows actual column names so errors don't happen

    st.subheader("Dataset Preview")
    st.dataframe(df)

    # --- FIX COMMON COLUMN NAME ISSUES ---
    # Convert all column names to lowercase without spaces
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    st.subheader("Normalized Column Names")
    st.write(list(df.columns))

    # Now safe to use:
    # sector → df["sector"]
    # amount_in_usd → df["amount_in_usd"]

    if "sector" in df.columns and "amount_in_usd" in df.columns:
        st.subheader("Funding by Sector")
        fig = px.bar(df, x="sector", y="amount_in_usd", color="sector")
        st.plotly_chart(fig)
    else:
        st.error("Your dataset must include 'Sector' and 'Amount In Usd' columns.")
