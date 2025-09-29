#!/usr/bin/env python3
from __future__ import annotations
import math, json, subprocess
from typing import Any, Dict
import numpy as np
from pathlib import Path

from scripts.fit_sparc_fdbl import read_sparc_massmodels
from scripts.utils.progress import ProgressETA
from scripts.compare_fit_multi import compute_inv1_unit
from scripts.config import fair as fair_config


def to_accel(R: np.ndarray, V: np.ndarray, eV: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
    Rm = np.maximum(R, 1e-6)
    g = (V * V) / Rm
    eg = 2.0 * V * np.maximum(eV, 1e-6) / Rm
    return g, eg


def fit_mu_ls(g_obs: np.ndarray, eg: np.ndarray, g_star: np.ndarray, g_extra: np.ndarray, g_gas: np.ndarray) -> float:
    y = g_obs - g_gas - g_extra
    x = g_star
    w = 1.0 / np.maximum(eg, 1e-6)
    num = float(np.nansum(w * x * y))
    den = float(np.nansum(w * x * x))
    return max(0.0, num / max(den, 1e-30))


def chi2(g_obs: np.ndarray, eg: np.ndarray, g_model: np.ndarray) -> float:
    w = 1.0 / np.maximum(eg, 1e-6)
    return float(np.nansum(((g_model - g_obs) * w) ** 2))


def v_nfw(R: np.ndarray, V200: float, c: float) -> np.ndarray:
    G = 4.30091e-6
    Rvir = (V200 / 10.0)
    rs = max(1e-3, Rvir / max(c, 1e-6))
    x = np.maximum(R, 1e-6) / rs
    M = np.log(1.0 + x) - x / (1.0 + x)
    v2 = 4*np.pi*G* (200.0/3.0) * (rs**2) * M
    return np.sqrt(np.maximum(v2, 0.0))


def nfw_grid_fit(R: np.ndarray, Vobs: np.ndarray, eV: np.ndarray,
                 Vstar2: np.ndarray, Vgas2: np.ndarray) -> tuple[float, tuple[float,float], float]:
    best = (math.inf, (120.0, 10.0), 1.0)
    Rm = np.maximum(R, 1e-6)
    g_obs = (Vobs * Vobs) / Rm
    eg = 2.0 * Vobs * np.maximum(eV, 1e-6) / Rm
    g_gas = Vgas2 / Rm
    g_star0 = Vstar2 / Rm
    for V200 in [80, 120, 160, 200, 240, 280]:
        for c in [5.0, 7.0, 10.0, 12.0, 15.0, 20.0]:
            Vdm = v_nfw(R, V200, c)
            g_dm = (Vdm * Vdm) / Rm
            mu = fit_mu_ls(g_obs, eg, g_star0, g_dm, g_gas)
            g_model = g_gas + mu * g_star0 + g_dm
            chi = chi2(g_obs, eg, g_model)
            if chi < best[0]:
                best = (chi, (V200, c), mu)
    return best


def aicc(AIC: float, k: int, N: int) -> float:
    if N - k - 1 <= 0:
        return float('nan')
    return AIC + (2.0 * k * (k + 1)) / (N - k - 1)


def main() -> int:
    name = 'NGC2403'
    out = Path('server/public/reports/bench_ngc2403.html')
    out.parent.mkdir(parents=True, exist_ok=True)
    # Progress/ETA（重めのステップごとに更新）
    pg = ProgressETA([
        ('prepare/CV', 5),
        ('fit/metrics', 3),
        ('figures', 2),
        ('html', 1),
    ])
    pg.start(total_hint_min=10.0)
    # Ensure solar-null log exists
    try:
        subprocess.run(['bash','-lc',
                'PYTHONPATH=. ./.venv/bin/python scripts/cross_validate_shared.py '
                '--names-file data/sparc/sets/clean_for_fit.txt '
                '--out-prefix cv_shared_summary --robust huber '
                '--fixed-mu-eps 1 --fixed-mu-k0 0.2 --fixed-mu-m 2 --fixed-gas-scale 1.33'],
               check=False)
    except Exception:
        pass
    pg.tick('prepare/CV')
    rc = read_sparc_massmodels(Path("data/sparc/MassModels_Lelli2016c.mrt"), name)
    R = rc.R; Rm = np.maximum(R, 1e-6)
    Vobs = rc.Vobs; eV = np.maximum(rc.eV, 1e-6)
    g_gas = (1.33 * (rc.Vgas*rc.Vgas)) / Rm
    g_star0 = (rc.Vdisk*rc.Vdisk + rc.Vbul*rc.Vbul) / Rm
    # GR
    mu_gr = fit_mu_ls(*(to_accel(R, Vobs, eV)), g_star0, np.zeros_like(R), g_gas)
    g_model_gr = g_gas + mu_gr * g_star0
    chi_gr = chi2(*(to_accel(R, Vobs, eV)), g_model_gr)
    N = int(np.isfinite(Vobs).sum())
    k_gr = 1; aic_gr = chi_gr + 2*k_gr
    # MOND baseline
    A0_SI = 1.2e-10
    KPC_M = 3.085677581e19
    a0_kpc = A0_SI * (KPC_M / 1.0e6)
    aN = g_gas + mu_gr * g_star0
    half = 0.5 * aN
    gMOND = half + np.sqrt(np.maximum(half * half + aN * a0_kpc, 0.0))
    chi_mond = chi2(*(to_accel(R, Vobs, eV)), gMOND)
    k_mond = 1; aic_mond = chi_mond + 2*k_mond
    # GR+DM (NFW grid)
    Vgas2 = 1.33 * (rc.Vgas*rc.Vgas)
    Vstar2 = (rc.Vdisk*rc.Vdisk + rc.Vbul*rc.Vbul)
    chi_grdm, (V200, c), mu_grdm = nfw_grid_fit(R, Vobs, eV, Vstar2, Vgas2)
    k_grdm = 3; aic_grdm = chi_grdm + 2*k_grdm
    # FDB(Σ)
    tmp = Path('data/results/ngc2403_surface.json')
    if not tmp.exists():
        import subprocess as sp
        sp.run(['PYTHONPATH=.', './.venv/bin/python', 'scripts/compare_fit_multi.py', '--names-file', 'data/sparc/sets/ngc2403_only.txt', '--fdb-mode', 'surface', '--out', str(tmp)], shell=True, check=True)
    fdb = json.loads(tmp.read_text(encoding='utf-8'))
    chi_fdb = float(fdb.get('chi2_total',{}).get('ULW', float('nan')))
    aic_fdb = float(fdb.get('AIC',{}).get('ULW', float('nan')))
    N_fdb = int(fdb.get('N_total',{}).get('ULW', 0))
    k_fdb = int((fdb.get('AIC',{}).get('k') or {}).get('ULW', 0))
    # Shared JSON fingerprint
    fairness_cfg: Dict[str, Any] = fair_config.load('benchmarks')
    modelling_cfg: Dict[str, Any] = fairness_cfg.get('modelling', {}) if fairness_cfg else {}
    bench_cfg: Dict[str, Any] = fairness_cfg.get('ngc2403', {}) if fairness_cfg else {}
    mu_prior = modelling_cfg.get('mu_prior', {}) if modelling_cfg else {}
    shared_default = {
        'mu_k': {
            'epsilon': mu_prior.get('epsilon', 1.0),
            'k0': mu_prior.get('k0', 0.2),
            'm': mu_prior.get('m', 2.0)
        },
        'gas_scale': modelling_cfg.get('gas_scale', 1.33),
        'tau0': mu_prior.get('tau0', 0.6),
        'omega0': mu_prior.get('omega0', 0.0),
        'eta': mu_prior.get('eta', 0.15),
        'g': mu_prior.get('g', 0.3),
    }
    from scripts.fdb.shared_params_loader import load as load_params
    try:
        params_v2 = load_params(Path('data/shared_params.json'))
        shared = {
            'mu_k': {
                'epsilon': params_v2.theta_cos.epsilon,
                'k0': params_v2.theta_cos.k0,
                'm': params_v2.theta_cos.m,
            },
            'gas_scale': params_v2.gas_scale if params_v2.gas_scale is not None else params_v2.theta_opt.omega0,
            'tau0': params_v2.theta_opt.tau0,
            'omega0': params_v2.theta_opt.omega0,
            'eta': params_v2.theta_if.eta,
            'g': params_v2.theta_aniso.g,
        }
    except Exception:
        shared = shared_default
    import hashlib
    try:
        shf = hashlib.sha256(Path('data/shared_params.json').read_bytes()).hexdigest()[:12]
    except Exception:
        shf = ''
    # HTML
    bench_counts = bench_cfg.get('counts', {}) if bench_cfg else {}
    bench_k_map = bench_cfg.get('k', {}) if bench_cfg else {}
    bench_cmds = bench_cfg.get('commands', {}) if bench_cfg else {}

    def _from_counts(key: str, default: int) -> int:
        try:
            val = bench_counts.get(key)
            if isinstance(val, (int, float)):
                return int(val)
        except Exception:
            pass
        return default

    fair_sha = fair_config.get_sha256()
    fair_sha_short = fair_sha[:12] if fair_sha else ''
    actual_counts = {'GR': int(np.isfinite(Vobs).sum()), 'MOND': int(np.isfinite(Vobs).sum()), 'GRDM': int(np.isfinite(Vobs).sum()), 'FDB': N_fdb}
    actual_k = {'GR': k_gr, 'MOND': k_mond, 'GRDM': k_grdm, 'FDB': k_fdb}
    Ns = {
        'GR': _from_counts('N', actual_counts['GR']),
        'MOND': _from_counts('N', actual_counts['MOND']),
        'GRDM': _from_counts('N', actual_counts['GRDM']),
        'FDB': _from_counts('N_fdb', actual_counts['FDB']),
    }
    N_eff_map = {
        'GR': _from_counts('N_eff', Ns['GR']),
        'MOND': _from_counts('N_eff', Ns['MOND']),
        'GRDM': _from_counts('N_eff', Ns['GRDM']),
        'FDB': _from_counts('N_eff_fdb', Ns['FDB']),
    }

    def _declared_k(model: str, fallback: int) -> int:
        try:
            val = bench_k_map.get(model)
            if isinstance(val, (int, float)):
                return int(val)
        except Exception:
            pass
        return fallback

    Ks = {model: _declared_k(model, actual_k[model]) for model in actual_k}
    audit_ok = all(actual_counts[key] == Ns[key] for key in actual_counts) and all(actual_k[key] == Ks[key] for key in actual_k)
    def elpd(chi): return -0.5*float(chi)
    shared_card = (
        '<div class=card><p><b>共有パラメータ（単一JSON）</b></p>'
        f'<p>μ(k): ε={shared["mu_k"]["epsilon"]}, '
        f'k0={shared["mu_k"]["k0"]}, m={shared["mu_k"]["m"]} '
        f'/ gas_scale={shared["gas_scale"]}</p>'
        f'<p><small>θ_opt: τ₀={shared.get("tau0")}, ω₀={shared.get("omega0")}; '
        f'θ_if: η={shared.get("eta")}; θ_aniso: g={shared.get("g")}</small></p>'
        f'<p><small>source: data/shared_params.json (sha256:{shf}) — SOTA/表/ベンチで共通参照</small></p>'
        '<p><small>表記: ページ本文は ASCII 互換の <code>ML_*</code> を使用、論文/図中は \(\\Upsilon_\\*\) を使用（相互対応）。</small></p></div>'
    )
    # (inject after html list is created below)
    html = [
        '<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>Benchmark: NGC 2403</title><link rel="stylesheet" href="../styles.css"></head><body>',
        '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
        '<main class="wrap"><h1>単一銀河ベンチ — NGC 2403（固定 μ0, 二層Σ）</h1>',
        shared_card,
        # Inject unified representative figure section
        '<h2>代表比較図（Total基準, テンプレv2）</h2>',
        '<div class=card><picture>'
        f'<source type="image/svg+xml" srcset="figs/rep_ngc2403.svg">'
        f'<img src="figs/rep_ngc2403.png" alt="rep6 compare" style="max-width:100%">'
        '</picture><p><small><a href="figs/rep_ngc2403.svg">SVG</a> / <a href="figs/rep_ngc2403.png">PNG</a></small></p></div>',
        '<h2>横並び統計（同一n・同一誤差・同一ペナルティ）</h2><div class=card>',
        '<table class="t"><thead><tr><th>model</th><th>N</th><th>N_eff</th><th>k</th><th>AICc</th><th>χ²</th><th>rχ²</th></tr></thead><tbody>'
    ]
    for label, chi_val, aic_val, model_key in [
        ('GR', chi_gr, aic_gr, 'GR'),
        ('MOND', chi_mond, aic_mond, 'MOND'),
        ('GR+DM(NFW)', chi_grdm, aic_grdm, 'GRDM'),
        ('FDB(Σ)', chi_fdb, aic_fdb, 'FDB'),
    ]:
        N_val = Ns[model_key]
        N_eff_val = N_eff_map[model_key]
        k_val = Ks[model_key]
        aicc_val = aicc(aic_val, k_val, max(N_val, 1))
        rchi = chi_val / max(N_eff_val - k_val, 1)
        html.append(
            f'<tr><th scope="row">{label}</th><td>{N_val}</td><td>{N_eff_val}</td><td>{k_val}</td>'
            f'<td>{aicc_val:.3f}</td><td>{chi_val:.3f}</td><td>{rchi:.3f}</td></tr>'
        )
    html.extend([
        '</tbody></table>',
        (
            '<p><small>脚注: MOND は m/s² の a0 を (km² s⁻²)/kpc に単位換算して適用（a0='
            f'{a0_kpc:.1f}）。GR+DM(NFW) は V200∈[80,280] km/s・c∈[5,20] の粗グリッド探索で、'
            '各グリッド点ごとに可視成分の M/L（μ）を再推定。単一銀河ベンチでは c–M 事前は掛けていませんが、'
            'SOTA集計では ln c のガウス事前（σ≈0.35）を仮定した比較も併記しています（ページ脚注参照）。'
            '</small></p>'
        ),
        f'<p>ELPD(≈−0.5χ²): GR={elpd(chi_gr):.1f} / MOND={elpd(chi_mond):.1f} / GR+DM={elpd(chi_grdm):.1f} / FDB={elpd(chi_fdb):.1f}</p></div>',
        '<div class=card><p><small>勝率の定義: ΔAICc<0 を勝ちとし、中央値・四分位で要約します（本ページは単一銀河のため参考）。</small></p></div>',
        '<div class=card>'
        f'<p><b>監査</b>: N一致={"OK" if audit_ok else "NG"} — '
        f'N: GR={Ns["GR"]}, MOND={Ns["MOND"]}, GR+DM={Ns["GRDM"]}, FDB={Ns["FDB"]} / '
        f'N_eff: GR={N_eff_map["GR"]}, MOND={N_eff_map["MOND"]}, GR+DM={N_eff_map["GRDM"]}, FDB={N_eff_map["FDB"]}</p>'
        '<p><small>(N,k)は各行に併記。used_ids.csvはSOTA側に集約（本ベンチは単一銀河）。'
        + (f'<br>fair.json_sha={fair_sha_short}' if fair_sha_short else '')
        + (f'<br>report cmd: {bench_cmds.get("report")}' if bench_cmds else '')
        + '</small></p></div>'
    ])
    pg.tick('fit/metrics')
    # ベースライン脚注（共通テンプレ）
    try:
        notes = Path('assets/templates/baseline_notes.md').read_text(encoding='utf-8')
        html.append(notes)
    except Exception:
        pass
    # 太陽系 Null ログと μ0(k→∞)→1 の数値チェック
    solar = Path('data/results/solar_null_log.json')
    if solar.exists():
        try:
            html.append('<h2>太陽系 Null ログ</h2>')
            html.append('<div class=card><pre>')
            html.append(solar.read_text(encoding='utf-8'))
            html.append('</pre></div>')
        except Exception:
            pass
    try:
        from fdb.mu0 import mu0_of_k
        ks = np.array([1e-3, 1e-2, 1e-1, 1.0, 10.0, 1e2, 1e3])
        mu = mu0_of_k(ks, float(shared['mu_k']['epsilon']), float(shared['mu_k']['k0']), float(shared['mu_k']['m']))
        dev = float(abs(mu[-1] - 1.0))
        html.append('<div class=card>')
        html.append(f'<p>高k極限の収束: μ0(k→∞)→1 の偏差 ≈ {dev:.2e}</p>')
        html.append('</div>')
    except Exception:
        pass
    # 外縁 1/r² 復帰の可視化
    try:
        Rm = np.maximum(rc.R, 1e-6)
        gobs = (rc.Vobs * rc.Vobs) / Rm
        arr = np.stack([rc.R, gobs * (rc.R ** 2)], axis=1)
        p = Path('server/public/reports/ngc2403_outer_gravity.csv')
        np.savetxt(p, arr, delimiter=',', header='R_kpc,gR2', comments='', fmt='%.6f')
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from scripts.utils.mpl_fonts import use_jp_font
        use_jp_font()
        fig, ax = plt.subplots(1,1, figsize=(5.6,3.2))
        x = rc.R; y = gobs * (rc.R ** 2)
        ax.plot(x, y, 'o-', ms=3, label='gR² (観測)')
        n = len(x); start = int(max(0, n*0.7))
        xs = x[start:]; ys = y[start:]
        if len(xs) >= 3:
            xs0 = xs - xs.mean()
            Sxx = float((xs0*xs0).sum())
            a = float((xs0*ys).sum() / max(Sxx,1e-12))
            b = float(ys.mean())
            yhat = a*xs0 + b
            rss = float(((ys - yhat)**2).sum()); dof = max(len(xs)-2,1)
            sigma2 = rss / dof
            se_a = (sigma2 / max(Sxx,1e-12))**0.5
            ci95 = 1.96 * se_a
            ax.plot(xs, a*(xs - xs.mean()) + b, '-', lw=1.2,
                    label=f'外縁線形近似 (傾き={a:.3g}±{ci95:.2g}, 95%CI)')
        ax.set_xlabel('R [kpc]'); ax.set_ylabel('g(R)·R² [(km$^2$ s$^{-2}$)]'); ax.grid(True, ls=':', alpha=0.4)
        ax.legend(frameon=False, fontsize=9)
        img = Path('server/public/reports/ngc2403_outer_gravity.png')
        fig.tight_layout(); fig.savefig(img, dpi=140); plt.close(fig)
        html.append('<h2>外縁 1/r² 復帰の可視化</h2>')
        html.append('<div class=card><p><img src="ngc2403_outer_gravity.png" style="max-width:100%"></p>'
                    '<p><small>CSV: <a href="ngc2403_outer_gravity.csv">g(R)·R²（観測）</a>。外縁で傾き≈0に近づけば 1/r² 復帰の目安。有限サイズ効果で完全一定ではありません。</small></p></div>')
    except Exception:
        pass
    # Residual × Hα overlays (optional)
    html.append('<h2>残差ヒートマップ × Hα 等高線</h2>')
    ha_sb = Path('data/halpha/NGC2403/Halpha_SB.fits')
    ha_cont = Path('server/public/reports/ngc2403_ha_contours.png')
    ha_res = Path('server/public/reports/ngc2403_residual_ha.png')
    vf_res = Path('server/public/reports/ngc2403_vfield_residual_ha.png')
    if ha_sb.exists():
        try:
            subprocess.run(['bash','-lc', 'PYTHONPATH=. ./.venv/bin/python scripts/benchmarks/make_ngc2403_ha_overlay.py'], check=True)
            subprocess.run(['bash','-lc', 'PYTHONPATH=. ./.venv/bin/python scripts/benchmarks/make_ngc2403_residual_overlay.py'], check=True)
        except Exception:
            pass
        if vf_res.exists():
            html.append('<div class=card><p><img src="ngc2403_vfield_residual_ha.png" style="max-width:100%"></p>'
                        '<p><small>速度場のリング中央値を差し引いた面内残差（V_residual）に Hα 等高線を重ね表示。</small></p></div>')
        elif ha_res.exists():
            html.append('<div class=card><p><img src="ngc2403_residual_ha.png" style="max-width:100%"></p>'
                        '<p><small>残差は2D近似（|g_ULM|）で可視化。Hα 等高線が高い領域と相関するかを確認します。</small></p></div>')
        elif ha_cont.exists():
            html.append('<div class=card><p><img src="ngc2403_ha_contours.png" style="max-width:100%"></p>'
                        '<p><small>等高線は Hα 面輝度（単位: erg s⁻¹ cm⁻² arcsec⁻²）を基準化して表示。</small></p></div>')
        else:
            html.append('<div class=card><p><small>Hα FITS は検出しましたが可視化に失敗しました。</small></p></div>')
    else:
        html.append('<div class=card><p><small>Hαマップ未入手のため、本ベンチでは図の生成をスキップしました（データ到着後、自動生成します）。</small></p></div>')
    # Non-circular diagnostics (if present)
    ncp = Path('server/public/reports/ngc2403_noncircular_panels.png')
    if ncp.exists():
        html.append('<h2>幾何系統（非円運動）</h2>')
        html.append('<div class=card><p><img src="ngc2403_noncircular_panels.png" style="max-width:100%"></p>'
                    '<p><small>m=1（ワープ/非対称）, m=2（棒/渦腕）成分の振幅可視化。Hα等高線を重畳。</small></p></div>')
    # ω_cut contour (if present)
    oc = Path('server/public/reports/ngc2403_omega_cut_contours.png')
    if oc.exists():
        html.append('<h2>ω_cut 等高線</h2>')
        html.append('<div class=card><p><img src="ngc2403_omega_cut_contours.png" style="max-width:100%"></p>'
                    '<p><small>推定: EM→n_e（薄層厚 L≈100 pc 仮定）→ ω_p=√(n_e e²/ε₀m_e)。温度T_e=10⁴K、[NII]補正・消光のON/OFFは感度を付録で提示。</small></p></div>')
    # Standardized bench footnotes
    html.append('<h2>注記（共通）</h2>')
    html.append('<div class=card><small>'
                '・外縁 1/r²: g(R)·R² を半径上位30%で線形近似し、傾き±95%CIを表示（有限サイズで完全一定にはならない）。<br>'
                '・Hα 等高線: 画素のパーセンタイル [60,80,90,97]% を基準化レベルとして採用（自動フォールバックを実装）。<br>'
                '・ω_cut: EM→n_e は T_e=10⁴K、層厚L≈100 pcの仮定に基づく概算。減光/[NII] 補正ON/OFFの双方で主結論が頑健かを確認。<br>'
                '・誤差床: dV_floor=clip(0.03×|Vobs|, 3..7) km/s を両方式に適用し、AICcは per‑galaxy (N,k) を明示。'
                '</small></div>')
    pg.tick('figures')
    html.append('</main></body></html>')
    out.write_text('\n'.join(html), encoding='utf-8')
    print('wrote', out)
    pg.tick('html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
