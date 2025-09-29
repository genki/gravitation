#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess as sp
from pathlib import Path

def run(cmd: list[str]) -> tuple[int, dict]:
    p = sp.run(' '.join(cmd), shell=True, capture_output=True, text=True)
    try:
        data = json.loads(p.stdout.strip() or '{}')
    except Exception:
        data = {'raw': p.stdout}
    return p.returncode, data

def main() -> int:
    Path('server/public/state_of_the_art').mkdir(parents=True, exist_ok=True)
    rc1, cv = run(['PYTHONPATH=.', './.venv/bin/python', 'scripts/qa/audit_consistency.py'])
    rc2, lk = run(['PYTHONPATH=.', './.venv/bin/python', 'scripts/qa/audit_links.py'])
    rc3, hp = run(['PYTHONPATH=.', './.venv/bin/python', 'scripts/qa/audit_http.py'])
    rc4, sp = run(['PYTHONPATH=.', './.venv/bin/python', 'scripts/qa/audit_shared_params.py'])
    rc5, sh = run(['PYTHONPATH=.', './.venv/bin/python', 'scripts/qa/audit_shared_sha.py'])
    # Rep6 presence / minimal structure
    rep6_ok = False
    try:
        r6 = Path('server/public/reports/surface_vs_volumetric.html')
        if r6.exists():
            html = r6.read_text(encoding='utf-8')
            required = ['AICc (Surface)', 'AICc (Volumetric', 'rχ²', 'ΔAICc']
            rep6_ok = all(s in html for s in required)
    except Exception:
        rep6_ok = False

    ok = (rc1 == 0) and (rc2 == 0) and (rc3 == 0) and (rc4 == 0) and (rc5 == 0) and rep6_ok
    out = {'ok': ok, 'cv': cv, 'links': lk, 'http': hp, 'shared_params': sp, 'shared_sha': sh, 'rep6': {'ok': rep6_ok}}
    (Path('server/public/state_of_the_art')/'audit.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print(json.dumps(out, indent=2))
    return 0 if ok else 1

if __name__ == '__main__':
    raise SystemExit(main())
