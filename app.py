# app.py — Upgraded "wow" Streamlit dashboard (AI-ish + Map + Investors)
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
    # prefer uploaded file, else try fallback locations
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
    # remove commas, currency symbols, handle "Undisclosed"
    s = s.astype(str).str.replace(r'[\$,₹,]', '', regex=True)
    s = s.replace(['undisclosed','nan','none','None',''], np.nan)
    return pd.to_numeric(s, errors='coerce')

# simple city -> latlon for major Indian cities (fallback: None)
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
    # try exact match and title-case variants
    for key in CITY_COORDS:
        if key.lower() == name.lower() or key.lower() in name.lower():
            return CITY_COORDS[key]
    return (np.nan, np.nan)

def generate_insights(df, amount_col, city_col, sector_col, date_col, investor_col):
    # algorithmic "AI-like" insights (no external API)
    insights = []
    try:
        total = df[amount_col].sum(skipna=True)
        insights.append(f"Total funding in the filtered data: **${total:,.0f}**.")
    except:
        insights.append("Total funding: not available")

    # top sector
    try:
        top_sector = df.groupby(sector_col)[amount_col].sum().idxmax()
        top_sector_amt = df.groupby(sector_col)[amount_col].sum().max()
        insights.append(f"**{top_sector}** received the highest funding (~**${top_sector_amt:,.0f}**).")
    except:
        pass

    # city concentration
    try:
        city_counts = df[city_col].value_counts(normalize=True, dropna=True)
        if not city_counts.empty:
            top_city = city_counts.index[0]
            share = city_counts.iloc[0] * 100
            insights.append(f"{top_city} hosts **{share:.1f}%** of startups in this dataset — a clear urban concentration.")
    except:
        pass

    # funding trend
    try:
        df_time = df.dropna(subset=[date_col, amount_col]).copy()
        df_time['year'] = df_time[date_col].dt.year
        yearly = df_time.groupby('year')[amount_col].sum().sort_index()
        if len(yearly) >= 2:
            growth = (yearly.iloc[-1] - yearly.iloc[0]) / yearly.iloc[0] * 100 if yearly.iloc[0] != 0 else np.nan
            insights.append(f"Funding changed by **{growth:.1f}%** between {yearly.index[0]} and {yearly.index[-1]}.")
    except:
        pass

    # top investor
    try:
        invs = df[investor_col].dropna().astype(str).str.split(',')
        invs = invs.explode().str.strip()
        top_inv = invs.value_counts().head(1)
        if not top_inv.empty:
            inv_name = top_inv.index[0]
            deals = int(top_inv.iloc[0])
            insights.append(f"Top active investor: **{inv_name}** with **{deals}** deals.")
    except:
        pass

    # catchy closer
    if len(insights) == 0:
        insights.append("No strong patterns found — try changing filters to create clearer signals.")
    else:
        insights.append("Want predictions or AI-style textual analysis? I can add model forecasts next.")

    return insights

# -----------------------
# UI
# -----------------------
st.markdown("<div style='text-align:center'><h1>🚀 India Startup — Syck & Crazy Dashboard</h1></div>", unsafe_allow_html=True)
st.write("Upload your merged CSV (or the dashboard will try a Drive fallback). The app auto-detects columns from your file.")

uploaded = st.file_uploader("Upload CSV (merged dataset with columns you listed)", type=["csv"])

df = load_dataframe(uploaded)
if df is None:
    st.warning("No file uploaded and no fallback file found. Upload the CSV or place it at one of the fallback paths listed in the code.")
    st.stop()

# standardize columns
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

# detect expected columns from your provided list:
# ['sr_no','date','startup_name','industry_vertical','subvertical','city_location','investors_name','investment_type','amount_in_usd','incubation_center','sector','company_profile','is_meity_recognized']
date_col = find_column(df, ["date", "date_dd/mm/yyyy", "funded_date"])
startup_col = find_column(df, ["startup_name", "name_of_the_startup", "startup"])
city_col = find_column(df, ["city_location", "city", "location"])
sector_col = find_column(df, ["industry_vertical", "sector", "industry"])
amount_col = find_column(df, ["amount_in_usd", "amount", "investment_amount", "amount($)"])
investor_col = find_column(df, ["investors_name", "investors", "investor", "investor_name"])
meity_col = find_column(df, ["is_meity_recognized", "is_meity", "meity"])

