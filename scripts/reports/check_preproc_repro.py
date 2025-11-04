#!/usr/bin/env python3
"""FAST↔FULL 前処理STAMPと指標再現性のチェックツール.

Outputs:
  - 各ホールドアウトごとの preproc_stamp (sha12) 一覧
  - FAST / FULL の S_shadow, Spearman 差分 (mean / std / max)
  - tmp/preproc_digest に記録された SHA と実データの整合性
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import statistics
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from scripts.reports.make_bullet_holdout import (  # type: ignore
    _build_preproc_signature,
    _ensure_native,
    _signature_diff,
)


def _hash_signature(sig: dict) -> str:
    payload = json.dumps(sig, sort_keys=True, default=_ensure_native).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _iter_holdout_json(paths: Iterable[Path]):
    for path in paths:
        try:
            with path.open(encoding="utf-8") as fh:
                obj = json.load(fh)
        except Exception:
            continue
        yield path, obj


def _get_holdout_slug(path: Path, data: dict) -> str:
    slug = data.get("metadata", {}).get("holdout")
    if isinstance(slug, str) and slug:
        return slug
    # fallback: ファイル名の先頭トークン
    name = path.name
    return name.split("_", 1)[0]


def _get_mode(data: dict, path: Path) -> str:
    meta = data.get("metadata", {})
    if isinstance(meta.get("fast_mode"), bool):
        return "FAST" if meta["fast_mode"] else "FULL"
    name = path.stem.lower()
    if "fast" in name:
        return "FAST"
    if "full" in name:
        return "FULL"
    return "UNKNOWN"


def _safe_float(value: object) -> Optional[float]:
    try:
        f = float(value)
    except Exception:
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return f


def gather_runs(base: Path) -> List[dict]:
    entries: List[dict] = []
    for path, data in _iter_holdout_json(base.glob("*.json")):
        processing = data.get("processing") or {}
        try:
            signature = _build_preproc_signature(data, processing)
        except Exception:
            continue
        sig_hash = _hash_signature(signature)
        norm_signature = copy.deepcopy(signature)
        if isinstance(norm_signature, dict):
            norm_signature.pop("fast_mode", None)
        norm_hash = _hash_signature(norm_signature)
        meta = data.get("metadata", {})
        mode = _get_mode(data, path)
        s_shadow = (
            data.get("indicators", {})
            .get("S_shadow", {})
            .get("values", {})
            .get("global")
        )
        spearman = data.get("indicators", {}).get("spear_r")
        entries.append(
            {
                "path": path,
                "holdout": _get_holdout_slug(path, data),
                "mode": mode,
                "stamp": sig_hash,
                "stamp12": sig_hash[:12],
                "norm_stamp": norm_hash,
                "norm_stamp12": norm_hash[:12],
                "signature": signature,
                "norm_signature": norm_signature,
                "metadata": meta,
                "s_shadow": _safe_float(s_shadow),
                "spearman": _safe_float(spearman),
                "generated_at": meta.get("generated_at_utc"),
            }
        )
    return entries


def load_digest_map(digest_dir: Path) -> Dict[str, Dict[str, dict]]:
    result: Dict[str, Dict[str, dict]] = {}
    if not digest_dir.exists():
        return result
    for path in digest_dir.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        holdout = data.get("holdout")
        mode = data.get("mode")
        if not holdout or not mode:
            continue
        result.setdefault(holdout, {})[mode.upper()] = data
    return result


def summarize(entries: List[dict], digests: Dict[str, Dict[str, dict]]) -> int:
    pairs = 0
    s_diffs: List[float] = []
    spear_diffs: List[float] = []
    print("=== Preproc comparison (FAST vs FULL) ===")
    by_holdout: Dict[Tuple[str, str], Dict[str, dict]] = {}
    for entry in entries:
        key = (entry["holdout"], entry.get("norm_stamp"))
        by_holdout.setdefault(key, {})[entry["mode"]] = entry
    for (holdout, _norm_stamp), modes in sorted(by_holdout.items()):
        fast = modes.get("FAST")
        full = modes.get("FULL")
        if not fast or not full:
            continue
        pairs += 1
        digest_note = ""
        digest_fast = digests.get(holdout, {}).get("FAST")
        if digest_fast and digest_fast.get("signature_hash") != fast["stamp"]:
            digest_note += " [FAST stamp mismatch]"
        digest_full = digests.get(holdout, {}).get("FULL")
        if digest_full and digest_full.get("signature_hash") != full["stamp"]:
            digest_note += " [FULL stamp mismatch]"
        diff_fields = _signature_diff(fast.get("norm_signature", {}), full.get("norm_signature", {}))
        filtered_diff = [f for f in diff_fields if f != "fast_mode"]
        print(
            f"- {holdout}: FAST<{fast['path'].name}> FULL<{full['path'].name}>"
            + (f" diff={filtered_diff}" if filtered_diff else " diff=[]")
            + digest_note
        )
        if fast["s_shadow"] is not None and full["s_shadow"] is not None:
            s_diffs.append(fast["s_shadow"] - full["s_shadow"])
        if fast["spearman"] is not None and full["spearman"] is not None:
            spear_diffs.append(fast["spearman"] - full["spearman"])
    if pairs == 0:
        print("No FAST/FULL pairs found.")
        return 1
    print("\n=== Metric deltas (FAST - FULL) ===")
    if s_diffs:
        mean = statistics.fmean(s_diffs)
        sd = statistics.pstdev(s_diffs) if len(s_diffs) > 1 else 0.0
        max_abs = max(abs(x) for x in s_diffs)
        print(
            f"S_shadow Δ: count={len(s_diffs)}, mean={mean:+.4f}, sd={sd:.4f}, max|Δ|={max_abs:.4f}"
        )
    else:
        print("S_shadow Δ: no numeric pairs.")
    if spear_diffs:
        mean = statistics.fmean(spear_diffs)
        sd = statistics.pstdev(spear_diffs) if len(spear_diffs) > 1 else 0.0
        max_abs = max(abs(x) for x in spear_diffs)
        print(
            f"Spearman Δ: count={len(spear_diffs)}, mean={mean:+.4f}, sd={sd:.4f}, max|Δ|={max_abs:.4f}"
        )
    else:
        print("Spearman Δ: no numeric pairs.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="FAST/FULL preprocessing reproducibility checker")
    ap.add_argument(
        "--runs-dir",
        default="server/public/reports/holdout_runs",
        help="Holdout JSON directory",
    )
    ap.add_argument(
        "--digest-dir",
        default="tmp/preproc_digest",
        help="Directory storing FAST/FULL preprocessing digests",
    )
    args = ap.parse_args()
    runs_dir = Path(args.runs_dir)
    if not runs_dir.exists():
        print(f"[error] runs dir not found: {runs_dir}")
        return 1
    entries = gather_runs(runs_dir)
    digests = load_digest_map(Path(args.digest_dir))
    return summarize(entries, digests)


if __name__ == "__main__":
    raise SystemExit(main())
import copy
