
import pandas as pd
import datetime
import re
from typing import List, Dict, Any
from core.canonical_schema import CanonicalRecord


class StandardizerAgent:
    """
    Takes a raw DataFrame + a Schema Mapping and produces a list of CanonicalRecords.
    Handles data type conversion (strings to floats, parsing dates).
    """

    def process_dataframe(self, df: pd.DataFrame, mapping: Dict[str, str], source_file: str, vendor: str) -> List[CanonicalRecord]:
        # Check required columns
        req_cols = ["language", "date"] # Minimal Requirement
        for rc in req_cols:
            if rc not in mapping:
                # Can't process this sheet
                return []
        
        # Make a working copy to avoid modifying original
        work_df = df.copy()
        
        # VECTORIZED OPERATIONS: Process all rows at once
        
        # 1. Parse Dates (vectorized)
        date_col = mapping.get("date")
        work_df['_clean_date'] = work_df[date_col].apply(self._parse_date)
        
        # 2. Parse Language (vectorized)
        lang_col = mapping.get("language")
        work_df['_clean_language'] = work_df[lang_col].astype(str).str.strip()
        
        # 3. Parse Minutes (vectorized)
        mins_col = mapping.get("minutes")
        if mins_col:
            work_df['_clean_minutes'] = work_df[mins_col].apply(self._parse_float)
        else:
            work_df['_clean_minutes'] = 0.0
            
        # 4. Parse Charge (vectorized)
        charge_col = mapping.get("charge") or mapping.get("cost")
        if charge_col:
            work_df['_clean_charge'] = work_df[charge_col].apply(self._parse_float)
        else:
            work_df['_clean_charge'] = 0.0
            
        # 5. Parse Modality (vectorized)
        if "modality" in mapping:
            modality_col = mapping.get("modality")
            work_df['_clean_modality'] = work_df[modality_col].astype(str).str.strip()
        else:
            work_df['_clean_modality'] = "UNKNOWN"
        
        # 6. Calculate rate per minute (vectorized)
        work_df['_rate_per_minute'] = work_df.apply(
            lambda r: (r['_clean_charge'] / r['_clean_minutes']) if r['_clean_minutes'] > 0 else 0.0,
            axis=1
        )
        
        # FILTER: Remove rows with invalid data
        valid_mask = (
            work_df['_clean_date'].notna() &  # Must have valid date
            (work_df['_clean_language'] != '') &  # Must have language
            (work_df['_clean_language'].str.lower() != 'nan')  # Language not "nan"
        )
        
        valid_df = work_df[valid_mask].copy()
        
        # BUILD RECORDS: Convert filtered dataframe to CanonicalRecords
        records = []
        for _, row in valid_df.iterrows():
            try:
                rec = CanonicalRecord(
                    source_file=source_file,
                    vendor=vendor,
                    date=row['_clean_date'],
                    language=row['_clean_language'],
                    modality=row['_clean_modality'],
                    minutes_billed=row['_clean_minutes'],
                    total_charge=row['_clean_charge'],
                    rate_per_minute=row['_rate_per_minute'],
                    raw_columns=row.to_dict()
                )
                records.append(rec)
            except Exception:
                # Skip malformed rows
                pass
                
        return records

    def _parse_date(self, val: Any) -> datetime.date:
        if pd.isna(val):
            return None
        
        if isinstance(val, datetime.datetime):
            return val.date()
        if isinstance(val, datetime.date):
            return val
            
        # String parsing
        val_str = str(val).split(" ")[0].strip() # Remove time
        
        # Handle YYYY-MM explicitly (Nuvance)
        if re.match(r'^\d{4}-\d{2}$', val_str):
             try:
                 # Default to 1st of month
                 return datetime.datetime.strptime(val_str, "%Y-%m").date()
             except:
                 pass

        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%d-%b-%y", "%B %d, %Y"]:
            try:
                return datetime.datetime.strptime(val_str, fmt).date()
            except:
                continue
        return None

    def _parse_float(self, val: Any) -> float:
        if pd.isna(val):
            return 0.0
        
        # Determine format (e.g. "$ 50.00", "5 min")
        s = str(val).replace('$', '').replace(',', '').replace('min', '').strip()
        
        if ':' in s:
            # Handle MM:SS format?
            parts = s.split(':')
            if len(parts) == 2:
                try:
                     # Minutes + Seconds/60
                     return float(parts[0]) + float(parts[1])/60.0
                except:
                    return 0.0
            if len(parts) == 3: # HH:MM:SS
                 try:
                     return float(parts[0])*60 + float(parts[1]) + float(parts[2])/60.0
                 except: # return 0.0
                    return 0.0
                    
        try:
            return float(s)
        except:
            return 0.0
