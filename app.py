import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Startup Dashboard", layout="wide")

st.title("🚀 Startup Funding Dashboard")

uploaded_file = st.file_uploader("Upload 'startups.csv' file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Clean column names
    df.columns = df.columns.str.lower().str.replace(" ", "_")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount_in_usd"] = pd.to_numeric(df["amount_in_usd"], errors="coerce")

    # Sidebar filters
    st.sidebar.header("Filters")
    cities = sorted(df["city_location"].unique())
    sectors = sorted(df["sector"].unique())

    city_filter = st.sidebar.multiselect("Choose City", cities)
    sector_filter = st.sidebar.multiselect("Choose Sector", sectors)

    filtered = df.copy()

    if city_filter:
        filtered = filtered[filtered["city_location"].isin(city_filter)]
    if sector_filter:
        filtered = filtered[filtered["sector"].isin(sector_filter)]

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Startups", len(filtered))
    col2.metric("Total Funding", f"${filtered['amount_in_usd'].sum():,}")
    col3.metric("Unique Sectors", filtered['sector'].nunique())

    # Funding by Sector
    st.subheader("📊 Funding by Sector")
    sector_funding = (
        filtered.groupby("sector")["amount_in_usd"]
        .sum()
        .reset_index()
        .sort_values("amount_in_usd", ascending=False)
    )
    st.plotly_chart(
        px.bar(sector_funding, x="sector", y="amount_in_usd", title="Funding by Sector"),
        use_container_width=True
    )

    # Funding by City
    st.subheader("🏙 Funding by City")
    city_funding = (
        filtered.groupby("city_location")["amount_in_usd"]
        .sum()
        .reset_index()
    )
    st.plotly_chart(
        px.pie(city_funding, values="amount_in_usd", names="city_location", title="City Funding Share"),
        use_container_width=True
    )

    # Table
    st.subheader("📄 Dataset Preview")
    st.dataframe(filtered)

    # Insights
    st.subheader("💡 Insights")

    if len(sector_funding) > 0:
        top_sector = sector_funding.iloc[0]["sector"]
        st.write(f"✔ *Highest funded sector:* {top_sector}")

else:
    st.info("Upload the CSV file to see the dashboard.")
