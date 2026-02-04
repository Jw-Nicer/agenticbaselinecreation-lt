
import pandas as pd
import os

# Path to the specific file
file_path = r"c:\Users\John\.gemini\antigravity\playground\multiagent-baseline-lt\data_files\Language Services\Healthpoint - Propio Transaction Download.xlsx"

print(f"🔍 Inspecting File: {os.path.basename(file_path)}")

# Load the file to find sheet names
xls = pd.ExcelFile(file_path)
print(f"Sheets found: {xls.sheet_names}")

# We assume the data is in the first sheet or one named 'Detail'
target_sheet = xls.sheet_names[0] 
df = pd.read_excel(file_path, sheet_name=target_sheet)

print(f"\n📋 Analyzing Sheet: '{target_sheet}'")
print(f"Total Rows: {len(df)}")
print(f"Columns: {list(df.columns)}")

print("\n🔎 RAW DATA SAMPLES (First 5 Rows):")
print("-" * 80)
# Print headers with column letters
headers = list(df.columns)
header_str = "    "
for i, h in enumerate(headers):
    col_letter = chr(65 + i) # A, B, C...
    header_str += f"{col_letter}: {str(h)[:15]:<15} | "
print(header_str)
print("-" * 80)

# Print first 5 rows with Row Numbers
for idx, row in df.head(5).iterrows():
    row_num = idx + 2 # +2 because Excel is 1-indexed and header is row 1
    row_str = f"Row {row_num:<2} "
    for col in df.columns:
        val = str(row[col])
        if len(val) > 15: val = val[:12] + "..."
        row_str += f"{val:<18} | "
    print(row_str)

print("\n" + "="*80)
