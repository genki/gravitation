#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import shutil


def maybe_copy(src: Path, dst: Path) -> None:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print('copied', src, '->', dst)


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    out_dir = root / 'paper' / 'figures'
    out_dir.mkdir(parents=True, exist_ok=True)
    # Prefer existing SOTA/report figures
    candidates = [
        (root / 'server/public/reports' / 'ngc3198_outer_gravity.png', out_dir / 'ngc3198_outer_gravity.png'),
        (root / 'server/public/reports' / 'ne_null_ngc3198.png', out_dir / 'ne_null_ngc3198.png'),
        (root / 'server/public/reports' / 'sensitivity_ngc3198.png', out_dir / 'sensitivity_ngc3198.png'),
        (root / 'server/public/reports' / 'cluster' / 'bullet_kappa_panels.png', out_dir / 'bullet_kappa_panels.png'),
    ]
    for s, d in candidates:
        maybe_copy(s, d)
    # Also copy representative SOTA panel if present
    for name in ['sota_improvement_hist.png', 'sota_redchi2_scatter.png', 'sota_vr_panel.png']:
        p = root / 'paper' / 'figures' / name
        if not p.exists():
            q = root / 'assets' / 'figures' / name
            maybe_copy(q, p)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
