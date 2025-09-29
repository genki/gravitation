#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

def main() -> int:
    checks = {
        'used_ids_csv': Path('server/public/state_of_the_art/used_ids.csv').exists(),
        'cv_shared_summary': Path('server/public/reports/cv_shared_summary.html').exists(),
    }
    ok = all(checks.values())
    out = {'ok': ok, 'checks': checks}
    Path('server/public/state_of_the_art').mkdir(parents=True, exist_ok=True)
    (Path('server/public/state_of_the_art')/ 'audit_links.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print(json.dumps(out))
    return 0 if ok else 1

if __name__ == '__main__':
    raise SystemExit(main())
