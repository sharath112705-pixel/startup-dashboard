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
DATA_FILE = "/content/drive/MyDrive/data/startup_funding_2015_2017.csv"

# ---------- Helpers ----------
def load_dataframe(uploaded_file):
    # prefer uploaded file from uploader
    if uploaded_file is not None:
        try:
            return pd.read_csv(uploaded_file, encoding="utf-8", low_memory=False)
        except:
            return pd.read_csv(uploaded_file, encoding="latin1", low_memory=False)

    # else try fallback drive path
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
    s = s.astype(str).str.replace(r'[\$,₹]', '', regex=True)
    s = s.replace(['undisclosed', 'nan', 'none', 'None', ''], np.nan)
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
    "noida": (28.5355, 77.3910),
    "faridabad": (28.4089, 77.3178),
    "ghaziabad": (28.6692, 77.4538)
}


def geocode_city(city):
    if pd.isna(city): return (np.nan, np.nan)
    name = str(city).strip().lower()
    for k, v in CITY_COORDS.items():
        if k == name or k in name:
            return v
    return (np.nan, np.nan)


def generate_insights(df, amount_col, city_col, sector_col, date_col, investor_col):
    insights = []

    try:
        total = df[amount_col].sum(skipna=True)
        insights.append(f"Total funding in the filtered data: ${total:,.0f}.")
    except: pass

    try:
        top_sector = df.groupby(sector_col)[amount_col].sum().idxmax()
        top_sector_amt = df.groupby(sector_col)[amount_col].sum().max()
        insights.append(f"{top_sector} received the highest funding (~${top_sector_amt:,.0f}).")
    except: pass

    try:
        city_counts = df[city_col].value_counts(normalize=True, dropna=True)
        if not city_counts.empty:
            top_city = city_counts.index[0]
            share = city_counts.iloc[0] * 100
            insights.append(f"{top_city} contains {share:.1f}% of startups in the filtered set.")
    except: pass

    try:
        df_time = df.dropna(subset=[date_col, amount_col]).copy()
        df_time['year'] = df_time[date_col].dt.year
        yearly = df_time.groupby('year')[amount_col].sum().sort_index()
        if len(yearly) >= 2 and yearly.iloc[0] != 0:
            growth = (yearly.iloc[-1] - yearly.iloc[0]) / yearly.iloc[0] * 100
            insights.append(f"Funding changed by {growth:.1f}% between {yearly.index[0]} and {yearly.index[-1]}.")
    except: pass

    try:
        invs = df[investor_col].dropna().astype(str).str.split(',').explode().str.strip()
        top_inv = invs.value_counts().head(1)
        if not top_inv.empty:
            inv_name = top_inv.index[0]
            deals = int(top_inv.iloc[0])
            insights.append(f"Top active investor: {inv_name} ({deals} deals).")
    except: pass

    if not insights:
        insights.append("No strong patterns found — adjust filters to explore different slices.")

    return insights


# ---------- UI ----------
st.title("🚀 India Startup Intelligence")
st.markdown("<small>Upload your merged CSV or use default Drive file if present.</small>", unsafe_allow_html=True)

uploaded = st.file_uploader("Upload merged CSV (optional)", type=["csv"])
df = load_dataframe(uploaded)

if df is None:
    st.warning("⚠ No data loaded. Upload a CSV.")
    st.stop()

df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

# Detect columns
date_col = find_column(df, ["date"])
startup_col = find_column(df, ["startup_name", "name_of_the_startup"])
city_col = find_column(df, ["city_location", "city"])
industry_col = find_column(df, ["industry_vertical", "industry"])
sector_col = find_column(df, ["sector"])
amount_col = find_column(df, ["amount_in_usd", "amount"])
investor_col = find_column(df, ["investors_name", "investor"])
meity_col = find_column(df, ["is_meity_recognized", "is_meity"])

if amount_col:
    df[amount_col] = clean_amount_series(df[amount_col])

if date_col:
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

if meity_col:
    df[meity_col] = df[meity_col].astype(str).str.lower().str.strip()
    df[meity_col] = df[meity_col].map({
        "yes": "Recognized",
        "no": "Not Recognized"
    }).fillna("Unknown")

df['year'] = df[date_col].dt.year if date_col else np.nan

# Sidebar
st.sidebar.header("Filters")
year_min, year_max = 2015, 2025
year_range = st.sidebar.slider("Year Range", min_value=year_min, max_value=year_max, value=(year_min, year_max))

filtered = df.copy()
if 'year' in filtered:
    filtered = filtered[filtered['year'].between(year_range[0], year_range[1])]


# KPIs
st.subheader("📌 Key Metrics")

total_funding = filtered[amount_col].sum()
unique_startups = filtered[startup_col].nunique()
avg_round = filtered[amount_col].mean()

col1, col2, col3 = st.columns(3)
col1.metric("Total Funding", f"${total_funding:,.0f}")
col2.metric("Unique Startups", unique_startups)
col3.metric("Avg Funding", f"${avg_round:,.0f}")

# Charts
st.subheader("Funding by Year")
trend = filtered.groupby('year')[amount_col].sum().reset_index()
fig = px.line(trend, x='year', y=amount_col, markers=True)
st.plotly_chart(fig, use_container_width=True)

# Insights
st.subheader("Smart Insights")
for i, text in enumerate(generate_insights(filtered, amount_col, city_col, sector_col, date_col, investor_col), 1):
    st.write(f"{i}. {text}")

# Data Table
st.subheader("Filtered Data")
st.dataframe(filtered.reset_index(drop=True))
