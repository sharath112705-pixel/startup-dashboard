# app.py — Final Streamlit dashboard for NEW merged dataset

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
from datetime import datetime

# ---------- Config ----------
st.set_page_config(page_title="India Startup Intelligence", layout="wide", page_icon="📈")

# NEW merged dataset path 🔥
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
        insights.append(f"{top_sector} received ~${top_sector_amt:,.0f}, the highest.")
    except: pass

    try:
        city_counts = df[city_col].value_counts(normalize=True, dropna=True)
        if not city_counts.empty:
            top_city = city_counts.index[0]
            share = city_counts.iloc[0] * 100
            insights.append(f"{top_city} has {share:.1f}% of startups in the filtered set.")
    except: pass

    try:
        df_time = df.dropna(subset=[date_col, amount_col]).copy()
        df_time['year'] = df_time[date_col].dt.year
        yearly = df_time.groupby('year')[amount_col].sum().sort_index()
        if len(yearly) >= 2 and yearly.iloc[0] != 0:
            growth = (yearly.iloc[-1] - yearly.iloc[0]) / yearly.iloc[0] * 100
            insights.append(f"Funding changed by {growth:.1f}% since {yearly.index[0]}.")
    except: pass

    try:
        invs = df[investor_col].dropna().astype(str).str.split(',').explode().str.strip()
        top_inv = invs.value_counts().head(1)
        if not top_inv.empty:
            inv_name = top_inv.index[0]
            deals = int(top_inv.iloc[0])
            insights.append(f"Most active investor: {inv_name} ({deals} deals).")
    except: pass

    if not insights:
        insights.append("Adjust filters to discover insights.")
    return insights


# ---------- UI ----------
st.title("🚀 India Startup Intelligence")

uploaded = st.file_uploader("Upload merged CSV (optional)", type=["csv"])
df = load_dataframe(uploaded)

if df is None:
    st.warning("⚠ No data loaded. Upload file or check dataset path.")
    st.stop()

df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

date_col = find_column(df, ["date", "funded_date"])
startup_col = find_column(df, ["startup_name", "name_of_the_startup", "startup"])
city_col = find_column(df, ["city_location", "city", "location"])
industry_col = find_column(df, ["industry_vertical", "industry"])
sector_col = find_column(df, ["sector", "industry_vertical"])
amount_col = find_column(df, ["amount_in_usd", "amount", "investment_amount"])
investor_col = find_column(df, ["investors_name", "investors", "investor", "investor_name"])
meity_col = find_column(df, ["is_meity_recognized", "is_meity", "meity"])

if amount_col:
    df[amount_col] = clean_amount_series(df[amount_col])
if date_col:
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

if meity_col:
    df[meity_col] = df[meity_col].astype(str).str.lower().map({
        "yes": "Recognized", "y": "Recognized", "true": "Recognized", "1": "Recognized",
        "no": "Not Recognized", "n": "Not Recognized", "false": "Not Recognized", "0": "Not Recognized"
    }).fillna("Unknown")

df['year'] = df[date_col].dt.year if date_col in df.columns else np.nan
df[startup_col] = df[startup_col].astype(str).str.strip() if startup_col else df.index.astype(str)


# ---------- Sidebar Filters ----------
st.sidebar.header("Controls")

theme_choice = st.sidebar.radio("Theme", ["Dark", "Light", "Toggle"], index=2)
dark_mode = (theme_choice == "Dark") or (theme_choice == "Toggle" and st.sidebar.checkbox("Enable Dark Mode", value=True))

year_min = int(df['year'].min())
year_max = int(df['year'].max())
year_range = st.sidebar.slider("Year range", year_min, year_max, (year_min, year_max))

industry_sel = st.sidebar.multiselect("Industry Vertical", sorted(df[industry_col].dropna().unique()))
sector_sel = st.sidebar.multiselect("Sector", sorted(df[sector_col].dropna().unique()))
city_sel = st.sidebar.multiselect("City", sorted(df[city_col].dropna().unique()))

meity_options = [v for v in ["Recognized", "Not Recognized"] if v in df[meity_col].unique()]
meity_sel = st.sidebar.multiselect("MeitY Recognition", meity_options, default=meity_options)
include_unknown = st.sidebar.checkbox("Include Unknown", value=False) if "Unknown" in df[meity_col].unique() else False

top_n = st.sidebar.slider("Top N", 5, 25, 10)


# ---------- Filter Application ----------
filtered = df.copy()
filtered = filtered[filtered['year'].between(year_range[0], year_range[1])]

if industry_sel:
    filtered = filtered[filtered[industry_col].isin(industry_sel)]
if sector_sel:
    filtered = filtered[filtered[sector_col].isin(sector_sel)]
