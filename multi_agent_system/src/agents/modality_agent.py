
import re
from typing import List, Dict
from core.canonical_schema import CanonicalRecord

class ModalityRefinementAgent:
    """
    Normalizes messy vendor-specific service strings into canonical modalities:
    OPI, VRI, OnSite, Translation.
    
    Uses Hybrid Approach:
    1. Fast Regex Rules (covers 95% of cases)
    2. AI Fallback (handles novel/ambiguous terms)
    """

    def __init__(self):
        # Keyword mapping for regex (priority matters)
        self.rules = [
            ("VRI", [r"vri", r"video", r"visual", r"ipad", r"tablet", r"remote"]),
            ("OnSite", [r"onsite", r"on-site", r"face-to-face", r"f2f", r"in-person", r"travel"]),
            ("Translation", [r"translation", r"document", r"written", r"localization", r"proofread"]),
            ("OPI", [r"opi", r"phone", r"audio", r"telephonic", r"voice", r"interpretation services"])
        ]
        
        # AI Setup
        try:
            from core.ai_client import AIClient
            self.ai = AIClient()
        except ImportError:
            self.ai = None
            
        # Cache for AI decisions to avoid repeated API calls for same string
        self.ai_cache = {} 

    def refine_records(self, records: List[CanonicalRecord]) -> Dict[str, int]:
        """
        Updates the modality field of CanonicalRecords in-place.
        Returns a summary of distribution.
        """
        stats = {"OPI": 0, "VRI": 0, "OnSite": 0, "Translation": 0, "Unknown": 0}

        for rec in records:
            raw_val = str(rec.modality).strip()
            raw_lower = raw_val.lower()
            
            # 1. Try Fast Regex First
            found = False
            for canonical_name, patterns in self.rules:
                if any(re.search(p, raw_lower) for p in patterns):
                    rec.modality = canonical_name
                    stats[canonical_name] += 1
                    found = True
                    break
            
            if found:
                continue

            # 2. Try AI Fallback
            if self.ai and self.ai.enabled:
                # Check Cache
                if raw_lower in self.ai_cache:
                    classification = self.ai_cache[raw_lower]
                else:
                    # Ask AI
                    classification = self._ask_ai_to_classify(raw_val)
                    self.ai_cache[raw_lower] = classification
                
                # Apply if valid
                if classification in ["OPI", "VRI", "OnSite", "Translation"]:
                    rec.modality = classification
                    stats[classification] += 1
                    found = True
            
            # 3. Last Resort
            if not found:
                rec.modality = "UNKNOWN"
                stats["Unknown"] += 1

        return stats

    def _ask_ai_to_classify(self, service_string: str) -> str:
        """Uses LLM to classify an ambiguous service string."""
        sys_prompt = "You are a classifier for Language Services. Categories: OPI, VRI, OnSite, Translation. Return ONLY the category name."
        user_prompt = f"Classify this service description: '{service_string}'"
        
        try:
            # We expect a single word response
            resp = self.ai.complete_text(sys_prompt, user_prompt)
            if resp:
                clean_resp = resp.strip().replace('"', '').replace('.', '')
                if clean_resp in ["OPI", "VRI", "OnSite", "Translation"]:
                    return clean_resp
        except:
            pass
        return "Unknown"
