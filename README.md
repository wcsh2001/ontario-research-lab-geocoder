# Ontario Research Facilities Scraper and Geocoder

This project scrapes public data on Ontario research facilities from the CFI Research Facilities Navigator, geocodes the resulting addresses using the Google Geocoding API, and generates visualizations (charts and maps) to explore the provincial research landscape.

## Features

- Scrapes all research facility profile URLs for Ontario from the CFI Navigator search interface.
- Extracts key details for each facility, including lab name, sectors of application, institution, and location.
- Cleans and stores the scraped records as a structured CSV in a `data/` directory.
- Geocodes facility addresses to latitude/longitude using the Google Geocoding API, with handling for invalid URL-only locations.
- Exports geocoded facilities as:
  - CSV for further analysis.
  - KML for use in GIS or Google Earth.
  - Interactive HTML map built with Folium.
- Provides an analysis notebook to explore spatial patterns, top institutions, and sectoral distribution across Ontario.

## Project Structure

- `lab_scraper.py`  
  - Discovers all Ontario facility URLs via the Navigator search pages (`province=2100`, 44 pages total by Dec 2025).
  - For each facility page, extracts:
    - `Lab Name` (from the page title).
    - `Sectors` of application (from the sectors field on the profile).
    - `Institution` (from the contact page under the Institution section).
    - `Location` (full mailing address composed of address line, city, province, postal code, and country).
  - Falls back to a Google Maps link if no structured address is present.
  - Saves:
    - `lab_urls.csv` – list of all discovered facility URLs.
    - `lab_details.csv` – tabular facility data.

- `lab_geocoder.py`  
  - Loads `lab_details.csv` as the input dataset.  
  - Uses `GOOGLE_API_KEY` from a `.env` file (via `python-dotenv`) to call the Google Geocoding API.
  - Skips geocoding for missing locations or those stored only as URLs (e.g., a raw Google Maps link), returning `None` coordinates for those records.
  - Adds `Latitude` and `Longitude` columns to the dataset and writes:
    - `ON_labs_geocoded.csv` – geocoded facility table.
    - `ON_labs_geocoded.kml` – point layer for mapping tools.
    - `ON_labs_map.html` – interactive Leaflet/Folium web map centered on Ontario.

- `ontario_labs_overview.ipynb`  
  - Loads the geocoded data and performs exploratory analysis of the Ontario research facility landscape.
  - Includes examples such as:
    - Viewing the first rows of facilities with lab name, sectors, institution, city, and coordinates.
    - Investigating the distribution of facilities across regions and institutions.
    - Producing charts and maps to visualize spatial and sectoral patterns.

## Requirements

See `requirement.txt`.

## Usage

1. **Set up environment**

   - Create and activate a virtual environment.
   - Install dependencies (example):

     ```
     pip install -r requirements.txt
     ```

   - Add your Google Geocoding API key to `.env`.

2. **Run the scraper**
    ```
    python lab_scraper.py
    ```

- This:
  - Crawls all Ontario facility result pages (by default 44 pages).
  - Writes discovered facility URLs to `lab_urls.csv`.
  - Writes scraped facility attributes to `lab_details.csv`.

3. **Run the geocoder and map generator**
    ```
    python lab_geocoder.py
    ```

- This:
  - Loads `lab_details.csv`.
  - Calls the Google Geocoding API for each non-URL address in the `Location` column.
  - Writes:
    - `ON_labs_geocoded.csv` with new `Latitude` and `Longitude` columns.
    - `ON_labs_geocoded.kml` for GIS/Google Earth.
    - `ON_labs_map.html` as an interactive map of Ontario facilities.

4. **Explore the data and visualizations**

- Open `ontario_labs_overview.ipynb` in Jupyter Lab/Notebook:

  ```
  jupyter notebook ontario_labs_overview.ipynb
  ```

- Use the notebook to:
  - Inspect sample records.
  - Analyze counts by city, institution, or sector.
  - Create charts and maps to understand the distribution of Ontario research facilities.

## Notes and Limitations

- The scraper targets the public CFI Navigator site for Ontario (`province=2100`) and assumes the HTML structure used by facility profile and contact pages; changes to the site may require updates to the parsing logic.
- Polite delays (`time.sleep`) are added between requests to reduce load on the Navigator servers and adhere to ethical scraping practices.
- Some facilities may lack a structured mailing address and may only provide a Google Maps link; these are explicitly skipped by the geocoder and will not appear on spatial outputs.
- The analysis notebook currently focuses on descriptive statistics and spatial distribution; additional modeling or dashboards can be layered on top of the geocoded CSV.





