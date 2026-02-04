
import pandas as pd
from typing import List, Dict, Any

class SimulatorAgent:
    """
    Runs 'What-If' scenarios to identify savings opportunities.
    Delivers v10 of the baseline factory.
    """

    def __init__(self, target_opi_rate: float = 0.70, target_vri_rate: float = 0.90):
        self.target_opi_rate = target_opi_rate
        self.target_vri_rate = target_vri_rate

    def run_scenarios(self, baseline_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Executes simulations across the entire baseline.
        """
        if baseline_df.empty:
            return {"status": "No data to simulate", "total_actual_cost": 0.0, "scenarios": {}}

        results = {
            "total_actual_cost": float(baseline_df["Cost"].sum()),
            "scenarios": {}
        }

        # --- Scenario 1: Rate Normalization ---
        results["scenarios"]["rate_normalization"] = self._simulate_rate_normalization(baseline_df)

        # --- Scenario 2: Modality Shift (VRI -> OPI) ---
        results["scenarios"]["vri_to_opi_shift"] = self._simulate_modality_shift(baseline_df, shift_pct=0.25)

        return results

    def _simulate_rate_normalization(self, df: pd.DataFrame) -> Dict:
        """Calculates savings if all rates were capped at target levels."""
        sim_df = df.copy()
        
        # Apply caps based on modality
        def get_target(row):
            if row["Modality"] == "VRI": return self.target_vri_rate
            if row["Modality"] == "OPI": return self.target_opi_rate
            return row["CPM"]

        sim_df["Target_CPM"] = sim_df.apply(get_target, axis=1)
        sim_df["Target_Cost"] = sim_df["Minutes"] * sim_df["Target_CPM"]
        
        # Potential savings is current cost minus target cost (if target is lower)
        sim_df["Potential_Savings"] = (sim_df["Cost"] - sim_df["Target_Cost"]).clip(lower=0)
        
        total_savings = sim_df["Potential_Savings"].sum()
        
        return {
            "name": "Standardize Rates",
            "description": f"Cap OPI at ${self.target_opi_rate:.2f}/min and VRI at ${self.target_vri_rate:.2f}/min",
            "annual_impact": float(total_savings),
            "savings_pct": float(total_savings / df["Cost"].sum() * 100) if df["Cost"].sum() > 0 else 0
        }

    def _simulate_modality_shift(self, df: pd.DataFrame, shift_pct: float) -> Dict:
        """Calculates savings from shifting expensive VRI minutes to cheaper OPI."""
        vri_records = df[df["Modality"] == "VRI"]
        if vri_records.empty:
            return {"name": "VRI Shift", "description": "No VRI usage data found for this vendor.", "annual_impact": 0.0, "status": "No VRI volume found"}

        vri_total_cost = vri_records["Cost"].sum()
        vri_minutes = vri_records["Minutes"].sum()
        current_vri_cpm = vri_total_cost / vri_minutes

        # Calculate OPI average from the data as the landing rate
        opi_records = df[df["Modality"] == "OPI"]
        if not opi_records.empty:
            opi_cpm = opi_records["Cost"].sum() / opi_records["Minutes"].sum()
        else:
            opi_cpm = self.target_opi_rate
        
        minutes_to_shift = vri_minutes * shift_pct
        savings = minutes_to_shift * (current_vri_cpm - opi_cpm)
        
        return {
            "name": f"{int(shift_pct*100)}% VRI to OPI Shift",
            "description": f"Transition {int(shift_pct*100)}% of video interpretation back to audio interpretation",
            "annual_impact": float(max(0, savings)),
            "savings_pct": float(max(0, savings) / df["Cost"].sum() * 100) if df["Cost"].sum() > 0 else 0
        }

    def print_opportunity_register(self, results: Dict):
        print("\n=== SIMULATOR AGENT: OPPORTUNITY REGISTER (v10) ===")
        print(f"Baseline Portfolio Spend: ${results['total_actual_cost']:,.2f}")
        print("-" * 65)
        
        for key, data in results["scenarios"].items():
            if "annual_impact" in data:
                print(f"Project: {data['name']}")
                print(f"  Description: {data['description']}")
                print(f"  Estimated Savings Opportunity: ${data['annual_impact']:,.2f}")
                print(f"  % of Total Spend: {data.get('savings_pct', 0):.1f}%")
                print("")
