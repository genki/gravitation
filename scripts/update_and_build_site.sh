#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/update_and_build_site.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

# 解析→図生成→SOTA同期→サイト生成を一括実行

echo "[1/3] 図の生成(統計/VR/共有比較)"
PYTHONPATH=. .venv/bin/python scripts/plot_sota_figs.py || true
PYTHONPATH=. .venv/bin/python scripts/plot_compare_shared.py \
  DDO154 DDO161 || true

echo "[2/3] SOTAページの最終更新日更新+図同期"
PYTHONPATH=. .venv/bin/python scripts/update_sota_lastmod.py
bash scripts/sync_figs_to_docs.sh

# 銀河プロファイル一覧ページの生成
echo "[2.5/3] 銀河プロファイル一覧を生成"
PYTHONPATH=. .venv/bin/python scripts/build_galaxy_profiles_page.py || true

# 研究キットのデモ図を公開assetsへコピー（存在すれば）
if [ -f kits/.work/solar_residual_demo.png ]; then
  mkdir -p server/public/assets/kits
  cp -f kits/.work/solar_residual_demo.png server/public/assets/kits/
fi

# TODO.md をダッシュボードから参照できるように配置
if [ -f ./TODO.md ]; then
  cp -f ./TODO.md server/public/TODO.md
fi
if [ -f kits/.work/pta_rms_vs_f.png ]; then
  mkdir -p server/public/assets/kits
  cp -f kits/.work/pta_rms_vs_f.png server/public/assets/kits/
fi

echo "[3/3] mkdocs build"
# prefer venv mkdocs when available
MKDOCS_BIN="./.venv/bin/mkdocs"
if [[ -x "$MKDOCS_BIN" ]]; then
  "$MKDOCS_BIN" build --strict
else
  mkdocs build --strict
fi

# Ensure root index.html has fresh last-updated epoch for client banner
PYTHONPATH=. .venv/bin/python scripts/update_root_lastmod.py || true

echo "done: ./site に出力しました"
