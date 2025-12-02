#!/usr/bin/env python3
"""
Build a simple SVG mosaic `out/all.svg` from all `out/*_v2_summary.svg` plots.

各銀河の SVG を XML レベルで読み込み、<g> transform で 5 列グリッドに
並べて 1 つの SVG として保存します（中身はベクタのまま）。
"""

import glob
import math
import os
from typing import List
import xml.etree.ElementTree as ET
import copy


def collect_summary_svgs(out_dir: str = "out") -> List[str]:
    pattern = os.path.join(out_dir, "*_v2_summary.svg")
    files = sorted(glob.glob(pattern))
    files = [
        f
        for f in files
        if os.path.basename(f) != "all.svg"
        and not os.path.basename(f).startswith("MW_")
    ]
    return files


def parse_size(attr: str, default: float = 300.0) -> float:
    if not attr:
        return default
    # strip common units (pt, px); keep numeric part
    s = attr.strip()
    for suf in ("pt", "px", "cm", "mm", "in"):
        if s.endswith(suf):
            s = s[: -len(suf)]
            break
    try:
        return float(s)
    except ValueError:
        return default


def build_mosaic(out_dir: str = "out", ncols: int = 5, tile_px: float = 300.0) -> None:
    files = collect_summary_svgs(out_dir)
    if not files:
        print("No *_v2_summary.svg files found under", out_dir)
        return

    n = len(files)
    nrows = math.ceil(n / ncols)

    # 名前空間の設定（matplotlib SVG と互換）
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    ns = {"svg": "http://www.w3.org/2000/svg"}

    width = ncols * tile_px
    height = nrows * tile_px

    root = ET.Element(
        "{http://www.w3.org/2000/svg}svg",
        attrib={
            "width": f"{width}",
            "height": f"{height}",
            "viewBox": f"0 0 {width} {height}",
        },
    )

    for idx, path in enumerate(files):
        row = idx // ncols
        col = idx % ncols
        x = col * tile_px
        y = row * tile_px

        try:
            tree = ET.parse(path)
        except Exception as e:
            print(f"skip {path}: parse error {e}")
            continue
        src_root = tree.getroot()
        w_src = parse_size(src_root.get("width"), tile_px)
        h_src = parse_size(src_root.get("height"), tile_px)
        sx = tile_px / w_src if w_src > 0 else 1.0
        sy = tile_px / h_src if h_src > 0 else 1.0

        g = ET.SubElement(
            root,
            "{http://www.w3.org/2000/svg}g",
            attrib={"transform": f"translate({x},{y}) scale({sx},{sy})"},
        )
        # src_root の子ノードをコピー（metadata などもまとめて）
        for child in list(src_root):
            g.append(copy.deepcopy(child))

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "all.svg")
    ET.ElementTree(root).write(out_path, encoding="utf-8", xml_declaration=True)
    print(f"Saved SVG mosaic with {len(files)} panels to {out_path}")


if __name__ == "__main__":
    build_mosaic()
