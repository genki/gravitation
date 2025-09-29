#!/usr/bin/env python3
from __future__ import annotations
import json
import subprocess as sp
from pathlib import Path
import argparse


def run_eval(names: Path, eps: float, k0: float, m: int, gas: float, aniso_lambda: float = 0.0, out_json: Path = Path('data/results/prospective.json')) -> dict:
    args = [
        "PYTHONPATH=.", "./.venv/bin/python", "scripts/compare_fit_multi.py",
        "--names-file", str(names),
        "--boost", "0.5", "--boost-tie-lam", "--auto-geo",
        "--pad-factor", "2",
        "--eg-frac-floor", "0.15",
        "--err-floor-kms", "5",
        "--inv1-orth", "--line-eps", "0.8",
        "--mu-eps-grid", f"{eps}",
        "--mu-k0-grid", f"{k0}",
        "--mu-m-grid", f"{m}",
        "--gas-scale-grid", f"{gas}",
        "--aniso-lambda", f"{aniso_lambda}",
        "--out", str(out_json),
    ]
    sp.run(" ".join(args), shell=True, check=True)
    return json.loads(out_json.read_text(encoding='utf-8'))


def main() -> int:
    ap = argparse.ArgumentParser(description='Prospective hold-out evaluation with shared μ0(k) and Ahat fixed; fit only Υ★ and gas_scale')
    ap.add_argument('--names-file', type=Path, required=True)
    ap.add_argument('--cv-best', type=Path, default=Path('data/results/cv_shared_best.json'))
    ap.add_argument('--aniso-lambda', type=float, default=0.0)
    ap.add_argument('--out', type=Path, default=Path('data/results/prospective.json'))
    args = ap.parse_args()
    cv = json.loads(args.cv_best.read_text(encoding='utf-8'))
    res = run_eval(args.names_file, float(cv['eps']), float(cv['k0']), int(cv['m']), float(cv.get('gas', 1.0)), args.aniso_lambda, args.out)
    (Path('server/public/reports')).mkdir(parents=True, exist_ok=True)
    rep = Path('server/public/reports/prospective.html')
    # Collect metrics
    chi = res.get("chi2_total", {})
    aic = res.get("AIC", {})
    N = res.get("N_total", {})
    k = (aic.get('k') or {})
    def aicc(AIC: float, kk: int, NN: int) -> float:
        return (float(AIC) + (2.0 * int(kk) * (int(kk) + 1)) / max(int(NN) - int(kk) - 1, 1))
    aicc_gr = aicc(aic.get('GR', 0.0), k.get('GR', 0), N.get('GR', 0))
    aicc_ulw = aicc(aic.get('ULW', 0.0), k.get('ULW', 0), N.get('ULW', 0))
    try:
        rchi_gr = float(chi.get('GR')) / max(int(N.get('GR')) - int(k.get('GR')), 1)
        rchi_ulw = float(chi.get('ULW')) / max(int(N.get('ULW')) - int(k.get('ULW')), 1)
    except Exception:
        rchi_gr = None; rchi_ulw = None
    html = []
    html.append('<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                '<title>Prospective</title><link rel="stylesheet" href="../styles.css"></head><body>')
    html.append('<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div>'
                '<nav class="nav"><a href="../index.html">ホーム</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>'
                '<main class="wrap">')
    html.append('<h1>Prospective 検証（共有 μ0(k), Â 固定; Υ★/gas のみ調整）</h1>')
    line_rchi = '' if (rchi_gr is None or rchi_ulw is None) else f' / rχ² GR={rchi_gr:.3f} / ULM={rchi_ulw:.3f}'
    warn = ''
    try:
        if rchi_ulw is not None and rchi_ulw < 0.05:
            warn = ' <b>注:</b> rχ²(ULM) が極端に小さいため、本カードは診断用（フェア比較からは除外）。誤差床・(N,k)・正則化はSOTA方針に揃えています。'
    except Exception:
        pass
    html.append('<div class=card>'
                f'<p>χ²: GR={chi.get("GR")} / ULM={chi.get("ULW")}</p>'
                f'<p>AICc: GR={aicc_gr:.3f} (N={N.get("GR")},k={k.get("GR")}) / '
                f'ULM={aicc_ulw:.3f} (N={N.get("ULW")},k={k.get("ULW")}){line_rchi}</p>'
                f'<p><small>前提: 共有 μ0(k), Â を固定し、Υ★/gas のみを再調整。誤差床: clip(0.03×Vobs, 3..7 km/s)。{warn}</small></p></div>')
    html.append('</main></body></html>')
    rep.write_text('\n'.join(html), encoding='utf-8')
    print('wrote', rep)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
