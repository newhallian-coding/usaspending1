from pathlib import Path
import pandas as pd

# Directory where your fetched parquet files are stored
PARQUET_DIR = Path("usa_spending_defense")

# List all parquet files
files = list(PARQUET_DIR.glob("*.parquet"))
print(f"Found {len(files)} parquet files.")

if not files:
    raise FileNotFoundError("No parquet files found in this folder.")

# Read the first file
df = pd.read_parquet(files[0])

# 1️⃣ Show all column names
print("Columns in this file:")
print(df.columns.tolist())

# 2️⃣ Show first 5 rows of all columns (no truncation)
pd.set_option('display.max_columns', None)
print("\nFirst 5 rows:")
print(df.head())

# 3️⃣ Quick summary of each column
print("\nData types and non-null counts:")
print(df.info())

# 4️⃣ Inspect the Primary Place of Performance column
pop_col = "pop_state_code"  # adjust if your column is named differently
if pop_col in df.columns:
    print(f"\nTop 10 states by number of contracts in {files[0].name}:")
    print(df[pop_col].value_counts().head(10))
else:
    print(f"\nColumn '{pop_col}' not found in this file. Check your column names.")

# 5️⃣ Optionally check NAICS codes present
if "naics_code" in df.columns:
    print("\nNAICS codes present in this file:")
    print(df["naics_code"].value_counts().head(10))
