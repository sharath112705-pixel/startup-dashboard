import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="🚀 Indian Startup Dashboard",
    layout="wide",
    page_icon="📊"
)

st.markdown("<h1 style='text-align:center;color:#00eaff;'>India Startup Intelligence Dashboard</h1>",
            unsafe_allow_html=True)

uploaded_file = st.file_uploader("📌 Upload merged Startup Dataset (.csv)", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    df.columns = df.columns.str.lower().str.replace(" ", "_")
    df["amount_in_usd"] = pd.to_numeric(df["amount_in_usd"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Sidebar Filters
    st.sidebar.header("🔍 Filters")
    city = st.sidebar.multiselect("City", sorted(df["city"].dropna().unique()))
    sector = st.sidebar.multiselect("Sector", sorted(df["industry_vertical"].dropna().unique()))

    filtered = df.copy()
    if city:
        filtered = filtered[filtered["city"].isin(city)]
    if sector:
        filtered = filtered[filtered["industry_vertical"].isin(sector)]

    # KPIs
    st.markdown("### 📌 Key Metrics")
    k1, k2, k3 = st.columns(3)

    total_funding = filtered["amount_in_usd"].sum()
    total_startups = filtered["startup_name"].nunique()
    unique_sectors = filtered["industry_vertical"].nunique()

    k1.metric("💰 Total Funding", f"${total_funding:,.0f}")
    k2.metric("🚀 Total Startups", total_startups)
    k3.metric("🏭 Sectors Covered", unique_sectors)

    st.markdown("---")

    st.markdown("## 📊 Visual Insights")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📍 City Funding", "💼 Sector Distribution", "📈 Funding Trend", "🏆 Top Funded Startups"]
    )

    with tab1:
        city_funding = filtered.groupby("city")["amount_in_usd"].sum().reset_index()
        if not city_funding.empty:
            fig1 = px.bar(city_funding, x="city", y="amount_in_usd",
                          title="Funding by Cities", text_auto=True)
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.warning("No data available for the selected filter.")

    with tab2:
        sector_funding = filtered.groupby("industry_vertical")["amount_in_usd"].sum().reset_index()
        if not sector_funding.empty:
            fig2 = px.pie(sector_funding, values="amount_in_usd",
                          names="industry_vertical", title="Sector-wise Funding Share")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("No data available for the selected filter.")

    with tab3:
        trend = filtered.groupby(filtered["date"].dt.to_period("M"))["amount_in_usd"].sum().reset_index()
        trend["date"] = trend["date"].astype(str)
        if not trend.empty:
            fig3 = px.line(trend, x="date", y="amount_in_usd", markers=True,
                           title="Funding Trend Over Time")
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.warning("No data available for the selected filter.")

    with tab4:
        top_funded = filtered.groupby("startup_name")["amount_in_usd"].sum().nlargest(10).reset_index()
        if not top_funded.empty:
            fig4 = px.bar(top_funded, x="amount_in_usd", y="startup_name", orientation="h",
                          title="Top Funded Startups")
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.warning("No data available for the selected filter.")

    st.markdown("---")
    st.markdown("## 📄 Dataset View")
    st.dataframe(filtered, use_container_width=True)

    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download Filtered Dataset",
                       data=csv, file_name="filtered_startups.csv",
                       mime="text/csv")
else:
    st.info("👆 Please upload the merged startup dataset to continue.")
