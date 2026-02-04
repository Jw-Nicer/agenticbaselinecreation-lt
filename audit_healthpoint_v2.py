
import pandas as pd
import os

file_path = r"c:\Users\John\.gemini\antigravity\playground\multiagent-baseline-lt\data_files\Language Services\Healthpoint - Propio Transaction Download.xlsx"
df = pd.read_excel(file_path, sheet_name='ag-grid')

print(f"🕵️ AUDIT REPORT for {os.path.basename(file_path)}")
print("-" * 60)

# 1. Check for Missing Costs
# Duration > 0 but Total Charge is 0 or Blank
missing_cost = df[((df['Total Charge'].isna()) | (df['Total Charge'] == 0)) & (df['Duration'] > 0)]

if len(missing_cost) > 0:
    print(f"\n🚨 FOUND {len(missing_cost)} ROWS WITH MISSING COSTS:")
    for idx, row in missing_cost.head(3).iterrows():
        print(f"   • Row {idx+2}: {row['Duration']} min call but ${row['Total Charge']} charge.")

# 2. Check for Duplicates
# Same Date, Time, Language, Duration
df['dup_key'] = df['Service Date'].astype(str) + df['Start Time (Central)'].astype(str) + df['Language'] + df['Duration'].astype(str)
dups = df[df.duplicated(subset=['dup_key'], keep='first')]

if len(dups) > 0:
    print(f"\n🚨 FOUND {len(dups)} DUPLICATE CHARGES:")
    for idx, row in dups.head(3).iterrows():
        print(f"   • Row {idx+2}: Duplicate of {row['Language']} call on {row['Service Date']}")

# 3. Check for Outliers
# CPM > $5.00
df['cpm_calc'] = df['Total Charge'] / df['Duration']
outliers = df[(df['cpm_calc'] > 5.0) & (df['Duration'] > 1)]

if len(outliers) > 0:
    print(f"\n🚨 FOUND {len(outliers)} EXPENSIVE OUTLIERS:")
    for idx, row in outliers.head(3).iterrows():
        print(f"   • Row {idx+2}: ${row['cpm_calc']:.2f}/min ({row['Language']}, {row['Duration']} min)")

print("-" * 60)
