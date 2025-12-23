"""Configuration helpers for world_builder."""
import json
from pathlib import Path
from typing import Any, Dict


DEFAULT_CONFIG = {
    "SHOW_ADVANCED_ERRORS": False,
    "AUTOSAVE_ENABLED": True,
}


def load_config(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return DEFAULT_CONFIG.copy()
    try:
        with p.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(path: str | Path, cfg: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2)
