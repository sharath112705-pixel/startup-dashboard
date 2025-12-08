# app.py — Final Streamlit Dashboard with Extended Visualizations
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

st.set_page_config(page_title="India Startup Intelligence", layout="wide", page_icon="📈")

DATA_FILE = "india_startup_funding_2015_2025_REAL_CLEANED_v2.csv"

# ---------- Load Data ----------
def load_dataframe(uploaded):
    if uploaded is not None:
        return pd.read_csv(uploaded)
    elif os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return None

uploaded = st.file_uploader("Upload Startup Dataset (CSV)", type=["csv"])
df = load_dataframe(uploaded)

if df is None:
    st.stop()

df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
df["date"] = pd.to_datetime(df["date"])
df["year"] = df["date"].dt.year
df["amount_in_usd"] = pd.to_numeric(df["amount_in_usd"], errors="coerce")

# ---------- Sidebar Filters ----------
st.sidebar.header("Filters")

year_range = st.sidebar.slider("Year Range", int(df.year.min()), int(df.year.max()),
                               (int(df.year.min()), int(df.year.max())))

industry_sel = st.sidebar.multiselect("Industry", df["industry_vertical"].unique(),
                                      df["industry_vertical"].unique())
sector_sel = st.sidebar.multiselect("Sector", df["sector"].unique(), df["sector"].unique())
city_sel = st.sidebar.multiselect("City", df["city"].unique(), df["city"].unique())
meity_sel = st.sidebar.multiselect("MeitY", df["is_meity_recognized"].unique(),
                                   df["is_meity_recognized"].unique())

top_n = st.sidebar.slider("Top N", 5, 25, 10)

filtered = df[
    (df["year"].between(year_range[0], year_range[1])) &
    (df["industry_vertical"].isin(industry_sel)) &
    (df["sector"].isin(sector_sel)) &
    (df["city"].isin(city_sel)) &
    (df["is_meity_recognized"].isin(meity_sel))
]

# ---------- KPIs ----------
st.title("🚀 India Startup Intelligence Dashboard")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Funding", f"${filtered.amount_in_usd.sum():,.0f}")
k2.metric("Startups", filtered.startup_name.nunique())
k3.metric("Avg Funding", f"${filtered.amount_in_usd.mean():,.0f}")
k4.metric("MeitY %", f"{(filtered.is_meity_recognized=='Yes').mean()*100:.1f}%")

# =========================
# ROW 1
# =========================
r1c1, r1c2 = st.columns(2)

with r1c1:
    st.subheader("MeitY Recognition Distribution (Pie Chart)")
    meity_df = filtered.is_meity_recognized.value_counts().reset_index()
    meity_df.columns = ["Recognition", "Count"]
    fig_meity = px.pie(meity_df, names="Recognition", values="Count", hole=0.4)
    st.plotly_chart(fig_meity, use_container_width=True)

with r1c2:
    st.subheader("Funding Distribution (Histogram)")
    fig_hist = px.histogram(filtered, x="amount_in_usd", nbins=30)
    st.plotly_chart(fig_hist, use_container_width=True)

# =========================
# ROW 2
# =========================
r2c1, r2c2 = st.columns(2)

with r2c1:
    st.subheader("Top Cities by Funding (Bar Chart)")
    city_sum = filtered.groupby("city")["amount_in_usd"].sum().reset_index()
    fig_city = px.bar(city_sum, x="amount_in_usd", y="city", orientation="h")
    st.plotly_chart(fig_city, use_container_width=True)

with r2c2:
    st.subheader("Top Startups by Funding")
    top_start = filtered.groupby("startup_name")["amount_in_usd"].sum().nlargest(top_n).reset_index()
    fig_start = px.bar(top_start, x="amount_in_usd", y="startup_name", orientation="h")
    st.plotly_chart(fig_start, use_container_width=True)

# =========================
# ROW 3
# =========================
r3c1, r3c2 = st.columns(2)

with r3c1:
    st.subheader("Sector-wise Funding (Treemap)")
    sec_df = filtered.groupby("sector")["amount_in_usd"].sum().reset_index()
    fig_sec = px.treemap(sec_df, path=["sector"], values="amount_in_usd")
    st.plotly_chart(fig_sec, use_container_width=True)

with r3c2:
    st.subheader("Industry-wise Funding Comparison (Stacked Bar)")
    ind_df = filtered.groupby(["year","industry_vertical"])["amount_in_usd"].sum().reset_index()
    fig_ind = px.bar(ind_df, x="year", y="amount_in_usd", color="industry_vertical")
    st.plotly_chart(fig_ind, use_container_width=True)

# =========================
# ROW 4
# =========================
r4c1, r4c2 = st.columns(2)

with r4c1:
    st.subheader("Year-wise Funding Growth (Area Chart)")
    year_df = filtered.groupby("year")["amount_in_usd"].sum().reset_index()
    fig_year = px.area(year_df, x="year", y="amount_in_usd")
    st.plotly_chart(fig_year, use_container_width=True)

with r4c2:
    st.subheader("MeitY vs Non-MeitY Funding Comparison")
    meity_fund = filtered.groupby("is_meity_recognized")["amount_in_usd"].sum().reset_index()
    fig_meity_bar = px.bar(meity_fund, x="is_meity_recognized", y="amount_in_usd")
    st.plotly_chart(fig_meity_bar, use_container_width=True)

# =========================
# ROW 5
# =========================
st.subheader("Top Investors by Number of Deals")
inv = filtered["investors_name"].astype(str).str.split(",").explode()
inv_summary = inv.value_counts().head(top_n).reset_index()
inv_summary.columns = ["Investor", "Deals"]
fig_inv = px.bar(inv_summary, x="Deals", y="Investor", orientation="h")
st.plotly_chart(fig_inv, use_container_width=True)

# =========================
# DATA PREVIEW
# =========================
st.subheader("Filtered Dataset Preview")
st.dataframe(filtered, use_container_width=True)

csv = filtered.to_csv(index=False).encode("utf-8")
st.download_button("Download Filtered CSV", csv, "filtered_startups.csv")

st.markdown("<div style='text-align:center;color:gray'>✅ Dashboard Ready for Final Year Review</div>",
            unsafe_allow_html=True)
