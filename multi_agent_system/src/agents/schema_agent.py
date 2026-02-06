
import pandas as pd
import re
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from core.canonical_schema import CANONICAL_FIELDS
from core.memory_store import ensure_memory_dir, load_json, save_json
from core.config import get_schema_config

# Few-shot examples for AI prompting - covers diverse vendor formats
FEW_SHOT_EXAMPLES = [
    {
        "columns": ["Service Date", "Language", "Duration", "Total Charge", "Rate"],
        "sample": {"Service Date": "2024-01-15", "Language": "Spanish", "Duration": "15.5", "Total Charge": "$23.25", "Rate": "$1.50"},
        "mapping": {"date": "Service Date", "language": "Language", "minutes": "Duration", "charge": "Total Charge", "rate": "Rate"},
        "reasoning": "Service Date contains ISO date format, Duration is numeric minutes, Total Charge has currency prefix indicating cost"
    },
    {
        "columns": ["Year-Month", "Lang", "MinuteswithTPD", "ChargeswithTPD", "Service Type"],
        "sample": {"Year-Month": "2024-01", "Lang": "ALBANIAN", "MinuteswithTPD": "42.3", "ChargeswithTPD": "65.00", "Service Type": "OPI"},
        "mapping": {"date": "Year-Month", "language": "Lang", "minutes": "MinuteswithTPD", "charge": "ChargeswithTPD", "modality": "Service Type"},
        "reasoning": "Year-Month is a period date format, MinuteswithTPD contains duration with vendor suffix, Lang is abbreviated language column"
    },
    {
        "columns": ["Call Date & Time", "Language", "Min", "Billed", "Connect time (sec)", "Service Line"],
        "sample": {"Call Date & Time": "01/15/2024 10:30", "Language": "Mandarin", "Min": "8", "Billed": "12.00", "Service Line": "Phone"},
        "mapping": {"date": "Call Date & Time", "language": "Language", "minutes": "Min", "charge": "Billed", "modality": "Service Line"},
        "reasoning": "Call Date & Time has datetime format, Min is abbreviated minutes (not Connect time which is seconds), Billed is the charge amount"
    },
    {
        "columns": ["Invoice Date", "Target Language", "Qty", "Extended Price", "Unit Price", "Product"],
        "sample": {"Invoice Date": "15-Jan-24", "Target Language": "Vietnamese", "Qty": "22", "Extended Price": "33.00", "Unit Price": "1.50", "Product": "VRI"},
        "mapping": {"date": "Invoice Date", "language": "Target Language", "minutes": "Qty", "charge": "Extended Price", "rate": "Unit Price", "modality": "Product"},
        "reasoning": "Qty represents quantity/duration, Extended Price is total charge, Unit Price is per-minute rate, Target Language specifies the interpreted language"
    }
]

