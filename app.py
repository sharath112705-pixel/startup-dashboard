# app.py — Final Streamlit dashboard (two filters, MeitY fixed, theme toggle)
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
from datetime import datetime

# ---------- Config ----------
st.set_page_config(page_title="India Startup Intelligence", layout="wide", page_icon="📈")

DATA_FILE = "india_startup_funding_2015_2025_REAL_CLEANED_v2.csv"

# ---------- Helpers ----------
def load_dataframe(uploaded_file):
    if uploaded_file is not None:
        try:
            return pd.read_csv(uploaded_file, encoding="utf-8", low_memory=False)
        except:
            return pd.read_csv(uploaded_file, encoding="latin1", low_memory=False)
    if os.path.exists(DATA_FILE):
        try:
            return pd.read_csv(DATA_FILE, encoding="utf-8", low_memory=False)
        except:
            return pd.read_csv(DATA_FILE, encoding="latin1", low_memory=False)
    return None

def find_column(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

def clean_amount_series(s):
    s = s.astype(str).str.replace(r'[\$,₹,]', '', regex=True)
    s = s.replace(['undisclosed','nan','none','None',''], np.nan)
    return pd.to_numeric(s, errors='coerce')

CITY_COORDS = {
    "bengaluru": (12.9716, 77.5946),
    "bangalore": (12.9716, 77.5946),
    "mumbai": (19.0760, 72.8777),
    "delhi": (28.7041, 77.1025),
    "new delhi": (28.6139, 77.2090),
    "chennai": (13.0827, 80.2707),
    "hyderabad": (17.3850, 78.4867),
    "pune": (18.5204, 73.8567),
    "kolkata": (22.5726, 88.3639),
    "ahmedabad": (23.0225, 72.5714),
    "gurgaon": (28.4595, 77.0266),
    "noida": (28.5355, 77.3910),
    "faridabad": (28.4089, 77.3178),
    "ghaziabad": (28.6692, 77.4538)
}

def geocode_city(city):
    if pd.isna(city): return (np.nan, np.nan)
    name = str(city).strip().lower()
    for k,v in CITY_COORDS.items():
        if k in name:
            return v
    return (np.nan, np.nan)

def generate_insights(df, amount_col, city_col, sector_col, date_col, investor_col):
    insights = []
    try:
        insights.append(f"Total funding: ${df[amount_col].sum():,.0f}")
        insights.append(f"Top sector: {df.groupby(sector_col)[amount_col].sum().idxmax()}")
        insights.append(f"Top city: {df[city_col].mode()[0]}")
        invs = df[investor_col].str.split(',').explode().str.strip()
        insights.append(f"Top investor: {invs.value_counts().idxmax()}")
    except:
        pass
    return insights

# ---------- UI ----------
st.title("🚀 India Startup Intelligence")

uploaded = st.file_uploader("Upload merged CSV (optional)", type=["csv"])
df = load_dataframe(uploaded)

if df is None:
    st.stop()

df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

date_col = find_column(df, ["date"])
startup_col = find_column(df, ["startup_name"])
city_col = find_column(df, ["city"])
industry_col = find_column(df, ["industry_vertical"])
sector_col = find_column(df, ["sector"])
amount_col = find_column(df, ["amount_in_usd"])
investor_col = find_column(df, ["investors_name"])
meity_col = find_column(df, ["is_meity_recognized"])

df[amount_col] = clean_amount_series(df[amount_col])
df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
df = df.dropna(subset=[date_col, amount_col, startup_col])
df["year"] = df[date_col].dt.year

# ---------- Sidebar ----------
st.sidebar.header("Controls")

year_range = st.sidebar.slider(
    "Year Range",
    int(df.year.min()),
    int(df.year.max()),
    (int(df.year.min()), int(df.year.max()))
)

industry_sel = st.sidebar.multiselect("Industry", df[industry_col].unique(), default=df[industry_col].unique())
sector_sel = st.sidebar.multiselect("Sector", df[sector_col].unique(), default=df[sector_col].unique())
city_sel = st.sidebar.multiselect("City", df[city_col].unique(), default=df[city_col].unique())
meity_sel = st.sidebar.multiselect("MeitY", df[meity_col].unique(), default=df[meity_col].unique())

top_n = st.sidebar.slider("Top N", 5, 25, 10)

filtered = df[
    (df["year"].between(year_range[0], year_range[1])) &
    (df[industry_col].isin(industry_sel)) &
    (df[sector_col].isin(sector_sel)) &
    (df[city_col].isin(city_sel)) &
    (df[meity_col].isin(meity_sel))
]

# ---------- KPIs ----------
st.subheader("Key Metrics")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Funding", f"${filtered[amount_col].sum():,.0f}")
k2.metric("Startups", filtered[startup_col].nunique())
k3.metric("Avg Round", f"${filtered[amount_col].mean():,.0f}")
k4.metric("MeitY %", f"{(filtered[meity_col]=='Yes').mean()*100:.1f}%")

# ================================
# DASHBOARD VISUALIZATION GRID
# ================================

# ---------- ROW 1 ----------
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.subheader("MeitY Recognition Distribution (Pie Chart)")
    meity_df = filtered[meity_col].value_counts().reset_index()
    meity_df.columns = ["Recognition", "Count"]
    fig_meity = px.pie(meity_df, names="Recognition", values="Count", hole=0.4)
    st.plotly_chart(fig_meity, use_container_width=True)

with row1_col2:
    st.subheader("Smart Insights Summary")
    for i in generate_insights(filtered, amount_col, city_col, sector_col, date_col, investor_col):
        st.write("•", i)

# ---------- ROW 2 ----------
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.subheader("Startup Distribution Across India (Map)")
    temp = filtered.copy()
    temp[["lat","lon"]] = temp[city_col].apply(lambda x: pd.Series(geocode_city(x)))
    map_df = temp.dropna(subset=["lat","lon"])
    fig_map = px.scatter_mapbox(
        map_df, lat="lat", lon="lon",
        hover_name=startup_col, size=amount_col, zoom=4
    )
    fig_map.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig_map, use_container_width=True)

