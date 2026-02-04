
import pandas as pd
import numpy as np
import os

# File Path
file_path = r"c:\Users\John\.gemini\antigravity\playground\multiagent-baseline-lt\data_files\Language Services\Healthpoint - Propio Transaction Download.xlsx"
sheet_name = "ag-grid"

print(f"🕵️ INVESTIGATION: Auditing {os.path.basename(file_path)}...")

# Load Data
df = pd.read_excel(file_path, sheet_name=sheet_name)
print(f" Loaded {len(df)} rows.")

# --- 1. FIND MISSING COSTS (Column M vs K) ---
# Column M = Total_Charge, Column K = Total_Minutes
# We want rows where Minutes > 0 but Charge is 0 or NaN

print("\n🚨 ISSUE 1: MISSING COSTS (Zero/Blank Charge but Valid Minutes)")
print(f"   Checking Column M (Charge) vs K (Minutes)...")

missing_cost_mask = ((df['Total_Charge'].isna()) | (df['Total_Charge'] == 0)) & (df['Total_Minutes'] > 0)
bad_rows = df[missing_cost_mask]

if len(bad_rows) > 0:
    print(f"   found {len(bad_rows)} rows with missing costs.")
    print(f"   Examples:")
    for idx, row in bad_rows.head(3).iterrows():
        excel_row = idx + 2 # Header is 1
        print(f"   -> Row {excel_row}: Minutes={row['Total_Minutes']}, Charge={row['Total_Charge']} (Should be paid!)")
else:
    print("   ✓ No missing costs found.")

# --- 2. FIND DUPLICATES ---
# We look for rows that are EXACTLY the same in key columns
print("\n🚨 ISSUE 2: DUPLICATE CHARGES")
print("   Checking for identical Date + Start Time + Language + Duration...")

# Create a signature
df['dup_sig'] = df['Service Date'].astype(str) + df['Start Time (Central)'].astype(str) + df['Language'] + df['Total_Minutes'].astype(str)
duplicates = df[df.duplicated(subset=['dup_sig'], keep='first')]

if len(duplicates) > 0:
    print(f"   Found {len(duplicates)} DUPLICATE rows.")
    print(f"   Examples (Double Billing?):")
    for idx, row in duplicates.head(3).iterrows():
        excel_row = idx + 2
        print(f"   -> Row {excel_row}: {row['Service Date']} | {row['Start Time (Central)']} | {row['Language']} | {row['Total_Minutes']} min | ${row['Total_Charge']}")
else:
    print("   ✓ No duplicates found.")


# --- 3. FIND OUTLIERS (Expensive calls) ---
print("\n🚨 ISSUE 3: EXPENSIVE CALL OUTLIERS (>$5.00/min)")
df['cpm_check'] = df['Total_Charge'] / df['Total_Minutes']
expensive = df[(df['cpm_check'] > 5.0) & (df['Total_Minutes'] > 1)]

if len(expensive) > 0:
    print(f"   Found {len(expensive)} very expensive calls.")
    for idx, row in expensive.head(3).iterrows():
        excel_row = idx + 2
        print(f"   -> Row {excel_row}: {row['Language']} call cost ${row['Total_Charge']} for {row['Total_Minutes']} min (${row['cpm_check']:.2f}/min)")
else:
    print("   ✓ No extreme rate outliers found.")
