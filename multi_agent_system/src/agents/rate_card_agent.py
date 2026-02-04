
import pandas as pd
from typing import Optional, Dict, Tuple
from core.canonical_schema import CanonicalRecord

class RateCardAgent:
    """
    Validates cost data and flags missing costs.
    
    IMPORTANT: This agent does NOT impute costs with estimated rates.
    It only works with data that exists in the source files.
    
    If a file has no cost column, records are flagged as "cost_missing"
    for human review - they are NOT filled with fake numbers.
    """
    
    def __init__(self):
        # No default rates - we only use file data
        self.rate_card = {}
        
    def _load_default_rates(self) -> Dict[Tuple, float]:
        """
        REMOVED: We no longer use placeholder rates.
        Rates must come from actual contract data or be left empty.
        """
        return {}
    
    def add_rate(self, vendor: str, modality: str, language: Optional[str], rate: float):
        """Add a verified contract rate (only if you have documentation)."""
        key = (vendor, modality, language)
        self.rate_card[key] = rate
        
    def get_rate(self, vendor: str, modality: str, language: str) -> Optional[float]:
        """
        Look up a verified rate.
        Returns None if no verified rate exists.
        """
        # Try exact match
        if (vendor, modality, language) in self.rate_card:
            return self.rate_card[(vendor, modality, language)]
        
        # Try vendor + modality
        if (vendor, modality, None) in self.rate_card:
            return self.rate_card[(vendor, modality, None)]
        
        # No guessing - return None if no verified rate
        return None
    
    def validate_cost(self, record: CanonicalRecord) -> CanonicalRecord:
        """
        Validate that a record has cost data.
        If cost is missing, FLAG it - do not impute.
        """
        if record.minutes_billed > 0 and record.total_charge == 0.0:
            # Cost is missing - FLAG it, don't fake it
            if record.raw_columns is None:
                record.raw_columns = {}
            record.raw_columns['_cost_status'] = 'MISSING'
            record.raw_columns['_cost_note'] = 'Source file has no cost column'
            record.confidence_score = 0.5  # Lower confidence
        else:
            # Cost exists in file
            if record.raw_columns is None:
                record.raw_columns = {}
            record.raw_columns['_cost_status'] = 'FROM_FILE'
        
        return record
    
    def batch_impute(self, records: list[CanonicalRecord]) -> Tuple[list[CanonicalRecord], Dict]:
        """
        Process records and identify those with missing costs.
        NO IMPUTATION with fake numbers - only flagging.
        """
        stats = {
            'total_records': len(records),
            'records_with_cost': 0,
            'records_missing_cost': 0,
            'imputed_count': 0,  # Always 0 now - we don't impute
            'imputed_total_cost': 0.0,  # Always 0 now
            'missing_cost_vendors': set()
        }
        
        updated_records = []
        
        for record in records:
            updated_record = self.validate_cost(record)
            
            if record.total_charge > 0:
                stats['records_with_cost'] += 1
            elif record.minutes_billed > 0:
                stats['records_missing_cost'] += 1
                stats['missing_cost_vendors'].add(record.vendor)
            
            updated_records.append(updated_record)
        
        # Convert set to list for JSON serialization
        stats['missing_cost_vendors'] = list(stats['missing_cost_vendors'])
        
        return updated_records, stats
    
    def export_rate_card(self, filepath: str):
        """Export verified rates (if any) to CSV."""
        if not self.rate_card:
            print("No verified rates configured. Rate card is empty.")
            print("To add rates, use add_rate() with verified contract data.")
            return
            
        rows = []
        for (vendor, modality, language), rate in self.rate_card.items():
            rows.append({
                'Vendor': vendor or 'ANY',
                'Modality': modality or 'ANY',
                'Language': language or 'ANY',
                'Rate_Per_Minute': rate
            })
        
        df = pd.DataFrame(rows)
        df.to_csv(filepath, index=False)
        print(f"Rate card exported to: {filepath}")
    
    def import_rate_card(self, filepath: str):
        """Import verified rates from a CSV file."""
        df = pd.read_csv(filepath)
        
        for _, row in df.iterrows():
            vendor = None if row['Vendor'] == 'ANY' else row['Vendor']
            modality = None if row['Modality'] == 'ANY' else row['Modality']
            language = None if row['Language'] == 'ANY' else row['Language']
            rate = float(row['Rate_Per_Minute'])
            
            self.rate_card[(vendor, modality, language)] = rate
        
        print(f"Imported {len(df)} verified rates from: {filepath}")