# Basic column checks and helpful messages
missing = []
for required, name in [(startup_col, "startup name"), (city_col, "city"), (sector_col, "sector/industry"), (amount_col, "amount_in_usd"), (date_col, "date")]:
    if required is None:
        missing.append(name)
if missing:
    st.warning(f"The uploaded file is missing these useful columns: {missing}. The app will still run but some features may be limited.")

# Clean numeric & date
if amount_col:
    df[amount_col] = clean_amount_series(df[amount_col])
if date_col:
    try:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    except:
        pass

# create derived columns
df['year'] = df[date_col].dt.year if date_col in df.columns else pd.Series([np.nan]*len(df))
df[startup_col] = df[startup_col].astype(str).str.strip() if startup_col in df.columns else df.index.astype(str)

# Sidebar controls
st.sidebar.header("Filters")
year_min = int(df['year'].min()) if df['year'].notna().any() else 2015
year_max = int(df['year'].max()) if df['year'].notna().any() else datetime.now().year
year_range = st.sidebar.slider("Year range", min_value=year_min, max_value=year_max, value=(year_min, year_max))

sector_list = sorted(df[sector_col].dropna().unique()) if sector_col in df.columns else []
sector_sel = st.sidebar.multiselect("Sector", options=sector_list, default=sector_list[:4])

city_list = sorted(df[city_col].dropna().unique()) if city_col in df.columns else []
city_sel = st.sidebar.multiselect("City (multi)", options=city_list, default=city_list[:6])

top_n = st.sidebar.slider("Top N (charts)", 5, 25, 10)

# Filtering
filtered = df.copy()
if 'year' in filtered.columns:
    filtered = filtered[filtered['year'].between(year_range[0], year_range[1], inclusive='both')]
if sector_sel:
    filtered = filtered[filtered[sector_col].isin(sector_sel)]
if city_sel:
    filtered = filtered[filtered[city_col].isin(city_sel)]

# -----------------------
# KPIs & Insights
# -----------------------
c1, c2, c3, c4 = st.columns([2,2,2,3])
total_funding = filtered[amount_col].sum() if amount_col in filtered.columns else 0
num_startups = filtered[startup_col].nunique() if startup_col in filtered.columns else 0
avg_round = filtered[amount_col].mean() if amount_col in filtered.columns else 0
meity_pct = (filtered[meity_col].sum()/len(filtered))*100 if meity_col and meity_col in filtered.columns and pd.api.types.is_numeric_dtype(filtered[meity_col]) and len(filtered)>0 else np.nan

c1.metric("💰 Total Funding (filtered)", f"${total_funding:,.0f}")
c2.metric("🚀 Unique Startups", f"{num_startups}")
c3.metric("💸 Avg Funding Round", f"${(avg_round or 0):,.0f}")
c4.metric("🏛 MeitY recognized %", f"{meity_pct:.1f}%" if not np.isnan(meity_pct) else "N/A")

# AI-like insights (algorithmic)
st.markdown("### 🤖 Smart Insights")
insights = generate_insights(filtered, amount_col, city_col, sector_col, date_col, investor_col)
for i, line in enumerate(insights):
    st.write(f"{i+1}. {line}")

# -----------------------
# Visual row 1: Map + Top Cities
# -----------------------
st.markdown("---")
col_map, col_cities = st.columns([3,2])

