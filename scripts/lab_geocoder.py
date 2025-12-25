import pandas as pd
import requests
import time
import simplekml
import folium
import os
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

# Configuration Constants
INPUT_FILE = "ontario_lab_details_final.csv"
OUTPUT_CSV = "ON_labs_geocoded.csv"
OUTPUT_KML = "ON_labs_geocoded.kml"
OUTPUT_HTML_MAP = "ON_labs_map.html"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

INPUT_FILE = os.path.join(DATA_DIR, "lab_details.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "ON_labs_geocoded.csv")
OUTPUT_KML = os.path.join(DATA_DIR, "ON_labs_geocoded.kml")
OUTPUT_HTML_MAP = os.path.join(DATA_DIR, "ON_labs_map.html")

def geocode_address(address, api_key):
    """
    Fetches coordinates for a single address using the Google Geocoding API.
    Includes a check to skip URLs passed as addresses.
    """
    # BUG FIX: If 'address' is actually a Google Maps URL from the scraper fallback, 
    # the Geocoding API will fail. We should return None immediately.
    if not address or "http" in str(address):
        return None, None

    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": api_key
    }
    try:
        # Increased timeout for slower network connections
        response = requests.get(base_url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK':
                location = data['results'][0]['geometry']['location']
                return float(location['lat']), float(location['lng'])
            else:
                # Provides specific Google API error status
                print(f"API Warning: {data.get('status')} for address: {address}")
        else:
            print(f"HTTP Error: Status code {response.status_code} for address: {address}")
    except Exception as e:
        print(f"Connection error geocoding {address}: {e}")
    
    return None, None

def process_geocoding(df, api_key):
    """
    Iterates through a DataFrame to geocode addresses.
    """
    latitudes = []
    longitudes = []
    
    # Check if 'Location' column exists
    if 'Location' not in df.columns:
        print("Error: 'Location' column missing from input file.")
        return df

    for i, address in enumerate(df['Location']):
        print(f"[{i+1}/{len(df)}] Geocoding: {address}")
        lat, lng = geocode_address(address, api_key)
        latitudes.append(lat)
        longitudes.append(lng)
        
        # Respect rate limits
        time.sleep(1) 
        
    df['Latitude'] = latitudes
    df['Longitude'] = longitudes
    return df

def create_kml(df, output_path):
    """
    Converts a geocoded DataFrame into a KML file.
    """
    kml = simplekml.Kml()
    # Filter only valid coordinates
    valid_points = df.dropna(subset=['Latitude', 'Longitude'])
    
    for _, row in valid_points.iterrows():
        pnt = kml.newpoint(name=row['Lab Name'], coords=[(row['Longitude'], row['Latitude'])])
        pnt.description = f"Institution: {row.get('Institution', 'N/A')}\nSectors: {row.get('Sectors', 'N/A')}"
    
    kml.save(output_path)
    print(f"KML file saved to: {output_path}")

def create_folium_map(df, output_path):
    """
    Generates an interactive HTML map.
    """
    map_df = df.dropna(subset=['Latitude', 'Longitude'])
    
    if map_df.empty:
        print("No valid coordinates found to map.")
        return

    # Center the map on Ontario
    m = folium.Map(location=[45.0, -79.0], zoom_start=6)

    for _, row in map_df.iterrows():
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=f"<b>{row['Lab Name']}</b><br>{row['Institution']}",
            tooltip=row['Lab Name']
        ).add_to(m)

    m.save(output_path)
    print(f"Interactive map saved to: {output_path}")

def main():
    """
    Main workflow.
    """
    if not GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY not found in environment. Check your .env file.")
        return

    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found. Please run the scraper first.")
        return

    # Load Data
    df = pd.read_csv(INPUT_FILE)
    
    # Run Geocoding
    print("Starting geocoding process...")
    geocoded_df = process_geocoding(df, GOOGLE_API_KEY)
    
    # Save CSV result
    geocoded_df.to_csv(OUTPUT_CSV, index=False)
    print(f"Geocoded data saved to: {OUTPUT_CSV}")

    # Generate spatial files
    create_kml(geocoded_df, OUTPUT_KML)
    create_folium_map(geocoded_df, OUTPUT_HTML_MAP)

    print("All tasks completed successfully.")

if __name__ == "__main__":
    main()