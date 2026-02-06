"""
Data-driven type inference for column classification.

This module analyzes actual cell values to infer the semantic type of a column,
complementing keyword-based matching in the SchemaAgent.
"""

import re
from typing import List, Dict, Any, Set
import pandas as pd

# Date patterns with their format descriptions
DATE_PATTERNS = [
    (r'^\d{4}-\d{2}-\d{2}$', "YYYY-MM-DD"),
    (r'^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}', "YYYY-MM-DD HH:MM"),
    (r'^\d{2}/\d{2}/\d{4}$', "MM/DD/YYYY"),
    (r'^\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}', "MM/DD/YYYY HH:MM"),
    (r'^\d{4}/\d{2}/\d{2}$', "YYYY/MM/DD"),
    (r'^\d{4}-\d{2}$', "YYYY-MM"),
    (r'^\d{2}-[A-Za-z]{3}-\d{2,4}$', "DD-Mon-YY"),
    (r'^[A-Za-z]{3}\s+\d{1,2},?\s+\d{4}$', "Mon DD, YYYY"),
    (r'^\d{1,2}/\d{1,2}/\d{2,4}$', "M/D/YY"),
]

# Common language names in interpreter services (lowercase for matching)
KNOWN_LANGUAGES: Set[str] = {
    # Top languages
    "spanish", "mandarin", "cantonese", "vietnamese", "korean", "arabic",
    "russian", "portuguese", "french", "haitian creole", "polish", "bengali",
    "japanese", "italian", "urdu", "hindi", "tagalog", "farsi", "persian",
    # African languages
    "albanian", "somali", "swahili", "amharic", "tigrinya", "oromo", "yoruba",
    # Asian languages
    "burmese", "nepali", "thai", "khmer", "cambodian", "laotian", "lao",
    "indonesian", "malay", "filipino", "cebuano", "ilocano", "hmong",
    "punjabi", "gujarati", "tamil", "telugu", "malayalam", "kannada", "marathi",
    # European languages
    "turkish", "greek", "german", "dutch", "hebrew", "romanian", "ukrainian",
    "serbian", "croatian", "bosnian", "macedonian", "bulgarian", "czech",
    "slovak", "hungarian", "lithuanian", "latvian", "estonian", "finnish",
    "swedish", "norwegian", "danish", "icelandic",
    # Other
    "asl", "american sign language", "sign language", "dari", "pashto", "kurdish",
    "armenian", "georgian", "azerbaijani", "uzbek", "kazakh", "mongolian",
}


