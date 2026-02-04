"""
TEST: Enhanced IntakeAgent on all source files
Verifies the pipeline can properly load and process each file.
"""

import sys
sys.path.insert(0, r'c:\Users\John\.gemini\antigravity\playground\multiagent-baseline-lt\multi_agent_system\src')

from agents.intake_agent import IntakeAgent
from agents.schema_agent import SchemaAgent
import os

DATA_DIR = r"c:\Users\John\.gemini\antigravity\playground\multiagent-baseline-lt\data_files\Language Services"

def main():
    print("="*70)
    print("TESTING ENHANCED INTAKE AGENT")
    print("="*70)
    
    intake = IntakeAgent(DATA_DIR)
    schema = SchemaAgent()
    
    files = intake.scan_files()
    print(f"\nFound {len(files)} files to process.\n")
    
    results = []
    
    for filepath in files:
        filename = os.path.basename(filepath)
        print(f"\n{'='*70}")
        print(f"PROCESSING: {filename}")
        print("="*70)
        
        # Load sheets
        sheets = intake.load_clean_sheet(filepath)
        
        result = {
            'file': filename,
            'sheets_loaded': len(sheets),
            'sheets': {},
            'status': 'UNKNOWN'
        }
        
        if not sheets:
            print(f"  [FAIL] No usable sheets found")
            result['status'] = 'FAIL - No data sheets'
            results.append(result)
            continue
            
        for sheet_name, df in sheets.items():
            print(f"\n  Sheet: '{sheet_name}' ({len(df):,} rows, {len(df.columns)} cols)")
            print(f"  Columns: {list(df.columns)[:8]}...")
            
            # Try schema mapping
            try:
                mapping = schema.infer_mapping(list(df.columns), df.iloc[0] if len(df) > 0 else None)
                confidence = schema.get_mapping_confidence(mapping)
                
                has_date = 'date' in mapping
                has_lang = 'language' in mapping
                has_mins = 'minutes' in mapping
                has_cost = 'cost' in mapping
                
                result['sheets'][sheet_name] = {
                    'rows': len(df),
                    'mapping': mapping,
                    'confidence': confidence,
                    'has_required': has_date and has_lang and has_mins
                }
                
                print(f"  Mapping confidence: {confidence:.0%}")
                print(f"  Fields found:")
                print(f"    Date:     {'[OK] ' + mapping.get('date', 'N/A') if has_date else '[MISSING]'}")
                print(f"    Language: {'[OK] ' + mapping.get('language', 'N/A') if has_lang else '[MISSING]'}")
                print(f"    Minutes:  {'[OK] ' + mapping.get('minutes', 'N/A') if has_mins else '[MISSING]'}")
                print(f"    Cost:     {'[OK] ' + mapping.get('cost', 'N/A') if has_cost else '[WARN] Missing'}")
                
            except Exception as e:
                print(f"  [ERROR] Schema mapping failed: {e}")
                result['sheets'][sheet_name] = {'error': str(e)}
        
        # Determine overall status
        any_usable = any(s.get('has_required', False) for s in result['sheets'].values())
        result['status'] = 'OK' if any_usable else 'PARTIAL' if sheets else 'FAIL'
        results.append(result)
    
    # Print compatibility report from IntakeAgent
    print("\n" + intake.get_file_compatibility_report())
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    ok_count = sum(1 for r in results if r['status'] == 'OK')
    partial_count = sum(1 for r in results if r['status'] == 'PARTIAL')
    fail_count = sum(1 for r in results if 'FAIL' in r['status'])
    
    print(f"""
    Files tested: {len(results)}
    
    [OK]      Fully compatible:      {ok_count}
    [PARTIAL] Missing some fields:   {partial_count}
    [FAIL]    Cannot process:        {fail_count}
    """)
    
    print("DETAILED STATUS:")
    for r in results:
        status_icon = "[OK]" if r['status'] == 'OK' else "[PARTIAL]" if r['status'] == 'PARTIAL' else "[FAIL]"
        print(f"  {status_icon} {r['file'][:50]}: {r['status']}")
        

if __name__ == "__main__":
    main()
