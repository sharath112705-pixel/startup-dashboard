# app.py — Final Streamlit dashboard (two filters, MeitY fixed, theme toggle)
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
from datetime import datetime

# ---------- Config ----------
st.set_page_config(page_title="India Startup Intelligence", layout="wide", page_icon="📈")

# fallback path (your uploaded / drive file)
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

# small city -> lat/lon table (major metros)
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
    "noida": (28.5355, 77.3910)
}

def geocode_city(city):
    if pd.isna(city): 
        return (np.nan, np.nan)
    name = str(city).strip().lower()
    for k,v in CITY_COORDS.items():
        if k in name:
            return v
    return (np.nan, np.nan)

# ---------- UI ----------
st.title("🚀 India Startup Intelligence")

uploaded = st.file_uploader("Upload merged CSV", type=["csv"])
df = load_dataframe(uploaded)

if df is None:
    st.stop()

# normalize columns
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

# detect relevant columns
date_col = find_column(df, ["date"])
startup_col = find_column(df, ["startup_name"])
city_col = find_column(df, ["city"])
industry_col = find_column(df, ["industry_vertical"])
sector_col = find_column(df, ["sector"])
amount_col = find_column(df, ["amount_in_usd"])
investor_col = find_column(df, ["investors_name"])
meity_col = find_column(df, ["is_meity_recognized"])

# basic checks
df[amount_col] = clean_amount_series(df[amount_col])
df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
df = df.dropna(subset=[date_col, amount_col, startup_col])
df['year'] = df[date_col].dt.year

# ---------- Sidebar ----------
st.sidebar.header("Controls")

year_range = st.sidebar.slider(
    "Year range",
    int(df['year'].min()),
    int(df['year'].max()),
    (int(df['year'].min()), int(df['year'].max()))
)

industry_list = sorted(df[industry_col].dropna().unique())
sector_list = sorted(df[sector_col].dropna().unique())
city_list = sorted(df[city_col].dropna().unique())

industry_sel = st.sidebar.multiselect("Industry Vertical", industry_list, default=industry_list)
sector_sel = st.sidebar.multiselect("Sector", sector_list, default=sector_list)
city_sel = st.sidebar.multiselect("City", city_list, default=city_list)

meity_sel = st.sidebar.multiselect("MeitY Recognition", ["Yes","No"], default=["Yes","No"])
top_n = st.sidebar.slider("Top N (charts)", 5, 25, 10)

# ---------- Apply Filters ----------
filtered = df[
    (df['year'].between(year_range[0], year_range[1])) &
    (df[industry_col].isin(industry_sel)) &
    (df[sector_col].isin(sector_sel)) &
    (df[city_col].isin(city_sel)) &
    (df[meity_col].isin(meity_sel))
]

# ---------- KPIs ----------
st.markdown("## Key metrics")
col1, col2, col3, col4 = st.columns(4)

total_funding = filtered[amount_col].sum()
unique_startups = filtered[startup_col].nunique()
avg_round = filtered[amount_col].mean()
meity_pct = (filtered[meity_col] == "Yes").mean()*100 if not filtered.empty else 0

col1.metric("💰 Total Funding", f"${total_funding:,.0f}")
col2.metric("🚀 Unique Startups", f"{unique_startups}")
col3.metric("💸 Avg Funding Round", f"${(avg_round or 0):,.0f}")
col4.metric("🏛 MeitY Recognized", f"{meity_pct:.1f}%")

# ---------- MeitY Pie ----------
st.subheader("MeitY Recognition Breakdown")
meity_df = filtered[meity_col].value_counts().reset_index()
meity_df.columns = ["Recognition", "Count"]
fig_meity = px.pie(meity_df, names="Recognition", values="Count", hole=0.4)
st.plotly_chart(fig_meity, use_container_width=True)

# ---------- Map + Top Cities ----------
st.markdown("---")
left, right = st.columns([3,2])

with left:
    st.subheader("Startup Map (city-level)")
    if not filtered.empty:
        temp = filtered.copy()
        temp['lat'], temp['lon'] = zip(*temp[city_col].map(geocode_city))
        map_df = temp.dropna(subset=['lat','lon'])
        if not map_df.empty:
            fig_map = px.scatter_mapbox(
                map_df, lat='lat', lon='lon', hover_name=startup_col,
                size=amount_col, zoom=4
            )
            fig_map.update_layout(mapbox_style="open-street-map")
            st.plotly_chart(fig_map, use_container_width=True)

with right:
    st.subheader("Top Cities by Funding")
    city_sum = filtered.groupby(city_col)[amount_col].sum().sort_values(ascending=False).head(top_n).reset_index()
    fig_city = px.bar(city_sum, x=amount_col, y=city_col, orientation='h')
    st.plotly_chart(fig_city, use_container_width=True)

# ---------- Sector Treemap ----------
st.subheader("Sector (Treemap) — Top contributors")
sec_df = filtered.groupby(sector_col)[amount_col].sum().reset_index()
fig_sec = px.treemap(sec_df, path=[sector_col], values=amount_col)
st.plotly_chart(fig_sec, use_container_width=True)

# ---------- Funding Trend ----------
st.subheader("Funding Trend (monthly)")
trend = filtered.groupby(pd.Grouper(key=date_col, freq='M'))[amount_col].sum().reset_index()
fig_trend = px.line(trend, x=date_col, y=amount_col)
st.plotly_chart(fig_trend, use_container_width=True)

# ---------- Investors panel ----------
st.markdown("---")
st.subheader("Top Investors Explorer")

if not filtered.empty:
    invs = filtered[investor_col].astype(str).str.split(',').explode()
    invs = invs[~invs.isin(['', 'nan', 'None'])]
    
    inv_summary = invs.value_counts().head(top_n).reset_index()
    inv_summary.columns = ["Investor", "Deals"]

    fig_inv = px.bar(inv_summary, x="Deals", y="Investor", orientation='h')
    st.plotly_chart(fig_inv, use_container_width=True)

# ---------- Data & download ----------
st.markdown("---")
st.subheader("Filtered Data")
st.dataframe(filtered.reset_index(drop=True))
csv = filtered.to_csv(index=False).encode('utf-8')
st.download_button("Download filtered CSV", csv, file_name="filtered_startups.csv", mime="text/csv")

# Footer
st.markdown("<div style='text-align:center;color:gray;margin-top:10px'>Dashboard ready. Use filters to explore.</div>", unsafe_allow_html=True)
