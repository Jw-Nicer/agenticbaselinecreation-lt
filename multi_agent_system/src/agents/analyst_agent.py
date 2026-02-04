
import pandas as pd
from typing import Dict, Any, List

class AnalystAgent:
    """
    Performs 'Mix Analysis' and Variance Decomposition.
    Explains the 'Why' behind spend changes between months.
    Delivers v7/v8 of the baseline factory.
    """

    def analyze_variance(self, baseline_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculates Price-Volume-Mix (PVM) effects between consecutive months.
        
        Formulae used:
        - Price Effect: (Rate_new - Rate_old) * Volume_new
        - Volume Effect: (Volume_new - Volume_old) * Rate_old
        - Mix/Other: Total_Variance - (Price_Effect + Volume_Effect)
        """
        if baseline_df.empty or "Month" not in baseline_df.columns:
            return {"status": "Insufficient data"}

        # Get sorted list of months
        months = sorted(baseline_df["Month"].unique())
        if len(months) < 2:
            return {"status": "Need at least 2 consecutive months for variance analysis"}

        analysis_report = {}
        
        for i in range(1, len(months)):
            prior_m = months[i-1]
            curr_m = months[i]
            
            # Filter periods
            p_df = baseline_df[baseline_df["Month"] == prior_m].copy()
            c_df = baseline_df[baseline_df["Month"] == curr_m].copy()
            
            # Key for joining: Vendor, Language, Modality
            join_cols = ["Vendor", "Language", "Modality"]
            
            # Merge to align records
            merged = pd.merge(
                p_df, c_df, 
                on=join_cols, 
                suffixes=('_prior', '_curr'), 
                how='outer'
            ).fillna(0)
            
            # --- Decompose Variance ---
            
            # 1. Price Effect: Due to changes in the rate per minute
            # (CPM_curr - CPM_prior) * Minutes_curr
            merged["Price_Effect"] = (merged["CPM_curr"] - merged["CPM_prior"]) * merged["Minutes_curr"]
            
            # 2. Volume Effect: Due to changes in total minutes at the original rate
            # (Minutes_curr - Minutes_prior) * CPM_prior
            merged["Volume_Effect"] = (merged["Minutes_curr"] - merged["Minutes_prior"]) * merged["CPM_prior"]
            
            # 3. Total Variance
            merged["Total_Variance"] = merged["Cost_curr"] - merged["Cost_prior"]
            
            # 4. Mix/Other: The residual (e.g. impact of new vs dropped languages)
            merged["Mix_Other_Effect"] = merged["Total_Variance"] - (merged["Price_Effect"] + merged["Volume_Effect"])
            
            # Aggregate stats for the period
            month_stats = {
                "prior_month": prior_m,
                "current_month": curr_m,
                "total_variance": float(merged["Total_Variance"].sum()),
                "price_impact": float(merged["Price_Effect"].sum()),
                "volume_impact": float(merged["Volume_Effect"].sum()),
                "mix_impact": float(merged["Mix_Other_Effect"].sum()),
                "top_movers": self._get_top_movers(merged)
            }
            analysis_report[f"{prior_m} -> {curr_m}"] = month_stats

        return analysis_report

    def _get_top_movers(self, merged_df: pd.DataFrame) -> List[Dict]:
        """Identifies the biggest drivers of variance in the period."""
        # Sort by absolute variance
        movers = merged_df.reindex(merged_df.Total_Variance.abs().sort_values(ascending=False).index).head(5)
        
        results = []
        for _, row in movers.iterrows():
            results.append({
                "Vendor": row["Vendor"],
                "Language": row["Language"],
                "Modality": row["Modality"],
                "Variance": row["Total_Variance"]
            })
        return results

    def print_summary(self, analysis_results: Dict[str, Any]):
        """Prints a human-readable insight report."""
        print("\n=== ANALYST AGENT: VARIANCE DECOMPOSITION (v7/v8) ===")
        
        for period, data in analysis_results.items():
            if "status" in data: 
                print(f"Skipping {period}: {data['status']}")
                continue
            
            print(f"\nPeriod Comparison: {period}")
            print(f"  Total Spend Change: ${data['total_variance']:,.2f}")
            print(f"  -------------------------------------------")
            print(f"  1. Volume Effect: ${data['volume_impact']:>12,.2f}  (More/Less usage)")
            print(f"  2. Price Effect:  ${data['price_impact']:>12,.2f}  (Rate changes)")
            print(f"  3. Mix/Other:     ${data['mix_impact']:>12,.2f}  (Shifts in Language/Modality)")
            
            # Determine dominant factor
            impacts = [
                ("Volume", abs(data['volume_impact'])), 
                ("Price", abs(data['price_impact'])), 
                ("Mix", abs(data['mix_impact']))
            ]
            dominant = max(impacts, key=lambda x: x[1])[0]
            
            print(f"\n  INSIGHT: Spend change is primarily driven by {dominant} impact.")
            
            print(f"\n  Top Contributors to Change:")
            for m in data["top_movers"]:
                sign = "+" if m['Variance'] >= 0 else ""
                print(f"    - {m['Vendor']} | {m['Language']} | {m['Modality']}: {sign}${m['Variance']:,.2f}")
