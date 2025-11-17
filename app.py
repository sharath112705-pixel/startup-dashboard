# app.py — Upgraded "wow" Streamlit dashboard (AI-ish + Map + Investors + MeitY Fix)
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime

st.set_page_config(page_title="🚀 India Startup Intelligence", layout="wide", page_icon="📈")

# -----------------------
# Helpers
# -----------------------
FALLBACK_PATHS = [
    "/content/drive/MyDrive/data/startup_funding_2015_2017.csv",
    "/content/drive/MyDrive/startup_data/startup_funding_2015_2017.csv"
]

def load_dataframe(uploaded_file):
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8', low_memory=False)
        except Exception:
            df = pd.read_csv(uploaded_file, encoding='latin1', low_memory=False)
        return df
    for p in FALLBACK_PATHS:
        if os.path.exists(p):
            try:
                return pd.read_csv(p, encoding='utf-8', low_memory=False)
            except:
                return pd.read_csv(p, encoding='latin1', low_memory=False)
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
    "Bengaluru": (12.9716, 77.5946),
    "Bangalore": (12.9716, 77.5946),
    "Mumbai": (19.0760, 72.8777),
    "Delhi": (28.7041, 77.1025),
    "New Delhi": (28.6139, 77.2090),
    "Chennai": (13.0827, 80.2707),
    "Hyderabad": (17.3850, 78.4867),
    "Pune": (18.5204, 73.8567),
    "Kolkata": (22.5726, 88.3639),
    "Ahmedabad": (23.0225, 72.5714),
    "Gurgaon": (28.4595, 77.0266),
    "Noida": (28.5355, 77.3910),
    "Faridabad": (28.4089, 77.3178),
    "Ghaziabad": (28.6692, 77.4538)
}

def geocode_city(city):
    if pd.isna(city):
        return (np.nan, np.nan)
    name = str(city).strip()
    for key in CITY_COORDS:
        if key.lower() == name.lower() or key.lower() in name.lower():
            return CITY_COORDS[key]
    return (np.nan, np.nan)

def generate_insights(df, amount_col, city_col, sector_col, date_col, investor_col):
    insights = []
    try:
        total = df[amount_col].sum(skipna=True)
        insights.append(f"Total funding in the filtered data: *${total:,.0f}*.")
    except:
        insights.append("Total funding: not available")

    try:
        top_sector = df.groupby(sector_col)[amount_col].sum().idxmax()
        top_sector_amt = df.groupby(sector_col)[amount_col].sum().max()
        insights.append(f"**{top_sector}** received the highest funding (~${top_sector_amt:,.0f}).")
    except:
        pass

    try:
        city_counts = df[city_col].value_counts(normalize=True, dropna=True)
        if not city_counts.empty:
            top_city = city_counts.index[0]
            share = city_counts.iloc[0] * 100
            insights.append(f"{top_city} hosts *{share:.1f}%* of startups.")
    except:
        pass

    try:
        df_time = df.dropna(subset=[date_col, amount_col]).copy()
        df_time['year'] = df_time[date_col].dt.year
        yearly = df_time.groupby('year')[amount_col].sum().sort_index()
        if len(yearly) >= 2:
            growth = (yearly.iloc[-1] - yearly.iloc[0]) / yearly.iloc[0] * 100 if yearly.iloc[0] != 0 else np.nan
            insights.append(f"Funding changed by *{growth:.1f}%* over the years.")
    except:
        pass

    try:
        invs = df[investor_col].dropna().astype(str).str.split(',')
        invs = invs.explode().str.strip()
        top_inv = invs.value_counts().head(1)
        if not top_inv.empty:
            inv_name = top_inv.index[0]
            deals = int(top_inv.iloc[0])
            insights.append(f"Top investor: *{inv_name}* with *{deals}* deals.")
    except:
        pass

    if not insights:
        insights.append("No strong patterns found — try adjusting filters.")
    else:
        insights.append("Want ML predictions next? I can add them 🔥")

    return insights

# -----------------------
# UI
# -----------------------
st.markdown("<h1 style='text-align:center'>🚀 India Startup — Syck & Crazy Dashboard</h1>", unsafe_allow_html=True)

uploaded = st.file_uploader("Upload CSV", type=["csv"])
df = load_dataframe(uploaded)
if df is None:
    st.stop()

df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

date_col = find_column(df, ["date"])
startup_col = find_column(df, ["startup_name"])
city_col = find_column(df, ["city_location", "city"])
sector_col = find_column(df, ["industry_vertical", "sector"])
amount_col = find_column(df, ["amount_in_usd"])
investor_col = find_column(df, ["investors_name"])
meity_col = find_column(df, ["is_meity_recognized", "is_meity"])

