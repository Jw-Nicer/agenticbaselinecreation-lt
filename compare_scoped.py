import pandas as pd

baseline = pd.read_csv('baseline_v1_output.csv')
hp = baseline[baseline['Vendor'].str.contains('Healthpoint', case=False, na=False)]

print("="*70)
print("ADJUSTED COMPARISON: Matching Consultant's Scope")
print("="*70)

# Consultant's scope: 12 months ending November 2024
# This means: December 2023 through November 2024
scope_months = ['2023-12', '2024-01', '2024-02', '2024-03', '2024-04', '2024-05',
                '2024-06', '2024-07', '2024-08', '2024-09', '2024-10', '2024-11']

# Filter to matching scope
hp_scoped = hp[hp['Month'].isin(scope_months)]

print(f"\nSCOPE ADJUSTMENT:")
print(f"  Consultant Period: Dec 2023 - Nov 2024 (12 months)")
print(f"  Filtering to:      {scope_months[0]} to {scope_months[-1]}")
print(f"  Original records:  {len(hp):,}")
print(f"  After filter:      {len(hp_scoped):,}")

# Calculate metrics
total_cost = hp_scoped['Cost'].sum()
total_mins = hp_scoped['Minutes'].sum()
total_calls = hp_scoped['Calls'].sum()
cpm = total_cost / total_mins if total_mins > 0 else 0

# Consultant values
consultant_cost = 788400
consultant_hours = 13140
consultant_mins = consultant_hours * 60  # 788,400 minutes

print("\n" + "="*70)
print("APPLES-TO-APPLES COMPARISON (Same 12-Month Period)")
print("="*70)
print(f"""
| Metric              | Consultant    | Pipeline       | Difference     |
|---------------------|---------------|----------------|----------------|
| Total Expenditure   | ${consultant_cost:,}      | ${total_cost:,.0f}   | {((total_cost - consultant_cost) / consultant_cost * 100):+.1f}%       |
| Total Minutes       | {consultant_mins:,}       | {total_mins:,.0f}    | {((total_mins - consultant_mins) / consultant_mins * 100):+.1f}%       |
| Total Hours         | {consultant_hours:,}        | {total_mins/60:,.0f}         | {((total_mins/60 - consultant_hours) / consultant_hours * 100):+.1f}%       |
| CPM                 | $1.00         | ${cpm:.2f}          | {((cpm - 1.0) / 1.0 * 100):+.1f}%       |
""")

# Top languages
print("TOP LANGUAGES COMPARISON:")
top = hp_scoped.groupby('Language')['Cost'].sum().sort_values(ascending=False).head(5)
total = hp_scoped['Cost'].sum()
print(f"\n  Consultant says: Spanish (31.5%), Dari (19.5%), Pashto, Portuguese")
print(f"\n  Pipeline (same period):")
for lang, cost in top.items():
    pct = cost / total * 100
    print(f"    - {lang}: {pct:.1f}%")

# Detailed month-by-month breakdown
print("\n" + "="*70)
print("MONTH-BY-MONTH BREAKDOWN (Pipeline)")
print("="*70)
monthly = hp_scoped.groupby('Month').agg({
    'Cost': 'sum',
    'Minutes': 'sum',
    'Calls': 'sum'
}).sort_index()
monthly['CPM'] = monthly['Cost'] / monthly['Minutes']

print(f"\n{'Month':<10} | {'Cost':>12} | {'Minutes':>10} | {'Calls':>8} | {'CPM':>8}")
print("-" * 60)
for month, row in monthly.iterrows():
    print(f"{month:<10} | ${row['Cost']:>11,.0f} | {row['Minutes']:>10,.0f} | {row['Calls']:>8,.0f} | ${row['CPM']:>7.2f}")

print("-" * 60)
print(f"{'TOTAL':<10} | ${total_cost:>11,.0f} | {total_mins:>10,.0f} | {total_calls:>8,.0f} | ${cpm:>7.2f}")

# Remaining difference analysis
print("\n" + "="*70)
print("REMAINING DIFFERENCE ANALYSIS")
print("="*70)

diff_cost = total_cost - consultant_cost
diff_mins = total_mins - consultant_mins

print(f"""
After matching the scope (Dec 2023 - Nov 2024):

EXPENDITURE:
  Consultant: ${consultant_cost:,}
  Pipeline:   ${total_cost:,.0f}
  Difference: ${diff_cost:,.0f} ({diff_cost/consultant_cost*100:+.1f}%)

MINUTES:
  Consultant: {consultant_mins:,} ({consultant_hours:,} hours)
  Pipeline:   {total_mins:,.0f} ({total_mins/60:,.0f} hours)
  Difference: {diff_mins:,.0f} mins ({diff_mins/consultant_mins*100:+.1f}%)

POSSIBLE REMAINING CAUSES:
1. Consultant may have received a FILTERED data extract (not raw transactions)
2. Consultant may have applied EXCLUSIONS we're not aware of
3. Different duplicate detection methodology
4. Rounding/estimation in consultant's "approximately" figures
""")
