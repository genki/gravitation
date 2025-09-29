#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path


def main() -> int:
    root = Path('data/cluster')
    root.mkdir(parents=True, exist_ok=True)
    # Expected inputs (user to provide): kappa.fits (WCS), xray.fits (I_X), temp.fits (optional), icl.fits (optional)
    # For now, record a manifest and exit gracefully if data is missing.
    targets = {
        'bullet': {
            'kappa': str((root / 'bullet' / 'kappa.fits').resolve()),
            'xray': str((root / 'bullet' / 'xray.fits').resolve()),
            'temp': str((root / 'bullet' / 'temp.fits').resolve()),
            'galaxies': str((root / 'bullet' / 'galaxies.fits').resolve()),
            'icl': str((root / 'bullet' / 'icl.fits').resolve()),
        },
        'train': [
            {'name': 'MACS_J0025', 'kappa': str((root / 'MACS_J0025' / 'kappa.fits').resolve()), 'xray': str((root / 'MACS_J0025' / 'xray.fits').resolve())},
            {'name': 'A520', 'kappa': str((root / 'A520' / 'kappa.fits').resolve()), 'xray': str((root / 'A520' / 'xray.fits').resolve())},
        ]
    }
    out = Path('data/cluster/manifest.json')
    out.write_text(json.dumps(targets, indent=2), encoding='utf-8')
    print('wrote manifest:', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

