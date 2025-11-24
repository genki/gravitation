# paper ディレクトリ独立公開準備メモ

## 背景
- 旧ドラフト用サブツリーを論文ワークツリーとして使っていたが、公開時にリポジトリ直下へ統合する必要がある。
- GitHub 公開 URL (genki/gravitation) で直接参照できるよう、コード・データの相対パスと README を整備する。

## 作業
1. 旧ドラフトディレクトリ → ルートへ `rsync` で配置 (`main.md`, `figures/`, `src/`, `data/`, `build/` 等)。旧ディレクトリは削除し、Makefile を論文ビルド専用に簡素化。
2. `main.md`, `appendix_f_h1.md`, `table2_aicc.md`, `memo/` などの旧パス参照を `figures/`, `build/`, `src/`, `data/` に読み替え。
3. 解析スクリプト (`src/analysis/h1_ratio_test.py`, `src/analysis/sparc_fit_light.py`, `src/scripts/sparc_sweep.py`) の出力先を `build/` と `figures/` に更新。
4. `data/strong_lensing/`, `data/sparc/` をリポジトリに含めるため `.gitignore` に例外を追加。
5. README.md を新規追加し、構成・ビルド方法・再現ステップ・ライセンス方針を記載。`memo/result3.md`, `memo/run_2025-11-24.md` を新構成に合わせて更新。
6. “Data and code availability” 節に GitHub URL を明記して公開準備を完了。

## 状態
- `make pdf` で `build/main.pdf` を生成済み。
- スクリプトとデータは `https://github.com/genki/gravitation` を前提とした相対パスに統一。
- 旧ドラフトディレクトリの内容はコミット `Adopt paper layout` で反映済み。

## 2025-11-24 追記
- 新リポジトリ URL (https://github.com/genki/gravitation) 公開前提で本文・README・スクリプトのパスを調整。
- `src/analysis/h1_ratio_test.py`, `src/analysis/sparc_fit_light.py`, `src/scripts/sparc_sweep.py` などの出力先を `build/`・`figures/` に統一。
- README を追加し、ビルド手順・再現ステップ・ディレクトリ構成を明文化。
- `git push` を実行し、`main` ブランチをリモート（github.com:genki/gravitation.git）へ同期済み。
