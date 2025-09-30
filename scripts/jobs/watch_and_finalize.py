#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess as sp
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def read_holdout_brief(holdout: str) -> str:
    p = REPO / 'server/public/reports' / f'{holdout}_holdout.json'
    if not p.exists():
        return '(結果JSON未検出)'
    try:
        j = json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return '(結果JSON読取失敗)'
    delta = j.get('delta') or {}
    d_shift = delta.get('FDB_minus_shift')
    s = j.get('S_shadow') or j.get('indicators', {}).get('S_shadow') or {}
    perm = s.get('perm') or {}
    svals = (s.get('values') or {})
    line = (
        f"ΔAICc(FDB−shift)={d_shift:.1f}, "
        f"S_shadow(global)={(svals.get('global') if svals else float('nan')):.3f}, "
        f"p_perm={(perm.get('p_perm_one_sided_pos') if perm else float('nan')):.3g}"
    )
    return line


def write_memo(holdout: str, title_hint: str) -> Path:
    now = datetime.now(timezone.utc).astimezone()
    stamp = now.strftime('%Y-%m-%d_%H%M')
    memo = REPO / 'memo' / f'run_{stamp}_a4_full_{holdout}.md'
    brief = read_holdout_brief(holdout)
    memo.write_text(
        "# A-4 FULL 完了メモ\n\n"
        f"## 結果サマリ\n- {holdout}: {brief}\n\n"
        "## 生成物\n"
        f"- server/public/reports/{holdout}_holdout.html\n"
        f"- server/public/reports/{holdout}_holdout.json\n\n"
        "## 次アクション\n- SOTAへ反映済み。必要なら追加FULL/再スイープ。\n",
        encoding='utf-8'
    )
    return memo


def main() -> int:
    ap = argparse.ArgumentParser(description='Watch a BG job (by meta JSON) and finalize SOTA + notify on finish')
    ap.add_argument('--meta', required=True, help='tmp/jobs/<name>_*.json')
    ap.add_argument('--holdout', required=True)
    args = ap.parse_args()
    meta = json.loads(Path(args.meta).read_text(encoding='utf-8'))
    pid = int(meta.get('pid') or 0)
    if pid <= 0:
        print('[watch] invalid pid in meta')
        return 2
    print(f"[watch] waiting pid={pid} ...")
    while pid_alive(pid):
        time.sleep(15)
    print('[watch] job finished; rebuilding SOTA ...')
    # Rebuild SOTA (best-effort)
    sp.call(['bash', '-lc', 'PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py'], cwd=str(REPO))
    # Write memo and notify
    memo = write_memo(args.holdout, Path(args.meta).name)
    os.environ.pop('AUTO_PUBLISH_SITE', None)
    sp.call(['bash', '-lc', 'make notify-done-site'], cwd=str(REPO))
    print(f'[watch] done. memo={memo}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

