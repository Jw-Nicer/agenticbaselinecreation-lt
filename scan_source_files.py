"""
SOURCE FILE SCANNER
Deeply analyzes each language service file to ensure pipeline compatibility.
"""

import pandas as pd
import os
import sys
import warnings
warnings.filterwarnings('ignore')

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = r"c:\Users\John\.gemini\antigravity\playground\multiagent-baseline-lt\data_files\Language Services"

# Define what columns we need for the baseline
REQUIRED_FIELDS = {
    'date': ['date', 'call date', 'service date', 'invoice date', 'session date'],
    'language': ['language', 'target language', 'lang'],
    'minutes': ['minutes', 'duration', 'min billed', 'connect time', 'length', 'total minutes'],
    'cost': ['cost', 'charge', 'amount', 'total charge', 'charges', 'total amount', 'price'],
    'modality': ['modality', 'service type', 'type', 'interpretation type', 'mode']
}

def scan_excel_file(filepath):
    """Deep scan of an Excel file."""
    filename = os.path.basename(filepath)
    result = {
        'file': filename,
        'size_mb': os.path.getsize(filepath) / (1024*1024),
        'sheets': [],
        'total_rows': 0,
        'field_matches': {},
        'issues': [],
        'sample_columns': []
    }
    
    try:
        # Get sheet names
        xl = pd.ExcelFile(filepath)
        result['sheets'] = xl.sheet_names
        
        # Analyze first sheet (or largest)
        for sheet in xl.sheet_names[:3]:  # Check first 3 sheets
            try:
                df = pd.read_excel(filepath, sheet_name=sheet, nrows=50)
                
                if df.empty or len(df.columns) < 2:
                    continue
                
                # Store sample columns
                result['sample_columns'] = list(df.columns)[:10]
                    
                # Clean column names
                cols = [str(c).lower().strip() for c in df.columns]
                
                # Check for required fields
                for field, keywords in REQUIRED_FIELDS.items():
                    for col_idx, col in enumerate(cols):
                        for kw in keywords:
                            if kw in col:
                                if field not in result['field_matches']:
                                    result['field_matches'][field] = []
                                result['field_matches'][field].append({
                                    'sheet': sheet,
                                    'column': str(df.columns[col_idx]),
                                    'keyword': kw
                                })
                
                # Get row count (without reading all data for large files)
                if result['size_mb'] < 5:
                    df_full = pd.read_excel(filepath, sheet_name=sheet)
                    result['total_rows'] += len(df_full)
                else:
                    # Estimate for large files
                    result['total_rows'] = "Large file - estimated 100k+"
                    
            except Exception as e:
                result['issues'].append(f"Sheet '{sheet}': {str(e)[:50]}")
                
    except Exception as e:
        result['issues'].append(f"File error: {str(e)[:100]}")
        
    # Check for missing required fields
    for field in ['date', 'language', 'minutes']:
        if field not in result['field_matches']:
            result['issues'].append(f"MISSING REQUIRED: '{field}' column not found")
            
    if 'cost' not in result['field_matches']:
        result['issues'].append(f"WARNING: 'cost' column not found (will need rate card)")
        
    return result


def main():
    print("="*80)
    print("SOURCE FILE DEEP SCAN")
    print("Verifying pipeline compatibility with all language service files")
    print("="*80)
    
    files = [f for f in os.listdir(DATA_DIR) 
             if f.endswith(('.xlsx', '.xls', '.XLS')) and not f.startswith('~$')]
    
    print(f"\nFound {len(files)} Excel files to scan.\n")
    
    all_results = []
    
    for f in files:
        filepath = os.path.join(DATA_DIR, f)
        print(f"Scanning: {f[:60]}...")
        result = scan_excel_file(filepath)
        all_results.append(result)
        
    # Summary Report
    print("\n" + "="*80)
    print("SCAN RESULTS")
    print("="*80)
    
    for r in all_results:
        print(f"\n[FILE] {r['file']}")
        print(f"   Size: {r['size_mb']:.1f} MB | Rows: {r['total_rows']} | Sheets: {len(r['sheets'])}")
        print(f"   Columns found: {r['sample_columns'][:5]}...")
        
        print("   FIELD MAPPING:")
        for field in ['date', 'language', 'minutes', 'cost', 'modality']:
            if field in r['field_matches']:
                matches = r['field_matches'][field]
                col = matches[0]['column']
                print(f"     [OK] {field.upper()}: '{col}'")
            else:
                if field in ['date', 'language', 'minutes']:
                    print(f"     [CRITICAL] {field.upper()}: NOT FOUND")
                elif field == 'cost':
                    print(f"     [WARN] {field.upper()}: NOT FOUND (will flag for rate card)")
                else:
                    print(f"     [WARN] {field.upper()}: NOT FOUND (will default to UNKNOWN)")
                    
        if r['issues']:
            print("   ISSUES:")
            for issue in r['issues'][:5]:
                print(f"     - {issue}")
                
    # Overall Assessment
    print("\n" + "="*80)
    print("OVERALL PIPELINE COMPATIBILITY ASSESSMENT")
    print("="*80)
    
    fully_compatible = 0
    partial = 0
    problematic = 0
    
    for r in all_results:
        required_found = sum(1 for f in ['date', 'language', 'minutes'] if f in r['field_matches'])
        if required_found == 3:
            fully_compatible += 1
        elif required_found >= 2:
            partial += 1
        else:
            problematic += 1
            
    print(f"""
    FILES ANALYZED: {len(all_results)}
    
    [OK] Fully Compatible:      {fully_compatible} files (have date, language, minutes)
    [WARN] Partially Compatible: {partial} files (missing 1 required field)
    [CRITICAL] Problematic:     {problematic} files (missing 2+ required fields)
    
    COST DATA STATUS:
""")
    
    for r in all_results:
        has_cost = 'cost' in r['field_matches']
        status = "[OK] Has cost data" if has_cost else "[WARN] NO cost data (needs rate card)"
        print(f"      {r['file'][:45]}: {status}")
        
    print("""
    
    RECOMMENDATION:
    - Files WITH cost data: Pipeline produces accurate baseline
    - Files WITHOUT cost data: Populate rate_card_current.csv with contract rates
    """)


if __name__ == "__main__":
    main()
