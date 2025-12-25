import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

# Configuration Constants
ROOT_URL = 'https://navigator.innovation.ca'
SEARCH_BASE_URL = f'{ROOT_URL}/en/search?f%5B0%5D=province%3A2100&page='
TOTAL_SEARCH_PAGES = 44
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def get_soup(url):
    """Utility to fetch a URL and return a BeautifulSoup object."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return BeautifulSoup(response.content, 'html.parser')
        print(f"Warning: Failed to reach {url} (Status: {response.status_code})")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None

def discover_lab_urls(total_pages):
    """Phase 1: Scrapes search results to compile a list of individual lab URLs."""
    all_links = []
    for page_num in range(total_pages):
        page_url = f"{SEARCH_BASE_URL}{page_num}"
        soup = get_soup(page_url)
        
        if soup:
            for item in soup.find_all('div', class_='views-row'):
                link = item.find('a')
                if link and 'href' in link.attrs:
                    all_links.append(ROOT_URL + link['href'])
            print(f"Discovered links from page {page_num + 1} of {total_pages}")
        
        time.sleep(1)  # Polite delay between search pages
    return all_links

def extract_lab_details(lab_url):
    """Phase 2: Extracts specific data from an individual lab page."""
    soup = get_soup(lab_url)
    if not soup:
        return None

    # Basic Info
    lab_name = soup.find('title').get_text(strip=True) if soup.find('title') else "N/A"
    
    sectors_div = soup.find('div', class_='field--name-field-sectors-of-application')
    sectors = [li.get_text(strip=True) for li in sectors_div.find_all('li')] if sectors_div else []

    # Initialize data dictionary
    data = {
        'Lab Name': lab_name,
        'Sectors': ', '.join(sectors),
        'Location': 'N/A',
        'Institution': 'N/A'
    }

    # Navigate to Contact Page
    contact_btn = soup.find('a', string='Contact this facility')
    if contact_btn:
        contact_soup = get_soup(ROOT_URL + contact_btn['href'])
        if contact_soup:
            # Extract Institution
            inst_h2 = contact_soup.find('h2', string='Institution')
            if inst_h2:
                data['Institution'] = inst_h2.find_next('li').get_text(strip=True)

            # Extract Address
            addr_p = contact_soup.find('p', class_='address')
            if addr_p:
                parts = [addr_p.find('span', class_=c).get_text(strip=True) 
                         for c in ['address-line1', 'locality', 'administrative-area', 'postal-code', 'country']
                         if addr_p.find('span', class_=c)]
                data['Location'] = ", ".join(parts)

    # Fallback to Google Maps if no physical address found
    if data['Location'] == 'N/A':
        maps_link = soup.find('a', string='Google Maps')
        if maps_link:
            data['Location'] = maps_link['href']

    return data

def main():
    """Orchestrates the full scraping workflow."""
    # Discovery
    print("Starting link discovery...")
    lab_urls = discover_lab_urls(TOTAL_SEARCH_PAGES)
    discovery_file = os.path.join(DATA_DIR, 'lab_urls.csv')
    
    # Save discovery checkpoint
    pd.DataFrame(lab_urls, columns=['Lab URL']).to_csv(discovery_file, index=False)
    print(f"Discovery complete. {len(lab_urls)} labs found.")

    # Extraction
    lab_details = []
    for i, url in enumerate(lab_urls):
        print(f"[{i+1}/{len(lab_urls)}] Processing: {url}")
        details = extract_lab_details(url)
        if details:
            lab_details.append(details)
        
        time.sleep(2)  # Critical delay for ethical scraping

    # Save Final Results
    df = pd.DataFrame(lab_details)
    final_details_file = os.path.join(DATA_DIR, 'lab_details.csv')
    df.to_csv(final_details_file, index=False)
    print("Scraping completed successfully.")

if __name__ == "__main__":
    main()