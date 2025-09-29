#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path


def main() -> int:
    src = Path('data/results/ngc3198_surface.json')
    if not src.exists():
        print('missing:', src)
        return 1
    d = json.loads(src.read_text(encoding='utf-8'))
    chi = d.get('chi2_total', {})
    aic = d.get('AIC', {})
    N = d.get('N_total', {})
    k = (aic.get('k') or {})
    def aicc(A, K, NN):
        try:
            A, K, NN = float(A or 0.0), int(K or 0), int(NN or 0)
            return A + (2*K*(K+1))/(NN-K-1) if (NN-K-1)>0 else float('inf')
        except Exception:
            return float('inf')
    aicc_gr = aicc(aic.get('GR'), k.get('GR'), N.get('GR'))
    aicc_ulw = aicc(aic.get('ULW'), k.get('ULW'), N.get('ULW'))
    rchi_gr = (float(chi.get('GR') or 0.0) / max((int(N.get('GR') or 0) - int(k.get('GR') or 0)), 1))
    rchi_ulw = (float(chi.get('ULW') or 0.0) / max((int(N.get('ULW') or 0) - int(k.get('ULW') or 0)), 1))
    delta_aicc = aicc_ulw - aicc_gr if aicc_gr == aicc_gr and aicc_ulw == aicc_ulw else None
    out = Path('server/public/reports/bench_ngc3198.html')
    out.parent.mkdir(parents=True, exist_ok=True)
    html = [
        '<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>Benchmark: NGC 3198</title><link rel="stylesheet" href="../styles.css"></head><body>',
        '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">ホーム</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
        '<main class="wrap"><h1>単一銀河系ベンチ — NGC 3198（固定 μ0, 二層Σ）</h1>',
        '<p>手順書: <a href="../../docs/benchmarks/NGC3198_procedure.md">NGC3198_procedure.md</a></p>',
        '<h2>統計（同一n・同一誤差・同一ペナルティ）</h2>',
        f'<div class=card><p>χ²: GR={chi.get("GR")} / FDB(Σ)={chi.get("ULW")}</p>'
        f'<p>AIC: GR={aic.get("GR")} (n={N.get("GR")},k={k.get("GR")}) / FDB={aic.get("ULW")} (n={N.get("ULW")},k={k.get("ULW")})</p>'
        f'<p>AICc: GR={aicc_gr:.3f} / FDB={aicc_ulw:.3f} / ΔAICc={(delta_aicc if delta_aicc is not None else float("nan")):.3f}</p>'
        f'<p>rχ²: GR={rchi_gr:.3f} / FDB={rchi_ulw:.3f}</p></div>',
        '<p><small>MOND/GR+DM(NFW,c–M) の横並びはSOTA本線の比較器に順次統合します。</small></p>',
        '</main></body></html>'
    ]
    out.write_text('\n'.join(html), encoding='utf-8')
    print('wrote', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
