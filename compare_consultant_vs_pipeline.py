"""
SIDE-BY-SIDE COMPARISON: Consultant vs. Pipeline
Analyzes HealthPoint data to compare against ERA's reported numbers.
"""

import pandas as pd
import os

# Paths
BASE_DIR = r"c:\Users\John\.gemini\antigravity\playground\multiagent-baseline-lt"
BASELINE_CSV = os.path.join(BASE_DIR, "baseline_v1_output.csv")
TRANSACTIONS_CSV = os.path.join(BASE_DIR, "baseline_transactions.csv")

print("="*70)
print("CONSULTANT vs PIPELINE: HealthPoint Comparison")
print("="*70)

# ============================================================================
# CONSULTANT'S NUMBERS (From HealthPoint Report)
# ============================================================================
print("\n" + "="*70)
print("CONSULTANT'S REPORTED NUMBERS (ERA Group)")
print("="*70)

consultant = {
    "report_date": "February 24, 2025",
    "data_period": "12 months ending November 2024",
    "annual_expenditure": 788400,  # $788,400
    "annual_hours": 13140,         # 13,140 hours
    "annual_minutes": 13140 * 60,  # Convert to minutes
    "top_language": "Spanish",
    "top_language_pct": 31.5,
    "vendor": "Propio"
}

print(f"Report Date:        {consultant['report_date']}")
print(f"Data Period:        {consultant['data_period']}")
print(f"Annual Expenditure: ${consultant['annual_expenditure']:,.2f}")
print(f"Annual Hours:       {consultant['annual_hours']:,} hrs ({consultant['annual_minutes']:,} mins)")
print(f"Implied CPM:        ${consultant['annual_expenditure'] / consultant['annual_minutes']:.4f}/min")
print(f"Top Language:       {consultant['top_language']} ({consultant['top_language_pct']}%)")

# ============================================================================
# PIPELINE'S NUMBERS (From our processed data)
# ============================================================================
print("\n" + "="*70)
print("PIPELINE'S CALCULATED NUMBERS")
print("="*70)

# Load baseline (aggregated)
baseline = pd.read_csv(BASELINE_CSV)

# Filter to Healthpoint only
hp = baseline[baseline['Vendor'].str.contains('Healthpoint', case=False, na=False)]

if len(hp) == 0:
    print("WARNING: No Healthpoint data found in baseline. Checking vendor names...")
    print(f"Vendors in baseline: {baseline['Vendor'].unique()}")
else:
    pipeline = {
        "total_rows": len(hp),
        "total_cost": hp['Cost'].sum(),
        "total_minutes": hp['Minutes'].sum(),
        "total_calls": hp['Calls'].sum(),
        "date_range": f"{hp['Month'].min()} to {hp['Month'].max()}"
    }
    
    print(f"Data Period:        {pipeline['date_range']}")
    print(f"Total Expenditure:  ${pipeline['total_cost']:,.2f}")
    print(f"Total Minutes:      {pipeline['total_minutes']:,.0f}")
    print(f"Total Hours:        {pipeline['total_minutes']/60:,.0f}")
    print(f"Total Calls:        {pipeline['total_calls']:,}")
    print(f"Calculated CPM:     ${pipeline['total_cost'] / pipeline['total_minutes']:.4f}/min")
    
    # Top Language
    lang_breakdown = hp.groupby('Language')['Cost'].sum().sort_values(ascending=False)
    top_lang = lang_breakdown.index[0]
    top_lang_pct = (lang_breakdown.iloc[0] / lang_breakdown.sum()) * 100
    print(f"Top Language:       {top_lang} ({top_lang_pct:.1f}%)")
    
    # Modality
    modality_breakdown = hp.groupby('Modality')['Cost'].sum()
    print(f"\nModality Breakdown:")
    for mod, cost in modality_breakdown.items():
        pct = (cost / hp['Cost'].sum()) * 100
        print(f"  {mod}: ${cost:,.2f} ({pct:.1f}%)")

# ============================================================================
# SIDE-BY-SIDE COMPARISON
# ============================================================================
print("\n" + "="*70)
print("SIDE-BY-SIDE COMPARISON")
print("="*70)

print(f"\n{'Metric':<25} | {'Consultant':>15} | {'Pipeline':>15} | {'Difference':>15}")
print("-"*70)

if len(hp) > 0:
    # Expenditure
    diff_cost = pipeline['total_cost'] - consultant['annual_expenditure']
    diff_cost_pct = (diff_cost / consultant['annual_expenditure']) * 100
    print(f"{'Annual Expenditure':<25} | ${consultant['annual_expenditure']:>14,} | ${pipeline['total_cost']:>14,.0f} | {'+' if diff_cost > 0 else ''}{diff_cost_pct:>13.1f}%")
    
    # Minutes
    diff_mins = pipeline['total_minutes'] - consultant['annual_minutes']
    diff_mins_pct = (diff_mins / consultant['annual_minutes']) * 100
    print(f"{'Total Minutes':<25} | {consultant['annual_minutes']:>15,} | {pipeline['total_minutes']:>15,.0f} | {'+' if diff_mins > 0 else ''}{diff_mins_pct:>13.1f}%")
    
    # CPM
    consultant_cpm = consultant['annual_expenditure'] / consultant['annual_minutes']
    pipeline_cpm = pipeline['total_cost'] / pipeline['total_minutes']
    diff_cpm = pipeline_cpm - consultant_cpm
    print(f"{'CPM (Cost/Min)':<25} | ${consultant_cpm:>14.4f} | ${pipeline_cpm:>14.4f} | {'+' if diff_cpm > 0 else ''}{diff_cpm:>13.4f}")
    
    # Top Language
    print(f"{'Top Language':<25} | {consultant['top_language']:>15} | {top_lang:>15} | {'MATCH' if top_lang == consultant['top_language'] else 'DIFF'}")

# ============================================================================
# ANALYSIS OF DIFFERENCES
# ============================================================================
print("\n" + "="*70)
print("ANALYSIS OF DIFFERENCES")
print("="*70)

if len(hp) > 0:
    print(f"""
CAUSE 1: DATA PERIOD MISMATCH
  - Consultant analyzed: "12 months ending November 2024"
  - Pipeline processed:  "{pipeline['date_range']}"
  - Our data may include different months or more transactions.

CAUSE 2: CONSULTANT USED "ESTIMATED" ANNUAL FIGURES
  - Consultant states: "estimated annual utilization... approximately 13,140 hours"
  - Consultant states: "annual expenditure approximately $788,400"
  - The word "approximately" means they may have extrapolated.
  - Pipeline uses ACTUAL transaction data (227,272 records).

CAUSE 3: DUPLICATE HANDLING
  - Pipeline removed 131,589 duplicate records.
  - If consultant didn't detect duplicates, their totals would be inflated.
  - OR if they used the raw file, they may have manually excluded some rows.

CAUSE 4: DATA SOURCE DIFFERENCES
  - Consultant: "Propio transaction activity for the 12 months ending November 2024"
  - Pipeline: Processed the full "Healthpoint - Propio Transaction Download.xlsx"
  - The Excel file may contain MORE data than what consultant analyzed.
""")

# Count transactions by month
print("\nTRANSACTION COUNT BY MONTH (Our Pipeline):")
print(hp.groupby('Month')['Calls'].sum().sort_index())
