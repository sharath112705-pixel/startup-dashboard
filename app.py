import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Startup Funding Dashboard", layout="wide")
st.title("🚀 India's Startup Funding Dashboard")

uploaded_file = st.file_uploader("Upload cleaned_startup_funding.csv", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # CLEAN COLUMN NAMES
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("", "_")
    )

    # Safe numeric conversion
    df["amount_in_usd"] = pd.to_numeric(df["amount_in_usd"], errors="coerce")

    # Convert date
    df["date"] = pd.to_datetime(df["date_dd/mm/yyyy"], errors="coerce")
    df["year"] = df["date"].dt.year

    # Replace NaN text fields
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].fillna("Unknown")

    # -----------------------------------------------------
    # SIDEBAR FILTERS
    # -----------------------------------------------------
    st.sidebar.header("Filters")

    year_filter = st.sidebar.multiselect(
        "Select Year", 
        sorted(df["year"].dropna().unique()), 
        default=sorted(df["year"].dropna().unique())
    )

    sector_filter = st.sidebar.multiselect(
        "Select Sector",
        sorted(df["sector"].dropna().unique()),
        default=sorted(df["sector"].dropna().unique())
    )

    city_filter = st.sidebar.multiselect(
        "Select City",
        sorted(df["city__location"].dropna().unique()),
        default=sorted(df["city__location"].dropna().unique())
    )

    investor_filter = st.sidebar.multiselect(
        "Select Investor",
        sorted(df["investors_name"].dropna().unique()),
        default=sorted(df["investors_name"].dropna().unique())
    )

    # Reset Button
    if st.sidebar.button("Reset Filters"):
        st.experimental_rerun()

    # -----------------------------------------------------
    # FILTER DATA
    # -----------------------------------------------------
    filtered = df[
        df["year"].isin(year_filter)
        & df["sector"].isin(sector_filter)
        & df["city__location"].isin(city_filter)
        & df["investors_name"].isin(investor_filter)
    ]

    if filtered.empty:
        st.error("❌ No data available for selected filters. Try resetting filters.")
        st.stop()

    # -----------------------------------------------------
    # KPIs
    # -----------------------------------------------------
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("💰 Total Funding", f"${filtered['amount_in_usd'].sum():,.0f}")
    col2.metric("🚀 Total Startups", filtered["startup_name"].nunique())
    col3.metric("📊 Avg Funding", f"${filtered['amount_in_usd'].mean():,.0f}")
    col4.metric("🧑‍💼 Unique Investors", filtered["investors_name"].nunique())

    # -----------------------------------------------------
    # VISUALS
    # -----------------------------------------------------

    st.subheader("📌 Funding by Sector")
    fig1 = px.bar(
        filtered.groupby("sector")["amount_in_usd"].sum().reset_index(),
        x="sector",
        y="amount_in_usd",
        color="sector"
    )
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("📌 Top 15 Funded Startups")
    top_startups = (
        filtered.groupby("startup_name")["amount_in_usd"]
        .sum()
        .sort_values(ascending=False)
        .head(15)
        .reset_index()
    )
    fig2 = px.bar(top_startups, x="startup_name", y="amount_in_usd", color="amount_in_usd")
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("📌 Funding Trend Over Years")
    yearly = filtered.groupby("year")["amount_in_usd"].sum().reset_index()
    fig3 = px.line(yearly, x="year", y="amount_in_usd", markers=True)
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("📌 City-wise Startup Count")
    city_counts = filtered["city__location"].value_counts().head(15).reset_index()
    city_counts.columns = ["city", "count"]
    fig4 = px.bar(city_counts, x="city", y="count", color="count")
    st.plotly_chart(fig4, use_container_width=True)

    st.subheader("📌 Investment Type Breakdown")
    fig5 = px.pie(filtered, names="investmentntype", hole=0.45)
    st.plotly_chart(fig5, use_container_width=True)

    st.subheader("📌 Sector → Startup Funding Treemap")
    fig6 = px.treemap(
        filtered,
        path=["sector", "startup_name"],
        values="amount_in_usd"
    )
    st.plotly_chart(fig6, use_container_width=True)

else:
    st.info("⬆ Upload your CSV file to get started.")