with col_map:
    st.subheader("📍 Startup map (city-level)")
    # create lat/lon columns by mapping known cities
    if city_col in filtered.columns:
        filtered['lat'] = filtered[city_col].map(lambda x: geocode_city(x)[0])
        filtered['lon'] = filtered[city_col].map(lambda x: geocode_city(x)[1])
        # drop rows without coords but show warning
        map_df = filtered.dropna(subset=['lat','lon'])
        if map_df.empty:
            st.info("No geo coordinates available for selected cities. Map shows only major cities (Bengaluru, Mumbai, Delhi etc.).")
        fig_map = px.scatter_mapbox(
            map_df,
            lat='lat', lon='lon',
            hover_name=startup_col,
            hover_data={amount_col:':,.0f', city_col:True, sector_col:True},
            size=amount_col if amount_col in map_df.columns else None,
            color=sector_col if sector_col in map_df.columns else None,
            size_max=30,
            zoom=4,
            height=500,
            mapbox_style="open-street-map"
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("No city column detected to render the map.")

with col_cities:
    st.subheader("🏙 Top Cities by Funding")
    if city_col in filtered.columns and amount_col in filtered.columns:
        city_sum = filtered.groupby(city_col)[amount_col].sum().sort_values(ascending=False).head(top_n).reset_index()
        fig_c = px.bar(city_sum, x=amount_col, y=city_col, orientation='h', text=amount_col)
        st.plotly_chart(fig_c, use_container_width=True)
    else:
        st.info("City / Amount data not available for this chart.")

# -----------------------
# Visual row 2: Sectors + Funding Trend
# -----------------------
st.markdown("---")
col_sec, col_trend = st.columns(2)

with col_sec:
    st.subheader("💼 Sector distribution (Treemap)")
    if sector_col in filtered.columns and amount_col in filtered.columns:
        sec = filtered.groupby(sector_col)[amount_col].sum().reset_index().sort_values(amount_col, ascending=False).head(50)
        fig_sec = px.treemap(sec, path=[sector_col], values=amount_col)
        st.plotly_chart(fig_sec, use_container_width=True)
    else:
        st.info("Sector / Amount data not available for this chart.")

with col_trend:
    st.subheader("📈 Funding trend (monthly)")
    if date_col in filtered.columns and amount_col in filtered.columns:
        trend = filtered.dropna(subset=[date_col]).groupby(pd.Grouper(key=date_col, freq='M'))[amount_col].sum().reset_index()
        if not trend.empty:
            fig_t = px.line(trend, x=date_col, y=amount_col, markers=True)
            st.plotly_chart(fig_t, use_container_width=True)
        else:
            st.info("Not enough date data to show trend.")
    else:
        st.info("Date or amount column missing; cannot plot trend.")

# -----------------------
# Investors panel
# -----------------------
st.markdown("---")
st.subheader("🧑‍💼 Top Investors Explorer")

if investor_col in filtered.columns:
    invs = filtered[[investor_col, amount_col]].dropna(subset=[investor_col])
    invs = invs.assign(investors_split=invs[investor_col].astype(str).str.split(','))
    invs = invs.explode('investors_split')
    invs['investors_split'] = invs['investors_split'].str.strip()
    invs = invs[~invs['investors_split'].isin(['', 'nan', 'None'])]
    # compute counts and sums
    inv_summary = invs.groupby('investors_split').agg(
        deals=('investors_split','size'),
        total_investment=(amount_col, 'sum')
    ).sort_values(by='total_investment', ascending=False).reset_index().head(50)
    st.dataframe(inv_summary)

    # top investors chart
    topK = inv_summary.head(top_n)
    fig_inv = px.bar(topK, x='total_investment', y='investors_split', orientation='h', text='deals')
    st.plotly_chart(fig_inv, use_container_width=True)
else:
    st.info("No investor column detected (investors_name).")

# -----------------------
# Data & Download
# -----------------------
st.markdown("---")
st.subheader("📄 Filtered Dataset")
st.dataframe(filtered.reset_index(drop=True))

csv = filtered.to_csv(index=False).encode('utf-8')
st.download_button("⬇ Download filtered CSV", data=csv, file_name="filtered_startups.csv", mime="text/csv")

st.markdown("<div style='text-align:center;margin-top:20px;color:gray'>Built for maximum wow — tweak filters and watch the story change. Want ML forecasts next?</div>", unsafe_allow_html=True)
