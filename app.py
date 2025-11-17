import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------
# PAGE SETUP
# ---------------------------------------------------
st.set_page_config(
    page_title="India's Startup Boom Dashboard",
    layout="wide",
)

st.title("🚀 India's Startup Boom Dashboard")
st.markdown("### A complete interactive startup funding analysis (Python + Streamlit + Plotly)")

# ---------------------------------------------------
# FILE UPLOADER
# ---------------------------------------------------
uploaded_file = st.file_uploader("Upload your cleaned_startup_funding.csv", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Show user the real columns
    st.write("### 📌 Dataset Columns Detected")
    st.write(list(df.columns))

    # ---------------------------------------------------
    # CLEAN COLUMN NAMES
    # ---------------------------------------------------
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # Convert date
    df["date"] = pd.to_datetime(df["date_dd/mm/yyyy"], errors='coerce')
    df["year"] = df["date"].dt.year

    # Ensure numeric
    df["amount_in_usd"] = pd.to_numeric(df["amount_in_usd"], errors="coerce")

    # ---------------------------------------------------
    # SIDEBAR FILTERS
    # ---------------------------------------------------
    st.sidebar.header("📊 Filters")

    years = sorted(df["year"].dropna().unique())
    sectors = sorted(df["sector"].dropna().unique())
    cities = sorted(df["city__location"].dropna().unique())
    investors = sorted(df["investors_name"].dropna().unique())

    year_filter = st.sidebar.multiselect("Select Year", years, years)
    sector_filter = st.sidebar.multiselect("Select Sector", sectors, sectors)
    city_filter = st.sidebar.multiselect("Select City", cities, cities)
    investor_filter = st.sidebar.multiselect("Select Investor", investors, investors)

    # Filter data
    filtered = df[
        (df["year"].isin(year_filter)) &
        (df["sector"].isin(sector_filter)) &
        (df["city__location"].isin(city_filter)) &
        (df["investors_name"].isin(investor_filter))
    ]

    # ---------------------------------------------------
    # TOP KPI METRICS
    # ---------------------------------------------------
    total_funding = filtered["amount_in_usd"].sum()
    total_startups = filtered["startup_name"].nunique()
    avg_funding = filtered["amount_in_usd"].mean()
    total_investors = filtered["investors_name"].nunique()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("💰 Total Funding", f"${total_funding:,.0f}")
    col2.metric("🚀 Total Startups", total_startups)
    col3.metric("📊 Avg Funding", f"${avg_funding:,.0f}")
    col4.metric("🧑‍💼 Unique Investors", total_investors)

    # ---------------------------------------------------
    # VISUAL 1: Funding by Sector
    # ---------------------------------------------------
    st.subheader("📌 Funding by Sector")
    fig1 = px.bar(
        filtered,
        x="sector",
        y="amount_in_usd",
        color="sector",
        title="Funding Distribution by Sector",
        height=450
    )
    st.plotly_chart(fig1, use_container_width=True)

    # ---------------------------------------------------
    # VISUAL 2: Top 15 Funded Startups
    # ---------------------------------------------------
    st.subheader("📌 Top Funded Startups")
    top_startups = (
        filtered.groupby("startup_name")["amount_in_usd"]
        .sum()
        .nlargest(15)
        .reset_index()
    )
    fig2 = px.bar(
        top_startups,
        x="startup_name",
        y="amount_in_usd",
        color="amount_in_usd",
        title="Top 15 Funded Startups",
        height=450
    )
    st.plotly_chart(fig2, use_container_width=True)

    # ---------------------------------------------------
    # VISUAL 3: Yearly Funding Trend
    # ---------------------------------------------------
    st.subheader("📌 Yearly Funding Trend")
    yearly = filtered.groupby("year")["amount_in_usd"].sum().reset_index()
    fig3 = px.line(
        yearly,
        x="year",
        y="amount_in_usd",
        markers=True,
        title="Funding Trend Over Years",
        height=450
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ---------------------------------------------------
    # VISUAL 4: Startup Count by City
    # ---------------------------------------------------
    st.subheader("📌 City-wise Startup Count")
    city_count = filtered["city__location"].value_counts().head(15).reset_index()
    city_count.columns = ["city", "count"]

    fig4 = px.bar(
        city_count,
        x="city",
        y="count",
        color="count",
        title="Top Cities by Startup Count",
        height=450
    )
    st.plotly_chart(fig4, use_container_width=True)

    # ---------------------------------------------------
    # VISUAL 5: Investment Type Distribution
    # ---------------------------------------------------
    st.subheader("📌 Investment Type Distribution")
    fig5 = px.pie(
        filtered,
        names="investmentntype",
        title="Funding Types",
        hole=0.4,
        height=450
    )
    st.plotly_chart(fig5, use_container_width=True)

    # ---------------------------------------------------
    # VISUAL 6: Treemap - Sector → Startup Funding
    # ---------------------------------------------------
    st.subheader("📌 Sector-Level Funding Treemap")
    fig6 = px.treemap(
        filtered,
        path=["sector", "startup_name"],
        values="amount_in_usd",
        title="Treemap of Funding by Sector & Startup",
        height=550
    )
    st.plotly_chart(fig6, use_container_width=True)

    # ---------------------------------------------------
    # INSIGHTS SECTION
    # ---------------------------------------------------
    st.subheader("📌 Automated Insights")

    st.write(f"✔ The highest funded sector is:** {top_startups.iloc[0,0]}")
    st.write(f"✔ Total funding during selected period:** ${total_funding:,.0f}")
    st.write(f"✔ Number of active startups:** {total_startups}")
    st.write(f"✔ Top city for startups:** {city_count.iloc[0,0]}")

else:
    st.info("⬆ Upload your CSV file to begin.")
