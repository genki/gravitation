#!/usr/bin/env python3
from __future__ import annotations
import json, argparse, math
from pathlib import Path


def audit_cv(json_path: Path) -> dict:
    d = json.loads(json_path.read_text(encoding='utf-8'))
    agg = d.get('aggregate', {})
    Ns = agg.get('N_sum', {})
    Ks = agg.get('K_sum', {})
    issues = []
    if Ns.get('GR') != Ns.get('ULW'):
        issues.append(f"N_sum mismatch: GR={Ns.get('GR')} ULW={Ns.get('ULW')}")
    if any(v is None for v in (Ns.get('GR'), Ks.get('GR'), Ns.get('ULW'), Ks.get('ULW'))):
        issues.append('Missing N_sum/K_sum entries')
    return {'file': str(json_path), 'issues': issues, 'N_sum': Ns, 'K_sum': Ks}


def main() -> int:
    ap = argparse.ArgumentParser(description='Audit same-n / rχ² bookkeeping across CV summaries')
    ap.add_argument('--glob', type=str, default='data/results/cv_shared_summary*.json')
    args = ap.parse_args()
    import glob
    reports = []
    for p in glob.glob(args.glob):
        try:
            reports.append(audit_cv(Path(p)))
        except Exception as e:
            reports.append({'file': p, 'issues': [f'error: {e}']})
    ok = all((not r['issues']) for r in reports)
    out = {'ok': ok, 'reports': reports}

    # Numeric self-consistency on aggregate (AICc vs AIC, rχ² vs χ²/(N−k))
    try:
        agg_p = Path('data/results/cv_shared_summary.json')
        if agg_p.exists():
            d = json.loads(agg_p.read_text(encoding='utf-8'))
            agg = d.get('aggregate', {})
            Ns = agg.get('N_sum', {})
            Ks = agg.get('K_sum', {})
            issues = []
            # rχ² checks
            for key in ('GR','ULW'):
                chi = float(agg.get(f'chi2_{key}') or math.nan)
                rchi = float(agg.get(f'rchi2_{key}') or math.nan)
                N = int(Ns.get(key) or 0)
                K = int(Ks.get(key) or 0)
                denom = max(N - K, 1)
                r_exp = chi / denom if math.isfinite(chi) else math.nan
                if not (math.isfinite(rchi) and abs(rchi - r_exp) / max(abs(r_exp), 1e-9) < 1e-3):
                    issues.append(f'rchi2 mismatch {key}: got={rchi}, expect={r_exp} (N={N},K={K})')
            # AICc checks
            for key in ('GR','ULW'):
                AIC = float(agg.get(f'AIC_{key}') or math.nan)
                AICc = float(agg.get(f'AICc_{key}') or math.nan)
                N = int(Ns.get(key) or 0)
                K = int(Ks.get(key) or 0)
                corr = (2.0 * K * (K + 1)) / max(N - K - 1, 1)
                exp = AIC + corr if math.isfinite(AIC) else math.nan
                if not (math.isfinite(AICc) and abs(AICc - exp) / max(abs(exp), 1e-9) < 1e-3):
                    issues.append(f'AICc mismatch {key}: got={AICc}, expect={exp} (N={N},K={K})')
            out['numeric'] = {'ok': not issues, 'issues': issues}
            ok = ok and (not issues)
    except Exception as e:
        out['numeric'] = {'ok': False, 'issues': [f'error: {e}']}
        ok = False

    print(json.dumps(out, indent=2))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
