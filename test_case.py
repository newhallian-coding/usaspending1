import requests
import pandas as pd
from pathlib import Path

BASE_URL = "https://api.usaspending.gov/api/v2/search/spending_by_transaction/"

OUTPUT_DIR = Path("test_storage")
OUTPUT_DIR.mkdir(exist_ok=True)

# Sort parameters
SORT_FIELD = "Transaction Amount"
ORDER = "desc"
page = 1
limit = 2
NAICS =  ["336411","334511"]
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
for naics in NAICS:
    payload = {
        "filters":
            { "award_type_codes": ["A", "B", "C", "D"],
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
        "order": ORDER }

    response = requests.post(BASE_URL, json=payload)
    print(response.status_code)
    print(response.text)
    response.raise_for_status()
    data = response.json().get("results", [])

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Save to Parquet
    parquet_file = OUTPUT_DIR / "naics_336411_test.parquet"
    df.to_parquet(parquet_file, index=False)
    print(f"Saved {len(df)} records to {parquet_file}")

    # Path to the Parquet file you saved
    parquet_file = Path("test_storage/naics_336411_test.parquet")

    # Read the file back into a DataFrame
    df = pd.read_parquet(parquet_file, engine="pyarrow")  # specify engine if needed

    # Check the contents
    print(df.head())
    print(f"Number of rows: {len(df)}")