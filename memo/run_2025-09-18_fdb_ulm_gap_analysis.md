# 2025-09-18 FDB/ULM ギャップ分析と研究指示

## 目的
- 版 2025-09-18 付の FDB/ULM 指示と現行リポジトリの状態を突き合わせ、証明準拠ラインに到達するための不足点・即時アクションを棚卸しする。

## 結果サマリ
- S_shadow は global 帯域で p_perm≈0.002 まで改善済みだが、帯域統合・FDR 管理・core/outer 分岐が未整備で DoD を満たさない箇所が残存。
- 公平条件の統一や BAO 尤度、太陽系ペナルティ、パラスキーマ移行、CI 再現性など 8 要件のうち複数が未完了と判定。
- Sprint-1 で着手すべき 5 件（shadow モジュール化、fair.json、BAO 尤度、太陽系上限、パラ移行 CI）を抽出し、TODO に反映。

## 生成物
- memo/run_2025-09-18_fdb_ulm_gap_analysis.md（証明準拠に向けた不足点と優先タスクの整理）
- TODO.md（fair.json・BAO 尤度・太陽系ペナルティの追記）

## 次アクション
- Sprint-1 優先 5 件の実装計画をチームでレビューし、担当アサインを確定。
- 新ホールドアウト候補のデータ可用性を調査し、Lenstool κ パイプライン再現のスケジュールを設定。

## 全体所見
- 方向情報 (S_shadow) と CLASS 連携は直近コミットで大幅更新済み。ただしバンド統合と Q2 指標の最終仕様化、FDR 管理、core/outer 各帯域の整備が未完。
- 公平条件は `config/baseline_conditions.json` に集約されつつあるが、指示で言及の `fair.json` は未構築。AICc 表の必須列 (N, N_eff, k, χ², rχ²) 常設も HTML では暫定対応のまま。
- 新規クラスタ/銀河のホールドアウト鎖はデータ取得手前で停止。Lenstool tarball から κ を生成する仕組みは用意済みだが、凍結パラメタでの再予測ドキュメント化と PASS 判定は未実演。
- BAO 距離点は CLASS ベースラインを実行できる段階。ただし Δχ²/AICc 算出・ fig_eu1c.json への書き込み・SOTA 表示への導線が不足。
- 太陽系上限の定量 (1 AU 近傍) はスクリプト未実装。ペナルティ項は `src/fdb` 内に見当たらず、CI 常時適用の枠組みが必要。
- パラ再編 (schema_v2) は導入済みだが旧→新変換スクリプトや CI テストの赤判定は未整備。既存 JSON をどこまで移行済みかの棚卸しも未実施。
- Docker/conda ベースの 1-click 再現 (`make repro`) は docs 掲載のみ。CI の緑化・リンク監査など 7 条件のうち半分程度が未着手。
- FDB 固有予測 (幾何/外縁/遮蔽差) は解析コード未確認で、 p<0.01 の統計レポートも不在。

## セクション別の不足点と対応案

### 1. 方向情報強化
- `scripts/reports/make_bullet_holdout.py` で band 別 S_shadow/Q2/Fisher を計算しているが、core/outer 別マスクや FDR q=0.05 の補正が HTML に反映されていない。
- Permutation ≥10k・ブロック Bootstrap は達成済み。`memo/run_2025-09-18_shadow_tuning.md` で p_perm=0.0023 を確認。DoD は global 帯域のみ PASS。
- ToDo: `analysis/shadow_bandpass.py` 相当のモジュール化、Q2/V-test/Rayleigh の表記整備、core_r50 マスク対策、FDR 適用ログを JSON へ明文化。

### 2. AICc 公平条件
- `config/baseline_conditions.json` は存在。AICc 表の必須列は JSON 出力 (`server/public/reports/bullet_holdout.json`) に含まれるが、HTML 側の常設テーブルが未統一。
- 指示の `fair.json` は未作成。`analysis` ディレクトリも未成立。
- ToDo: `scripts/reports/make_bullet_holdout.py`・銀河/bench スクリプトから共有できる fair-condition ローダを実装。SHA を脚注固定。

