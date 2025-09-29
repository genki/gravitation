#!/usr/bin/env python3
from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any, Dict

_FAIR_PATH = Path('config/fair.json')


def load(section: str | None = None) -> Dict[str, Any]:
    """Load fairness configuration from config/fair.json."""
    if not _FAIR_PATH.exists():
        return {}
    try:
        payload = json.loads(_FAIR_PATH.read_text(encoding='utf-8'))
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    if section:
        value = payload.get(section)
        return value if isinstance(value, dict) else {}
    return payload


def get(section: str, key: str, default: Any = None) -> Any:
    cfg = load(section)
    return cfg.get(key, default) if isinstance(cfg, dict) else default


def get_sha256() -> str:
    if not _FAIR_PATH.exists():
        return ''
    try:
        return hashlib.sha256(_FAIR_PATH.read_bytes()).hexdigest()
    except Exception:
        return ''


def path() -> Path:
    return _FAIR_PATH


__all__ = ['load', 'get', 'get_sha256', 'path']
