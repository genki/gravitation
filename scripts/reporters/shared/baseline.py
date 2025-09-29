#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

_BASELINE_PATH = Path('config/baseline_conditions.json')


def load(section: str | None = None) -> Dict[str, Any]:
    if not _BASELINE_PATH.exists():
        return {}
    try:
        payload = json.loads(_BASELINE_PATH.read_text())
        if not isinstance(payload, dict):
            return {}
        if section:
            piece = payload.get(section)
            return piece if isinstance(piece, dict) else {}
        return payload
    except Exception:
        return {}


def get(section: str, key: str, default: Any = None) -> Any:
    cfg = load(section)
    return cfg.get(key, default) if isinstance(cfg, dict) else default

