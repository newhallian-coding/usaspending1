import requests
import pandas as pd
from pathlib import Path
import time

# Base URL for USAspending transaction search
BASE_URL = "https://api.usaspending.gov/api/v2/search/spending_by_transaction/"

DEFENSE_NAICS = [
    # Aerospace & vehicles
    "336411",  # Aircraft Manufacturing
    "336412",  # Aircraft Engine & Engine Parts
    "336413",  # Other Aircraft Parts
    "336414",  # Guided Missile & Space Vehicle Manufacturing
    "336415",  # Space Vehicle Propulsion
    "336419",  # Other Guided Missile / Space Manufacturing

    # Weapons & ordnance
    "332992",  # Small Arms Manufacturing
    "332993",  # Ammunition Manufacturing
    "332994",  # Small Arms, Ordnance, Accessories
    "332995",  # Other Ordnance & Accessories

    # Electronics & sensors
    "334511",  # Search, Detection, Navigation, Guidance
    "334512",  # Automatic Environmental Controls
    "334515",  # Instrument Manufacturing
    "334419",  # Other Electronic Component Manufacturing

    # Vehicles & shipbuilding
    "336992",  # Military Armored Vehicle Manufacturing
    "336611",  # Ship Building and Repairing (Naval)

    # Precision & machining
    "332710",  # Machine Shops
    "332721",  # Precision Turned Products
]

# Directory to save Parquet files
OUTPUT_DIR = Path("usa_spending_defense")
OUTPUT_DIR.mkdir(exist_ok=True)

# [\'Action Date\', \'Action Type\', \'Award ID\', \'Award Type\', \'Awarding Agency\', \'awarding_agency_id\', \'awarding_agency_slug\', \'Awarding Sub Agency\', \'cfda_number\', \'cfda_title\', \'def_codes\', \'Funding Agency\', \'funding_agency_slug\', \'Funding Sub Agency\', \'generated_internal_id\', \'internal_id\', \'Issued Date\', \'Last Date to Order\', \'Loan Value\', \'Mod\', \'naics_code\', \'naics_description\', \'pop_city_name\', \'pop_country_name\', \'pop_state_code\', \'product_or_service_code\', \'product_or_service_description\', \'recipient_id\', \'recipient_location_address_line1\', \'recipient_location_address_line2\', \'recipient_location_address_line3\', \'recipient_location_city_name\', \'recipient_location_country_name\', \'recipient_location_state_code\', \'Recipient Name\', \'Recipient UEI\', \'Subsidy Cost\', \'Transaction Amount\', \'Transaction Description\', \'Assistance Listing\', \'NAICS\', \'Primary Place of Performance\', \'PSC\', \'Recipient Location\']"}'

# Fields to retrieve (from your working payload)
FIELDS = [
    "Award ID",
    "Mod",
    "Recipient Name",
    "Recipient UEI",
    "Recipient Location",
    "Primary Place of Performance",
    "Action Date",
    "Transaction Amount",
    "Transaction Description",
    "Awarding Agency",
    "Awarding Sub Agency",
    "Award Type",
    "NAICS",
    "PSC",
    "pop_state_code",
    "recipient_location_state_code",
    "pop_city_name",
    "recipient_location_city_name",
    "Funding Agency"
]

# Sort parameters
SORT_FIELD = "Transaction Amount"
ORDER = "desc"


# Retry function
def fetch_with_retry(payload, max_retries=7):
    retries = 0
    while retries < max_retries:
        try:
            response = requests.post(BASE_URL, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            retries += 1
            wait = 2 ** retries
            print(f"Connection error: {e}. Retrying in {wait}s... ({retries}/{max_retries})")
            time.sleep(wait)
    raise Exception("Max retries exceeded for payload")


# Loop over each NAICS code
for naics in DEFENSE_NAICS:
    print(f"Fetching NAICS {naics}...")

    page = 1
    limit = 100  # adjust up to 5000 if needed
    all_records = []

    while True:
        payload = {
            "filters": {
                "award_type_codes": ["A", "B", "C", "D"],
                "naics_codes": [naics],
                "award_date_range": {
                    "start_date": "2023-01-01",
                    "end_date": "2025-12-31"
                }
            },
            "fields": FIELDS,
            "page": page,
            "limit": limit,
            "sort": SORT_FIELD,
            "order": ORDER
        }

        try:
            data = fetch_with_retry(payload)
        except Exception as e:
            print(f"Failed to fetch page {page} for NAICS {naics}: {e}")
            break

        results = data.get("results", [])
        if not results:
            break  # no more pages

        all_records.extend(results)
        print(f"  Page {page} fetched, {len(results)} records")
        page += 1
        time.sleep(0.3)  # polite pause

    # Save results immediately
    if all_records:
        df = pd.DataFrame(all_records)
        file_path = OUTPUT_DIR / f"naics_{naics}.parquet"
        df.to_parquet(file_path, engine="pyarrow", index=False)
        print(f"Saved {len(all_records)} records for NAICS {naics}")
    else:
        print(f"No records found for NAICS {naics}")

print("All NAICS codes processed!")