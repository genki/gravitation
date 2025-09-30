#!/usr/bin/env python3
from __future__ import annotations
import tarfile
import urllib.request
from pathlib import Path
import hashlib
import json

URL = "http://kids.strw.leidenuniv.nl/cs2016/KiDS-450_COSMIC_SHEAR_DATA_RELEASE.tar.gz"

def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def main() -> int:
    root = Path(__file__).resolve().parents[2]
    out_dir = root / 'data' / 'weak_lensing'
    out_dir.mkdir(parents=True, exist_ok=True)
    tar_path = out_dir / 'KiDS-450_COSMIC_SHEAR_DATA_RELEASE.tar.gz'
    if not tar_path.exists():
        print(f"downloading {URL} → {tar_path}")
        with urllib.request.urlopen(URL) as r, tar_path.open('wb') as w:
            w.write(r.read())
    else:
        print(f"found existing {tar_path} (skip download)")
    sha = sha256_of(tar_path)
    extr = out_dir / 'kids450_release'
    extr.mkdir(exist_ok=True)
    with tarfile.open(tar_path, 'r:gz') as tf:
        tf.extractall(extr)
    manifest = {
        'source': URL,
        'archive': str(tar_path.relative_to(root)),
        'sha256': sha,
        'extracted_to': str(extr.relative_to(root)),
    }
    (extr / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('extracted to', extr)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

