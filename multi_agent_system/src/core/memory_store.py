import json
from pathlib import Path
from typing import Any


def get_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def ensure_memory_dir() -> Path:
    mem_dir = get_repo_root() / "agent_memory"
    mem_dir.mkdir(exist_ok=True)
    return mem_dir


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
