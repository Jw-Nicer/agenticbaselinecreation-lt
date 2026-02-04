
import re
from typing import List, Dict
from core.canonical_schema import CanonicalRecord

class ModalityRefinementAgent:
    """
    Normalizes messy vendor-specific service strings into canonical modalities:
    OPI, VRI, OnSite, Translation.
    
    This agent prevents 'data fragmentation' where different names for the same
    service skew aggregation.
    """

    def __init__(self):
        # Keyword mapping for regex (priority matters)
        # We check specific terms before general terms
        self.rules = [
            ("VRI", [r"vri", r"video", r"visual", r"ipad", r"tablet", r"remote"]),
            ("OnSite", [r"onsite", r"on-site", r"face-to-face", r"f2f", r"in-person", r"travel"]),
            ("Translation", [r"translation", r"document", r"written", r"localization", r"proofread"]),
            ("OPI", [r"opi", r"phone", r"audio", r"telephonic", r"voice", r"interpretation services"])
        ]

    def refine_records(self, records: List[CanonicalRecord]) -> Dict[str, int]:
        """
        Updates the modality field of CanonicalRecords in-place.
        Returns a summary of distribution.
        """
        stats = {"OPI": 0, "VRI": 0, "OnSite": 0, "Translation": 0, "Unknown": 0}

        for rec in records:
            raw_val = str(rec.modality).lower().strip()
            # If standardizer already set it to a canonical value, just count it
            found = False
            for canonical_name, patterns in self.rules:
                if any(re.search(p, raw_val) for p in patterns):
                    rec.modality = canonical_name
                    stats[canonical_name] += 1
                    found = True
                    break
            
            if not found:
                # Data faithful: mark as UNKNOWN for manual review
                rec.modality = "UNKNOWN"
                stats["Unknown"] += 1

        return stats
