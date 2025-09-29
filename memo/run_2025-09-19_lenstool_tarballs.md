# 2025-09-19 Lenstool tarball取得

## 結果サマリ
- Frontier Fields 公開サイトの MACSJ0416 / Abell S1063 Lenstool v4 (CATS, Sharon) ディレクトリから個別FITS一覧を確認。
- `scripts/fetch/fetch_frontier_lenstool.py` を作成し、主要FITSを自動取得して cluster ごとの tarball (`macs0416_lenstool_v4.tar.gz`, `abells1063_lenstool_v4.tar.gz`) を生成。
- ダウンロード済みFITSは `data/raw/frontier/<cluster>/<team>_v4/` に格納。

## 生成物
- `scripts/fetch/fetch_frontier_lenstool.py`
- `data/raw/frontier/macs0416/macs0416_lenstool_v4.tar.gz`
- `data/raw/frontier/abells1063/abells1063_lenstool_v4.tar.gz`

## 次アクション
- range サブディレクトリのサンプル群が必要な場合はスクリプトに再帰取得オプションを追加する。
- tarballのチェックサム生成やメタデータ整理を検討。

## 作業概要
1. Frontier Fields Lenstool v4 ディレクトリを確認し、トップレベルに公開されている主要FITS名称を把握。
2. Python スクリプトで `.fits` を列挙してダウンロードし、取得済みファイルを cluster 配下に整理。
3. cluster ごとに tarball を作成し、後続工程での共有に備えた。
