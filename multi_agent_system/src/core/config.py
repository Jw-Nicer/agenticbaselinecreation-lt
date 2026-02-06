import json
from pathlib import Path
from typing import Dict, Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def get_schema_config() -> Dict[str, Any]:
    defaults = {
        "auto_learn": True,
        "require_manual_approval": False,
        "min_field_confidence": 0.75,
        "min_data_confidence": 0.70,
        "min_final_confidence": 0.60,
        "auto_approve_field_confidence": 0.90,
        "auto_approve_data_confidence": 0.85,
        "heuristic_validation": {
            "enabled": True,
            "min_type_confidence": 0.65,
            "min_date_parse": 0.6,
            "min_numeric_rate": 0.6,
            "min_language_match": 0.3
        },
        "heuristic_ai_validation": {
            "enabled": True,
            "min_field_confidence": 0.6,
            "require_overall_ok": True,
            "min_overall_confidence": 0.65
        }
    }
    cfg_path = _repo_root() / "config" / "schema_config.json"
    overrides = _load_json(cfg_path)
    if not isinstance(overrides, dict):
        return defaults
    merged = {**defaults, **overrides}
    return merged
