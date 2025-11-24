import argparse
import subprocess
from pathlib import Path

sets = [
    dict(err=5, c=10, mld=0.5, mlb=0.7),
    dict(err=3, c=10, mld=0.5, mlb=0.7),
    dict(err=2, c=10, mld=0.5, mlb=0.7),
    dict(err=5, c=10, mld=0.44, mlb=0.65),
]

for opts in sets:
    print(f"Running err={opts['err']} c={opts['c']} M/L={opts['mld']}/{opts['mlb']}")
    cmd = [
        'python', 'analysis/sparc_fit_light.py',
        '--err-floor', str(opts['err']),
        '--c-fixed', str(opts['c']),
        '--mldisk', str(opts['mld']),
        '--mlbulge', str(opts['mlb']),
    ]
    subprocess.run(cmd, check=True)
