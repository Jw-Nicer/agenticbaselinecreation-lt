
import pandas as pd
import os

data_dir = r"c:\Users\John\.gemini\antigravity\playground\multiagent-baseline-lt\data_files\Language Services"

files_config = [
    {
        "filename": "Healthpoint - Propio Transaction Download.xlsx",
        "sheet": "ag-grid",
        "skiprows": 0,
        "column_map": {
            "Date": "Service Date",
            "Language": "Language", 
            "Minutes": "Duration",
            "Cost": "Total Charge",
            "Modality": "Service Line"
        }
    },
    {
        "filename": "Nuvance - Cyracom Utilization.xlsx",
        "sheet": None,
        "skiprows": 0,
        "column_map": {
            "Date": "Year-Month",
            "Language": "Language",
            "Minutes": "MinuteswithTPD",
            "Cost": "ChargeswithTPD",
            "Modality": "Servicey Type"
        }
    },
    {
        "filename": "Peak Vista - AMN Download.xls",
        "sheet": None,
        "skiprows": 8,
        "column_map": {
            "Date": "Call Date",
            "Language": "Language",
            "Minutes": "Duration",
            "Cost": None,
            "Modality": "Session Type"
        }
    }
]

print("=" * 70)
print("FILE SUFFICIENCY ANALYSIS")
print("=" * 70)

results = []

for config in files_config:
    filepath = os.path.join(data_dir, config["filename"])
    if not os.path.exists(filepath):
        print(f"\n[X] {config['filename']} - FILE NOT FOUND")
        continue
    
    print(f"\n{'='*60}")
    print(f"FILE: {config['filename']}")
    print(f"{'='*60}")
    
    try:
        if config["sheet"]:
            df = pd.read_excel(filepath, sheet_name=config["sheet"], skiprows=config["skiprows"])
        else:
            df = pd.read_excel(filepath, skiprows=config["skiprows"])
        
        print(f"Total Rows: {len(df):,}")
        
        result = {"file": config["filename"], "rows": len(df)}
        
        print(f"\nREQUIRED FIELDS:")
        
        for field, col_name in config["column_map"].items():
            if col_name is None:
                print(f"  [X] {field}: MISSING - No column exists in file")
                result[field] = "MISSING"
            elif col_name in df.columns:
                non_null = df[col_name].notna().sum()
                pct = (non_null / len(df)) * 100
                sample = df[col_name].iloc[0] if non_null > 0 else "N/A"
                print(f"  [OK] {field}: Column '{col_name}'")
                print(f"        - {non_null:,} values ({pct:.1f}% complete)")
                print(f"        - Sample: {sample}")
                result[field] = "OK"
            else:
                print(f"  [X] {field}: Column '{col_name}' not found")
                result[field] = "NOT FOUND"
        
        # Overall status
        missing = [f for f, c in config["column_map"].items() if c is None or c not in df.columns]
        if not missing:
            print(f"\n[STATUS] SUFFICIENT - All required fields present")
            result["status"] = "SUFFICIENT"
        else:
            print(f"\n[STATUS] INSUFFICIENT - Missing: {', '.join(missing)}")
            result["status"] = "INSUFFICIENT"
        
        results.append(result)
        
    except Exception as e:
        print(f"  [ERROR] {e}")

print("\n" + "=" * 70)
print("SUMMARY TABLE")
print("=" * 70)
print("\n| File                      | Rows    | Date | Lang | Min | Cost | Modal | Status |")
print("|---------------------------|---------|------|------|-----|------|-------|--------|")
for r in results:
    print(f"| {r['file'][:25]:<25} | {r['rows']:>7,} | {r.get('Date', '?'):^4} | {r.get('Language', '?'):^4} | {r.get('Minutes', '?'):^3} | {r.get('Cost', '?'):^4} | {r.get('Modality', '?'):^5} | {r['status'][:8]} |")
