import streamlit as st
import pandas as pd
import plotly.express as px

# Streamlit Page Config
st.set_page_config(page_title="Indian Startup Funding Dashboard",
                   layout="wide")

st.title("🚀 Indian Startup Funding Dashboard (2018 - 2025)")

uploaded_file = st.file_uploader("📤 Upload Merged CSV File", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file, encoding="latin1")

    # Try multiple column name variations
    def get_col(cols):
        for col in cols:
            if col.lower().replace(" ", "_") in df.columns.str.lower().str.replace(" ", "_"):
                return df.columns[df.columns.str.lower().str.replace(" ", "_") == col.lower().replace(" ", "_")][0]
        return None

    date_col = get_col(["date", "funded_date", "funding_date"])
    startup_col = get_col(["startup", "startup_name", "company"])
    industry_col = get_col(["industry", "sector", "category", "vertical"])
    city_col = get_col(["city", "location", "headquarter", "location_city"])
    investor_col = get_col(["investor", "investors", "investor_name"])
    funding_col = get_col(["amount", "raised_amount", "funding", "amount_in_usd"])

    # Convert date
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    # Clean funding column
    if funding_col:
        df[funding_col] = (
            df[funding_col]
            .astype(str)
            .str.replace(",", "")
            .str.replace("₹", "")
            .str.replace("$", "")
        )
        df[funding_col] = pd.to_numeric(df[funding_col], errors="coerce")
        df = df[df[funding_col] > 0]

    # Sidebar Filters
    st.sidebar.header("🔍 Filter Options")

    if industry_col:
        industries = sorted(df[industry_col].dropna().unique())
        selected_industry = st.sidebar.multiselect("Industry", industries)
        if len(selected_industry) > 0:
            df = df[df[industry_col].isin(selected_industry)]

    if city_col:
        cities = sorted(df[city_col].dropna().unique())
        selected_city = st.sidebar.multiselect("City", cities)
        if len(selected_city) > 0:
            df = df[df[city_col].isin(selected_city)]

    if investor_col:
        investors = sorted(df[investor_col].dropna().unique())
        selected_investor = st.sidebar.multiselect("Investor", investors)
        if len(selected_investor) > 0:
            df = df[df[investor_col].isin(selected_investor)]

    # KPI Cards
    total_funding = df[funding_col].sum() if funding_col else 0
    total_startups = df[startup_col].nunique() if startup_col else 0
    total_investors = df[investor_col].nunique() if investor_col else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Funding", f"${total_funding:,.0f}")
    col2.metric("🏢 Startups Funded", total_startups)
    col3.metric("🧑‍💼 Unique Investors", total_investors)

    st.markdown("---")

    # Charts Section
    if industry_col and funding_col:
        fig1 = px.bar(
            df.groupby(industry_col)[funding_col].sum().sort_values(ascending=False).head(10),
            orientation="h",
            title="🏭 Top 10 Industries by Funding"
        )
        st.plotly_chart(fig1, use_container_width=True)

    if city_col and funding_col:
        fig2 = px.pie(
            df,
            names=city_col,
            values=funding_col,
            title="📍 Funding Share by City"
        )
        st.plotly_chart(fig2, use_container_width=True)

    if date_col and funding_col:
        df_time = df.groupby(df[date_col].dt.to_period("M"))[funding_col].sum()
        df_time.index = df_time.index.to_timestamp()
        fig3 = px.line(df_time, title="📈 Funding Trend Over Time")
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("### 📄 Filtered Data Preview")
    st.dataframe(df.head(50))

    # Option to Download Filtered Data
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇ Download Filtered Data", data=csv, file_name="filtered_startup_funding.csv")

else:
    st.info("📌 Upload your merged CSV file to generate the dashboard.")
