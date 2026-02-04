
import pandas as pd

# Load Healthpoint data (which HAS costs)
df = pd.read_excel(r'data_files/Language Services/Healthpoint - Propio Transaction Download.xlsx', sheet_name='ag-grid')

# Filter valid rows
df = df[(df['Duration'] > 0) & (df['Total Charge'] > 0)]

# Calculate Cost Per Minute for each row
df['CPM'] = df['Total Charge'] / df['Duration']

print("="*60)
print("HOW RATE CARD IS CALCULATED")
print("="*60)
print("\nFrom Healthpoint file (which HAS cost data):")
print(f"  Column L: Total Charge")
print(f"  Column J: Duration (minutes)")
print(f"  Formula: Rate = Column L ÷ Column J")
print()

# Calculate averages by modality
for modality in ['OPI', 'VRI']:
    subset = df[df['Service Line'] == modality]
    if len(subset) > 0:
        avg_rate = subset['CPM'].mean()
        print(f"  {modality} Average Rate: ${avg_rate:.2f}/min (from {len(subset):,} transactions)")

print()
print("="*60)
print("EXAMPLE CALCULATION (Row 2):")
print("="*60)
row = df.iloc[0]
print(f"  Column L (Total Charge): ${row['Total Charge']:.2f}")
print(f"  Column J (Duration):     {row['Duration']:.0f} minutes")
print(f"  Calculated Rate:         ${row['Total Charge']:.2f} ÷ {row['Duration']:.0f} = ${row['CPM']:.2f}/min")
