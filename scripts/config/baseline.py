#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

_BASELINE_PATH = Path('config/baseline_conditions.json')


def load_baseline(section: str | None = None) -> Dict[str, Any]:
    if not _BASELINE_PATH.exists():
        return {}
    try:
        data = json.loads(_BASELINE_PATH.read_text())
        if not isinstance(data, dict):
            return {}
        if section:
            value = data.get(section)
            return value if isinstance(value, dict) else {}
        return data
    except Exception:
        return {}


def get_value(section: str, key: str, default: Any = None) -> Any:
    cfg = load_baseline(section)
    return cfg.get(key, default) if isinstance(cfg, dict) else default

