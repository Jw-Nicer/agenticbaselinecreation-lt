
import pandas as pd
import os

file_path = r"c:\Users\John\.gemini\antigravity\playground\multiagent-baseline-lt\data_files\Language Services\Healthpoint - Propio Transaction Download.xlsx"
df = pd.read_excel(file_path, sheet_name='ag-grid', nrows=5)

print("ALL COLUMNS:")
for i, col in enumerate(df.columns):
    print(f"  {i}: '{col}'")
