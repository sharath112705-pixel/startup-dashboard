import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Startup Funding Dashboard")

uploaded_file = st.file_uploader("Upload your CSV dataset", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    st.subheader("Dataset Preview")
    st.dataframe(df)

    st.subheader("Funding by Sector")
    fig = px.bar(df, x="Sector", y="Amount In Usd", color="Sector")
    st.plotly_chart(fig)
