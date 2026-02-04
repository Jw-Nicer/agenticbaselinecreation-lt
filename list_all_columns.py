
import pandas as pd
import os

files = [
    ("Healthpoint - Propio Transaction Download.xlsx", "ag-grid", 0),
    ("Nuvance - Cyracom Utilization.xlsx", None, 0),
    ("VFC - Pacific Interpreters Invoice.xls", None, 0),
    ("Wellspace - LanguageLine Invoice.XLS", None, 0),
    ("Peak Vista - AMN Download.xls", None, 8),  # This file needs skiprows=8
]

data_dir = r"c:\Users\John\.gemini\antigravity\playground\multiagent-baseline-lt\data_files\Language Services"

for filename, sheet, skip in files:
    filepath = os.path.join(data_dir, filename)
    if not os.path.exists(filepath):
        print(f"❌ {filename} - NOT FOUND")
        continue
    
    try:
        if sheet:
            df = pd.read_excel(filepath, sheet_name=sheet, nrows=2)
        else:
            df = pd.read_excel(filepath, skiprows=skip, nrows=2)
        
        print(f"\n{'='*60}")
        print(f"📂 {filename}")
        print(f"{'='*60}")
        print("COLUMNS:")
        for i, col in enumerate(df.columns):
            col_letter = chr(65 + i) if i < 26 else f"A{chr(65 + i - 26)}"
            # Check if column has numeric data (potential cost/minutes)
            sample = df[col].iloc[0] if len(df) > 0 else None
            print(f"  {col_letter}: '{col}' (sample: {sample})")
    except Exception as e:
        print(f"❌ {filename} - Error: {e}")
