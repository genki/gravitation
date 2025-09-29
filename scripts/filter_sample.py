#!/usr/bin/env python3
from __future__ import annotations
"""
SPARC母集団(all.txt)からフィッティングに不適な銀河を除外し、
クリーンな学習用セットを生成する。

除外基準(デフォルト):
  - 品質Q > max_q（既定2）
  - 傾き(傾斜) i_deg not in [i_min, i_max]（既定[30, 80]）
  - 近傍/外乱候補リストに含まれる（nearby.txt, exclude_env.txt）
  - データ点が少ない (N_R < min_pts; 既定8)
  - 半径被覆が不十分 (max(R) < min_R_over_Rd * Rd; 既定1.5)

使い方:
  PYTHONPATH=. .venv/bin/python scripts/filter_sample.py \
    --all data/sparc/sets/all.txt --out data/sparc/sets/clean_for_fit.txt
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

import numpy as np

from scripts.fit_sparc_fdbl import read_sparc_meta, read_sparc_massmodels


def load_names(p: Path) -> List[str]:
    return [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.strip().startswith('#')]


def write_names(p: Path, arr: Iterable[str]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(arr) + "\n", encoding="utf-8")


@dataclass
class Criteria:
    max_q: int = 2
    i_min: float = 30.0
    i_max: float = 80.0
    min_pts: int = 8
    min_R_over_Rd: float = 1.5


def should_exclude(name: str, crit: Criteria, table1: Path,
                   mrt: Path,
                   env_lists: List[Path]) -> Tuple[bool, str]:
    # environment lists
    for lst in env_lists:
        if lst.exists() and name in set(load_names(lst)):
            return True, f"env_list:{lst.name}"

    meta = read_sparc_meta(table1, name)
    if meta is None:
        return True, "meta_missing"
    if isinstance(meta.Q, int) and meta.Q > crit.max_q:
        return True, f"Q>{crit.max_q}"
    if isinstance(meta.Inc_deg, float):
        if not (crit.i_min <= float(meta.Inc_deg) <= crit.i_max):
            return True, "inclination_out_of_range"

    # coverage / datapoints
    try:
        rc = read_sparc_massmodels(mrt, name)
        n = len(rc.R)
        if n < crit.min_pts:
            return True, "few_points"
        Rd = float(meta.Rdisk_kpc or 0.0)
        if Rd > 0:
            if float(np.nanmax(rc.R)) < crit.min_R_over_Rd * Rd:
                return True, "short_radius_coverage"
    except SystemExit:
        return True, "rc_missing"
    except Exception:
        return True, "rc_error"

    return False, ""


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--all', type=Path, default=Path('data/sparc/sets/all.txt'))
    ap.add_argument('--out', type=Path, default=Path('data/sparc/sets/clean_for_fit.txt'))
    ap.add_argument('--max-q', type=int, default=2)
    ap.add_argument('--i-min', type=float, default=30.0)
    ap.add_argument('--i-max', type=float, default=80.0)
    ap.add_argument('--min-pts', type=int, default=8)
    ap.add_argument('--min-R-over-Rd', type=float, default=1.5)
    ap.add_argument('--nearby', type=Path, default=Path('data/sparc/sets/nearby.txt'))
    ap.add_argument('--exclude-env', type=Path, default=Path('data/sparc/sets/exclude_env.txt'))
    args = ap.parse_args()

    crit = Criteria(max_q=args.max_q, i_min=args.i_min, i_max=args.i_max,
                    min_pts=args.min_pts, min_R_over_Rd=args.min_R_over_Rd)
    names = load_names(args.all)
    table1 = Path('data/sparc/SPARC_Lelli2016c.mrt')
    mrt = Path('data/sparc/MassModels_Lelli2016c.mrt')
    env_lists = [args.nearby, args.exclude_env]

    kept: List[str] = []
    dropped: List[Tuple[str, str]] = []
    for nm in names:
        ex, why = should_exclude(nm, crit, table1, mrt, env_lists)
        if ex:
            dropped.append((nm, why))
        else:
            kept.append(nm)

    write_names(args.out, kept)
    # write audit log
    logp = args.out.with_suffix('.log')
    lines = [f"kept {len(kept)} / total {len(names)}"]
    lines.append("# dropped list: name,reason")
    for nm, why in dropped:
        lines.append(f"{nm},{why}")
    logp.write_text("\n".join(lines) + "\n", encoding='utf-8')

    print(f"wrote {args.out} (kept={len(kept)}, dropped={len(dropped)})")
    print(f"audit: {logp}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

