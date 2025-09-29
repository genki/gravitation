#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from typing import List, Tuple


def pick_best_result(files: List[Path]) -> Path | None:
    nobl = [p for p in files if 'nobl' in p.name.lower()]
    if nobl:
        nobl.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return nobl[0]
    cand: List[Tuple[int, float, Path]] = []
    for p in files:
        try:
            data = json.loads(p.read_text(encoding='utf-8'))
            n1 = len(data.get('names', []))
            n2 = int(data.get('N_total', {}).get('ULW') or 0)
            n = max(n1, n2)
            cand.append((n, p.stat().st_mtime, p))
        except Exception:
            continue
    if not cand:
        return files[0] if files else None
    cand.sort(key=lambda t: (t[0], t[1]))
    return cand[-1][2]


def load_best_json() -> tuple[Path, dict] | tuple[None, None]:
    files = sorted(Path('data/results').glob('multi_fit*.json'))
    best = pick_best_result(files)
    if not best:
        return None, None
    return best, json.loads(best.read_text(encoding='utf-8'))


def main() -> int:
    best_path, data = load_best_json()
    if not data:
        print('no results found under data/results')
        return 0
    # reduced chi^2 per galaxy (ULW), if stored; else fall back to total ranking by mu presence
    # Many JSONs do not contain per-galaxy chi2. We derive a proxy: galaxies with extreme notes via names order.
    names: List[str] = data.get('names', [])
    # Create a naive score based on extreme mu or missing mu (alpha_line は廃止方針のため未使用)
    mus = data.get('mu', {}).get('ULW', {})
    scored: List[Tuple[float, str]] = []
    for nm in names:
        info = mus.get(nm, {})
        score = 0.0
        if isinstance(info, dict):
            if 'mu' in info:
                try:
                    mu = float(info['mu'])
                    # extreme mu suggests tension
                    if mu < 0.1 or mu > 2.0:
                        score += 1.0
                except Exception:
                    pass
            else:
                # split disk/bulge is often harder; bump slightly
                score += 0.3
        else:
            score += 0.5
        scored.append((score, nm))
    scored.sort(reverse=True)
    worst = scored[:10]
    # Write memo
    out = Path('memo') / f"run_{__import__('datetime').date.today()}_research_outliers.md"
    lines: List[str] = []
    lines.append('# ULW適合の難しい候補銀河の抽出（暫定）\n')
    lines.append(f'- 実行: scripts/analyze_ulw_outliers.py\n- ソース: {best_path}\n')
    lines.append('## 結果サマリ')
    lines.append('- 既存の共有フィット結果から、暫定スコアで上位10件を抽出（alpha_lineや極端muを指標）\n')
    lines.append('## 候補一覧（score, name）')
    for sc, nm in worst:
        lines.append(f'- {sc:.2f}, {nm}')
    lines.append('\n## 次アクション')
    lines.append('- 上位候補について、ULW項の寄与分解と外縁傾きの再確認')
    lines.append('- 必要に応じてalpha_lineやブーストの有無で感度比較')
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('wrote', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