if amount_col:
    df[amount_col] = clean_amount_series(df[amount_col])

if date_col:
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

# -----------------------
# MeitY 🔥 FIXED LOGIC
# -----------------------
if meity_col:
    df[meity_col] = df[meity_col].astype(str).str.strip().str.lower()
    df[meity_col] = df[meity_col].map({
        "yes": "Recognized",
        "y": "Recognized",
        "true": "Recognized",
        "1": "Recognized",
        "no": "Not Recognized",
        "n": "Not Recognized",
        "false": "Not Recognized",
        "0": "Not Recognized"
    }).fillna("Unknown")

df['year'] = df[date_col].dt.year if date_col else np.nan

# -----------------------
# Filters
# -----------------------
st.sidebar.header("Filters")

year_min = int(df['year'].min()) if df['year'].notna().any() else 2015
year_max = int(df['year'].max()) if df['year'].notna().any() else datetime.now().year
year_range = st.sidebar.slider("Year range", year_min, year_max, (year_min, year_max))

sector_sel = st.sidebar.multiselect("Sector", sorted(df[sector_col].dropna().unique()),
                                    default=sorted(df[sector_col].dropna().unique())[:4]
                                    if sector_col else [])

city_sel = st.sidebar.multiselect("City (multi)", sorted(df[city_col].dropna().unique()),
                                  default=sorted(df[city_col].dropna().unique())[:6]
                                  if city_col else [])

meity_options = sorted(df[meity_col].unique()) if meity_col else []
meity_sel = st.sidebar.multiselect("MeitY Recognition", meity_options, default=meity_options)

top_n = st.sidebar.slider("Top N", 5, 25, 10)

filtered = df.copy()
filtered = filtered[filtered['year'].between(year_range[0], year_range[1])]

if sector_sel:
    filtered = filtered[filtered[sector_col].isin(sector_sel)]
if city_sel:
    filtered = filtered[filtered[city_col].isin(city_sel)]
if meity_sel:
    filtered = filtered[filtered[meity_col].isin(meity_sel)]

# -----------------------
# KPIs
# -----------------------
c1, c2, c3, c4 = st.columns(4)

total_funding = filtered[amount_col].sum()
num_startups = filtered[startup_col].nunique()

if meity_col:
    recognized_count = (filtered[meity_col] == "Recognized").sum()
    total = len(filtered)
    meity_pct = (recognized_count/total*100) if total > 0 else 0
else:
    meity_pct = np.nan

c1.metric("💰 Total Funding", f"${total_funding:,.0f}")
c2.metric("🚀 Startups", f"{num_startups}")
c3.metric("💸 Avg Round", f"${filtered[amount_col].mean():,.0f}")
c4.metric("🏛 MeitY Recognized", f"{meity_pct:.1f}%" if not np.isnan(meity_pct) else "N/A")

# -----------------------
# MeitY Distribution Chart
# -----------------------
if meity_col:
    st.subheader("🏛 MeitY Recognition Distribution")
    pie_df = filtered[meity_col].value_counts().reset_index()
    pie_df.columns = ["Recognition", "Count"]
    fig_meity = px.pie(pie_df, names="Recognition", values="Count", hole=0.4)
    st.plotly_chart(fig_meity, use_container_width=True)

# -----------------------
# Insights
# -----------------------
st.subheader("🤖 Smart Insights")
for i, line in enumerate(generate_insights(filtered, amount_col, city_col, sector_col, date_col, investor_col)):
    st.write(f"{i+1}. {line}")

# -----------------------
# Map
# -----------------------
st.markdown("---")
st.subheader("📍 Startup Map")
if city_col:
    filtered['lat'], filtered['lon'] = zip(*filtered[city_col].map(geocode_city))
    map_df = filtered.dropna(subset=['lat','lon'])
    fig_map = px.scatter_mapbox(map_df, lat='lat', lon='lon',
                                size=amount_col, color=sector_col,
                                mapbox_style="open-street-map", zoom=4)
    st.plotly_chart(fig_map, use_container_width=True)

# -----------------------
# Dataset
# -----------------------
st.markdown("---")
st.subheader("📄 Filtered Dataset")
st.dataframe(filtered)

csv = filtered.to_csv(index=False).encode('utf-8')
st.download_button("⬇ Download CSV", csv, "filtered_startups.csv")

st.markdown("<h4 style='text-align:center;color:gray'>🔥 Built for WOW at Expo — Filters tell the story!</h4>", unsafe_allow_html=True)
