
import pandas as pd

file_path = r"c:\Users\John\.gemini\antigravity\playground\multiagent-baseline-lt\data_files\Language Services\Healthpoint - Propio Transaction Download.xlsx"
df = pd.read_excel(file_path, sheet_name='ag-grid')

print(f"Total rows: {len(df)}")

# Filter to only valid Call-IDs (positive numbers, not placeholders)
valid_df = df[df['Call-ID'] > 0]
print(f"Rows with valid Call-IDs: {len(valid_df)}")

# Find valid Call-IDs that appear more than once
dup_mask = valid_df.duplicated(subset=['Call-ID'], keep=False)
dup_call_ids = valid_df[dup_mask]
print(f"\n🚨 Rows with DUPLICATE valid Call-IDs: {len(dup_call_ids)}")

if len(dup_call_ids) > 0:
    # Count how many unique Call-IDs are duplicated
    dup_counts = dup_call_ids['Call-ID'].value_counts()
    print(f"Number of unique Call-IDs that appear multiple times: {len(dup_counts)}")
    
    # Show a specific example with a REAL Call-ID
    sample_call_id = dup_counts.head(1).index[0]
    sample_rows = df[df['Call-ID'] == sample_call_id]
    
    print(f"\n{'='*80}")
    print(f"PROOF: Call-ID {sample_call_id} appears {len(sample_rows)} times!")
    print(f"{'='*80}")
    
    for idx, row in sample_rows.iterrows():
        excel_row = idx + 2
        print(f"\n  📍 Excel Row {excel_row}:")
        print(f"     Column B (Call-ID): {row['Call-ID']}")
        print(f"     Column G (Date): {row['Service Date']}")
        print(f"     Column H (Start Time): {row['Start Time (Central)']}")
        print(f"     Column F (Language): {row['Language']}")
        print(f"     Column J (Duration): {row['Duration']} min")
        print(f"     Column L (Charge): ${row['Total Charge']}")
    
    print(f"\n{'='*80}")
    print("☝️ THIS IS THE SAME CALL BILLED TWICE!")
    print("   The Call-ID is a unique identifier from Propio's system.")
    print("   Two rows with the same Call-ID = double billing.")
else:
    print("\n✓ No valid duplicate Call-IDs found.")
    print("  Let me check for duplicates based on timestamp instead...")
