#!/usr/bin/env python3
from __future__ import annotations
import json
import os, sys
import random
import subprocess as sp
from pathlib import Path
from typing import Dict, Any, List, Tuple

# μ(k) shared grids (ε, k0, m) and gas scale
MU_EPS_GRID = [0.1, 0.3, 1.0]
MU_K0_GRID = [0.02, 0.05, 0.1, 0.2]
MU_M_GRID = [2, 3, 4]
ANISO_LAMBDA_GRID = [0.0, 0.3, 0.6]
GAS_GRID = [1.0, 1.33]

# Compare script common args (with error floor to stabilize rχ²)
def common_args(robust: str = 'none', err_floor_kms: float = 5.0) -> list[str]:
    args = [
        "--boost", "0.5", "--boost-tie-lam", "--auto-geo",
        "--pad-factor", "2",
        "--eg-frac-floor", "0.15",
        "--err-floor-kms", str(err_floor_kms),
        "--inv1-orth", "--line-eps", "0.8",
    ]
    if robust and robust.lower() in {"huber","student"}:
        args += ["--robust", robust.lower()]
    return args

def load_names(p: Path) -> List[str]:
    return [ln.strip() for ln in p.read_text(encoding='utf-8').splitlines() if ln.strip() and not ln.strip().startswith('#')]

def write_names(p: Path, arr: List[str]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(arr) + "\n", encoding='utf-8')

def run_multi(names_file: Path,
              mu_eps_grid: List[float], mu_k0_grid: List[float], mu_m_grid: List[int],
              gas_grid: List[float], out_json: Path, aniso_lambda: float = 0.0,
              robust: str = 'none', err_floor_kms: float = 5.0) -> Dict[str, Any]:
    args = [
        "PYTHONPATH=.", "./.venv/bin/python", "scripts/compare_fit_multi.py",
        "--names-file", str(names_file),
        *common_args(robust=robust, err_floor_kms=err_floor_kms),
        # Map μ grids to underlying lam/A search then pass μ(k) grids for scaffold selection
        "--lam-grid", ",".join(str(1.0/x) for x in mu_k0_grid),
        "--A-grid", ",".join(str(x) for x in mu_eps_grid),
        "--mu-eps-grid", ",".join(str(x) for x in mu_eps_grid),
        "--mu-k0-grid", ",".join(str(x) for x in mu_k0_grid),
        "--mu-m-grid", ",".join(str(x) for x in mu_m_grid),
        "--gas-scale-grid", ",".join(str(x) for x in gas_grid),
        "--aniso-lambda", str(aniso_lambda),
        "--out", str(out_json),
    ]
    sp.run(" ".join(args), shell=True, check=True)
    return json.loads(out_json.read_text(encoding='utf-8'))

