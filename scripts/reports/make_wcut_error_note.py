#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path


def main() -> int:
    out = Path('server/public/reports/wcut_error_note.html')
    out.parent.mkdir(parents=True, exist_ok=True)
    html = [
        '<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>ω_cut 誤差伝播（メモ）</title><link rel="stylesheet" href="../styles.css"></head><body>',
        '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
        '<main class="wrap"><h1>ω_cut ≃ ω_p(n_e) の誤差伝播（固定メモ）</h1>',
        '<div class=card><p><small>基本関係: ω_p ∝ √n_e。EM ≃ ∫ n_e² dl ≈ n_e² L（薄層厚L一定の近似）より、n_e ≈ √(EM/L)。</small></p>'
        '<p><small>相対誤差（一次近似）: δω_p/ω_p ≈ 0.5·δn_e/n_e, かつ δn_e/n_e ≈ 0.5·δEM/EM（L一定なら）。よって δω_p/ω_p ≈ 0.25·δEM/EM。</small></p>'
        '<p><small>系統要因: 温度T_e、[NII]寄与、消光補正、厚みLの仮定。本文では T_e=10⁴K、L≈100 pc を固定。ON/OFF感度は各銀河ページの補助図に誘導。</small></p></div>',
        '<div class=card><p><a href="ngc3198_wcut_corr.html">NGC 3198 — ω_cut × 残差 相関</a> · '
        '<a href="ngc3198_halpha_sensitivity.html">Hα補正 ON/OFF 感度</a></p>'
        '<p><a href="ngc2403_wcut_corr.html">NGC 2403 — ω_cut × 残差 相関</a> · '
        '<a href="ngc2403_halpha_sensitivity.html">Hα補正 ON/OFF 感度</a></p></div>',
        '</main></body></html>'
    ]
    out.write_text('\n'.join(html), encoding='utf-8')
    print('wrote', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
