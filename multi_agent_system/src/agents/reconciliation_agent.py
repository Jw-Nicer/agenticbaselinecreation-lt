
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from core.canonical_schema import CanonicalRecord

class ReconciliationAgent:
    """
    Compares the sum of line-item records (Bottom-Up) against invoice totals (Top-Down).
    Delivers the "v3 Invoices" layer for financial integrity.
    """

    def __init__(self):
        self.billed_totals = {} # vendor -> total

    def extract_totals_from_sheets(self, sheets: Dict[str, pd.DataFrame], vendor: str):
        """
        Scans all sheets for a spreadsheet to find the 'Ground Truth' billed total.
        Look for sheets named 'Invoice', 'Summary', 'Total'.
        """
        keywords = ["total amount due", "grand total", "total charges", "invoice total", "amount due", "net amount"]
        
        for sheet_name, df in sheets.items():
            # Priority to sheets named 'Invoice' or 'Summary'
            is_summary_sheet = any(s in sheet_name.lower() for s in ["invoice", "summary", "total", "billing"])
            
            # Flatten and search
            data_list = df.astype(str).values.flatten().tolist()
            
            for i, val in enumerate(data_list):
                if pd.isna(val):
                    continue
                cleaned_val = str(val).lower().strip()
                if any(k in cleaned_val for k in keywords):
                    # Look in subsequent cells for a float
                    for offset in range(1, 10):
                        if i + offset >= len(data_list): break
                        try:
                            pot_str = data_list[i + offset].replace('$', '').replace(',', '').strip()
                            if pot_str and pot_str != 'nan':
                                amount = float(pot_str)
                                if amount > 5.0: # Ignore tiny amounts that aren't totals
                                    # If we find multiple, we usually want the largest one on an invoice sheet
                                    current_best = self.billed_totals.get(vendor, 0.0)
                                    if amount > current_best or is_summary_sheet:
                                        self.billed_totals[vendor] = amount
                                        break 
                        except ValueError:
                            continue

    def run_reconciliation(self, records: List[CanonicalRecord]) -> Dict[str, Any]:
        """
        Strategic comparison of standardized results vs billed reality.
        """
        # Group by vendor
        vendor_data = {}
        for r in records:
            if r.vendor not in vendor_data:
                vendor_data[r.vendor] = {"calc_total": 0.0, "calc_minutes": 0.0, "record_count": 0}
            vendor_data[r.vendor]["calc_total"] += r.total_charge
            vendor_data[r.vendor]["calc_minutes"] += r.minutes_billed
            vendor_data[r.vendor]["record_count"] += 1

        results = {
            "overall_status": "MATCH",
            "vendors": {},
            "total_variance": 0.0
        }

        for vendor, stats in vendor_data.items():
            billed = self.billed_totals.get(vendor, 0.0)
            calculated = stats["calc_total"]
            
            variance = calculated - billed
            var_pct = (variance / billed * 100) if billed > 0 else 0.0
            
            # Threshold for status
            status = "MATCH"
            if billed == 0:
                status = "NO_INVOICE_FOUND"
            elif abs(var_pct) > 2.0: # 2% variance threshold
                status = "DISCREPANCY"
                results["overall_status"] = "ALERT"

            results["vendors"][vendor] = {
                "calculated": round(calculated, 2),
                "billed": round(billed, 2),
                "variance": round(variance, 2),
                "variance_pct": round(var_pct, 2),
                "record_count": stats["record_count"],
                "status": status
            }
            results["total_variance"] += abs(variance)

        return results
