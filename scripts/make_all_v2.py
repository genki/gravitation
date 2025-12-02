#!/usr/bin/env python3
"""
Build SVG mosaics from all `out/*_v2_summary.svg` plots.

- `all.svg`       : 全銀河 (5xN グリッド)
- `all-best.svg`  : 外縁 χ² が小さい上位 16 銀河 (4x4)
- `all-worst.svg` : 外縁 χ² が大きい下位 16 銀河 (4x4)

best/worst の順位は `/tmp/fdb2_<tag>.log` に出力された
`chi2_v2 (outer, ...)` を用いて決める。
"""

import glob
import math
import os
import re
import copy
from typing import List, Tuple
import xml.etree.ElementTree as ET


def collect_tags(out_dir: str = "out") -> List[str]:
    pattern = os.path.join(out_dir, "*_v2_summary.svg")
    files = sorted(glob.glob(pattern))
    tags: List[str] = []
    for f in files:
        base = os.path.basename(f)
        if base in {"all.svg", "all-best.svg", "all-worst.svg"}:
            continue
        if base.startswith("MW_"):
            continue
        tags.append(base.replace("_v2_summary.svg", ""))
    return tags


def parse_size(attr: str, default: float = 300.0) -> float:
    if not attr:
        return default
    s = attr.strip()
    for suf in ("pt", "px", "cm", "mm", "in"):
        if s.endswith(suf):
            s = s[: -len(suf)]
            break
    try:
        return float(s)
    except ValueError:
        return default


def load_outer_chi2_from_logs(tags: List[str]) -> List[Tuple[str, float]]:
    """Parse /tmp/fdb2_<tag>.log and extract chi2_v2 (outer, ...) values."""
    res: List[Tuple[str, float]] = []
    pat = re.compile(r"chi2_v2 \(outer.*=\s*([0-9.eE+-]+)")
    for tag in tags:
        log_path = f"/tmp/fdb2_{tag}.log"
        chi2 = float("inf")
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    for line in f:
                        m = pat.search(line)
                        if m:
                            try:
                                chi2 = float(m.group(1))
                            except ValueError:
                                chi2 = float("inf")
                            break
            except Exception:
                chi2 = float("inf")
        res.append((tag, chi2))
    return res


def build_mosaic_for_tags(
    tags: List[str],
    out_path: str,
    out_dir: str = "out",
    ncols: int = 5,
    tile_px: float = 300.0,
) -> None:
    if not tags:
        print(f"No tags to build mosaic for {out_path}")
        return

    ET.register_namespace("", "http://www.w3.org/2000/svg")

    n = len(tags)
    nrows = math.ceil(n / ncols)
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

    for idx, tag in enumerate(tags):
        row = idx // ncols
        col = idx % ncols
        x = col * tile_px
        y = row * tile_px

        svg_path = os.path.join(out_dir, f"{tag}_v2_summary.svg")
        try:
            tree = ET.parse(svg_path)
        except Exception as e:
            print(f"skip {svg_path}: parse error {e}")
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
        for child in list(src_root):
            g.append(copy.deepcopy(child))

    os.makedirs(out_dir, exist_ok=True)
    ET.ElementTree(root).write(out_path, encoding="utf-8", xml_declaration=True)
    print(f"Saved SVG mosaic ({len(tags)} panels) to {out_path}")


def main() -> None:
    out_dir = "out"
    tags = collect_tags(out_dir)
    if not tags:
        print("No *_v2_summary.svg files found under", out_dir)
        return

    # all.svg: 全銀河 (5列)
    build_mosaic_for_tags(
        tags,
        os.path.join(out_dir, "all.svg"),
        out_dir=out_dir,
        ncols=5,
        tile_px=300.0,
    )

    # best / worst: ログの outer chi2 から上位/下位を抽出
    chi2_list = load_outer_chi2_from_logs(tags)
    chi2_valid = [(t, c) for (t, c) in chi2_list if c < float("inf")]
    if not chi2_valid:
        print("No valid chi2_v2 (outer) in logs; skipping best/worst mosaics.")
        return

    chi2_sorted = sorted(chi2_valid, key=lambda x: x[1])
    k = min(16, len(chi2_sorted))
    best_tags = [t for (t, _) in chi2_sorted[:k]]
    worst_tags = [t for (t, _) in chi2_sorted[-k:]]

    build_mosaic_for_tags(
        best_tags,
        os.path.join(out_dir, "all-best.svg"),
        out_dir=out_dir,
        ncols=4,
        tile_px=300.0,
    )
    build_mosaic_for_tags(
        worst_tags,
        os.path.join(out_dir, "all-worst.svg"),
        out_dir=out_dir,
        ncols=4,
        tile_px=300.0,
    )


if __name__ == "__main__":
    main()

