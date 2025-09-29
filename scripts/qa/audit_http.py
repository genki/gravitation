#!/usr/bin/env python3
from __future__ import annotations
import json, urllib.request, os

def check(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return (200 <= r.status < 300)
    except Exception:
        return False

def main() -> int:
    base = os.environ.get('BASE') or 'http://localhost:3131'
    targets = {
        'used_ids_csv_http': f'{base}/state_of_the_art/used_ids.csv',
        'cv_shared_summary_http': f'{base}/reports/cv_shared_summary.html',
        'notifications_http': f'{base}/notifications/',
    }
    results = {k: check(v) for k, v in targets.items()}
    ok = all(results.values())
    print(json.dumps({'ok': ok, 'http': results}))
    return 0 if ok else 1

if __name__ == '__main__':
    raise SystemExit(main())
