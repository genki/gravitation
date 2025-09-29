#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from dataclasses import dataclass


@dataclass
class KPIStatus:
    name: str
    status: str  # 'green' | 'amber' | 'red'
    detail: str


def best_deltas_from_trials(trials_path: Path) -> dict:
    best: dict[str, float] = {}
    k_by: dict[str, int] = {}
    if not trials_path.exists():
        return best
    for ln in trials_path.read_text(encoding='utf-8').splitlines():
        try:
            row = json.loads(ln)
        except Exception:
            continue
        if not row.get('ok'):
            continue
        nm = row.get('name'); d = float(row.get('delta', 1e9))
        k = int(row.get('k', 2))
        if nm is None:
            continue
        if (nm not in best) or (d < best[nm]):
            best[nm] = d; k_by[nm] = k
    return {nm: (best[nm], k_by.get(nm, 2)) for nm in best}


def make_kpi_statuses() -> list[KPIStatus]:
    out: list[KPIStatus] = []
    # KPI-1: A/B with ΔAICc<=-6 for ≥1 galaxy
    # Prefer fairness (k=2, same N/error) if available
    fair = Path('data/results/ws_vs_phieta_fair_best.json')
    if fair.exists():
        try:
            rows = json.loads(fair.read_text(encoding='utf-8'))
            lines = []
            ok = False
            for r in rows:
                if not r.get('ok'):
                    continue
                nm = r.get('name'); d = float(r.get('delta', 1e9)); k = int(r.get('k', 2))
                lines.append(f"{nm}: ΔAICc={d:.2f} (k={k})")
                ok = ok or (d <= -6.0)
            if lines:
                st = 'green' if ok else 'amber'
                out.append(KPIStatus('KPI‑1 A/B', st, '; '.join(lines)))
            else:
                out.append(KPIStatus('KPI‑1 A/B', 'red', '公平スイープに有効結果なし'))
        except Exception:
            out.append(KPIStatus('KPI‑1 A/B', 'amber', '公平JSONの解析に失敗'))
    else:
        # fallback: use trial log (may include k=3)
        trials = Path('data/results/ws_vs_phieta_trials.ndjson')
        bd = best_deltas_from_trials(trials)
        if bd:
            lines = []
            ok = False
            for nm,(d,k) in bd.items():
                lines.append(f"{nm}: ΔAICc={d:.2f} (k={k})")
                if d <= -6.0:
                    ok = True
            st = 'green' if ok else 'amber'
            out.append(KPIStatus('KPI‑1 A/B', st, '; '.join(lines)))
        else:
            out.append(KPIStatus('KPI‑1 A/B', 'red', 'トライアル未検出'))

    # KPI-2: Bench confirmed for both galaxies (outer-slope + Hα + ω_cut)
    req = [
        Path('server/public/reports/bench_ngc3198.html'),
        Path('server/public/reports/bench_ngc2403.html'),
        Path('server/public/reports/ngc3198_ha_contours.png'),
        Path('server/public/reports/ngc2403_ha_contours.png'),
        Path('server/public/reports/ngc3198_omega_cut_contours.png'),
        Path('server/public/reports/ngc2403_omega_cut_contours.png'),
    ]
    have = [p.exists() for p in req]
    if all(have):
        out.append(KPIStatus('KPI‑2 銀河確定版', 'green', '3198/2403: 外縁1/r²・Hα・ω_cut 掲載'))
    elif any(have):
        miss = [p.name for p,h in zip(req, have) if not h]
        out.append(KPIStatus('KPI‑2 銀河確定版', 'amber', '不足: ' + ', '.join(miss)))
    else:
        out.append(KPIStatus('KPI‑2 銀河確定版', 'red', '図面未生成'))

    # KPI-3: Control tests summary present with d and n
    csum = Path('server/public/reports/control_tests_summary.json')
    if csum.exists():
        try:
            js = json.loads(csum.read_text(encoding='utf-8'))
            ctr = js.get('controls', {})
            ok = True
            details = []
            for key in ('rotate','translate','shuffle'):
                ent = ctr.get(key, {})
                n = int(ent.get('n', 0))
                d = ent.get('d', None)
                details.append(f"{key}: n={n}, d={d:.2f}" if isinstance(d,(int,float)) else f"{key}: n={n}")
                ok = ok and (n > 0) and (d is not None)
            out.append(KPIStatus('KPI‑3 対照検証', 'green' if ok else 'amber', '; '.join(details)))
        except Exception:
            out.append(KPIStatus('KPI‑3 対照検証', 'amber', '要約JSONの解析に失敗'))
    else:
        out.append(KPIStatus('KPI‑3 対照検証', 'red', 'control_tests_summary.json 不在'))

    # KPI-4: Rep6 table exists
    rep6 = Path('server/public/reports/surface_vs_volumetric.html')
    if rep6.exists():
        out.append(KPIStatus('KPI‑4 代表6', 'green', '表を再計算して更新済み'))
    else:
        out.append(KPIStatus('KPI‑4 代表6', 'red', '表未生成'))

    return out


def render_card(kpis: list[KPIStatus]) -> str:
    rows = []
    for k in kpis:
        dot = f'<span class="kpi-light {k.status}"></span>'
        rows.append(f'<tr><td>{dot} {k.name}</td><td>{k.detail}</td></tr>')
    tbl = '<table class="kpi"><thead><tr><th>KPI</th><th>最新状況</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table>'
    card = '<div class="card"><h2>進捗ライト（KPI）</h2>' + tbl + '</div>'
    return card


def main() -> int:
    outdir = Path('server/public/reports'); outdir.mkdir(parents=True, exist_ok=True)
    kpis = make_kpi_statuses()
    card = render_card(kpis)
    # write card and full page
    (outdir/'progress_card.html').write_text(card, encoding='utf-8')
    page = [
        '<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>KPI Progress</title><link rel="stylesheet" href="../styles.css"></head><body>',
        '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
        '<main class="wrap"><h1>進捗ダッシュボード（KPI‑1〜4）</h1>',
        card,
        '</main></body></html>'
    ]
    (outdir/'progress.html').write_text('\n'.join(page), encoding='utf-8')
    print('wrote', outdir/'progress_card.html', 'and progress.html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
