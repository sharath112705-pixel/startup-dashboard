import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

st.set_page_config(page_title="Indian Startup Analytics", layout="wide")

st.title("🚀 Indian Startup Funding Dashboard")

uploaded_file = st.file_uploader("📂 Upload your 'startups.csv' file", type="csv")

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    # Clean column names for easier access
    df.columns = df.columns.str.lower().str.replace(" ", "_")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount_in_usd"] = pd.to_numeric(df["amount_in_usd"], errors="coerce")

    # ---- Fix MeitY Recognition ----
    df["is_meity_recognized"] = df["is_meity_recognized"].astype(str).str.strip().str.lower()

    df["is_meity_recognized"] = df["is_meity_recognized"].map({
        "yes": "Recognized",
        "no": "Not Recognized"
    }).fillna("Unknown")

    # Sidebar Filters
    st.sidebar.header("📌 Filter Options")
    city = st.sidebar.multiselect("🏙 City", sorted(df["city_location"].dropna().unique()))
    sector = st.sidebar.multiselect("💼 Sector", sorted(df["sector"].dropna().unique()))
    meity = st.sidebar.multiselect("🏛 MeitY Recognition", sorted(df["is_meity_recognized"].unique()))

    filtered = df.copy()

    if city:
        filtered = filtered[filtered["city_location"].isin(city)]
    if sector:
        filtered = filtered[filtered["sector"].isin(sector)]
    if meity:
        filtered = filtered[filtered["is_meity_recognized"].isin(meity)]

    # Metrics Row
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Startups", len(filtered))
    col2.metric("Total Funding", f"${filtered['amount_in_usd'].sum():,.0f}")
    col3.metric("Unique Sectors", filtered['sector'].nunique())

    # --- Visualization 1: Top Funded Sectors ---
    st.subheader("💰 Top Funded Sectors")
    sector_funding = filtered.groupby("sector")["amount_in_usd"].sum().nlargest(10).reset_index()
    fig1 = px.bar(sector_funding, x="sector", y="amount_in_usd", text_auto=True)
    fig1.update_layout(xaxis_title="Sector", yaxis_title="Funding (USD Millions)")
    st.plotly_chart(fig1, use_container_width=True)

    # --- Visualization 2: Top Cities Funding ---
    st.subheader("🏙 City-Wise Funding Distribution")
    city_funding = filtered.groupby("city_location")["amount_in_usd"].sum().reset_index()
    fig2 = px.pie(city_funding, names="city_location", values="amount_in_usd", hole=0.35)
    st.plotly_chart(fig2, use_container_width=True)

    # --- Visualization 3: Funding Trend ---
    st.subheader("📈 Funding Trend Over Years")
    filtered["year"] = filtered["date"].dt.year
    yearly = filtered.groupby("year")["amount_in_usd"].sum().reset_index()
    fig3 = px.line(yearly, x="year", y="amount_in_usd", markers=True)
    st.plotly_chart(fig3, use_container_width=True)

    # --- Visualization 4: MeitY Recognition ---
    st.subheader("🏛 MeitY Recognition Status")
    meity_data = filtered["is_meity_recognized"].value_counts().reset_index()
    meity_data.columns = ["Recognition Status", "Count"]

    colA, colB, colC = st.columns(3)
    colA.metric("Recognized Startups",
                int(meity_data.loc[meity_data["Recognition Status"] == "Recognized", "Count"].sum()))
    colB.metric("Not Recognized",
                int(meity_data.loc[meity_data["Recognition Status"] == "Not Recognized", "Count"].sum()))
    colC.metric("Unknown",
                int(meity_data.loc[meity_data["Recognition Status"] == "Unknown", "Count"].sum()))

    fig4 = px.pie(meity_data, 
                  names="Recognition Status", 
                  values="Count",
                  hole=0.4,
                  title="MeitY Recognition Share")
    st.plotly_chart(fig4, use_container_width=True)

    # Dataset Preview
    st.subheader("📌 Browse Data")
    st.dataframe(filtered)

else:
    st.info("👉 Please upload the dataset to view the dashboard.")
