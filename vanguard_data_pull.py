import requests
import pandas as pd
from pathlib import Path
import time

# =========================
# CONFIG
# =========================

BASE_URL = "https://api.usaspending.gov/api/v2/search/spending_by_transaction/"

START_DATE = "2023-01-01"
END_DATE = "2025-12-31"

LIMIT = 100
MAX_PAGES = 200   # HARD SAFETY CAP — REQUIRED

OUTPUT_DIR = Path("usaspending_output")
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "aerospace_execution_transactions.csv"

# Aerospace + manufacturing NAICS (INTENTIONALLY BROAD)
AEROSPACE_NAICS = [
    "336411", "336412", "336413", "336414", "336415", "336419",
    "334511", "334515", "334419",
    "332710", "332721"
]

FIELDS = [
    "Award ID",
    "Mod",
    "Recipient Name",
    "Recipient UEI",
    "Recipient Location",
    "Primary Place of Performance",
    "Issued Date",
    "Action Date",
    "Transaction Amount",
    "Transaction Description",
    "Awarding Agency",
    "Awarding Sub Agency",
    "Award Type",
    "NAICS",
    "PSC",
    "Funding Agency"
]

# =========================
# HELPERS
# =========================

def fetch_with_retry(payload, max_retries=7):
    for attempt in range(max_retries):
        try:
            r = requests.post(BASE_URL, json=payload, timeout=30)
            r.raise_for_status()
            return r.json()
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            wait = 2 ** attempt
            print(f"Retry {attempt+1}/{max_retries} after {wait}s: {e}")
            time.sleep(wait)
    raise RuntimeError("USAspending API failed repeatedly")

def flatten(record):
    out = record.copy()

    naics = out.pop("NAICS", {}) or {}
    out["naics_code"] = naics.get("code")
    out["naics_description"] = naics.get("description")

    psc = out.pop("PSC", {}) or {}
    out["psc_code"] = psc.get("code")
    out["psc_description"] = psc.get("description")

    loc = out.pop("Recipient Location", {}) or {}
    out["recipient_city"] = loc.get("city_name")
    out["recipient_state"] = loc.get("state_code")

    pop = out.pop("Primary Place of Performance", {}) or {}
    out["pop_city"] = pop.get("city_name")
    out["pop_state"] = pop.get("state_code")

    return out

# =========================
# MAIN PIPELINE
# =========================

print("\nCollecting aerospace execution transactions...")

all_rows = []

for naics in AEROSPACE_NAICS:
    print(f"\nProcessing NAICS {naics}")
    page = 1

    while page <= MAX_PAGES:
        payload = {
            "filters": {
                "award_type_codes": ["A", "B", "C", "D"],
                "naics_codes": [naics],
                "award_date_range": {
                    "start_date": START_DATE,
                    "end_date": END_DATE
                }
            },
            "fields": FIELDS,
            "page": page,
            "limit": LIMIT,
            "sort": "Transaction Amount",
            "order": "desc"
        }

        data = fetch_with_retry(payload)
        results = data.get("results", [])

        if not results:
            print("  No results returned — stopping.")
            break

        print(f"  Page {page}: {len(results)} records")
        all_rows.extend(flatten(r) for r in results)

        # 🔑 CRITICAL STOP CONDITION (THIS FIXES THE INFINITE LOOP)
        if len(results) < LIMIT:
            print("  Final partial page reached — stopping.")
            break

        page += 1
        time.sleep(0.3)

    if page > MAX_PAGES:
        print("  MAX_PAGES reached — stopping to avoid runaway loop.")

# =========================
# OUTPUT
# =========================

df = pd.DataFrame(all_rows).drop_duplicates()
df.to_csv(OUTPUT_FILE, index=False)

print(f"\nDONE — Saved {len(df)} aerospace execution records")
print(OUTPUT_FILE)