with row2_col2:
    st.subheader("Top Cities by Total Funding (Bar Chart)")
    city_sum = filtered.groupby(city_col)[amount_col].sum().reset_index()
    fig_city = px.bar(city_sum, x=amount_col, y=city_col, orientation="h")
    st.plotly_chart(fig_city, use_container_width=True)

# ---------- ROW 3 ----------
row3_col1, row3_col2 = st.columns(2)

with row3_col1:
    st.subheader("Sector-wise Funding Contribution (Treemap)")
    sec_df = filtered.groupby(sector_col)[amount_col].sum().reset_index()
    fig_sec = px.treemap(sec_df, path=[sector_col], values=amount_col)
    st.plotly_chart(fig_sec, use_container_width=True)

with row3_col2:
    st.subheader("Monthly Funding Trend (Line Chart)")
    trend = filtered.groupby(pd.Grouper(key=date_col, freq="M"))[amount_col].sum().reset_index()
    fig_trend = px.line(trend, x=date_col, y=amount_col)
    st.plotly_chart(fig_trend, use_container_width=True)

# ---------- ROW 4 ----------
st.markdown("---")
st.subheader("Top Investors by Number of Deals (Bar Chart)")
invs = filtered[investor_col].astype(str).str.split(",").explode()
inv_summary = invs.value_counts().head(top_n).reset_index()
inv_summary.columns = ["Investor", "Deals"]
fig_inv = px.bar(inv_summary, x="Deals", y="Investor", orientation="h")
st.plotly_chart(fig_inv, use_container_width=True)

# ---------- Data ----------
st.markdown("---")
st.subheader("Filtered Dataset Preview")
st.dataframe(filtered)

csv = filtered.to_csv(index=False).encode("utf-8")
st.download_button("Download Filtered CSV", csv, "filtered_startups.csv")

st.markdown("<div style='text-align:center;color:gray'>Dashboard ready.</div>", unsafe_allow_html=True)
