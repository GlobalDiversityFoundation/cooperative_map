import streamlit as st
import pandas as pd
import folium
import numpy as np
from streamlit_folium import folium_static
import os

# Set page config
st.set_page_config(page_title="Partner Cooperatives Map - Prototype", layout="wide")

# Title
st.title("🌿 Partner Cooperatives Map - Prototype")

# Load data

def load_data():
    df = pd.read_excel("gdf_coops_data.xlsx", sheet_name="Data")
    df.columns = df.columns.str.strip()  # remove extra spaces from column names

    # Convert coordinates to numeric (force errors to NaN)
    df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
    df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")

    # Drop rows with missing or invalid coordinates
    df = df.dropna(subset=["Latitude", "Longitude"])

    return df
    
df = load_data()

def jitter_duplicates(df, lat_col="Latitude", lon_col="Longitude", jitter_amount=0.01):
    seen = {}
    new_lats = []
    new_lons = []

    for i, row in df.iterrows():
        coord = (row[lat_col], row[lon_col])
        if coord in seen:
            count = seen[coord]
            angle = np.random.uniform(0, 2 * np.pi)
            offset_lat = np.cos(angle) * jitter_amount * count
            offset_lon = np.sin(angle) * jitter_amount * count
            new_lats.append(coord[0] + offset_lat)
            new_lons.append(coord[1] + offset_lon)
            seen[coord] += 1
        else:
            new_lats.append(coord[0])
            new_lons.append(coord[1])
            seen[coord] = 1

    df[lat_col + "_jittered"] = new_lats
    df[lon_col + "_jittered"] = new_lons
    return df

def get_social_label(url):
    if pd.isna(url):
        return ""
    if "instagram.com" in url:
        return f"[Instagram]({url})"
    elif "facebook.com" in url:
        return f"[Facebook]({url})"
    else:
        return f"[Link]({url})"

# Sidebar filters
st.sidebar.header("🔍 Filter Cooperatives")
hubs = st.sidebar.multiselect("Filter by Hub", sorted(df["Hub"].dropna().unique()), default=None)
specialties = st.sidebar.multiselect("Filter by Specialty", sorted(df["Specialty"].dropna().unique()), default=None)

# Apply filters

filtered_df = df.copy()
filtered_df = jitter_duplicates(filtered_df)

if hubs:
    filtered_df = filtered_df[filtered_df["Hub"].isin(hubs)]
if specialties:
    filtered_df = filtered_df[filtered_df["Specialty"].isin(specialties)]

# Display filtered table

filtered_df["Social Media Link"] = filtered_df["Social Media"].apply(get_social_label)

st.dataframe(filtered_df[["Cooperative Name", "Hub", "Specialty", "Social Media Link"]], hide_index=True)

# Map
st.subheader("🗺️ Interactive Map")

if filtered_df.empty:
    st.warning("No cooperatives match the selected filters.")
else:
    # Center the map
    m = folium.Map(location=[filtered_df["Latitude"].mean(), filtered_df["Longitude"].mean()], zoom_start=7)

    # Create marker
    for _, row in filtered_df.iterrows():
        popup_content = f"<b>{row['Cooperative Name']}</b><br>"
        if pd.notna(row["Specialty"]):
            popup_content += f"Specializing in {row['Specialty']}<br>"
        if pd.notna(row["Social Media"]):
            popup_content += f"<a href='{row['Social Media']}' target='_blank'>Social Media</a>"

        folium.Marker(
            location=[row["Latitude_jittered"], row["Longitude_jittered"]],
            popup=folium.Popup(popup_content, max_width=300),
            icon=folium.Icon(color="blue", icon="users", prefix="fa")
        ).add_to(m)

    col1, col2, col3 = st.columns([0.5, 5, 2])  # adjust widths if needed
    with col2:
        folium_static(m)