def build_html(cv: Dict[str, Any], out: Path) -> None:
    def h(s: str) -> str:
        return (s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;'))
    rows: List[str] = []
    label = "BL除外" if ("noBL" in str(out)) else "全サンプル（BL含む）"
    rows.append("<h1>共有 μ(k) 5-fold 交差検証</h1>")
    meta = cv.get('meta', {})
    mode = meta.get('mode','shared')
    mode_lab = '共有(ε,k0,m,gas)' if mode=='shared' else '群別k0（ε,m,gas共有; k0_LSB/HSB）'
    rows.append(f"<div class=card><small>対象: {h(label)} / モード: {h(mode_lab)}</small></div>")
    rows.append(
        f"<p>grid: ε={MU_EPS_GRID}, k0={MU_K0_GRID} [kpc⁻¹], m={MU_M_GRID}, gas={GAS_GRID}, λ_an={ANISO_LAMBDA_GRID}</p>"
    )
    ag = cv.get('aggregate', {})
    rgr = ag.get('rchi2_GR'); rulm = ag.get('rchi2_ULW')
    rtxt = f" / rχ² GR={h(str(rgr))} / ULM={h(str(rulm))}" if (rgr is not None and rulm is not None) else ""
    rows.append(
        f"<div class=card><p>Aggregate test: χ² GR={h(str(ag.get('chi2_GR')))} / ULM={h(str(ag.get('chi2_ULW')))} "
        f"(改善×{h(str(ag.get('improve_factor')))}), ΔAICc={h(str(ag.get('delta_AICc')))}{rtxt}</p>"
        "<p><small><b>reduced χ²</b> = χ²/(N−k)。fold合算ではfoldごとのNとkを加算して算出。</small></p></div>"
    )
    rows.append("<table><thead><tr><th>Fold</th><th>Train best (ε,k0,m,gas)</th><th>Test χ² (GR/ULM)</th><th>rχ² (GR/ULM)</th><th>AICc_GR (n,k)</th><th>AICc_ULM (n,k)</th><th>ΔAICc</th><th>ELPD_test (GR/ULM)</th></tr></thead><tbody>")
    prev_test = None
    row_idx = 0
    for i, f in enumerate(cv.get('folds', []), 1):
        best = f.get('train_best', {})
        test = f.get('test', {})
        # skip exact duplicate of previous test block
        try:
            import json as _json
            if prev_test is not None and _json.dumps(test, sort_keys=True) == _json.dumps(prev_test, sort_keys=True):
                continue
            prev_test = test
        except Exception:
            pass
        row_idx += 1
        aicc_gr = test.get('AICc_GR'); aicc_ulm = test.get('AICc_ULW')
        N_gr = test.get('N_GR'); N_ulw = test.get('N_ULW')
        k_gr = test.get('k_GR'); k_ulw = test.get('k_ULW')
        def fmt_aicc(x):
            try:
                return f"{float(x):.3f}"
            except Exception:
                return ""
        # rchi2 per fold
        try:
            rgr = float(test.get('chi2_GR'))/max(int(N_gr)-int(k_gr),1)
            rulm = float(test.get('chi2_ULW'))/max(int(N_ulw)-int(k_ulw),1)
        except Exception:
            rgr = None; rulm = None
        # ELPD estimate from held-out (Gaussian approx): −0.5 χ²_test
        try:
            elpd_gr = -0.5 * float(test.get('chi2_GR'))
            elpd_ulm = -0.5 * float(test.get('chi2_ULW'))
        except Exception:
            elpd_gr = None; elpd_ulm = None
        rows.append(
            f"<tr><td>#{row_idx}</td><td>(ε={best.get('mu_eps')}, k0={best.get('mu_k0')}, m={best.get('mu_m')}, gas={best.get('gas_scale')}, λ_an={best.get('aniso_lambda')})</td>"
            f"<td>{test.get('chi2_GR')} / {test.get('chi2_ULW')}</td>"
            f"<td>{h(f'{rgr:.3f}' if rgr is not None else '')} / {h(f'{rulm:.3f}' if rulm is not None else '')}</td>"
            f"<td>{fmt_aicc(aicc_gr)} ({N_gr},{k_gr})</td>"
            f"<td>{fmt_aicc(aicc_ulm)} ({N_ulw},{k_ulw})</td>"
            f"<td>{test.get('delta_AICc','')}</td>"
            f"<td>{h(f'{elpd_gr:.1f}' if elpd_gr is not None else '')} / {h(f'{elpd_ulm:.1f}' if elpd_ulm is not None else '')}</td></tr>"
        )
    rows.append("</tbody></table>")
    rows.append('<div class=card><small>監査: 同一n・同一誤差・同一ペナルティ（AICc）で集計しています。</small></div>')
    # Append dataset IDs for transparency
    ids = cv.get('names', [])
    if ids:
        rows.append(f"<h2>対象銀河ID（{len(ids)}件）</h2>")
        rows.append("<div class=card><small>" + ", ".join(h(x) for x in ids) + "</small></div>")
        rows.append("<p><a href=\"../state_of_the_art/used_ids.csv\">使用ID一覧(CSV)</a></p>")
    html = (
        "<!doctype html>\n<html lang=\"ja-JP\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>CV(shared μ(k))</title><link rel=\"stylesheet\" href=\"../styles.css\"></head><body>"
        "<header class=\"site-header\"><div class=\"wrap\"><div class=\"brand\">研究進捗</div>"
        "<nav class=\"nav\"><a href=\"../index.html\">ホーム</a><a href=\"index.html\">レポート</a>"
        "<a href=\"../state_of_the_art/index.html\">SOTA</a></nav></div></header><main class=\"wrap\">"
        + "\n".join(rows) + "</main><footer class=\"site-footer\"><div class=\"wrap\">ローカル配信</div></footer></body></html>"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding='utf-8')

def _ensure_dispatched() -> None:
    if os.environ.get('GRAV_BG_JOB') != '1':
        sys.stderr.write(
            "[guard] This heavy job must be launched via dispatcher.\n"
            "Use dispatcher: scripts/jobs/dispatch_bg.sh -n cv_shared -- '<cmd>'\n"
        )
        raise SystemExit(1)

def main() -> int:
    _ensure_dispatched()
    root = Path('.')
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--names-file', type=Path, default=Path('data/sparc/sets/all.txt'))
    ap.add_argument('--out-prefix', type=str, default='cv_shared_summary', help='output JSON/report prefix')
    ap.add_argument('--mu-eps-grid', type=str, default=','.join(str(x) for x in MU_EPS_GRID))
    ap.add_argument('--mu-k0-grid', type=str, default=','.join(str(x) for x in MU_K0_GRID))
    ap.add_argument('--mu-m-grid', type=str, default=','.join(str(x) for x in MU_M_GRID))
    ap.add_argument('--group-lsb', type=Path, default=None, help='names file for LSB group (optional)')
    ap.add_argument('--group-hsb', type=Path, default=None, help='names file for HSB group (optional)')
    ap.add_argument('--mode', type=str, choices=['shared','grouped-k0'], default='shared', help='shared: one (ε,k0,m,gas); grouped-k0: ε,m,gas shared, k0 per group (LSB/HSB)')
    ap.add_argument('--robust', type=str, choices=['none','huber','student'], default='none', help='robust loss for compare_fit_multi')
    ap.add_argument('--err-floor-kms', type=float, default=5.0, help='velocity error floor [km/s]')
    # Fixed μ0(k) options (force single values; no micro-tuning)
    ap.add_argument('--fixed-mu-eps', type=float, default=None)
    ap.add_argument('--fixed-mu-k0', type=float, default=None)
    ap.add_argument('--fixed-mu-m', type=float, default=None)
    ap.add_argument('--fixed-gas-scale', type=float, default=None)
    args = ap.parse_args()
    names_all = load_names(args.names_file)
    # save names for transparency
    names_out = names_all[:]
    # deterministic shuffle
    rnd = random.Random(2109)
    idx = list(range(len(names_all)))
    rnd.shuffle(idx)
    K = 5
    folds = [idx[i::K] for i in range(K)]
    results: Dict[str, Any] = {'folds': [], 'names': names_out, 'meta': {'mode': args.mode, 'group_lsb': str(args.group_lsb) if args.group_lsb else '', 'group_hsb': str(args.group_hsb) if args.group_hsb else ''}}
    # parse μ grids
    mu_eps_grid = [float(x) for x in (args.mu_eps_grid.split(',') if isinstance(args.mu_eps_grid, str) else args.mu_eps_grid)]
    mu_k0_grid = [float(x) for x in (args.mu_k0_grid.split(',') if isinstance(args.mu_k0_grid, str) else args.mu_k0_grid)]
    mu_m_grid  = [int(float(x)) for x in (args.mu_m_grid.split(',') if isinstance(args.mu_m_grid, str) else args.mu_m_grid)]
    if args.fixed_mu_eps is not None:
        mu_eps_grid = [float(args.fixed_mu_eps)]
    if args.fixed_mu_k0 is not None:
        mu_k0_grid = [float(args.fixed_mu_k0)]
    if args.fixed_mu_m is not None:
        mu_m_grid = [int(float(args.fixed_mu_m))]
    gas_grid = GAS_GRID[:]
    if args.fixed_gas_scale is not None:
        gas_grid = [float(args.fixed_gas_scale)]
    # optional grouping
    lsb_set = set(load_names(args.group_lsb)) if args.group_lsb and args.group_lsb.exists() else set()
    hsb_set = set(load_names(args.group_hsb)) if args.group_hsb and args.group_hsb.exists() else set()
    agg_chi_gr = 0.0; agg_chi_ulw = 0.0; agg_aic_gr = 0.0; agg_aic_ulw = 0.0; agg_aicc_gr = 0.0; agg_aicc_ulw = 0.0
    for k in range(K):
        test_idx = set(folds[k])
        train_names = [names_all[i] for i in range(len(names_all)) if i not in test_idx]
        test_names  = [names_all[i] for i in sorted(test_idx)]
        tdir = Path('data/sparc/sets/cv'); tdir.mkdir(parents=True, exist_ok=True)
        train_file = tdir / f'train_{k+1}.txt'
        test_file  = tdir / f'test_{k+1}.txt'
        write_names(train_file, train_names)
        write_names(test_file, test_names)
        # train: pick best parameters
        best = None
        best_val = None
        best_lambda = 0.0
        best_tr_cache = None
        if args.mode == 'shared':
            for lam_an in ANISO_LAMBDA_GRID:
                train_out = Path('data/results') / f'multi_fit_cv_train_{k+1}_lam{lam_an:.2f}.json'
                tr_try = run_multi(train_file, mu_eps_grid, mu_k0_grid, mu_m_grid, gas_grid, train_out, aniso_lambda=lam_an, robust=args.robust, err_floor_kms=args.err_floor_kms)
                aic_ulw_try = float(tr_try.get('AIC', {}).get('ULW') or 1e99)
                if (best_val is None) or (aic_ulw_try < best_val):
                    best_val = aic_ulw_try; best_lambda = lam_an; best_tr_cache = tr_try
            tr = best_tr_cache
            muinfo = (tr.get('mu_k') or {})
            best = {'mu_eps': muinfo.get('eps'), 'mu_k0': muinfo.get('k0'), 'mu_m': muinfo.get('m'), 'gas_scale': tr.get('gas_scale'), 'aniso_lambda': best_lambda}
        else:
            # grouped-k0: ε,m,gas shared; k0_LSB and k0_HSB separate
            # derive group splits for train
            train_lsb = [n for n in train_names if n in lsb_set]
            train_hsb = [n for n in train_names if n in hsb_set]
            tf_lsb = tdir / f'train_{k+1}_lsb.txt'; tf_hsb = tdir / f'train_{k+1}_hsb.txt'
            write_names(tf_lsb, train_lsb); write_names(tf_hsb, train_hsb)
            for lam_an in ANISO_LAMBDA_GRID:
                for eps in mu_eps_grid:
                    for m in mu_m_grid:
                        best_k0_lsb = None; best_k0_hsb = None
                        best_aic_sum = None; picked_gas = None
                        for gas in GAS_GRID:
                            # LSB: scan k0
                            out_lsb = Path('data/results') / f'multi_fit_cv_train_{k+1}_lsb.json'
                            tr_lsb = run_multi(tf_lsb, [eps], mu_k0_grid, [m], [gas], out_lsb, aniso_lambda=lam_an, robust=args.robust, err_floor_kms=args.err_floor_kms)
                            # pick min AIC ULW
                            def pick_k0(trd: Dict[str,Any]) -> Tuple[float,float,float]:
                                mu = trd.get('mu_k') or {}
                                return float(mu.get('k0') or mu_k0_grid[0]), float(trd.get('AIC',{}).get('ULW') or 1e99), float(trd.get('gas_scale') or gas)
                            k0_lsb, aic_lsb, gas_lsb = pick_k0(tr_lsb)
                            # HSB
                            out_hsb = Path('data/results') / f'multi_fit_cv_train_{k+1}_hsb.json'
                            tr_hsb = run_multi(tf_hsb, [eps], mu_k0_grid, [m], [gas], out_hsb, aniso_lambda=lam_an, robust=args.robust, err_floor_kms=args.err_floor_kms)
                            k0_hsb, aic_hsb, gas_hsb = pick_k0(tr_hsb)
                            aic_sum = aic_lsb + aic_hsb
                            if (best_aic_sum is None) or (aic_sum < best_aic_sum):
                                best_aic_sum = aic_sum
                                best_k0_lsb = k0_lsb
                                best_k0_hsb = k0_hsb
                                picked_gas = gas_lsb  # gas shared
                        if (best_val is None) or (best_aic_sum is not None and best_aic_sum < best_val):
                            best_val = best_aic_sum
                            best = {'mu_eps': eps, 'mu_k0_LSB': best_k0_lsb, 'mu_k0_HSB': best_k0_hsb, 'mu_m': m, 'gas_scale': picked_gas, 'aniso_lambda': lam_an}
            best_lambda = float(best.get('aniso_lambda') or 0.0)
        # test: evaluate fixed best
        test_out = Path('data/results') / f'multi_fit_cv_test_{k+1}.json'
        # For test evaluation, freeze lam/A via mapping from μ grids
        lam = (1.0 / float(best['mu_k0'])) if (best.get('mu_k0') not in (None, 0)) else (1.0 / 0.1)
        A   = float(best['mu_eps']) if best.get('mu_eps') is not None else 0.3
        # test evaluation
        if args.mode == 'shared':
            te = run_multi(test_file,
                           [float(best['mu_eps'] or 0.3)], [float(best['mu_k0'] or 0.1)], [int(best['mu_m'] or 2)],
                           [float(best['gas_scale'] or 1.0)], test_out, aniso_lambda=best_lambda, robust=args.robust, err_floor_kms=args.err_floor_kms)
            agg_te = te
        else:
            # split test by group, run with respective k0
            test_lsb = [n for n in test_names if n in lsb_set]
            test_hsb = [n for n in test_names if n in hsb_set]
            tf_lsb = tdir / f'test_{k+1}_lsb.txt'; tf_hsb = tdir / f'test_{k+1}_hsb.txt'
            write_names(tf_lsb, test_lsb); write_names(tf_hsb, test_hsb)
            te_lsb = run_multi(tf_lsb,
                               [float(best['mu_eps'])], [float(best['mu_k0_LSB'])], [int(best['mu_m'])],
                               [float(best['gas_scale'])], Path('data/results')/f'multi_fit_cv_test_{k+1}_lsb.json', aniso_lambda=best_lambda, robust=args.robust, err_floor_kms=args.err_floor_kms)
            te_hsb = run_multi(tf_hsb,
                               [float(best['mu_eps'])], [float(best['mu_k0_HSB'])], [int(best['mu_m'])],
                               [float(best['gas_scale'])], Path('data/results')/f'multi_fit_cv_test_{k+1}_hsb.json', aniso_lambda=best_lambda, robust=args.robust, err_floor_kms=args.err_floor_kms)
            # aggregate
            def add(a: Dict[str,Any], b: Dict[str,Any]) -> Dict[str,Any]:
                out = {}
                out['chi2_total'] = {k: float(a.get('chi2_total',{}).get(k,0.0)) + float(b.get('chi2_total',{}).get(k,0.0)) for k in ['GR','ULW']}
                out['AIC'] = {k: float(a.get('AIC',{}).get(k,0.0)) + float(b.get('AIC',{}).get(k,0.0)) for k in ['GR','ULW']}
                out['N_total'] = {k: int(a.get('N_total',{}).get(k,0)) + int(b.get('N_total',{}).get(k,0)) for k in ['GR','ULW']}
                out['AIC'] |= {'k': {'GR': int(a.get('AIC',{}).get('k',{}).get('GR',0)) + int(b.get('AIC',{}).get('k',{}).get('GR',0)),
                                     'ULW': int(a.get('AIC',{}).get('k',{}).get('ULW',0)) + int(b.get('AIC',{}).get('k',{}).get('ULW',0))}}
                return out
            agg_te = add(te_lsb, te_hsb)
        # compute AICc using N and k from compare_fit_multi conventions
        N_gr = int(agg_te.get('N_total', {}).get('GR') or 0)
        N_ulw = int(agg_te.get('N_total', {}).get('ULW') or 0)
        k_gr = int(agg_te.get('AIC', {}).get('k', {}).get('GR') or 0)
        k_ulw = int(agg_te.get('AIC', {}).get('k', {}).get('ULW') or 0)
        AIC_gr = float(agg_te.get('AIC', {}).get('GR') or 0.0)
        AIC_ulw = float(agg_te.get('AIC', {}).get('ULW') or 0.0)
        def aicc(AIC: float, k: int, N: int) -> float:
            if N - k - 1 <= 0:
                return float('nan')
            return AIC + (2 * k * (k + 1)) / (N - k - 1)
        AICc_gr = aicc(AIC_gr, k_gr, N_gr)
        AICc_ulw = aicc(AIC_ulw, k_ulw, N_ulw)
        results['folds'].append({
            'train_best': best,
            'test': {
                'chi2_GR': agg_te.get('chi2_total', {}).get('GR'),
                'chi2_ULW': agg_te.get('chi2_total', {}).get('ULW'),
                'AICc_GR': AICc_gr,
                'AICc_ULW': AICc_ulw,
                'N_GR': N_gr, 'N_ULW': N_ulw,
                'k_GR': k_gr, 'k_ULW': k_ulw,
                'AICc_GR': AICc_gr,
                'AICc_ULW': AICc_ulw,
                'delta_AICc': (AICc_ulw - AICc_gr) if (AICc_gr == AICc_gr and AICc_ulw == AICc_ulw) else None,
            }
        })
        agg_chi_gr += float(agg_te.get('chi2_total', {}).get('GR') or 0.0)
        agg_chi_ulw += float(agg_te.get('chi2_total', {}).get('ULW') or 0.0)
        agg_aic_gr += float(agg_te.get('AIC', {}).get('GR') or 0.0)
        agg_aic_ulw += float(agg_te.get('AIC', {}).get('ULW') or 0.0)
        if AICc_gr == AICc_gr:
            agg_aicc_gr += AICc_gr
        if AICc_ulw == AICc_ulw:
            agg_aicc_ulw += AICc_ulw
    improve = (agg_chi_gr / max(agg_chi_ulw, 1e-9)) if agg_chi_ulw > 0 else float('inf')
    # compute reduced chi-square totals by summing N and k across folds
    N_sum_gr = 0; N_sum_ulw = 0; K_sum_gr = 0; K_sum_ulw = 0
    for f in results['folds']:
        t = f.get('test', {})
        N_sum_gr += int(t.get('N_GR') or 0)
        N_sum_ulw += int(t.get('N_ULW') or 0)
        K_sum_gr += int(t.get('k_GR') or 0)
        K_sum_ulw += int(t.get('k_ULW') or 0)
    rchi_gr = (agg_chi_gr / max(N_sum_gr - K_sum_gr, 1)) if N_sum_gr else None
    rchi_ulw = (agg_chi_ulw / max(N_sum_ulw - K_sum_ulw, 1)) if N_sum_ulw else None
    results['aggregate'] = {
        'chi2_GR': agg_chi_gr,
        'chi2_ULW': agg_chi_ulw,
        'improve_factor': improve,
        'AIC_GR': agg_aic_gr,
        'AIC_ULW': agg_aic_ulw,
        'delta_AIC': agg_aic_ulw - agg_aic_gr,
        'AICc_GR': agg_aicc_gr,
        'AICc_ULW': agg_aicc_ulw,
        'delta_AICc': (agg_aicc_ulw - agg_aicc_gr),
        'rchi2_GR': rchi_gr,
        'rchi2_ULW': rchi_ulw,
        'N_sum': {'GR': N_sum_gr, 'ULW': N_sum_ulw},
        'K_sum': {'GR': K_sum_gr, 'ULW': K_sum_ulw},
    }
    outj = Path('data/results') / f"{args.out_prefix}.json"
    outj.parent.mkdir(parents=True, exist_ok=True)
    outj.write_text(json.dumps(results, indent=2), encoding='utf-8')
    report_html = Path('server/public/reports') / f"{args.out_prefix}.html"
    build_html(results, report_html)
    # Solar-system null log for reproducibility
    try:
        from fdb.mu0 import mu0_of_k
        import numpy as _np
        ks = _np.geomspace(1e-3* (float(args.fixed_mu_k0) if args.fixed_mu_k0 else 0.2), 1e4* (float(args.fixed_mu_k0) if args.fixed_mu_k0 else 0.2), 200)
        mu = mu0_of_k(ks, float(args.fixed_mu_eps) if args.fixed_mu_eps is not None else 1.0, float(args.fixed_mu_k0) if args.fixed_mu_k0 is not None else 0.2, float(args.fixed_mu_m) if args.fixed_mu_m is not None else 2.0)
        log = {
            'eps': float(args.fixed_mu_eps) if args.fixed_mu_eps is not None else None,
            'k0': float(args.fixed_mu_k0) if args.fixed_mu_k0 is not None else None,
            'm': float(args.fixed_mu_m) if args.fixed_mu_m is not None else None,
            'mu_hi': float(mu[-1]), 'k_hi': float(ks[-1]), 'dev_hi': float(abs(mu[-1]-1.0)),
        }
        Path('data/results').mkdir(parents=True, exist_ok=True)
        Path('data/results/solar_null_log.json').write_text(json.dumps(log, indent=2), encoding='utf-8')
    except Exception:
        pass
    # Archive folds and mode for SOTA transparency
    try:
        arch = Path('server/public/state_of_the_art') / f"{args.out_prefix}_folds.json"
        arch.parent.mkdir(parents=True, exist_ok=True)
        arch.write_text(json.dumps({'mode': args.mode, 'folds': [[int(i) for i in f] for f in folds], 'names': names_out}, indent=2), encoding='utf-8')
    except Exception:
        pass
    # Write adopted best μ(k) as a single JSON for SOTA sync
    try:
        cnt = {}
        for f in results.get('folds', []):
            b = f.get('train_best', {})
            t = (b.get('mu_eps'), b.get('mu_k0'), b.get('mu_m'), b.get('gas_scale'))
            if None in t: continue
            cnt[t] = cnt.get(t, 0) + 1
        if cnt:
            best = max(cnt.items(), key=lambda it: it[1])[0]
            bestj = {
                'eps': float(best[0]), 'k0': float(best[1]), 'm': int(float(best[2])), 'gas': float(best[3])
            }
            Path('data/results').mkdir(parents=True, exist_ok=True)
            Path('data/results/cv_shared_best.json').write_text(json.dumps(bestj, indent=2), encoding='utf-8')
    except Exception:
        pass
    # Write ID list log for transparency
    try:
        ids_log = Path('server/public/reports') / f"{args.out_prefix}_ids.txt"
        ids = results.get('names', [])
        ids_log.write_text("\n".join(str(x) for x in ids) + "\n", encoding='utf-8')
        print('wrote ids:', ids_log)
    except Exception:
        pass
    print('wrote CV summary to', outj, 'and', report_html)
    # Also maintain a single CSV of used IDs for SOTA (linkable and auditable)
    try:
        import csv
        csvp = Path('server/public/state_of_the_art/used_ids.csv')
        csvp.parent.mkdir(parents=True, exist_ok=True)
        with csvp.open('w', encoding='utf-8', newline='') as f:
            w = csv.writer(f)
            w.writerow(['name'])
            for nm in ids:
                w.writerow([nm])
        print('wrote used_ids.csv:', csvp)
    except Exception:
        pass
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
