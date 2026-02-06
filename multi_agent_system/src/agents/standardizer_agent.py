
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
        records = []
        
        # Check required columns
        req_cols = ["language", "date"] # Minimal Requirement
        for rc in req_cols:
            if rc not in mapping:
                # Can't process this sheet
                return []

        for index, row in df.iterrows():
            try:
                # 1. Parse Date
                raw_date = row.get(mapping.get("date"))
                clean_date = self._parse_date(raw_date)
                
                # If no valid date, it might be a summary line or garbage -> skip
                if not clean_date:
                    continue

                # 2. Parse Language
                lang = str(row.get(mapping.get("language"), "Unknown")).strip()
                if not lang or lang.lower() == 'nan':
                     continue

                # 3. Parse Metrics
                mins = self._parse_float(row.get(mapping.get("minutes"), 0))
                charge_col = mapping.get("charge") or mapping.get("cost")
                charge = self._parse_float(row.get(charge_col, 0))
                
                # 4. Parse Modality
                # If mapped, use it. If not, flag as UNKNOWN (data faithful)
                modality = "UNKNOWN"
                if "modality" in mapping:
                    modality = str(row.get(mapping.get("modality"), "OPI")).strip()
                
                # Create Record
                rec = CanonicalRecord(
                    source_file=source_file,
                    vendor=vendor,
                    date=clean_date,
                    language=lang,
                    modality=modality,
                    minutes_billed=mins,
                    total_charge=charge,
                    rate_per_minute= (charge / mins) if mins > 0 else 0.0,
                    raw_columns=row.to_dict()
                )
                records.append(rec)
                
            except Exception as e:
                # Log specific row errors but don't crash whole file
                # print(f"Row error: {e}")
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
