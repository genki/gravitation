#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run $0" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FONT_DIR="$ROOT/assets/fonts"
mkdir -p "$FONT_DIR"

download() {
  local url="$1" out="$2"
  if [[ -s "$out" ]]; then
    echo "[fonts] exists: $(basename "$out")"
    return 0
  fi
  echo "[fonts] fetching: $(basename "$out")"
  curl -L --fail --retry 3 --connect-timeout 10 "$url" -o "$out"
}

# Noto Sans CJK JP Regular (OTF) — CJKグリフ本体
download "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansCJKjp-Regular.otf" \
         "$FONT_DIR/NotoSansCJKjp-Regular.otf"

# Noto Sans Symbols 2 Regular (TTF) — 記号（上付マイナスなど）
download "https://github.com/notofonts/noto-sans-symbols-2/releases/download/NotoSansSymbols2-v2.003/NotoSansSymbols2-Regular.ttf" \
         "$FONT_DIR/NotoSansSymbols2-Regular.ttf"

# Noto Sans Math Regular (TTF) — 数式の互換グリフ
download "https://github.com/notofonts/noto-fonts/raw/main/hinted/ttf/NotoSansMath/NotoSansMath-Regular.ttf" \
         "$FONT_DIR/NotoSansMath-Regular.ttf"

echo "[fonts] ready in $FONT_DIR"
