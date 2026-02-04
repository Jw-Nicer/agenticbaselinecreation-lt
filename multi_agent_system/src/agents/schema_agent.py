
import pandas as pd
import re
from typing import Dict, List, Any
from core.canonical_schema import CANONICAL_FIELDS

class SchemaAgent:
    """
    Agent responsible for deducing the map between Raw Excel Columns -> Canonical Schema.
    It uses heuristic fuzzy matching/keyword searching to generate a mapping strategy.
    """
    
    def __init__(self):
        self.known_mappings = {}

    def clean_header(self, header: str) -> str:
        """Strip and lowercase header for easier matching."""
        if not isinstance(header, str):
            return str(header)
        return header.strip().lower().replace('\n', ' ').replace('.', '')

    def infer_mapping(self, source_columns: List[str], sample_row: pd.Series = None) -> Dict[str, str]:
        """
        Given a list of columns from a raw file (and an optional sample row for value type checking),
        returns a dictionary mapping CanonicalField -> SourceColumn.
        """
        mapping = {}
        
        # Pre-process source columns
        cleaned_source = {col: self.clean_header(col) for col in source_columns}
        
        # 1. Direct Keyword Matching
        for canonical_field, keywords in CANONICAL_FIELDS.items():
            best_match = None
            
            for col_original, col_clean in cleaned_source.items():
                # Check exact keyword matches first
                if col_clean in keywords:
                    best_match = col_original
                    break
                
                # Check fuzzy contains
                for kw in keywords:
                    # Specific check to avoid matching "Rate" with "Corporate" or similar if we weren't careful
                    # But "Total Charge" contains "Charge", so we iterate carefully
                    if kw in col_clean:
                         # Prioritize "Total Charge" over "Charge" if both exist? 
                         # Simple logic: if we haven't found a match yet, take it.
                         if not best_match:
                             best_match = col_original
            
            if best_match:
                mapping[canonical_field] = best_match
        
        # 2. Heuristic Refinements (The "Agent" Logic)
        
        # HEURISTIC: Minutes vs Seconds. 
        # If we mapped 'minutes', check if the sample value looks like a timestamp (00:05) or float (5.0)
        # That logic happens during extraction, but the Mapper informs which col to look at.
        
        # HEURISTIC: "Connect Time" is often the minutes column if no explicit "Minutes" exists
        if "minutes" not in mapping:
            for col, clean in cleaned_source.items():
                if "connect" in clean and "time" in clean:
                    mapping["minutes"] = col
                    break
        
        # HEURISTIC: "Min Billed" is a strong candidate for minutes
        if "minutes" not in mapping:
             for col, clean in cleaned_source.items():
                if "min billed" in clean:
                    mapping["minutes"] = col
        
        # HEURISTIC: "Charges" often means total charge
        if "charge" not in mapping:
            for col, clean in cleaned_source.items():
                if "charges" in clean:
                    mapping["charge"] = col
        
        return mapping

    def validate_mapping(self, mapping: Dict[str, str]) -> float:
        """Returns a confidence score (0-1) for this mapping."""
        required = ["date", "language", "minutes"]
        optional = ["charge", "cost"]  # Either is acceptable
        hits = sum(1 for field in required if field in mapping)
        # Cost can be in either 'charge' or 'cost' key
        if any(field in mapping for field in optional):
            hits += 1
        return hits / (len(required) + 1)
    
    def get_mapping_confidence(self, mapping: Dict[str, str]) -> float:
        """Alias for validate_mapping for API consistency."""
        return self.validate_mapping(mapping)