### 3. サンプル拡張
- Lenstool tarball → κ 生成 (`scripts/cluster/prep/build_kappa_from_tarballs.py`) まで整備。ホールドアウト対象 (新規クラスタ/銀河) のデータ配置が未確認。
- `data/cluster/params_cluster.json` からの学習→固定は可能だが、ホールドアウト PASS 判定と ΔAICc≤−10 / S_shadow 有意の証跡が未作成。
- ToDo: 新ホールドアウト候補のデータ可用性調査、`memo` でのベンチ選定、`scripts/reports/make_bullet_holdout.py` の結果を SOTA ページに接続。

### 4. 宇宙論 (BAO 尤度)
- CLASS 実行と Fig-EU1c 描画は完了 (`memo/run_2025-09-17_fig_eu1c_class.md`)。`bao_points.yml` 未作成、Δχ²/AICc 計算スクリプト欠落。
- ToDo: `analysis/bao_likelihood.py` を追加し、`scripts/eu/class_validate.py` or `scripts/build_state_of_the_art.py` から読み込み。SOTA 表示で Δχ²/AICc を明示。

### 5. 太陽系／強重力制約
- 現行コードに太陽系ペナルティ関数が見当たらない。`src/fdb` 配下で 1 AU の加速度上限を適用する仕組みを要追加。
- ToDo: `physics/tests/solar_penalty.py` 等を新設し、CI で常時評価。SOTA ページへ数値図挿入。

### 6. パラ再編
- `params/schema_v2.(json|py)` はコミット済み。旧パラとの互換ローダ `migrate_v1_to_v2.py` は未着手、CI テスト (`curl=0` 等) も未整備。
- ToDo: 既存 `shared_params.json` のバージョンタグ調査、移行スクリプト作成、CI で失敗時に赤表示する仕組みを整備。

### 7. 完全再現
- `docker/` ディレクトリは現状空。`environment.yml` は 2025-09-17 以前のもの。`make repro` ルール未定義。
- ToDo: Dockerfile/environment を更新し、`Makefile` に `repro` ルールを追加。CI ワークフローが存在するか確認の上、代表値チェックを実装。

### 8. FDB 固有予測
- 幾何依存/外縁復帰/遮蔽差 の統計関数がコード内に見当たらず。関連メモもなし。
- ToDo: 指標計算モジュールを設計し、既存銀河サンプルで p<0.01 の証跡作成、SOTA ページにカード追加。

## 直近優先タスク (Sprint-1 対応)
1. `analysis/shadow_bandpass.py` (輪帯 FFT + Q2/V-test + FDR) を切り出し、`make_bullet_holdout.py` から呼び出し。
2. `fair.json` スキーマとローダを実装し、バレット/銀河/bench で整合させる。AICc 表の HTML に (N, N_eff, k, χ², rχ²) を常設。
3. `bao_points.yml` を新設し、`analysis/bao_likelihood.py` を作成。Fig‑EU1c 更新時に Δχ²/AICc を出力。
4. 太陽系ペナルティの数式化と SOTA 表示テンプレ作成。`physics/tests` で CI に組み込み。
5. `params/migrate_v1_to_v2.py` と CI 側での curl=0/球対称/μ→1 テストスイート。

## 派生 TODO
- TODO.md へ: "[urgent] fair.json 実装と AICc 表常設列の同期 — memo/run_2025-09-18_fdb_ulm_gap_analysis.md" を追記。
- TODO.md へ: "[high] BAO 尤度 (bao_points.yml + analysis/bao_likelihood.py) 実装 — memo/run_2025-09-18_fdb_ulm_gap_analysis.md" を追記。
- TODO.md へ: "太陽系ペナルティ常設と SOTA 図追加 — memo/run_2025-09-18_fdb_ulm_gap_analysis.md" を追記。

## 次アクション
- 上記 TODO を反映し、Sprint-1 で消化する作業順序を SOTA runbook に反映予定。
- データ面 (新規クラスタ/銀河) の進捗確認をチームにリクエスト。
