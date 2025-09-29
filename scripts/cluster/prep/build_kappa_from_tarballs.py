#!/usr/bin/env python3
from __future__ import annotations
import argparse, tarfile, json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def find_par(root: Path) -> Path | None:
    # Prefer best.par, then bestopt.par, then model.par/input.par
    cand = [
        root / 'best.par',
        root / 'bestopt.par',
        root / 'model.par',
        root / 'input.par',
    ]
    for c in cand:
        if c.exists():
            return c
    # search recursively
    for p in root.rglob('*.par'):
        return p
    return None


def parse_z_lens(par: Path) -> float | None:
    try:
        import re
        for ln in par.read_text(encoding='utf-8', errors='ignore').splitlines():
            m = re.search(r"z[_ ]?lens\s+([0-9.]+)", ln)
            if m:
                return float(m.group(1))
    except Exception:
        return None
    return None


def run_lenstool(par: Path, out_fits: Path, z_lens: float, grid: int = 512, fov_arcsec: float = 256.0) -> None:
    out_fits.parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(ROOT / '.venv/bin/python'), str(ROOT / 'tools/make_kappa_from_lenstool.py'),
           '--par', str(par), '--out', str(out_fits), '--zlens', str(z_lens),
           '--grid', str(grid), '--fov-arcsec', str(fov_arcsec)]
    print('[lenstool]', ' '.join(cmd))
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    sys.stdout.write(res.stdout)
    res.check_returncode()


def extract_tarball(tar_gz: Path, workdir: Path) -> Path:
    workdir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar_gz, 'r:gz') as tf:
        tf.extractall(workdir)
    # Return the most likely directory inside workdir
    subs = [p for p in workdir.iterdir() if p.is_dir()]
    return subs[0] if subs else workdir


def main() -> int:
    ap = argparse.ArgumentParser(description='Build κ FITS (kappa_obs.fits) for A1689/CL0024 from Lenstool tarballs')
    ap.add_argument('--a1689', default='tmp/a1689.tar.gz')
    ap.add_argument('--cl0024', default='tmp/cl0024.tar.gz')
    ap.add_argument('--grid', type=int, default=512)
    ap.add_argument('--fov', type=float, default=256.0, help='half FoV in arcsec (total=2*value)')
    args = ap.parse_args()

    jobs = [
        ('Abell1689', Path(args.a1689), ROOT / 'tmp' / 'work_a1689', ROOT / 'data/cluster/Abell1689/kappa_obs.fits'),
        ('CL0024',   Path(args.cl0024), ROOT / 'tmp' / 'work_cl0024', ROOT / 'data/cluster/CL0024/kappa_obs.fits'),
    ]
    records: list[dict] = []
    for name, tb, wd, outp in jobs:
        if not tb.exists():
            print(f'[skip] tarball missing: {tb}')
            continue
        print(f'[extract] {tb} -> {wd}')
        root = extract_tarball(tb, wd)
        # some tarballs have files at top-level; normalize
        par = find_par(root) or find_par(wd)
        if par is None:
            print(f'[error] .par not found under {root}')
            continue
        z = parse_z_lens(par)
        if z is None:
            # fallback to known literature values
            z = 0.184 if name == 'Abell1689' else (0.390 if name.upper().startswith('CL0024') else 0.3)
        run_lenstool(par, outp, z_lens=float(z), grid=args.grid, fov_arcsec=args.fov)
        records.append({'cluster': name, 'tarball': str(tb), 'workdir': str(root), 'par': str(par), 'out': str(outp), 'z_lens': float(z)})

    if records:
        meta = ROOT / 'server/public/state_of_the_art/cluster_inputs.json'
        meta.parent.mkdir(parents=True, exist_ok=True)
        meta.write_text(json.dumps({'lenstool_runs': records}, indent=2), encoding='utf-8')
        print('wrote', meta)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

