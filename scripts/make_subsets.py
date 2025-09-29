#!/usr/bin/env python3
from __future__ import annotations
"""
SPARC Table1のメタからサブセット(all.txtを母集団)を自動生成する。

出力先: data/sparc/sets/
 - lsb.txt / hsb.txt: SBdisk0_Lsunpc2 の下位1/3・上位1/3
 - q1.txt / q2.txt / q3.txt: 品質指標Qでのフィルタ
 - clean_for_fit.txt: scripts/filter_sample.py に委譲（学習向けクリーンセット）
"""
import statistics as st
from pathlib import Path
from typing import Dict, List, Tuple

from scripts.fit_sparc_fdbl import read_sparc_meta


def load_all_names(p: Path) -> List[str]:
    return [
        ln.strip() for ln in p.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.strip().startswith('#')
    ]


def build_meta_index(table1: Path, names: List[str]):
    metas: Dict[str, Tuple[float | None, int | None]] = {}
    for nm in names:
        m = read_sparc_meta(table1, nm)
        if m is None:
            metas[nm] = (None, None)
        else:
            metas[nm] = (getattr(m, 'SBdisk0_Lsunpc2', None), getattr(m, 'Q', None))
    return metas


def write_set(path: Path, names: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(names) + "\n", encoding="utf-8")


def main() -> int:
    sets = Path("data/sparc/sets")
    all_txt = sets / "all.txt"
    table1 = Path("data/sparc/SPARC_Lelli2016c.mrt")
    if not all_txt.exists():
        raise SystemExit(f"not found: {all_txt}")
    if not table1.exists():
        raise SystemExit(f"not found: {table1}")
    names = load_all_names(all_txt)
    meta = build_meta_index(table1, names)

    # LSB/HSB: SBdisk0_Lsunpc2 の分位で閾値を決定（下位1/3, 上位1/3）
    sb_pairs = [(nm, meta[nm][0]) for nm in names if isinstance(meta[nm][0], (int, float))]
    sb_vals = [float(v) for _, v in sb_pairs]
    if len(sb_vals) >= 9:
        sb_sorted = sorted(sb_vals)
        lo_thr = sb_sorted[len(sb_sorted)//3]
        hi_thr = sb_sorted[(2*len(sb_sorted))//3]
        lsb = [nm for nm, v in sb_pairs if float(v) <= lo_thr]
        hsb = [nm for nm, v in sb_pairs if float(v) >= hi_thr]
        # Optional: log diffs vs previous sets for debugging
        def _load_existing(p: Path) -> set[str]:
            try:
                return set(load_all_names(p)) if p.exists() else set()
            except Exception:
                return set()
        prev_lsb = _load_existing(sets / "lsb.txt")
        prev_hsb = _load_existing(sets / "hsb.txt")
        cur_lsb = set(lsb)
        cur_hsb = set(hsb)
        add_lsb = sorted(cur_lsb - prev_lsb)
        del_lsb = sorted(prev_lsb - cur_lsb)
        add_hsb = sorted(cur_hsb - prev_hsb)
        del_hsb = sorted(prev_hsb - cur_hsb)
        # Write new sets
        write_set(sets / "lsb.txt", lsb)
        write_set(sets / "hsb.txt", hsb)
        print(f"wrote lsb.txt({len(lsb)}), hsb.txt({len(hsb)})")
        # Emit a human-readable diff log under public reports for traceability
        try:
            from datetime import datetime
            rep = Path("server/public/reports")
            rep.mkdir(parents=True, exist_ok=True)
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            logp = rep / f"lsb_hsb_diff_{ts}.txt"
            lines = []
            lines.append(f"LSB threshold <= {lo_thr}\n")
            lines.append("[LSB added]\n" + ("\n".join(add_lsb) if add_lsb else "(none)") + "\n\n")
            lines.append("[LSB removed]\n" + ("\n".join(del_lsb) if del_lsb else "(none)") + "\n\n")
            lines.append(f"HSB threshold >= {hi_thr}\n")
            lines.append("[HSB added]\n" + ("\n".join(add_hsb) if add_hsb else "(none)") + "\n\n")
            lines.append("[HSB removed]\n" + ("\n".join(del_hsb) if del_hsb else "(none)") + "\n")
            logp.write_text("".join(lines), encoding="utf-8")
            print("wrote diff log:", logp)
        except Exception as e:
            print("warn: failed to write LSB/HSB diff log:", e)
    else:
        print("warn: insufficient SB entries to split LSB/HSB")

    # Q-based splits
    q_groups: Dict[int, List[str]] = {1: [], 2: [], 3: []}
    for nm in names:
        q = meta[nm][1]
        if isinstance(q, int) and q in q_groups:
            q_groups[q].append(nm)
    for q, arr in q_groups.items():
        if arr:
            write_set(sets / f"q{q}.txt", arr)
            print(f"wrote q{q}.txt({len(arr)})")
    # optional: build clean_for_fit via filter_sample
    try:
        import subprocess as sp
        sp.run(
            ["bash", "-lc",
             "PYTHONPATH=. .venv/bin/python scripts/filter_sample.py --out data/sparc/sets/clean_for_fit.txt"],
            check=True,
        )
    except Exception as e:
        print("warn: failed to build clean_for_fit.txt:", e)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
