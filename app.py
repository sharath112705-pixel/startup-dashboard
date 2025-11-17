import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Startup Funding Dashboard", layout="wide")

# -----------------------
# 1) Load CSV
# -----------------------
st.title("🚀 Startup Funding Dashboard")

uploaded_file = st.file_uploader("Upload your startup CSV file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # CLEAN COLUMN NAMES
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "").str.replace("-", "")

    # FIX BAD DATE COLUMN NAME
    if "date_dd/mm/yyyy" in df.columns:
        df.rename(columns={"date_dd/mm/yyyy": "date"}, inplace=True)

    # Convert date
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Clean USD Column
    if "amount_in_usd" in df.columns:
        df["amount_in_usd"] = (
            df["amount_in_usd"]
            .astype(str)
            .str.replace(",", "")
            .str.replace("$", "")
        )
        df["amount_in_usd"] = pd.to_numeric(df["amount_in_usd"], errors="coerce")

    # -----------------------
    # 2) SIDEBAR FILTERS
    # -----------------------
    st.sidebar.header("Filters")

    # City filter
    city_list = sorted(df["city__location"].dropna().unique())
    city_filter = st.sidebar.multiselect("Select City", city_list)

    # Sector filter
    sector_list = sorted(df["sector"].dropna().unique())
    sector_filter = st.sidebar.multiselect("Select Sector", sector_list)

    filtered_df = df.copy()

    if city_filter:
        filtered_df = filtered_df[filtered_df["city__location"].isin(city_filter)]

    if sector_filter:
        filtered_df = filtered_df[filtered_df["sector"].isin(sector_filter)]

    # -----------------------
    # 3) METRICS
    # -----------------------
    st.subheader("📊 Key Metrics")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Startups", len(filtered_df))
    col2.metric("Total Funding (USD)", f"${filtered_df['amount_in_usd'].sum():,}")
    col3.metric("Unique Sectors", filtered_df["sector"].nunique())

    # -----------------------
    # 4) FUNDING CHART
    # -----------------------
    if "sector" in filtered_df.columns:
        funding_by_sector = (
            filtered_df.groupby("sector")["amount_in_usd"]
            .sum()
            .reset_index()
            .sort_values("amount_in_usd", ascending=False)
        )

        fig1 = px.bar(
            funding_by_sector,
            x="sector",
            y="amount_in_usd",
            title="Funding by Sector",
        )
        st.plotly_chart(fig1, use_container_width=True)

    # -----------------------
    # 5) STARTUPS TABLE
    # -----------------------
    st.subheader("📄 Startup Data")
    st.dataframe(filtered_df)

    # -----------------------
    # 6) INSIGHTS
    # -----------------------
    st.subheader("💡 Insights")

    if not funding_by_sector.empty:
        top_sector = funding_by_sector.iloc[0]["sector"]
        st.write(f"✔ *Highest funded sector:* {top_sector}")

else:
    st.info("👆 Upload your CSV file to continue.")
