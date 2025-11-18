# app.py — Updated to use new merged dataset

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
from datetime import datetime

# ---------- Config ----------
st.set_page_config(page_title="India Startup Intelligence", layout="wide", page_icon="📈")

# Updated final merged dataset path 👇
DATA_FILE = "/content/drive/MyDrive/final_indian_startup_funding.csv"

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
    s = s.astype(str).str.replace(r'[\$,₹]', '', regex=True)
    s = s.replace(['undisclosed', 'nan', 'none', 'None', ''], np.nan)
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
    if pd.isna(city):
        return (np.nan, np.nan)
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

uploaded = st.file_uploader("Upload merged CSV (optional)", type=["csv"])
df = load_dataframe(uploaded)

if df is None:
    st.warning("⚠ No data loaded. Upload file or check path.")
    st.stop()

# --- everything below this remains unchanged (filters, KPIs, charts, map etc.) ---
# ✔ Column detection
# ✔ Filtering
# ✔ KPIs
# ✔ Charts & Insights
# ✔ Download feature
# ✔ Theme toggle
# ✔ MeitY handling
# ✔ Map & city funding
# ✔ Investor explorer

# ⛔ No changes required — your old code continues normally below ⛔
