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
    "noida": (28.5355, 77.3910),
    "faridabad": (28.4089, 77.3178),
    "ghaziabad": (28.6692, 77.4538)
}
def geocode_city(city):
    if pd.isna(city): return (np.nan, np.nan)
    name = str(city).strip().lower()
    for k,v in CITY_COORDS.items():
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
st.markdown("<small>Upload your merged CSV or the app will use the default Drive file if present.</small>", unsafe_allow_html=True)

uploaded = st.file_uploader("Upload merged CSV (optional)", type=["csv"])
df = load_dataframe(uploaded)

if df is None:
    st.warning(f"No data loaded. Put your CSV in Streamlit uploader or place the file at:\n{DATA_FILE}")
    st.stop()

# normalize columns
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

# detect relevant columns
date_col = find_column(df, ["date", "date_dd/mm/yyyy", "funded_date"])
startup_col = find_column(df, ["startup_name", "name_of_the_startup", "startup"])
city_col = find_column(df, ["city_location", "city", "location"])
industry_col = find_column(df, ["industry_vertical", "industry"])
sector_col = find_column(df, ["sector"])
amount_col = find_column(df, ["amount_in_usd", "amount", "investment_amount"])
investor_col = find_column(df, ["investors_name", "investors", "investor", "investor_name"])
meity_col = find_column(df, ["is_meity_recognized", "is_meity", "meity"])

# basic checks
if amount_col: df[amount_col] = clean_amount_series(df[amount_col])
if date_col: df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

# MeitY
if meity_col:
    df[meity_col] = df[meity_col].astype(str).str.strip().str.lower()
    df[meity_col] = df[meity_col].map({
        "yes": "Recognized","y": "Recognized","true": "Recognized","1": "Recognized",
        "no": "Not Recognized","n": "Not Recognized","false": "Not Recognized","0": "Not Recognized"
    }).fillna("Unknown")

df['year'] = df[date_col].dt.year if date_col in df.columns else np.nan
df[startup_col] = df[startup_col].astype(str).str.strip() if startup_col else df.index.astype(str)

# Sidebar
st.sidebar.header("Controls")
theme_choice = st.sidebar.radio("Theme", options=["Dark", "Light", "Toggle"], index=2)

if theme_choice == "Toggle":
    dark_mode = st.sidebar.checkbox("Enable Dark Mode", value=True)
else:
    dark_mode = (theme_choice == "Dark")

year_min = int(df['year'].min()) if df['year'].notna().any() else 2015
year_max = int(df['year'].max()) if df['year'].notna().any() else datetime.now().year
year_range = st.sidebar.slider("Year range", min_value=year_min, max_value=year_max, value=(year_min, year_max))

industry_list = sorted(df[industry_col].dropna().unique()) if industry_col in df.columns else []
sector_list = sorted(df[sector_col].dropna().unique()) if sector_col in df.columns else []
industry_sel = st.sidebar.multiselect("Industry Vertical", options=industry_list, default=industry_list[:6])
sector_sel = st.sidebar.multiselect("Sector", options=sector_list, default=sector_list[:6])

city_list = sorted(df[city_col].dropna().unique()) if city_col in df.columns else []
city_sel = st.sidebar.multiselect("City", options=city_list, default=city_list[:6])

meity_options = []
if meity_col and meity_col in df.columns:
    vals = df[meity_col].dropna().unique().tolist()
    meity_options = [v for v in ["Recognized", "Not Recognized"] if v in vals]

meity_sel = st.sidebar.multiselect("MeitY Recognition", options=meity_options, default=meity_options)
include_unknown = False
if meity_col and "Unknown" in df[meity_col].unique():
    include_unknown = st.sidebar.checkbox("Include Unknown MeitY values", value=False)

top_n = st.sidebar.slider("Top N (charts)", 5, 25, 10)

filtered = df.copy()
filtered = filtered[filtered['year'].between(year_range[0], year_range[1], inclusive='both')]

if industry_sel: filtered = filtered[filtered[industry_col].isin(industry_sel)]
if sector_sel: filtered = filtered[filtered[sector_col].isin(sector_sel)]
if city_sel: filtered = filtered[filtered[city_col].isin(city_sel)]

if meity_col and meity_sel:
    allowed = meity_sel + (["Unknown"] if include_unknown else [])
    filtered = filtered[filtered[meity_col].isin(allowed)]

if dark_mode:
    page_bg = "#0e1117"; text_color = "#f0f2f5"; plotly_template = "plotly_dark"
else:
    page_bg = "#ffffff"; text_color = "#0b0b0b"; plotly_template = "plotly_white"

st.markdown(f"""
<style>
.reportview-container .main {{ background-color: {page_bg}; color: {text_color}; }}
.stApp {{ background-color: {page_bg}; }}
</style>
""", unsafe_allow_html=True)

st.markdown("## Key metrics")
col1, col2, col3, col4 = st.columns(4)

total_funding = filtered[amount_col].sum() if amount_col in filtered.columns else 0
unique_startups = filtered[startup_col].nunique() if startup_col in filtered.columns else 0
avg_round = filtered[amount_col].mean() if amount_col in filtered.columns else 0

if meity_col and meity_col in filtered.columns:
    recognized_count = (filtered[meity_col] == "Recognized").sum()
    total_records = len(filtered)
    meity_pct = (recognized_count / total_records * 100) if total_records > 0 else 0.0
else:
    meity_pct = np.nan

col1.metric("💰 Total Funding", f"${total_funding:,.0f}")
col2.metric("🚀 Unique Startups", f"{unique_startups}")
col3.metric("💸 Avg Funding Round", f"${(avg_round or 0):,.0f}")
col4.metric("🏛 MeitY Recognized", f"{meity_pct:.1f}%" if not np.isnan(meity_pct) else "N/A")

if meity_col and meity_col in filtered.columns:
    st.subheader("MeitY Recognition Breakdown")
    meity_df = filtered[meity_col].value_counts().reset_index()
    meity_df.columns = ["Recognition", "Count"]
    fig_meity = px.pie(meity_df, names="Recognition", values="Count", hole=0.4, template=plotly_template)
    st.plotly_chart(fig_meity, use_container_width=True)

st.subheader("Smart Insights")
insights = generate_insights(filtered, amount_col, city_col, sector_col, date_col, investor_col)
for i, text in enumerate(insights, 1):
    st.write(f"{i}. {text}")

# Additional charts/maps/investor panels would continue here…
# (Same as you already pasted above — unchanged)
