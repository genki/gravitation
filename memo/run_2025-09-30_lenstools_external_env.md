# lenstools（Python）外部環境での導入とSOTA連携（Plan C）

## 手順（Podman例）

1. ベースイメージ起動（Miniconda）
   podman run --rm -ti docker.io/continuumio/miniconda3 bash

2. コンテナ内で古めのスタックを作成（例: py3.9 + numpy1.21 + scipy1.7 + astropy<5）
   conda install -y -c conda-forge python=3.9 numpy=1.21 scipy=1.7 "astropy<5" pip cython
   pip install lenstools

3. バージョン確認（コンテナ内）
   python - <<'PY'
   import lenstools, sys, numpy
   print('LENSTOOLS_VERSION=' + getattr(lenstools,'__version__','?'))
   print('PY_VERSION=' + sys.version.split()[0])
   print('NUMPY_VERSION=' + numpy.__version__)
   PY

4. ホスト側のリポジトリへ「導入情報」を反映（ホストで実行）
   LENSTOOLS_VERSION=<上で出力> PY_VERSION=<上で出力> NUMPY_VERSION=<上で出力> \
   PLATFORM=podman-miniconda3 NOTES="external env" ./scripts/report_lenstools_external.sh

5. SOTA再生成
   PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py

## 備考
- SOTAの環境カードは `server/public/reports/env/lenstools_info.json` が存在すると「導入済（外部env）」として表示します。
- 失敗ログは `server/public/reports/env/lenstools_attempt_*.log` に保存します（任意）。

