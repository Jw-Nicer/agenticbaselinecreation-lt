"""
REPORT GENERATOR AGENT (Prototype)
Produces a consultant-style baseline report from pipeline output.

This agent learns from the ERA consultant report format and generates
similar professional output automatically.
"""

import pandas as pd
from datetime import datetime
import os
from pathlib import Path

class ReportGeneratorAgent:
    """Generates a professional baseline report from pipeline output."""
    
    def __init__(self, baseline_csv: str = None, transactions_csv: str = None):
        if baseline_csv:
            self.baseline = pd.read_csv(baseline_csv)
        else:
            self.baseline = None
            
        if transactions_csv:
            self.transactions = pd.read_csv(transactions_csv)
        else:
            self.transactions = None
            
        self.report_lines = []
        
    def add_line(self, text: str = ""):
        self.report_lines.append(text)
        
    def add_section(self, title: str):
        self.add_line()
        self.add_line("=" * 70)
        self.add_line(title)
        self.add_line("=" * 70)
        
    def generate_executive_summary(self):
        """Section 1: Executive Summary"""
        self.add_section("1. EXECUTIVE SUMMARY")
        
        total_spend = self.baseline['Cost'].sum()
        total_mins = self.baseline['Minutes'].sum()
        total_calls = self.baseline['Calls'].sum()
        date_min = self.baseline['Month'].min()
        date_max = self.baseline['Month'].max()
        num_vendors = self.baseline['Vendor'].nunique()
        num_languages = self.baseline['Language'].nunique()
        
        self.add_line()
        self.add_line("This automated baseline report provides a comprehensive analysis of")
        self.add_line("Language Interpretation and Translation Services expenditure.")
        self.add_line()
        self.add_line("KEY METRICS:")
        self.add_line(f"  • Data Period:        {date_min} to {date_max}")
        self.add_line(f"  • Total Expenditure:  ${total_spend:,.2f}")
        self.add_line(f"  • Total Minutes:      {total_mins:,.0f} ({total_mins/60:,.0f} hours)")
        self.add_line(f"  • Total Calls:        {total_calls:,}")
        self.add_line(f"  • Average CPM:        ${total_spend/total_mins:.4f}")
        self.add_line(f"  • Vendors:            {num_vendors}")
        self.add_line(f"  • Languages:          {num_languages}")
        
    def generate_vendor_summary(self):
        """Section 2: Vendor Summary"""
        self.add_section("2. VENDOR SUMMARY")
        
        vendor_summary = self.baseline.groupby('Vendor').agg({
            'Cost': 'sum',
            'Minutes': 'sum',
            'Calls': 'sum'
        }).sort_values('Cost', ascending=False)
        
        total_spend = self.baseline['Cost'].sum()
        
        self.add_line()
        self.add_line(f"{'Vendor':<30} | {'Spend':>14} | {'% of Total':>10} | {'Minutes':>12}")
        self.add_line("-" * 75)
        
        for vendor, row in vendor_summary.iterrows():
            pct = row['Cost'] / total_spend * 100
            self.add_line(f"{vendor[:30]:<30} | ${row['Cost']:>13,.0f} | {pct:>9.1f}% | {row['Minutes']:>12,.0f}")
            
    def generate_top_languages(self, top_n: int = 10):
        """Section 3: Top Languages"""
        self.add_section(f"3. TOP {top_n} LANGUAGES BY SPEND")
        
        lang_summary = self.baseline.groupby('Language').agg({
            'Cost': 'sum',
            'Minutes': 'sum',
            'Calls': 'sum'
        }).sort_values('Cost', ascending=False).head(top_n)
        
        total_spend = self.baseline['Cost'].sum()
        
        self.add_line()
        self.add_line(f"{'Rank':<6} | {'Language':<25} | {'Spend':>14} | {'% Total':>8} | {'CPM':>8}")
        self.add_line("-" * 75)
        
        for i, (lang, row) in enumerate(lang_summary.iterrows(), 1):
            pct = row['Cost'] / total_spend * 100
            cpm = row['Cost'] / row['Minutes'] if row['Minutes'] > 0 else 0
            self.add_line(f"{i:<6} | {lang[:25]:<25} | ${row['Cost']:>13,.0f} | {pct:>7.1f}% | ${cpm:>7.2f}")
            
    def generate_modality_analysis(self):
        """Section 4: Modality Breakdown"""
        self.add_section("4. MODALITY ANALYSIS")
        
        modality_summary = self.baseline.groupby('Modality').agg({
            'Cost': 'sum',
            'Minutes': 'sum',
            'Calls': 'sum'
        }).sort_values('Cost', ascending=False)
        
        total_spend = self.baseline['Cost'].sum()
        total_mins = self.baseline['Minutes'].sum()
        
        self.add_line()
        self.add_line(f"{'Modality':<15} | {'Spend':>14} | {'% Spend':>8} | {'Minutes':>12} | {'% Mins':>8} | {'CPM':>8}")
        self.add_line("-" * 80)
        
        for modality, row in modality_summary.iterrows():
            pct_spend = row['Cost'] / total_spend * 100
            pct_mins = row['Minutes'] / total_mins * 100
            cpm = row['Cost'] / row['Minutes'] if row['Minutes'] > 0 else 0
            self.add_line(f"{modality:<15} | ${row['Cost']:>13,.0f} | {pct_spend:>7.1f}% | {row['Minutes']:>12,.0f} | {pct_mins:>7.1f}% | ${cpm:>7.2f}")
            
    def generate_monthly_trends(self):
        """Section 5: Monthly Trend Analysis"""
        self.add_section("5. MONTHLY TREND ANALYSIS")
        
        monthly = self.baseline.groupby('Month').agg({
            'Cost': 'sum',
            'Minutes': 'sum',
            'Calls': 'sum'
        }).sort_index()
        
        monthly['CPM'] = monthly['Cost'] / monthly['Minutes']
        monthly['MoM_Change'] = monthly['Cost'].pct_change() * 100
        
        self.add_line()
        self.add_line(f"{'Month':<10} | {'Spend':>14} | {'Minutes':>12} | {'Calls':>10} | {'CPM':>8} | {'MoM %':>8}")
        self.add_line("-" * 75)
        
        for month, row in monthly.iterrows():
            mom = f"{row['MoM_Change']:+.1f}%" if pd.notna(row['MoM_Change']) else "N/A"
            self.add_line(f"{month:<10} | ${row['Cost']:>13,.0f} | {row['Minutes']:>12,.0f} | {row['Calls']:>10,.0f} | ${row['CPM']:>7.2f} | {mom:>8}")
            
    def generate_baseline_rates(self):
        """Section 6: Baseline Rate Analysis"""
        self.add_section("6. BASELINE RATE ANALYSIS")
        
        # Group languages into tiers based on volume
        lang_summary = self.baseline.groupby('Language').agg({
            'Cost': 'sum',
            'Minutes': 'sum'
        })
        lang_summary['CPM'] = lang_summary['Cost'] / lang_summary['Minutes']
        
        total_mins = lang_summary['Minutes'].sum()
        lang_summary['Pct'] = lang_summary['Minutes'] / total_mins * 100
        
        # Define tiers
        tier1 = lang_summary[lang_summary['Pct'] >= 5].sort_values('Minutes', ascending=False)
        tier2 = lang_summary[(lang_summary['Pct'] >= 1) & (lang_summary['Pct'] < 5)].sort_values('Minutes', ascending=False)
        rare = lang_summary[lang_summary['Pct'] < 1].sort_values('Minutes', ascending=False)
        
        self.add_line()
        self.add_line("Languages grouped by utilization tier:")
        self.add_line()
        
        # Tier 1
        self.add_line("TIER 1 (≥5% of volume):")
        for lang, row in tier1.iterrows():
            self.add_line(f"  • {lang}: {row['Minutes']:,.0f} mins ({row['Pct']:.1f}%) @ ${row['CPM']:.2f}/min")
            
        self.add_line()
        self.add_line("TIER 2 (1-5% of volume):")
        for lang, row in tier2.head(5).iterrows():
            self.add_line(f"  • {lang}: {row['Minutes']:,.0f} mins ({row['Pct']:.1f}%) @ ${row['CPM']:.2f}/min")
        if len(tier2) > 5:
            self.add_line(f"  ... and {len(tier2)-5} more languages")
            
        self.add_line()
        self.add_line(f"RARE LANGUAGES (<1% of volume): {len(rare)} languages")
        avg_rare_cpm = rare['Cost'].sum() / rare['Minutes'].sum() if rare['Minutes'].sum() > 0 else 0
        self.add_line(f"  • Average CPM for rare languages: ${avg_rare_cpm:.2f}")
        
    def generate_full_report(self) -> str:
        """Generate the complete report."""
        self.report_lines = []
        
        # Header
        self.add_line("=" * 70)
        self.add_line("LANGUAGE SERVICES BASELINE REPORT")
        self.add_line(f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}")
        self.add_line("=" * 70)
        
        # Sections
        self.generate_executive_summary()
        self.generate_vendor_summary()
        self.generate_top_languages()
        self.generate_modality_analysis()
        self.generate_monthly_trends()
        self.generate_baseline_rates()
        
        # Footer
        self.add_line()
        self.add_section("APPENDIX: DATA QUALITY NOTES")
        self.add_line()
        self.add_line("This report was generated automatically by the Multi-Agent Baseline Pipeline.")
        self.add_line("All figures are calculated from raw transaction data, not estimates.")
        self.add_line()
        self.add_line("For questions about methodology, see: AGENT_ACTIVITY_LOG.md")
        self.add_line("For full audit trail, see: baseline_transactions.csv")
        
        return "\n".join(self.report_lines)
    
    def save_report(self, filepath: str):
        """Save report to file."""
        report = self.generate_full_report()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Report saved to: {filepath}")
        return report


# Run the agent
if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parents[2]
    
    agent = ReportGeneratorAgent(
        baseline_csv=os.path.join(BASE_DIR, "baseline_v1_output.csv"),
        transactions_csv=os.path.join(BASE_DIR, "baseline_transactions.csv")
    )
    
    report = agent.save_report(os.path.join(BASE_DIR, "BASELINE_REPORT.txt"))
    print("\n" + "="*70)
    print("REPORT PREVIEW (First 100 lines):")
    print("="*70)
    for line in report.split("\n")[:100]:
        print(line)
