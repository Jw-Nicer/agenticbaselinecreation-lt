
import pandas as pd

file_path = r"c:\Users\John\.gemini\antigravity\playground\multiagent-baseline-lt\data_files\Language Services\Peak Vista - AMN Download.xls"

# Load with correct skiprows
df = pd.read_excel(file_path, skiprows=8)

print(f"📂 File: Peak Vista - AMN Download.xls")
print(f"Total rows: {len(df)}")
print(f"\nAll columns:")
for i, col in enumerate(df.columns):
    print(f"  {i}: '{col}'")

# Check if there's ANY cost-related column
cost_cols = [c for c in df.columns if any(x in str(c).lower() for x in ['cost', 'charge', 'amount', 'price', 'rate', 'fee'])]
print(f"\n💰 Cost-related columns found: {cost_cols}")

if not cost_cols:
    print("\n🚨 NO COST COLUMN EXISTS IN THIS FILE!")
    print("   This entire file has ZERO cost data.")
    print("   Every row with a Duration is a 'missing cost' row.")
    
    # Show specific examples
    duration_col = [c for c in df.columns if 'duration' in str(c).lower()][0]
    rows_with_duration = df[df[duration_col].notna() & (df[duration_col] != '--')]
    
    print(f"\n📊 Rows with Duration but NO Cost: {len(rows_with_duration)}")
    
    print(f"\n{'='*80}")
    print("AUDITABLE EXAMPLES (Missing Cost):")
    print(f"{'='*80}")
    
    for idx, row in rows_with_duration.head(5).iterrows():
        excel_row = idx + 10  # +8 for skiprows, +2 for header/0-index
        print(f"\n  📍 Excel Row {excel_row}:")
        print(f"     Language: {row.get('Language', 'N/A')}")
        print(f"     Duration: {row.get('Duration', row.get(duration_col, 'N/A'))}")
        print(f"     Call Date: {row.get('Call Date', 'N/A')}")
        print(f"     ❌ Cost Column: DOES NOT EXIST")
    
    print(f"\n{'='*80}")
    print("☝️ The Rate Card Agent applied $0.70/min to fill these missing costs.")
