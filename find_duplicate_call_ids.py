
import pandas as pd

file_path = r"c:\Users\John\.gemini\antigravity\playground\multiagent-baseline-lt\data_files\Language Services\Healthpoint - Propio Transaction Download.xlsx"
df = pd.read_excel(file_path, sheet_name='ag-grid')

print(f"Total rows: {len(df)}")
print(f"Unique Call-IDs: {df['Call-ID'].nunique()}")

# Find rows where Call-ID appears more than once
dup_call_ids = df[df.duplicated(subset=['Call-ID'], keep=False)]
print(f"\nRows with DUPLICATE Call-IDs: {len(dup_call_ids)}")

if len(dup_call_ids) > 0:
    # Show a specific example
    print("\n🚨 PROOF OF DUPLICATE BILLING:")
    print("-" * 80)
    
    # Get one Call-ID that appears multiple times
    sample_call_id = dup_call_ids['Call-ID'].value_counts().head(1).index[0]
    sample_rows = df[df['Call-ID'] == sample_call_id]
    
    print(f"Call-ID '{sample_call_id}' appears {len(sample_rows)} times:")
    for idx, row in sample_rows.iterrows():
        excel_row = idx + 2
        print(f"\n  Row {excel_row}:")
        print(f"    Call-ID: {row['Call-ID']}")
        print(f"    Date: {row['Service Date']}")
        print(f"    Language: {row['Language']}")
        print(f"    Duration: {row['Duration']} min")
        print(f"    Total Charge: ${row['Total Charge']}")
    
    print("\n" + "-" * 80)
    print("☝️ SAME Call-ID = SAME CALL. This is being billed multiple times!")
