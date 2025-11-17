import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="🚀 Startup Funding Dashboard", layout="wide", page_icon="📊")

st.title("🚀 Indian Startup Funding Dashboard")

uploaded_file = st.file_uploader("Upload startup dataset (.csv)", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Clean column names
    df.columns = df.columns.str.lower().str.replace(" ", "_")

    # Standardize possible column names
    city_col = None
    for col in ["city", "city_location", "location"]:
        if col in df.columns:
            city_col = col
            break

    sector_col = None
    for col in ["industry_vertical", "sector", "industry", "vertical"]:
        if col in df.columns:
            sector_col = col
            break

    startup_col = None
    for col in ["startup_name", "startup", "company"]:
        if col in df.columns:
            startup_col = col
            break

    amount_col = None
    for col in ["amount_in_usd", "amount", "funding"]:
        if col in df.columns:
            amount_col = col
            break

    date_col = None
    for col in ["date", "funded_date", "year"]:
        if col in df.columns:
            date_col = col
            break

    # Convert column types safely
    df[amount_col] = pd.to_numeric(df[amount_col], errors="coerce")
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    city_filter = st.sidebar.multiselect("City", sorted(df[city_col].dropna().unique()))
    sector_filter = st.sidebar.multiselect("Sector", sorted(df[sector_col].dropna().unique()))

    filtered = df.copy()
    if city_filter:
        filtered = filtered[filtered[city_col].isin(city_filter)]
    if sector_filter:
        filtered = filtered[sector_col].isin(sector_filter)]

    # KPIs
    total_funding = filtered[amount_col].sum()
    total_startups = filtered[startup_col].nunique()
    unique_sectors = filtered[sector_col].nunique()

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("💰 Total Funding", f"${total_funding:,.0f}")
    kpi2.metric("🚀 Total Startups", total_startups)
    kpi3.metric("🏭 Sectors", unique_sectors)

    st.markdown("---")

    # City Funding Chart
    st.subheader("📍 Funding by City")
    city_funding = filtered.groupby(city_col)[amount_col].sum().reset_index()
    st.plotly_chart(px.bar(city_funding, x=city_col, y=amount_col), use_container_width=True)

    # Sector Funding Chart
    st.subheader("💼 Funding by Sector")
    sector_funding = filtered.groupby(sector_col)[amount_col].sum().reset_index()
    st.plotly_chart(px.pie(sector_funding, values=amount_col, names=sector_col), use_container_width=True)

    # Trend Chart
    st.subheader("📈 Funding Trend Over Time")
    trend = filtered.groupby(filtered[date_col].dt.year)[amount_col].sum()
    st.line_chart(trend)

    # View Data
    st.markdown("### 📄 Filtered Data")
    st.dataframe(filtered)

else:
    st.info("Please upload the CSV file to see the dashboard.")
