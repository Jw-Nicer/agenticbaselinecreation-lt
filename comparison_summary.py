import pandas as pd

baseline = pd.read_csv('baseline_v1_output.csv')
hp = baseline[baseline['Vendor'].str.contains('Healthpoint', case=False, na=False)]

print("="*60)
print("SIDE-BY-SIDE COMPARISON: HealthPoint")
print("="*60)

print("\nCONSULTANT (ERA Report - Feb 2025):")
print("  Data Period:        12 months ending Nov 2024")
print("  Annual Expenditure: $788,400")
print("  Annual Hours:       13,140 hrs (788,400 mins)")
print("  Implied CPM:        $1.00/min")
print("  Top Language:       Spanish (31.5%)")

print("\nPIPELINE OUTPUT:")
total_cost = hp['Cost'].sum()
total_mins = hp['Minutes'].sum()
total_calls = hp['Calls'].sum()
date_range = f"{hp['Month'].min()} to {hp['Month'].max()}"

print(f"  Data Period:        {date_range}")
print(f"  Total Expenditure:  ${total_cost:,.2f}")
print(f"  Total Minutes:      {total_mins:,.0f}")
print(f"  Total Calls:        {total_calls:,}")
print(f"  Calculated CPM:     ${total_cost / total_mins:.4f}/min")

top = hp.groupby('Language')['Cost'].sum().sort_values(ascending=False).head(3)
print("  Top 3 Languages:")
for lang, cost in top.items():
    pct = cost / total_cost * 100
    print(f"    - {lang}: {pct:.1f}%")

print("\n" + "="*60)
print("DIFFERENCES SUMMARY")
print("="*60)

diff_cost = total_cost - 788400
diff_pct = (diff_cost / 788400) * 100

print(f"""
| Metric              | Consultant    | Pipeline       | Difference     |
|---------------------|---------------|----------------|----------------|
| Total Expenditure   | $788,400      | ${total_cost:,.0f}   | {'+' if diff_cost > 0 else ''}{diff_pct:.1f}%     |
| Total Minutes       | 788,400       | {total_mins:,.0f}    | -              |
| CPM                 | $1.00         | ${total_cost/total_mins:.2f}        | -              |
| Top Language        | Spanish 31.5% | See above      | -              |
""")

print("="*60)
print("CAUSES OF DIFFERENCES")
print("="*60)
print("""
1. DATA PERIOD MISMATCH
   - Consultant: "12 months ending November 2024"
   - Pipeline: """ + date_range + """
   - Our file may contain different/more months of data.

2. CONSULTANT USED ESTIMATES
   - Report says "approximately 13,140 hours"
   - Report says "approximately $788,400"
   - They likely extrapolated from a sample, not full data.

3. DUPLICATE REMOVAL
   - Our pipeline removed 131,589 duplicate records.
   - If consultant counted duplicates, their totals would be HIGHER.
   - If they manually excluded some, they may have undercounted.

4. FILE VERSION
   - The Excel file we processed may be a DIFFERENT VERSION
   - Consultants may have received a filtered/cleaned extract.

5. TOP LANGUAGE DIFFERENCE
   - Consultant: Spanish (31.5%)
   - Our data may show different distribution due to data period.
""")