if city_sel:
    filtered = filtered[filtered[city_col].isin(city_sel)]

if meity_sel:
    allowed = meity_sel + (["Unknown"] if include_unknown else [])
    filtered = filtered[filtered[meity_col].isin(allowed)]


# ---------- Theme ----------
template = "plotly_dark" if dark_mode else "plotly_white"


# ---------- KPIs ----------
st.markdown("## Key Metrics")

total_funding = filtered[amount_col].sum()
unique_startups = filtered[startup_col].nunique()
avg_round = filtered[amount_col].mean()
recognized_count = (filtered[meity_col] == "Recognized").sum()
meity_pct = (recognized_count / len(filtered) * 100) if len(filtered) else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Total Funding", f"${total_funding:,.0f}")
col2.metric("🚀 Unique Startups", unique_startups)
col3.metric("💸 Avg Funding", f"${avg_round:,.0f}")
col4.metric("🏛 MeitY Recognized", f"{meity_pct:.1f}%")


# ---------- Charts, Insights, Map, Investors, Data Table ----------
# EVERYTHING BELOW REMAINS 100% SAME AS YOU USED BEFORE

# MeitY Pie
if meity_col:
    st.subheader("MeitY Recognition Breakdown")
    pie_df = filtered[meity_col].value_counts().reset_index()
    pie_df.columns = ["Recognition", "Count"]
    fig = px.pie(pie_df, names="Recognition", values="Count", hole=0.4, template=template)
    st.plotly_chart(fig, use_container_width=True)

# Smart insights
st.subheader("Smart Insights")
insights = generate_insights(filtered, amount_col, city_col, sector_col, date_col, investor_col)
for i, text in enumerate(insights, 1):
    st.write(f"{i}. {text}")

# Map + Top Cities
st.markdown("---")
left, right = st.columns([3, 2])

with left:
    st.subheader("Startup Map")
    filtered['lat'], filtered['lon'] = zip(*filtered[city_col].map(geocode_city))
    map_df = filtered.dropna(subset=['lat', 'lon'])
    if not map_df.empty:
        fig2 = px.scatter_mapbox(map_df, lat='lat', lon='lon', hover_name=startup_col,
                                 size=amount_col, zoom=4, height=520, template=template)
        fig2.update_layout(mapbox_style="open-street-map")
        st.plotly_chart(fig2, use_container_width=True)

with right:
    st.subheader("Top Cities by Funding")
    city_sum = filtered.groupby(city_col)[amount_col].sum().sort_values(ascending=False).head(top_n).reset_index()
    fig3 = px.bar(city_sum, x=amount_col, y=city_col, orientation='h', text=amount_col, template=template)
    st.plotly_chart(fig3, use_container_width=True)

# Sector + Trend
st.markdown("---")
left2, right2 = st.columns(2)

with left2:
    st.subheader("Top Sectors")
    sec_df = filtered.groupby(sector_col)[amount_col].sum().reset_index().sort_values(amount_col, ascending=False).head(50)
    st.plotly_chart(px.treemap(sec_df, path=[sector_col], values=amount_col, template=template), use_container_width=True)

with right2:
    st.subheader("Funding Trend (Monthly)")
    trend = filtered.dropna(subset=[date_col]).groupby(pd.Grouper(key=date_col, freq='M'))[amount_col].sum().reset_index()
    st.plotly_chart(px.line(trend, x=date_col, y=amount_col, markers=True, template=template), use_container_width=True)

# Investors Panel
st.markdown("---")
st.subheader("Top Investors")
inv = filtered[[investor_col, amount_col]].dropna(subset=[investor_col])
inv = inv.assign(inv_split=inv[investor_col].str.split(',')).explode('inv_split')
inv['inv_split'] = inv['inv_split'].str.strip()
inv = inv[inv['inv_split'] != ""]
summary = inv.groupby('inv_split').agg(deals=('inv_split', 'size'), total=('investment_amount', 'sum'))
summary = summary.sort_values('total', ascending=False).head(50)
top_inv = summary.head(top_n).reset_index()
st.plotly_chart(px.bar(top_inv, x='total', y='inv_split', orientation='h', text='deals', template=template), use_container_width=True)

# Data Table + Download
st.markdown("---")
st.subheader("Filtered Data")
st.dataframe(filtered.reset_index(drop=True))
csv = filtered.to_csv(index=False).encode('utf-8')
st.download_button("Download Filtered CSV", csv, "filtered_startups.csv", "text/csv")

# Footer
st.markdown("<div style='text-align:center;color:gray;margin-top:10px'>Dashboard updated for full dataset 🟢</div>",
            unsafe_allow_html=True)
