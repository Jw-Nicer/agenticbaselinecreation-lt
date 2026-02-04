"""
DEEP HEADER DETECTION SCAN
Finds the actual header row in each file by scanning row by row.
"""

import pandas as pd
import os
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = r"c:\Users\John\.gemini\antigravity\playground\multiagent-baseline-lt\data_files\Language Services"

# Keywords that indicate a header row
HEADER_KEYWORDS = ['language', 'date', 'minutes', 'duration', 'charge', 'amount', 
                   'service', 'call', 'interpreter', 'total', 'cost', 'type']

def find_header_row(filepath, max_rows=30):
    """Scan first N rows to find the actual header."""
    results = []
    
    try:
        xl = pd.ExcelFile(filepath)
        for sheet in xl.sheet_names[:2]:  # Check first 2 sheets
            try:
                # Read without header
                df = pd.read_excel(filepath, sheet_name=sheet, header=None, nrows=max_rows)
                
                for idx, row in df.iterrows():
                    row_str = ' '.join([str(x).lower() for x in row.values if pd.notna(x)])
                    score = sum(1 for kw in HEADER_KEYWORDS if kw in row_str)
                    
                    if score >= 2:
                        results.append({
                            'sheet': sheet,
                            'row': idx,
                            'score': score,
                            'sample': [str(x)[:20] for x in row.values if pd.notna(x)][:6]
                        })
            except Exception as e:
                pass
                
    except Exception as e:
        pass
        
    return results


def main():
    print("="*80)
    print("DEEP HEADER DETECTION SCAN")
    print("Finding actual header rows in each file")
    print("="*80)
    
    files = [f for f in os.listdir(DATA_DIR) 
             if f.endswith(('.xlsx', '.xls', '.XLS')) and not f.startswith('~$')]
    
    for f in files:
        filepath = os.path.join(DATA_DIR, f)
        print(f"\n{'='*80}")
        print(f"FILE: {f}")
        print("="*80)
        
        headers = find_header_row(filepath)
        
        if headers:
            print(f"HEADER CANDIDATES FOUND:")
            for h in headers[:3]:  # Show top 3
                print(f"  Sheet: '{h['sheet']}' | Row: {h['row']} | Score: {h['score']}")
                print(f"  Columns: {h['sample']}")
        else:
            print("  [!] No obvious header row found - may need manual inspection")
            
        # Also show first few rows raw
        try:
            df = pd.read_excel(filepath, header=None, nrows=10)
            print(f"\nRAW FIRST 5 ROWS:")
            for idx, row in df.head(5).iterrows():
                vals = [str(x)[:15] for x in row.values if pd.notna(x)][:5]
                print(f"  Row {idx}: {vals}")
        except Exception as e:
            print(f"  Error reading file: {e}")
            

if __name__ == "__main__":
    main()