class TypeInferenceEngine:
    """Analyzes column values to infer semantic type for schema mapping."""

    def __init__(self, sample_size: int = 100):
        """
        Initialize the type inference engine.

        Args:
            sample_size: Maximum number of rows to sample for analysis
        """
        self.sample_size = sample_size

    def analyze_column(self, series: pd.Series) -> Dict[str, Any]:
        """
        Analyze a column and return type inference results.

        Args:
            series: Pandas Series containing the column data

        Returns:
            Dict with 'type', 'confidence', and 'all_scores' keys
        """
        sample = series.dropna().head(self.sample_size)
        if len(sample) == 0:
            return {"type": "unknown", "confidence": 0.0, "all_scores": {}}

        results = {
            "date": self._score_date(sample),
            "language": self._score_language(sample),
            "minutes": self._score_minutes(sample),
            "charge": self._score_charge(sample),
            "rate": self._score_rate(sample),
        }

        # Find the best matching type
        best_type = max(results, key=results.get)
        best_score = results[best_type]

        # Only return a type if confidence is meaningful
        if best_score < 0.3:
            return {"type": "unknown", "confidence": best_score, "all_scores": results}

        return {
            "type": best_type,
            "confidence": best_score,
            "all_scores": results
        }

    def analyze_all_columns(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """
        Analyze all columns in a DataFrame.

        Args:
            df: DataFrame to analyze

        Returns:
            Dict mapping column name to type inference results
        """
        results = {}
        for col in df.columns:
            results[col] = self.analyze_column(df[col])
        return results

    def _score_date(self, sample: pd.Series) -> float:
        """Score likelihood this column contains dates."""
        if len(sample) == 0:
            return 0.0

        matches = 0
        for val in sample.astype(str):
            val_clean = str(val).strip()
            # Check if it's already a date type
            if hasattr(val, 'strftime'):
                matches += 1
                continue
            # Take first part if datetime with time
            val_date = val_clean.split()[0] if ' ' in val_clean else val_clean
            for pattern, _ in DATE_PATTERNS:
                if re.match(pattern, val_clean) or re.match(pattern, val_date):
                    matches += 1
                    break

        return matches / len(sample)

    def _score_language(self, sample: pd.Series) -> float:
        """Score likelihood this column contains language names."""
        if len(sample) == 0:
            return 0.0

        matches = 0
        for val in sample.astype(str):
            val_clean = val.strip().lower()
            # Direct match
            if val_clean in KNOWN_LANGUAGES:
                matches += 1
            # Check if language name is contained (e.g., "Spanish - Medical")
            elif any(lang in val_clean for lang in KNOWN_LANGUAGES if len(lang) > 3):
                matches += 0.8  # Partial credit for substring match

        return min(1.0, matches / len(sample))

    def _score_minutes(self, sample: pd.Series) -> float:
        """Score likelihood this column contains duration in minutes."""
        try:
            # Clean and convert to numeric
            cleaned = sample.astype(str).str.replace(',', '', regex=False)
            cleaned = cleaned.str.replace(r'\s*min(utes?)?\s*$', '', regex=True, flags=re.IGNORECASE)
            numeric = pd.to_numeric(cleaned, errors='coerce')
            valid = numeric.dropna()

            if len(valid) == 0:
                return 0.0

            # Minutes typically range from 0.5 to 300 (5 hours max)
            in_range = ((valid >= 0) & (valid <= 300)).sum()
            ratio = in_range / len(valid)

            # Boost score if mean is in typical call duration range (3-60 min)
            mean_val = valid.mean()
            if 1 <= mean_val <= 60:
                ratio = min(1.0, ratio + 0.2)
            elif 60 < mean_val <= 120:
                ratio = min(1.0, ratio + 0.1)

            # Penalize if values look like currency (too precise decimals)
            decimal_places = cleaned.str.extract(r'\.(\d+)$')[0].str.len()
            if decimal_places.mean() > 2:
                ratio *= 0.7  # Likely currency, not minutes

            return ratio
        except Exception:
            return 0.0

    def _score_charge(self, sample: pd.Series) -> float:
        """Score likelihood this column contains monetary charges."""
        try:
            str_sample = sample.astype(str)

            # Look for currency indicators
            has_dollar = str_sample.str.contains(r'^\s*\$', regex=True).sum()
            has_currency_word = str_sample.str.lower().str.contains(r'usd|eur|gbp').sum()

            # Clean and parse
            cleaned = str_sample.str.replace(r'[\$,]', '', regex=True)
            cleaned = cleaned.str.strip()
            numeric = pd.to_numeric(cleaned, errors='coerce')
            valid = numeric.dropna()

            if len(valid) == 0:
                return 0.0

            # Charges typically $0.01 to $10000
            in_range = ((valid >= 0) & (valid <= 10000)).sum()
            ratio = in_range / len(valid)

            # Strong boost for currency symbols
            currency_ratio = (has_dollar + has_currency_word) / len(sample)
            if currency_ratio > 0.1:
                ratio = min(1.0, ratio + 0.3)

            # Typical per-call charges are $0.50-$500
            mean_val = valid.mean()
            if 0.1 <= mean_val <= 500:
                ratio = min(1.0, ratio + 0.1)

            # Check for 2 decimal places (currency formatting)
            decimal_places = cleaned.str.extract(r'\.(\d+)$')[0].str.len()
            if 1.5 <= decimal_places.mean() <= 2.5:
                ratio = min(1.0, ratio + 0.1)

            return ratio
        except Exception:
            return 0.0

    def _score_rate(self, sample: pd.Series) -> float:
        """Score likelihood this column contains per-minute rates."""
        try:
            str_sample = sample.astype(str)

            # Clean and parse
            cleaned = str_sample.str.replace(r'[\$,]', '', regex=True)
            numeric = pd.to_numeric(cleaned, errors='coerce')
            valid = numeric.dropna()

            if len(valid) == 0:
                return 0.0

            # Rates typically $0.10 to $10.00 per minute
            in_range = ((valid >= 0.05) & (valid <= 15.0)).sum()
            ratio = in_range / len(valid)

            # Strong indicator: low variance (rates are usually consistent)
            if len(valid) > 5:
                std = valid.std()
                mean = valid.mean()
                if mean > 0:
                    cv = std / mean  # Coefficient of variation
                    if cv < 0.5:  # Low variation
                        ratio = min(1.0, ratio + 0.3)

            # Typical OPI rates: $0.50-$3.00/min
            mean_val = valid.mean()
            if 0.3 <= mean_val <= 5.0:
                ratio = min(1.0, ratio + 0.2)

            return ratio
        except Exception:
            return 0.0


def get_known_languages() -> Set[str]:
    """Return the set of known language names for external use."""
    return KNOWN_LANGUAGES.copy()
