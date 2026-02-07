
import pandas as pd
from typing import List
from core.canonical_schema import CanonicalRecord

class AggregatorAgent:
    """
    Consumes CanonicalRecords and produces the Baseline Table (v1).
    """

    def create_baseline(self, records: List[CanonicalRecord]) -> pd.DataFrame:
        if not records:
            return pd.DataFrame()
            
        # Convert to DataFrame
        data = [
            {
                "Month": r.date.strftime("%Y-%m"), # Bucket by Month
                "Vendor": r.vendor,
                "Language": r.language,
                "Modality": r.modality,
                "Minutes": r.minutes_billed,
                "Cost": r.total_charge,
                "Calls": 1
            }
            for r in records
        ]
        
        df = pd.DataFrame(data)
        
        # Aggregate
        # Group by Month, Vendor, Language, Modality
        # Sum Minutes, Cost, Calls
        
        baseline = df.groupby(["Month", "Vendor", "Language", "Modality"]).agg({
            "Minutes": "sum",
            "Cost": "sum",
            "Calls": "sum"
        }).reset_index()
        
        # Calculate derived metrics
        baseline["CPM"] = (
            baseline["Cost"]
            .div(baseline["Minutes"])
            .replace([float("inf"), -float("inf")], 0.0)
            .fillna(0.0)
        )
        baseline["Avg_Call_Length"] = (
            baseline["Minutes"]
            .div(baseline["Calls"])
            .replace([float("inf"), -float("inf")], 0.0)
            .fillna(0.0)
        )
        
        # Sort
        baseline = baseline.sort_values(["Month", "Cost"], ascending=[True, False])
        
        return baseline
