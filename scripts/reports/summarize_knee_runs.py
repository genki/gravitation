#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _load_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return {}


def _extract_metrics(d: dict) -> Tuple[float, float, float]:
    # returns (S_shadow_global, p_perm_one_sided_pos, delta_FDB_minus_shift)
    ind = d.get('indicators') or {}
    s_val = float('nan')
    p_perm = float('nan')
    s = ind.get('S_shadow') or {}
    if isinstance(s, dict):
        vals = s.get('values') or {}
        if isinstance(vals, dict):
            try:
                s_val = float(vals.get('global', float('nan')))
            except Exception:
                s_val = float('nan')
        perm = s.get('perm') or {}
        if isinstance(perm, dict):
            try:
                p_perm = float(perm.get('p_perm_one_sided_pos', float('nan')))
            except Exception:
                p_perm = float('nan')
    delta = d.get('delta') or {}
    try:
        d_shift = float(delta.get('FDB_minus_shift', float('nan')))
    except Exception:
        d_shift = float('nan')
    return s_val, p_perm, d_shift


def _extract_knobs(d: dict) -> Tuple[str, str, str]:
    meta = d.get('metadata') or {}
    env = meta.get('env_overrides') or {}
    q = str(env.get('BULLET_Q_KNEE', '—'))
    p = str(env.get('BULLET_P', '—'))
    xs = str(env.get('BULLET_XI_SAT', '—'))
    return q, p, xs


def _row_key(m: Tuple[float, float, float]) -> Tuple[int, float, float]:
    s_val, p_perm, d_shift = m
    # sort: prefer finite p (ascending), then larger S, then more negative delta
    p_rank = 0 if (p_perm == p_perm) else 1
    return (p_rank, p_perm if p_perm == p_perm else math.inf, -s_val if s_val == s_val else math.inf)


def summarize_holdout(holdout: str, outdir: Path) -> Path:
    runs_dir = Path('server/public/reports/holdout_runs')
    entries: List[Tuple[str, Path, dict]] = []
    if runs_dir.exists():
        for p in sorted(runs_dir.glob(f'{holdout}_*_*.json')):
            kind = 'FULL' if p.stem.endswith('_full') else 'FAST'
            d = _load_json(p)
            entries.append((kind, p, d))
    # Fallback: current single JSON
    cur = Path(f'server/public/reports/{holdout}_holdout.json')
    if cur.exists():
        d = _load_json(cur)
        entries.append(('CURRENT', cur, d))

    outdir.mkdir(parents=True, exist_ok=True)
    html: List[str] = []
    html.append('<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">')
    html.append(f'<title>{holdout}: A-3 knee summary</title><link rel="stylesheet" href="../styles.css"></head><body>')
    html.append('<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div>'
                '<nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>')
    html.append(f'<main class="wrap"><h1>{holdout}: A‑3（W_eff“膝”）サマリ</h1>')

    def render(kind_filter: str, title: str) -> None:
        data: List[Tuple[Tuple[float, float, float], Tuple[str, str, str], Path]] = []
        for kind, p, d in entries:
            if kind_filter == 'ALL' or kind == kind_filter:
                m = _extract_metrics(d)
                k = _extract_knobs(d)
                data.append((m, k, p))
        if not data:
            return
        data.sort(key=lambda x: _row_key(x[0]))
        html.append(f'<div class=card><h2>{title}</h2>')
        html.append('<table class="t"><thead><tr><th>#</th><th>q_knee</th><th>p</th><th>xi_sat</th><th>S_shadow</th><th>p_perm(+)</th><th>ΔAICc(FDB−shift)</th><th>JSON</th><th>Holdout</th></tr></thead><tbody>')
        for i, (m, k, p) in enumerate(data[:20], 1):
            s_val, p_perm, d_shift = m
            q, pp, xs = k
            jrel = p.relative_to(outdir.parent)
            hold_html = Path(f'server/public/reports/{holdout}_holdout.html')
            hrel = hold_html.relative_to(outdir.parent) if hold_html.exists() else ''
            html.append('<tr>'
                        f'<td>{i}</td><td>{q}</td><td>{pp}</td><td>{xs}</td>'
                        f'<td>{"{:.3f}".format(s_val) if s_val == s_val else "nan"}</td>'
                        f'<td>{"{:.2g}".format(p_perm) if p_perm == p_perm else "nan"}</td>'
                        f'<td>{"{:+.2f}".format(d_shift) if d_shift == d_shift else "nan"}</td>'
                        f'<td><a href="{jrel}">json</a></td>'
                        f'<td>{f"<a href=\"{hrel}\">page</a>" if hrel else ""}</td>'
                        '</tr>')
        html.append('</tbody></table></div>')

    render('FULL', 'FULL（perm=5000）ランキング')
    render('FAST', 'FAST（perm≈1200–2000）ランキング')
    render('CURRENT', '最新実行（参考）')
    html.append('</main></body></html>')

    out = Path('server/public/reports') / f'{holdout}_a3_summary.html'
    out.write_text('\n'.join(html), encoding='utf-8')
    print('wrote', out)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description='Summarize A-3 knee scans (FAST/FULL) for cluster holdouts')
    ap.add_argument('--holdout', default='AbellS1063,MACSJ0416', help='comma-separated list; default AbellS1063,MACSJ0416')
    args = ap.parse_args()
    outdir = Path('server/public/reports')
    for name in [n.strip() for n in args.holdout.split(',') if n.strip()]:
        summarize_holdout(name, outdir)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

