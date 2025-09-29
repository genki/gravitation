# 2025-09-19 P1タスク事前調査

## P1-1 サンプル拡張（クラスタ学習→凍結→新HO）
- `data/cluster/Abell1689` / `CL0024` には `omega_cut.fits`, `sigma_e.fits`, `kappa_obs.fits` が揃っており、`config/cluster_holdouts.yml` の train セクションは READY 状態。
- 新規ホールドアウト候補 `MACSJ0416`, `AbellS1063` の FITS は未整備。`data/raw/lenstool/` には該当 tarball が存在せず、`data/cluster/<name>/` も空のため、入手・展開が必要。
- `scripts/cluster/run_holdout_pipeline.py --auto-train --auto-holdout` を試行したところ、学習フェーズは動作するが新ホールドアウトは欠品で自動実行不可。ログと `server/public/state_of_the_art/holdout_status.json` に READY/MISSING が更新されている。
- 次アクション案: (1) tarball 受領と FITS 生成フローを確定、(2) 受領後に `run_holdout_pipeline.py --auto-train` でパラメタ凍結、(3) `--auto-holdout` で MACSJ0416→AbellS1063 の順に適用。

## P1-2 宇宙論の軽量尤度拡張
- RSD / 弱レンズ / CMB 用データはリポジトリ未整備。軽量尤度の雛形として `scripts/eu/lightweight_likelihood.py` を追加し、YAML (z, values, covariance) から χ² を計算できるコア機能を用意。
- 今後は dataset ごとに YAML/JSON 仕様を確定し、CLASS 既存設定とのトグルや再現スクリプト (`make repro`) での検証ステップを組み込む必要あり。
- TODO: データフォーマットのレビュー、既存 BAO YAML (`data/bao/bao_points.yml`) をテンプレとして RSD/weak lens/CMB の変換スクリプトを作成。

## P1-3 FDB 固有予測統計
- 現状はバレット向け `analysis/shadow_bandpass.py` と `scripts/galaxies/compute_fdb_signatures.py` が利用可能。幾何“陰影”・外縁1/r²・遮蔽非対称のうち 2/3 指標で p<0.01 を目指すには、対象天体のリストアップとデータ可用性の確認が必要。
- 提案: (1) 単一銀河ベンチ用 UI をテンプレ化して指標表示を共通化、(2) 多天体統計向けに `compute_fdb_signatures.py` のバッチ処理モードを実装、(3) FDR 管理と可視化を dashboard に統合。

## 次アクション
1. データ調達 — LENSTOOL tarball と追加 FITS の受領依頼を発行し、`data/cluster/MACSJ0416`, `AbellS1063` を整備。受領後に `run_holdout_pipeline.py` をフルパスで実行。
2. 軽量尤度 — RSD/弱レンズ/CMB の観測セットをリスト化し、yaml 形式とモデル生成関数をレビュー会で確定。`lightweight_likelihood.py` を `make repro` へ組み込むタイミングを検討。
3. 固有予測 — 対象銀河の候補リストと既存指標モジュールの改善項目を洗い出し、ブートストラップ/FDR 管理を含む計測フロー案を作成。
