
import pandas as pd
import numpy as np
import datetime
from typing import List, Dict, Tuple, Any, Optional
from core.canonical_schema import CanonicalRecord

class QAgent:
    """
    Scans CanonicalRecords for anomalies, duplicates, and data quality issues.
    Delivers the "v4 QA" layer of the baseline.
    """

    def __init__(self, config_path: str = None):
        if config_path is None:
             # Default to standardized location
             config_path = "config/agent_config.json"
             
        import json
        import os
        
        # Default fallback values
        self.rate_threshold = 3.0
        self.max_duration = 240.0
        self.min_rate = 0.10
        self.max_rate = 5.00
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    full_config = json.load(f)
                    qa_config = full_config.get("QAgent", {})
                    self.rate_threshold = qa_config.get("rate_std_dev_threshold", 3.0)
                    self.max_duration = qa_config.get("duration_max_minutes", 240.0)
                    self.min_rate = qa_config.get("min_rate_threshold", 0.10)
                    self.max_rate = qa_config.get("max_rate_threshold", 5.00)
            else:
                print(f"Config file not found at {config_path}, using defaults")
        except Exception as e:
            print(f"Warning: Could not load QA config, using defaults. Error: {e}")

    def process_records(self, records: List[CanonicalRecord]) -> Tuple[List[CanonicalRecord], Dict[str, Any]]:
        """
        Runs full QA suite on a list of records.
        Returns (Processed Records, QA Summary Stats)
        """
        if not records:
            return [], {
                "status": "Empty input",
                "total_records_input": 0,
                "duplicates_removed": 0,
                "outliers_flagged": 0,
                "critical_errors_quarantined": 0,
                "total_records_output": 0,
                "issue_counts": {}
            }

        # 1. Convert to temporary DataFrame for statistical analysis
        df_records = []
        for r in records:
            d = vars(r).copy()
            # Handle date for DF
            if isinstance(d['date'], (datetime.date, datetime.datetime)):
                d['date_str'] = str(d['date'])
            df_records.append(d)
            
        df = pd.DataFrame(df_records)
        
        # 2. Statistical Analysis (Z-Scores for Rates)
        # Only calculate for records that have both cost and minutes
        valid_mask = (df['minutes_billed'] > 0) & (df['total_charge'] > 0)
        valid_rates = df[valid_mask]['rate_per_minute']
        
        mean_rate = valid_rates.mean() if not valid_rates.empty else 0
        std_rate = valid_rates.std() if not valid_rates.empty else 0

        qa_stats = {
            "total_records_input": len(records),
            "duplicates_removed": 0,
            "outliers_flagged": 0,
            "critical_errors_quarantined": 0,
            "mean_rate_detected": float(mean_rate),
            "std_rate_detected": float(std_rate),
            "issue_counts": {}
        }

        clean_records = []
        
        # Track seen records for duplicate detection
        seen_keys = set()

        for rec in records:
            issues = []
            status = "CLEAN"

            # --- CHECK 1: Duplicates ---
            # Unique signature includes source metadata to avoid false-positive collapses
            # when distinct sessions happen to share the same business values.
            dup_key = self._build_duplicate_key(rec)
            if dup_key in seen_keys:
                qa_stats["duplicates_removed"] += 1
                continue # Skip duplicates
            seen_keys.add(dup_key)

            # --- CHECK 2: Sanity Thresholds ---
            if rec.minutes_billed <= 0:
                issues.append("Zero/Negative Duration")
                status = "FLAGGED"
            
            if rec.minutes_billed > self.max_duration:
                issues.append(f"Excessive Duration (> {self.max_duration} min)")
                status = "FLAGGED"

            # --- CHECK 3: Rate Outliers ---
            if rec.minutes_billed > 0 and rec.total_charge > 0:
                # Statistical check
                if std_rate > 0:
                    z_score = abs(rec.rate_per_minute - mean_rate) / std_rate
                    if z_score > self.rate_threshold:
                        issues.append(f"Statistical Rate Outlier (Z={z_score:.1f})")
                        status = "FLAGGED"
                
                # Logical threshold check
                if rec.rate_per_minute < self.min_rate:
                    issues.append(f"Rate suspiciously low (${rec.rate_per_minute:.2f}/min)")
                    status = "FLAGGED"
                elif rec.rate_per_minute > self.max_rate and "onsite" not in rec.modality.lower():
                    issues.append(f"Rate suspiciously high (${rec.rate_per_minute:.2f}/min)")
                    status = "FLAGGED"

            # --- CHECK 4: Missing Critical Data ---
            if not rec.language or rec.language.lower() == "unknown":
                issues.append("Missing Language")
                status = "QUARANTINED"
            
            if not rec.date:
                issues.append("Missing Date")
                status = "QUARANTINED"

            # Missing cost with non-zero utilization cannot be used in accurate baseline spend math.
            if rec.minutes_billed > 0 and rec.total_charge <= 0:
                issues.append("Missing Cost")
                status = "QUARANTINED"

            # Update record metadata
            if issues:
                # Record issues in stats
                for iss in issues:
                    qa_stats["issue_counts"][iss] = qa_stats["issue_counts"].get(iss, 0) + 1

                rec.confidence_score *= 0.5 # Lower confidence
                if rec.raw_columns is None: rec.raw_columns = {}
                rec.raw_columns["_qa_issues"] = issues
                rec.raw_columns["_qa_status"] = status
                
                if status == "QUARANTINED":
                    qa_stats["critical_errors_quarantined"] += 1
                    # Accuracy-first behavior: quarantine records are excluded from baseline math.
                    continue
                qa_stats["outliers_flagged"] += 1

            clean_records.append(rec)

        qa_stats["total_records_output"] = len(clean_records)
        return clean_records, qa_stats

    def _extract_row_identity(self, rec: CanonicalRecord) -> Optional[str]:
        """
        Return a source-row identifier when available (e.g., call/session/invoice id).
        This lowers duplicate false positives for repeated same-day transactions.
        """
        raw = rec.raw_columns if isinstance(rec.raw_columns, dict) else {}
        if not raw:
            return None

        id_hints = (
            "call_id",
            "session_id",
            "encounter_id",
            "interaction_id",
            "invoice_line_id",
            "line_id",
            "record_id",
            "id",
        )

        normalized = {str(k).strip().lower(): v for k, v in raw.items()}
        for hint in id_hints:
            if hint in normalized:
                val = normalized[hint]
                if val is not None:
                    sval = str(val).strip()
                    if sval and sval.lower() != "nan":
                        return sval
        return None

    def _build_duplicate_key(self, rec: CanonicalRecord) -> Tuple[Any, ...]:
        """
        Build a conservative duplicate signature that incorporates source context.
        """
        return (
            str(rec.source_file).strip().lower(),
            str(rec.vendor).strip().lower(),
            str(rec.date),
            str(rec.language).strip().lower(),
            str(rec.modality).strip().lower(),
            round(float(rec.minutes_billed), 4),
            round(float(rec.total_charge), 4),
            str(rec.timestamp_start) if rec.timestamp_start else "",
            str(rec.timestamp_end) if rec.timestamp_end else "",
            self._extract_row_identity(rec),
        )
