#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""VizieRの軽量カタログをターゲット名で取得して保存する。

既定ではRC3 (VII/155/rc3) を照会する。必要に応じてカタログIDを
増やせる。出力は `data/catalogs/vizier/<cat_sanitized>/` 以下に
ターゲット別TSVと、結合TSVを保存する。

使い方:
  uv run scripts/fetch_vizier_catalogs.py \
    --targets data/imaging/targets.txt \
    --cats VII/155/rc3
"""

from __future__ import annotations

import time
import urllib.parse as urlp
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import requests


VIZIER_ASU = "https://vizier.cds.unistra.fr/viz-bin/asu-tsv"


def read_targets(path: Path) -> list[str]:
    out: list[str] = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        out.append(s)
    return out


def sanitize_cat(cat: str) -> str:
    return cat.replace("/", "_").replace(" ", "")


def vizier_query(cat: str, name: str, nmax: int = 5) -> Optional[str]:
    params = {
        "-source": cat,
        "-out": "*",
        "-out.max": str(nmax),
        "Name": name,
    }
    try:
        r = requests.get(VIZIER_ASU, params=params, timeout=20)
        if r.status_code != 200:
            return None
        txt = r.text
        # 行頭が#のみの場合はデータ行無し
        if "\nRA2000\t" not in txt and "\n_" not in txt:
            # 形式は表ごとに異なるが、ヘッダにRA/DEが多い
            pass
        # データ行が1行も無ければ短い
        if txt.strip().endswith("-----"):
            return None
        return txt
    except Exception:
        return None


def save_tsv(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


PRESET_CATS = {
    # RC3 (reference galaxies)
    "rc3": ["VII/155/rc3"],
    # Bundle: S4G(P4), xGASS, xCOLDGASS, RC3, tentative PHANGS
    "bundle": [
        "VII/155/rc3",        # RC3
        "J/ApJS/219/3",       # S4G P4 photometry (Munoz-Mateos+2015)
        "J/MNRAS/464/3391",   # xGASS (Catinella+2017)
        "J/MNRAS/462/1747",   # xCOLDGASS (Saintonge+2016)
        # PHANGS master table (tentative; may vary by release)
        "J/ApJS/257/43",
    ],
}


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--targets",
        type=Path,
        default=Path("data/imaging/targets.txt"),
    )
    ap.add_argument(
        "--cats",
        nargs="+",
        default=["VII/155/rc3"],
        help="VizieR catalog IDs",
    )
    ap.add_argument(
        "--preset",
        choices=list(PRESET_CATS.keys()),
        help="Preset catalog groups to query",
    )
    ap.add_argument("--sleep", type=float, default=0.3)
    args = ap.parse_args()

    names = read_targets(args.targets)
    root = Path("data/catalogs/vizier")
    root.mkdir(parents=True, exist_ok=True)

    cats = list(args.cats)
    if args.preset:
        cats = PRESET_CATS.get(args.preset, []) + cats
    # de-duplicate while preserving order
    seen = set()
    cats_unique = []
    for c in cats:
        if c in seen:
            continue
        seen.add(c)
        cats_unique.append(c)

    for cat in cats_unique:
        cat_dir = root / sanitize_cat(cat)
        combined: list[str] = []
        header_written = False
        for nm in names:
            txt = vizier_query(cat, nm)
            if txt:
                # 抜粋: 先頭のコメント(#)は保持、2つ目以降の対象では
                # データヘッダ行以降だけ追記する
                lines = txt.splitlines()
                data_start = 0
                for i, ln in enumerate(lines):
                    if ln and not ln.startswith("#"):
                        data_start = i
                        break
                # 単一ターゲット保存
                save_tsv(cat_dir / f"{nm}.tsv", txt)
                # 結合用
                if not header_written:
                    combined.extend(lines[: data_start + 1])
                    header_written = True
                combined.extend(lines[data_start + 1 :])
            time.sleep(args.sleep)
        if combined:
            save_tsv(cat_dir / "combined.tsv", "\n".join(combined) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