class SchemaAgent:
    """
    Agent responsible for deducing the map between Raw Excel Columns -> Canonical Schema.
    It uses Generative AI (LLM) first, then falls back to heuristic matching.
    """
    
    def __init__(self):
        self.known_mappings = {}
        mem_dir = ensure_memory_dir()
        self._registry_path = mem_dir / "mapping_registry.json"
        self._mapping_registry = load_json(self._registry_path, {})
        self._pending_path = mem_dir / "pending_mappings.json"
        self._pending_mappings = load_json(self._pending_path, [])
        self._last_source = "heuristic"
        self.config = get_schema_config()
        self.auto_learn = bool(self.config.get("auto_learn", True))
        self.require_manual_approval = bool(self.config.get("require_manual_approval", False))
        self.min_field_confidence = float(self.config.get("min_field_confidence", 0.75))
        self.min_data_confidence = float(self.config.get("min_data_confidence", 0.70))
        self.min_final_confidence = float(self.config.get("min_final_confidence", 0.60))

        # Active learning: correction history
        self._correction_path = mem_dir / "correction_history.json"
        self._correction_history = load_json(self._correction_path, {
            "corrections": [],
            "vendor_patterns": {},
            "success_rates": {
                "ai": {"total": 0, "corrected": 0},
                "heuristic": {"total": 0, "corrected": 0},
                "cache": {"total": 0, "corrected": 0}
            }
        })

        # Delayed import to avoid circular dependency issues if core isn't ready
        try:
            from core.ai_client import AIClient
            self.ai = AIClient()
        except ImportError:
            self.ai = None

    def clean_header(self, header: str) -> str:
        """Strip and lowercase header for easier matching."""
        if not isinstance(header, str):
            return str(header)
        return header.strip().lower().replace('\n', ' ').replace('.', '')

    def _build_ai_prompt(self, source_columns: List[str], sample_row: Optional[pd.Series], vendor: Optional[str]) -> Tuple[str, str]:
        """Build enhanced AI prompt with few-shot examples and vendor context."""
        # Build examples text
        examples_text = "\n\n".join([
            f"Example {i+1}:\n"
            f"  Columns: {ex['columns']}\n"
            f"  Sample: {ex['sample']}\n"
            f"  Mapping: {ex['mapping']}\n"
            f"  Reasoning: {ex['reasoning']}"
            for i, ex in enumerate(FEW_SHOT_EXAMPLES)
        ])

        system_prompt = f"""You are a Data Engineering Agent specialized in mapping raw Excel columns to a canonical schema for Language Services billing data.

Canonical Schema Fields:
- date: Service/call date (formats: YYYY-MM-DD, MM/DD/YYYY, YYYY-MM, DD-Mon-YY, etc.)
- language: Language interpreted (e.g., Spanish, Mandarin, ALBANIAN, Vietnamese)
- minutes: Call duration in minutes (may be labeled: duration, qty, quantity, billable time, min)
- charge: Total cost/charge amount (may include $ prefix, labeled: amount, total, cost, billed, extended price)
- rate: Per-minute rate (optional, labeled: unit price, price, rate)
- modality: Service type like OPI, VRI, OnSite, Translation (optional, labeled: service type, service line, product)

{examples_text}

INSTRUCTIONS:
1. Analyze each column name AND the sample values to determine the best mapping
2. Return a JSON object with this exact structure:
{{
    "mapping": {{"canonical_field": "source_column", ...}},
    "confidence": {{"canonical_field": 0.0-1.0, ...}},
    "reasoning": "Brief explanation of your mapping decisions"
}}
3. Only include fields where you have reasonable confidence (>= 0.5)
4. If a field could map to multiple columns, choose the most semantically appropriate one
5. Be careful: "Connect time (sec)" is seconds not minutes; "Qty" may be minutes; distinguish rate from charge"""

        # Build user prompt with vendor context
        vendor_context = f"Vendor: {vendor}\n" if vendor else ""

        sample_payload = None
        if sample_row is not None and hasattr(sample_row, "to_dict"):
            try:
                sample_payload = {str(k): str(v) for k, v in sample_row.to_dict().items()}
            except Exception:
                sample_payload = None

        user_prompt = f"{vendor_context}Columns: {source_columns}\nSample Row: {sample_payload}"

        return system_prompt, user_prompt

    def _build_heuristic_validation_prompt(
        self,
        source_columns: List[str],
        sample_row: Optional[pd.Series],
        mapping: Dict[str, str],
        vendor: Optional[str],
        df: Optional[pd.DataFrame]
    ) -> Tuple[str, str]:
        """Build AI prompt to validate heuristic mappings using data samples."""
        system_prompt = """You are validating a proposed column mapping for language services billing data.

Return JSON only with this exact structure:
{
  "field_ok": {"date": true/false, "language": true/false, "minutes": true/false, "charge": true/false, "rate": true/false, "modality": true/false},
  "confidence": {"date": 0.0-1.0, "language": 0.0-1.0, "minutes": 0.0-1.0, "charge": 0.0-1.0, "rate": 0.0-1.0, "modality": 0.0-1.0},
  "overall_ok": true/false,
  "reasoning": "brief explanation"
}

Rules:
- Only mark a field true if the column values clearly match the intended meaning.
- Be conservative with low-quality or ambiguous columns.
- Use the sample values to decide, not just column names."""

        vendor_context = f"Vendor: {vendor}\n" if vendor else ""

        sample_payload = None
        if sample_row is not None and hasattr(sample_row, "to_dict"):
            try:
                sample_payload = {str(k): str(v) for k, v in sample_row.to_dict().items()}
            except Exception:
                sample_payload = None

        sample_values = {}
        if df is not None and mapping:
            for field, col in mapping.items():
                if col in df.columns:
                    vals = df[col].dropna().head(5).astype(str).tolist()
                    sample_values[col] = vals

        user_prompt = (
            f"{vendor_context}"
            f"Columns: {source_columns}\n"
            f"Proposed Mapping: {mapping}\n"
            f"Sample Row: {sample_payload}\n"
            f"Sample Values by Column: {sample_values}"
        )

        return system_prompt, user_prompt

    def _parse_ai_response(self, ai_response: Dict, source_columns: List[str]) -> Tuple[Dict[str, str], Dict[str, float], Optional[str]]:
        """Parse enhanced AI response with per-field confidence scores."""
        mapping = {}
        confidences = {}
        reasoning = None

        if not ai_response:
            return mapping, confidences, reasoning

        # Handle both old format (direct mapping) and new format (nested structure)
        if "mapping" in ai_response:
            raw_mapping = ai_response.get("mapping", {})
            raw_confidence = ai_response.get("confidence", {})
            reasoning = ai_response.get("reasoning")
        else:
            # Backward compatible: treat entire response as mapping
            raw_mapping = ai_response
            raw_confidence = {}

        for field, col in raw_mapping.items():
            if col in source_columns and field in CANONICAL_FIELDS:
                mapping[field] = col
                # Default to 0.8 confidence if not provided
                conf = raw_confidence.get(field, 0.8)
                confidences[field] = float(conf) if isinstance(conf, (int, float)) else 0.8

        return mapping, confidences, reasoning

    def _infer_types_from_data(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """
        Use data-driven type inference to analyze all columns.

        Args:
            df: DataFrame to analyze

        Returns:
            Dict mapping column name to type inference results
        """
        try:
            from core.type_inference import TypeInferenceEngine
        except ImportError:
            return {}

        type_config = self.config.get("type_inference", {})
        sample_size = type_config.get("sample_size", 100)

        engine = TypeInferenceEngine(sample_size=sample_size)
        return engine.analyze_all_columns(df)

    def _heuristic_mapping_with_type_inference(
        self,
        source_columns: List[str],
        df: Optional[pd.DataFrame] = None,
        vendor: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Enhanced heuristic mapping using vendor hints, keywords, and data-driven type inference.

        Args:
            source_columns: List of column names
            df: Optional DataFrame for type inference
            vendor: Optional vendor name for applying learned patterns

        Returns:
            Mapping from canonical fields to source columns
        """
        mapping = {}
        cleaned_source = {col: self.clean_header(col) for col in source_columns}

        # Phase 0: Apply learned vendor preferences first (active learning)
        active_learning_config = self.config.get("active_learning", {})
        if active_learning_config.get("enabled", True) and active_learning_config.get("apply_vendor_hints", True) and vendor:
            vendor_hints = self.get_vendor_hints(vendor)
            preferred = vendor_hints.get("preferred_columns", {})

            for field, pref_col in preferred.items():
                if pref_col in source_columns and field in CANONICAL_FIELDS:
                    mapping[field] = pref_col

            # Also try learned keywords from corrections
            learned_keywords = vendor_hints.get("learned_keywords", {})
            for canonical_field in CANONICAL_FIELDS:
                if canonical_field in mapping:
                    continue

                vendor_kws = learned_keywords.get(canonical_field, [])
                for col_original, col_clean in cleaned_source.items():
                    if col_clean in vendor_kws:
                        mapping[canonical_field] = col_original
                        break

        # Phase 1: Keyword matching (existing logic)
        for canonical_field, keywords in CANONICAL_FIELDS.items():
            if canonical_field in mapping:
                continue  # Already mapped by vendor hints

            best_match = None

            for col_original, col_clean in cleaned_source.items():
                if col_original in mapping.values():
                    continue  # Already used

                # Check exact keyword matches first
                if col_clean in keywords:
                    best_match = col_original
                    break

                # Check fuzzy contains
                for kw in keywords:
                    if kw in col_clean:
                        if not best_match:
                            best_match = col_original

            if best_match:
                mapping[canonical_field] = best_match

        # Keyword refinements
        if "minutes" not in mapping:
            for col, clean in cleaned_source.items():
                if col in mapping.values():
                    continue
                if "connect" in clean and "time" in clean:
                    mapping["minutes"] = col
                    break

        if "minutes" not in mapping:
            for col, clean in cleaned_source.items():
                if col in mapping.values():
                    continue
                if "min billed" in clean:
                    mapping["minutes"] = col
                    break

        if "charge" not in mapping:
            for col, clean in cleaned_source.items():
                if col in mapping.values():
                    continue
                if "charges" in clean:
                    mapping["charge"] = col
                    break

        # Phase 2: Data-driven type inference for unmapped fields
        type_config = self.config.get("type_inference", {})
        if type_config.get("enabled", True) and df is not None and len(df) > 0:
            type_results = self._infer_types_from_data(df)
            min_confidence = type_config.get("min_type_confidence", 0.6)

            for canonical_field in CANONICAL_FIELDS:
                if canonical_field in mapping:
                    continue  # Already mapped

                # Find best column by type inference
                best_col = None
                best_score = min_confidence

                for col, result in type_results.items():
                    if col in mapping.values():
                        continue  # Already used for another field

                    if result.get("type") == canonical_field and result.get("confidence", 0) > best_score:
                        best_col = col
                        best_score = result["confidence"]

                if best_col:
                    mapping[canonical_field] = best_col

        return mapping

    def _prune_mapping_with_data_validation(
        self,
        df: Optional[pd.DataFrame],
        mapping: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Prune heuristic mappings that don't make sense based on data patterns.
        """
        validation_cfg = self.config.get("heuristic_validation", {})
        if not validation_cfg.get("enabled", True):
            return mapping
        if df is None or df.empty:
            return mapping

        min_type_conf = float(validation_cfg.get("min_type_confidence", 0.65))
        min_date_parse = float(validation_cfg.get("min_date_parse", 0.6))
        min_numeric_rate = float(validation_cfg.get("min_numeric_rate", 0.6))
        min_language_match = float(validation_cfg.get("min_language_match", 0.3))

        pruned = dict(mapping)
        type_results = self._infer_types_from_data(df) if df is not None else {}

        for field, col in list(pruned.items()):
            if col not in df.columns:
                pruned.pop(field, None)
                continue

            inferred = type_results.get(col, {})
            inferred_type = inferred.get("type")
            inferred_conf = inferred.get("confidence", 0.0)

            # If data strongly suggests a different type, drop the mapping.
            if inferred_type and inferred_type != field and inferred_conf >= min_type_conf:
                pruned.pop(field, None)
                continue

            series = df[col].dropna()
            if len(series) == 0:
                continue

            if field == "date":
                parsed = pd.to_datetime(series, errors="coerce")
                parse_rate = parsed.notna().sum() / len(series)
                if parse_rate < min_date_parse:
                    pruned.pop(field, None)
                    continue

            if field in ("minutes", "charge", "rate"):
                cleaned = series.astype(str).str.replace(r'[\$,]', '', regex=True)
                numeric = pd.to_numeric(cleaned, errors="coerce")
                valid_rate = numeric.notna().sum() / len(series)
                if valid_rate < min_numeric_rate:
                    pruned.pop(field, None)
                    continue

            if field == "language":
                try:
                    from core.type_inference import get_known_languages
                    known = get_known_languages()
                except ImportError:
                    known = set()

                if known:
                    s = series.astype(str).str.strip().str.lower()
                    match_rate = s.isin(known).sum() / len(s)
                    if match_rate < min_language_match and inferred_type != "language":
                        pruned.pop(field, None)
                        continue

        return pruned

    def _validate_heuristic_with_ai(
        self,
        source_columns: List[str],
        sample_row: Optional[pd.Series],
        mapping: Dict[str, str],
        vendor: Optional[str],
        df: Optional[pd.DataFrame]
    ) -> Dict[str, str]:
        """
        Use AI to validate a heuristic mapping. Drops fields the AI confidently rejects.
        """
        cfg = self.config.get("heuristic_ai_validation", {})
        if not cfg.get("enabled", True):
            return mapping
        if not self.ai or not self.ai.enabled:
            return mapping
        if not mapping:
            return mapping

        min_conf = float(cfg.get("min_field_confidence", 0.6))
        require_overall_ok = bool(cfg.get("require_overall_ok", True))
        min_overall_conf = float(cfg.get("min_overall_confidence", 0.65))
        system_prompt, user_prompt = self._build_heuristic_validation_prompt(
            source_columns, sample_row, mapping, vendor, df
        )
        ai_response = self.ai.complete_json(system_prompt, user_prompt)
        if not ai_response:
            return mapping

        field_ok = ai_response.get("field_ok", {}) if isinstance(ai_response, dict) else {}
        conf = ai_response.get("confidence", {}) if isinstance(ai_response, dict) else {}
        overall_ok = ai_response.get("overall_ok") if isinstance(ai_response, dict) else None
        reasoning = ai_response.get("reasoning") if isinstance(ai_response, dict) else None

        # Store AI validation context for audit/UI
        self._last_ai_confidences = conf if isinstance(conf, dict) else {}
        self._last_ai_reasoning = reasoning

        conf_values = [v for v in conf.values() if isinstance(v, (int, float))]
        avg_conf = sum(conf_values) / len(conf_values) if conf_values else 0.0

        if require_overall_ok and overall_ok is False and avg_conf >= min_overall_conf:
            # AI is confident the overall mapping is wrong: force review by dropping all fields.
            self._last_source = "heuristic_ai_reject"
            return {}

        filtered = {}
        for field, col in mapping.items():
            ok = field_ok.get(field)
            score = conf.get(field, 0.0)
            # Keep if AI approves, or if AI is uncertain.
            if ok is True and score >= min_conf:
                filtered[field] = col
                continue
            if ok is False and score >= min_conf:
                continue
            # AI uncertain -> keep existing heuristic mapping
            filtered[field] = col

        # Mark source for audit trail
        self._last_source = "heuristic_ai"

        return filtered

    def infer_mapping(self, source_columns: List[str], sample_row: pd.Series = None, vendor: Optional[str] = None, df: Optional[pd.DataFrame] = None) -> Dict[str, str]:
        """
        Given a list of columns from a raw file (and an optional sample row for value type checking),
        returns a dictionary mapping CanonicalField -> SourceColumn.

        Args:
            source_columns: List of column names from the raw file
            sample_row: Optional sample row for AI context
            vendor: Optional vendor name for context and caching
            df: Optional DataFrame for data-driven type inference
        """
        # Store AI confidence for later use
        self._last_ai_confidences = {}
        self._last_ai_reasoning = None

        # 1. AI Attempt with enhanced few-shot prompting
        if self.ai and self.ai.enabled:
            system_prompt, user_prompt = self._build_ai_prompt(source_columns, sample_row, vendor)

            ai_response = self.ai.complete_json(system_prompt, user_prompt)
            if ai_response:
                validated_map, confidences, reasoning = self._parse_ai_response(ai_response, source_columns)
                self._last_ai_confidences = confidences
                self._last_ai_reasoning = reasoning

                # Check minimum confidence threshold from config
                min_ai_conf = self.config.get("ai_prompting", {}).get("min_ai_field_confidence", 0.5)

                # Filter out low-confidence mappings
                high_conf_map = {k: v for k, v in validated_map.items()
                                if confidences.get(k, 0.8) >= min_ai_conf}

                # If AI found the core fields with sufficient confidence, return
                if len(high_conf_map) >= 3:
                    self._last_source = "ai"
                    return high_conf_map

        # 2. Cached mapping (learned/approved)
        cached = self._get_cached_mapping(source_columns, vendor)
        if cached:
            return cached

        # 2. Heuristic Fallback with Type Inference and Vendor Hints
        self._last_source = "heuristic"
        mapping = self._heuristic_mapping_with_type_inference(source_columns, df, vendor)
        mapping = self._prune_mapping_with_data_validation(df, mapping)
        mapping = self._validate_heuristic_with_ai(source_columns, sample_row, mapping, vendor, df)

        return mapping

    def _validate_cross_field(self, df: pd.DataFrame, mapping: Dict[str, str], sample_size: int = 50) -> Dict[str, Any]:
        """
        Validate mapping by checking logical relationships between fields.

        Args:
            df: DataFrame to validate against
            mapping: Current field mapping
            sample_size: Number of rows to sample

        Returns:
            Dict with validation results and any issues found
        """
        sample = df.head(sample_size)
        results = {
            "charge_rate_consistency": None,
            "date_parse_rate": None,
            "language_validity_rate": None,
            "issues": []
        }

        # Check 1: If minutes, rate, charge all mapped, verify charge ≈ minutes × rate
        mins_col = mapping.get("minutes")
        rate_col = mapping.get("rate")
        charge_col = mapping.get("charge")

        if all([mins_col, rate_col, charge_col]) and all(c in sample.columns for c in [mins_col, rate_col, charge_col]):
            try:
                mins = pd.to_numeric(
                    sample[mins_col].astype(str).str.replace(',', '', regex=False),
                    errors='coerce'
                )
                rate = pd.to_numeric(
                    sample[rate_col].astype(str).str.replace(r'[\$,]', '', regex=True),
                    errors='coerce'
                )
                charge = pd.to_numeric(
                    sample[charge_col].astype(str).str.replace(r'[\$,]', '', regex=True),
                    errors='coerce'
                )

                expected_charge = mins * rate
                valid_mask = expected_charge.notna() & charge.notna() & (expected_charge > 0)

                if valid_mask.sum() > 0:
                    # Allow 5% tolerance for rounding
                    tolerance = 0.05
                    matches = (
                        abs(expected_charge[valid_mask] - charge[valid_mask]) /
                        expected_charge[valid_mask] <= tolerance
                    ).sum()
                    consistency = matches / valid_mask.sum()
                    results["charge_rate_consistency"] = float(consistency)

                    if consistency < 0.7:
                        results["issues"].append(
                            f"Low charge/rate consistency: {consistency:.1%} of rows have charge ≈ minutes × rate"
                        )
            except Exception as e:
                results["issues"].append(f"Cross-field validation error: {str(e)}")

        # Check 2: Date parse success rate
        date_col = mapping.get("date")
        if date_col and date_col in sample.columns:
            series = sample[date_col].dropna()
            if len(series) > 0:
                parsed = pd.to_datetime(series, errors='coerce')
                parse_rate = parsed.notna().sum() / len(series)
                results["date_parse_rate"] = float(parse_rate)

                if parse_rate < 0.8:
                    results["issues"].append(
                        f"Low date parse rate: {parse_rate:.1%} of dates could be parsed"
                    )

        # Check 3: Language validity (matches known languages)
        lang_col = mapping.get("language")
        if lang_col and lang_col in sample.columns:
            try:
                from core.type_inference import get_known_languages
                known_languages = get_known_languages()
            except ImportError:
                known_languages = set()

            if known_languages:
                series = sample[lang_col].dropna().astype(str).str.strip().str.lower()
                if len(series) > 0:
                    valid = series.isin(known_languages).sum()
                    validity_rate = valid / len(series)
                    results["language_validity_rate"] = float(validity_rate)

                    # Lower threshold since vendor-specific names may differ
                    if validity_rate < 0.5:
                        results["issues"].append(
                            f"Many unrecognized languages: {validity_rate:.1%} match known language names"
                        )

        return results

    def assess_mapping(self, df: pd.DataFrame, mapping: Dict[str, str], sample_size: int = 50) -> Dict[str, Any]:
        """
        Evaluate mapping quality using actual data samples and cross-field validation.

        Returns dict with field_confidence, data_confidence, cross_field_confidence,
        final_confidence, and issues list.
        """
        field_confidence = self.validate_mapping(mapping)
        if df is None or df.empty:
            return {
                "field_confidence": field_confidence,
                "data_confidence": 0.0,
                "cross_field_confidence": 0.0,
                "final_confidence": 0.0,
                "issues": []
            }

        sample = df.head(sample_size)
        ratios = []

        # Date parse ratio
        date_col = mapping.get("date")
        if date_col in sample.columns:
            series = sample[date_col]
            non_null = series.notna().sum()
            if non_null > 0:
                parsed = pd.to_datetime(series, errors="coerce")
                ratios.append(parsed.notna().sum() / non_null)

        # Language non-empty ratio
        lang_col = mapping.get("language")
        if lang_col in sample.columns:
            series = sample[lang_col]
            non_null = series.notna().sum()
            if non_null > 0:
                s = series.astype(str).str.strip()
                valid = s[(s != "") & (s.str.lower() != "nan")]
                ratios.append(len(valid) / non_null)

        # Minutes numeric ratio
        mins_col = mapping.get("minutes")
        if mins_col in sample.columns:
            series = sample[mins_col]
            non_null = series.notna().sum()
            if non_null > 0:
                numeric = pd.to_numeric(series, errors="coerce")
                valid = numeric[(numeric.notna()) & (numeric >= 0)]
                ratios.append(len(valid) / non_null)

        # Optional: cost numeric ratio
        cost_col = mapping.get("charge") or mapping.get("cost")
        if cost_col in sample.columns:
            series = sample[cost_col]
            non_null = series.notna().sum()
            if non_null > 0:
                numeric = pd.to_numeric(series, errors="coerce")
                valid = numeric[numeric.notna()]
                ratios.append(len(valid) / non_null)

        data_confidence = sum(ratios) / len(ratios) if ratios else 0.0

        # Cross-field validation
        cross_field_results = self._validate_cross_field(df, mapping, sample_size)

        # Calculate cross-field confidence from validation results
        cross_scores = [
            v for k, v in cross_field_results.items()
            if v is not None and isinstance(v, (int, float)) and k != "issues"
        ]
        cross_field_confidence = sum(cross_scores) / len(cross_scores) if cross_scores else 1.0

        # Combine confidences (weighted)
        # Cross-field is supplementary - don't let it dominate
        if ratios:
            combined_data_confidence = data_confidence * 0.7 + cross_field_confidence * 0.3
            final_confidence = min(field_confidence, combined_data_confidence)
        else:
            final_confidence = 0.0

        return {
            "field_confidence": float(field_confidence),
            "data_confidence": float(data_confidence),
            "cross_field_confidence": float(cross_field_confidence),
            "final_confidence": float(final_confidence),
            "issues": cross_field_results.get("issues", [])
        }

    def confirm_mapping(
        self,
        source_columns: List[str],
        mapping: Dict[str, str],
        vendor: Optional[str],
        data_confidence: float,
        field_confidence: Optional[float] = None,
        source: Optional[str] = None
    ) -> bool:
        """
        Persist mapping only if confidence is strong.
        """
        if field_confidence is None:
            field_confidence = self.validate_mapping(mapping)
        if field_confidence < self.min_field_confidence or data_confidence < self.min_data_confidence:
            return False
        if self.require_manual_approval:
            auto_field = float(self.config.get("auto_approve_field_confidence", 0.90))
            auto_data = float(self.config.get("auto_approve_data_confidence", 0.85))
            if field_confidence >= auto_field and data_confidence >= auto_data and self.auto_learn:
                src = source or self._last_source
                self._save_mapping(source_columns, mapping, vendor, src, data_confidence)
                return True
            self._queue_pending_mapping(source_columns, mapping, vendor, field_confidence, data_confidence, source)
            return False
        if not self.auto_learn:
            return False
        src = source or self._last_source
        self._save_mapping(source_columns, mapping, vendor, src, data_confidence)
        return True

    def _columns_signature(self, source_columns: List[str]) -> str:
        normalized = [str(c).strip().lower() for c in source_columns]
        joined = "|".join(sorted(normalized))
        return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]

    def _get_cached_mapping(self, source_columns: List[str], vendor: Optional[str]) -> Optional[Dict[str, str]]:
        signature = self._columns_signature(source_columns)
        vendor_key = vendor or "UNKNOWN"
        key = f"{vendor_key}::{signature}"
        entry = self._mapping_registry.get(key)
        if not entry:
            return None
        mapping = entry.get("mapping")
        if not isinstance(mapping, dict):
            return None
        # Validate mapping references current columns
        for field, col in mapping.items():
            if col not in source_columns or field not in CANONICAL_FIELDS:
                return None
        self._last_source = "cache"
        return mapping

    def _save_mapping(self, source_columns: List[str], mapping: Dict[str, str], vendor: Optional[str], source: str, data_confidence: float) -> None:
        field_confidence = self.validate_mapping(mapping)
        if field_confidence < self.min_field_confidence or data_confidence < self.min_data_confidence:
            return
        signature = self._columns_signature(source_columns)
        vendor_key = vendor or "UNKNOWN"
        key = f"{vendor_key}::{signature}"
        self._mapping_registry[key] = {
            "vendor": vendor_key,
            "columns_signature": signature,
            "columns": [str(c) for c in source_columns],
            "mapping": mapping,
            "field_confidence": field_confidence,
            "data_confidence": data_confidence,
            "source": source,
            "ai_confidences": self.get_last_ai_confidences(),
            "ai_reasoning": self.get_last_ai_reasoning()
        }
        save_json(self._registry_path, self._mapping_registry)

    def _queue_pending_mapping(
        self,
        source_columns: List[str],
        mapping: Dict[str, str],
        vendor: Optional[str],
        field_confidence: float,
        data_confidence: float,
        source: Optional[str]
    ) -> None:
        if not isinstance(self._pending_mappings, list):
            self._pending_mappings = []
        signature = self._columns_signature(source_columns)
        vendor_key = vendor or "UNKNOWN"
        entry = {
            "vendor": vendor_key,
            "columns_signature": signature,
            "columns": [str(c) for c in source_columns],
            "mapping": mapping,
            "field_confidence": field_confidence,
            "data_confidence": data_confidence,
            "source": source or self._last_source,
            "ai_confidences": self.get_last_ai_confidences(),
            "ai_reasoning": self.get_last_ai_reasoning()
        }
        self._pending_mappings.append(entry)
        save_json(self._pending_path, self._pending_mappings)

    def save_approved_mapping(self, entry: Dict[str, Any]) -> bool:
        """
        Save a manually approved mapping without applying confidence thresholds.
        """
        if not isinstance(entry, dict):
            return False
        source_columns = entry.get("columns") or []
        mapping = entry.get("mapping") or {}
        vendor = entry.get("vendor")
        if not source_columns or not mapping:
            return False
        signature = self._columns_signature(source_columns)
        vendor_key = vendor or "UNKNOWN"
        key = f"{vendor_key}::{signature}"
        self._mapping_registry[key] = {
            "vendor": vendor_key,
            "columns_signature": signature,
            "columns": [str(c) for c in source_columns],
            "mapping": mapping,
            "field_confidence": float(entry.get("field_confidence", 0.0)),
            "data_confidence": float(entry.get("data_confidence", 0.0)),
            "source": entry.get("source", "manual"),
            "ai_confidences": entry.get("ai_confidences"),
            "ai_reasoning": entry.get("ai_reasoning")
        }
        save_json(self._registry_path, self._mapping_registry)
        return True

    def validate_mapping(self, mapping: Dict[str, str]) -> float:
        """Returns a confidence score (0-1) for this mapping."""
        required = ["date", "language", "minutes"]
        optional = ["charge", "cost"]  # Either is acceptable (charge is canonical)
        hits = sum(1 for field in required if field in mapping)
        # Cost can be in either 'charge' or 'cost' key
        if any(field in mapping for field in optional):
            hits += 1
        return hits / (len(required) + 1)
    
    def get_mapping_confidence(self, mapping: Dict[str, str]) -> float:
        """Alias for validate_mapping for API consistency."""
        return self.validate_mapping(mapping)

    def get_last_source(self) -> str:
        """Returns the last mapping source: cache/ai/heuristic."""
        return self._last_source

    def get_last_ai_confidences(self) -> Dict[str, float]:
        """Returns per-field confidence scores from the last AI mapping attempt."""
        return getattr(self, '_last_ai_confidences', {})

    def get_last_ai_reasoning(self) -> Optional[str]:
        """Returns the reasoning from the last AI mapping attempt."""
        return getattr(self, '_last_ai_reasoning', None)

    # ==================== Active Learning Methods ====================

    def record_correction(
        self,
        source_columns: List[str],
        original_mapping: Dict[str, str],
        corrected_mapping: Dict[str, str],
        vendor: Optional[str]
    ) -> None:
        """
        Record a mapping correction for active learning.

        This tracks which mappings were corrected, enabling the system to learn
        vendor-specific patterns and improve future mapping accuracy.

        Args:
            source_columns: List of column names from the source file
            original_mapping: The mapping before correction
            corrected_mapping: The mapping after human correction
            vendor: Optional vendor name
        """
        import datetime

        # Find what changed
        corrections_made = []
        for field in CANONICAL_FIELDS:
            orig = original_mapping.get(field)
            corrected = corrected_mapping.get(field)
            if orig != corrected:
                corrections_made.append({
                    "field": field,
                    "original": orig,
                    "corrected": corrected
                })

        if not corrections_made:
            return  # No actual corrections

        signature = self._columns_signature(source_columns)
        vendor_key = vendor or "UNKNOWN"

        # Record correction entry
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "vendor": vendor_key,
            "columns_signature": signature,
            "columns": [str(c) for c in source_columns],
            "original_mapping": original_mapping,
            "corrected_mapping": corrected_mapping,
            "corrections": corrections_made
        }

        if not isinstance(self._correction_history.get("corrections"), list):
            self._correction_history["corrections"] = []
        self._correction_history["corrections"].append(entry)

        # Update vendor patterns with learned preferences
        self._update_vendor_patterns(vendor_key, corrections_made, source_columns)

        # Update success rates for the original source
        self._update_success_rates()

        save_json(self._correction_path, self._correction_history)

    def _update_vendor_patterns(
        self,
        vendor: str,
        corrections: List[Dict],
        columns: List[str]
    ) -> None:
        """Learn vendor-specific patterns from corrections."""
        if "vendor_patterns" not in self._correction_history:
            self._correction_history["vendor_patterns"] = {}

        if vendor not in self._correction_history["vendor_patterns"]:
            self._correction_history["vendor_patterns"][vendor] = {
                "preferred_columns": {},
                "learned_keywords": {},
                "correction_count": 0
            }

        patterns = self._correction_history["vendor_patterns"][vendor]
        patterns["correction_count"] = patterns.get("correction_count", 0) + 1

        for correction in corrections:
            field = correction["field"]
            corrected_col = correction["corrected"]

            if corrected_col:
                # Track preferred column for this field
                patterns["preferred_columns"][field] = corrected_col

                # Learn keywords from the corrected column name
                clean = self.clean_header(corrected_col)
                if field not in patterns["learned_keywords"]:
                    patterns["learned_keywords"][field] = []
                if clean not in patterns["learned_keywords"][field]:
                    patterns["learned_keywords"][field].append(clean)

    def _update_success_rates(self) -> None:
        """Update success rate tracking for mapping sources."""
        source = self._last_source
        if "success_rates" not in self._correction_history:
            self._correction_history["success_rates"] = {}

        if source not in self._correction_history["success_rates"]:
            self._correction_history["success_rates"][source] = {"total": 0, "corrected": 0}

        self._correction_history["success_rates"][source]["corrected"] += 1

    def track_mapping_success(self, source: Optional[str] = None) -> None:
        """
        Track a successful mapping (no correction needed).

        Call this when a mapping is confirmed without corrections to
        update success rate statistics.

        Args:
            source: The mapping source (ai/heuristic/cache). Uses last_source if not provided.
        """
        src = source or self._last_source
        if "success_rates" not in self._correction_history:
            self._correction_history["success_rates"] = {}

        if src not in self._correction_history["success_rates"]:
            self._correction_history["success_rates"][src] = {"total": 0, "corrected": 0}

        self._correction_history["success_rates"][src]["total"] += 1
        save_json(self._correction_path, self._correction_history)

    def get_vendor_hints(self, vendor: str) -> Dict[str, Any]:
        """
        Get learned patterns for a specific vendor.

        Returns vendor-specific preferences learned from past corrections,
        including preferred columns and learned keywords.

        Args:
            vendor: The vendor name

        Returns:
            Dict with preferred_columns, learned_keywords, and correction_count
        """
        return self._correction_history.get("vendor_patterns", {}).get(vendor, {})

    def get_success_rates(self) -> Dict[str, Dict[str, Any]]:
        """
        Get success rates for different mapping sources.

        Returns:
            Dict mapping source name to {total, corrected, rate} stats
        """
        rates = self._correction_history.get("success_rates", {})
        result = {}
        for source, stats in rates.items():
            total = stats.get("total", 0)
            corrected = stats.get("corrected", 0)
            result[source] = {
                "total": total,
                "corrected": corrected,
                "success_rate": (total - corrected) / total if total > 0 else 1.0
            }
        return result

    def get_correction_history(self, vendor: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """
        Get recent correction history, optionally filtered by vendor.

        Args:
            vendor: Optional vendor to filter by
            limit: Maximum number of entries to return

        Returns:
            List of correction entries, most recent first
        """
        corrections = self._correction_history.get("corrections", [])

        if vendor:
            corrections = [c for c in corrections if c.get("vendor") == vendor]

        # Return most recent first
        return list(reversed(corrections[-limit:]))
