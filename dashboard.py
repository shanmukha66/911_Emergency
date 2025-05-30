import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
import time
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
import json
import requests
import matplotlib.pyplot as plt
import altair as alt

# Function to read JSON data from a file
def read_json_data(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

# Function to process JSON data
def process_data(json_data):
    all_cases = []
    for category, cases in json_data.items():
        for case in cases:
            case['category'] = category
            all_cases.append(case)
    
    df = pd.DataFrame(all_cases)
    expected_columns = ['case_number', 'location', 'dispatch', 'situation', 'open_status', 'stack_rank', 'category']
    for col in expected_columns:
        if col not in df.columns:
            st.error(f"Missing expected column: {col}")
            return None
    return df

# Function to geocode locations
def geocode_locations(locations):
    geolocator = Nominatim(user_agent="emergency_app")
    coords = []
    for location in locations:
        try:
            loc = geolocator.geocode(location)
            if loc:
                coords.append((loc.latitude, loc.longitude))
            else:
                coords.append((None, None))
        except Exception as e:
            st.error(f"Error geocoding {location}: {e}")
            coords.append((None, None))
        time.sleep(1)  # To respect Nominatim's usage policy
    return coords

# Color mapping for categories
def get_color(category):
    color_map = {
        "wildlife": "green",
        "police": "blue",
        "water": "lightblue",
        "fire": "red"
    }
    return color_map.get(category, "gray")

# Function to send POST request
def send_post_request(data):
    url = "http://localhost:5000/webhook"
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, data=json.dumps(data), headers=headers)
        if response.status_code == 200:
            st.success("POST request successful!")
        else:
            st.error(f"POST request failed with status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred: {e}")

# Streamlit app
st.title("Emergency Call Insights")

# Path to the JSON file
json_file_path = "data.json"

# Initialize session state to store data
if 'data' not in st.session_state:
    st.session_state.data = {}

# Create placeholders for components
data_placeholder = st.empty()
insights_placeholder = st.empty()
map_placeholder = st.empty()

# Streamlit loop to check for file updates
while True:
    # Read the latest data
    new_data = read_json_data(json_file_path)

    # Check if the data has changed
    if new_data != st.session_state.data:
        st.session_state.data = new_data  # Update data if the file has changed
        
        # Send POST request with new data
        # send_post_request(new_data)

        # Process the updated data
        with st.spinner("Processing data..."):
            df = process_data(st.session_state.data)
            if df is None or df.empty:
                st.warning("No data available to display.")
                continue  # Skip the rest if there's no data

        # Update DataFrame
        with data_placeholder.container():
            st.subheader("Emergency Call Data")
            st.dataframe(df)

        # Update Insights
        with insights_placeholder.container():
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Open Status Distribution")
                open_status_counts = df['open_status'].value_counts()
                
                # Pie chart for open status
                fig, ax = plt.subplots()
                ax.pie(open_status_counts.values, labels=open_status_counts.index, autopct='%1.1f%%', startangle=90)
                ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
                st.pyplot(fig)

            with col2:
                st.subheader("Task Priority by Category")
                
                # Bar chart for stack rank by category
                chart = alt.Chart(df).mark_bar().encode(
                    x='category:N',
                    y='stack_rank:Q',
                    color='category:N',
                    tooltip=['category', 'stack_rank', 'situation']
                ).properties(
                    width=400,
                    height=300
                )
                
                st.altair_chart(chart, use_container_width=True)

            # Keep the existing category distribution chart
            category_counts = df['category'].value_counts()
            st.subheader("Emergency Category Distribution")
            st.bar_chart(category_counts)

        # Geocode locations
        with st.spinner("Geocoding locations..."):
            coords = geocode_locations(df['location'].tolist())
            df['latitude'] = [coord[0] for coord in coords]
            df['longitude'] = [coord[1] for coord in coords]

        # Prepare map data with colors
        map_data = df[['latitude', 'longitude', 'category', 'situation', 'case_number']].dropna()
        map_data['color'] = map_data['category'].apply(get_color)

        # Update Map
        with map_placeholder.container():
            st.subheader("Locations on Map")
            if not map_data.empty:
                with st.spinner("Generating map..."):
                    # Create a map centered around the mean location of all valid coordinates
                    m = folium.Map(location=[map_data['latitude'].mean(), map_data['longitude'].mean()], zoom_start=12)
                    marker_cluster = MarkerCluster().add_to(m)

                    # Add markers for each location
                    for _, row in map_data.iterrows():
                        folium.Marker(
                            location=(row['latitude'], row['longitude']),
                            popup=f"Case: {row['case_number']}\nCategory: {row['category']}\nSituation: {row['situation']}",
                            icon=folium.Icon(color=get_color(row['category']), icon='info-sign')
                        ).add_to(marker_cluster)

                    folium_static(m)
            else:
                st.write("No valid locations to display on the map.")

    # Wait for a while before checking for updates
    time.sleep(5)  # Adjust the sleep duration as needed
