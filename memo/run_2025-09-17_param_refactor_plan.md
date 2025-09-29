# 2025-09-17 FDBパラメタ再編 設計調査メモ

## 結果サマリ
- shared_params ローダ/スキーマ/マイグレーションを v2 構造対応に刷新し、旧フィールド互換を保ったまま新パラの参照を可能にした。
- SOTA/単一銀河ベンチ/QA/論文変数生成の各スクリプトを v2 パラメタ出力へ追随させ、θ_opt/θ_if/θ_aniso 等の値をカード表示に追加。
- `data/shared_params.json` を v2 形式へ移行し、監査スクリプトで CV サマリとの一致を確認。

## 生成物
- params/schema_v2.py（dataclass ベースの軽量スキーマ）
- scripts/fdb/shared_params_loader.py（v2 ローダ/互換ビュー）
- scripts/migrate_params_v1_to_v2.py（実データ換算＋互換キー同梱）
- data/shared_params.json（θ_* / μ(k) / gas_scale を含む v2 JSON）

## 次アクション
- Σ_ref・L_if・λ_D を導出する `physics/medium.py` と輸送カーネル `physics/transport.py` の実装に着手する。
- SOTA/HTML 側で θ_* 詳細を脚注に常設し、旧パラ表示から完全移行する。
- μ(a,k) 拡張パラの prior/テスト整備と CI への追加。

## 目的
- 研究指示「FDB パラメタ再編（理論拘束版）」に基づき、旧経験的ハイパパラから物理起源パラメタ `θ_opt/θ_if/θ_aniso/θ_cos` への移行計画を具体化する。
- 既存実装（`params/schema_v2.*`, `scripts/fdb/shared_params_loader.py`, `scripts/migrate_params_v1_to_v2.py` 等）の現状と不足を棚卸しする。

## 現状確認
- `data/shared_params.json` は旧スキーマ（μ(k)・gas_scaleのみ）で、`migrate_v1_to_v2` 実行時は既定値から擬似パラメタを生成している。実データからの換算は未実装。
- `params/schema_v2.py/json` は配置済みだが、`FDBParameterSetV2` 内でサブモデルを `ThetaOpt` 等として公開しておらず、`shared_params_loader.ParameterSet` が参照する `FDBParameterSetV2.ThetaOpt` は存在しないため、そのままでは実行時エラーとなる。
- `shared_params_loader.to_legacy_dict` は `tau_q` を 0.75 固定、`delta_tau_frac` に `eta` を直接流用する等、指示された物理換算（`η = δτ·L_if/λ_D` 等）には未対応。
- 物理量 `Σ_ref`, `L_if`, `λ_D`, `ω_p`, `g` の導出モジュールは未実装（`physics/` ディレクトリも未整備）。
- `scripts/cluster/min_kernel.py` や各レポートスクリプトは旧パラメタ `alpha, beta, xi, tau_q, delta_tau_frac` 等を直接利用しており、新パラ構成と整合していない。
- 物理拘束テスト（curl=0, 球対称極限, UV/early 収束など）を行う CI テストセットは未作成。

## 必要な設計要素（案）
1. **スキーマ & ローダ**
   - `params/schema_v2.py` を Pydantic v2 (`model_validate`) と互換な定義に修正し、`ThetaOpt` 等をモジュールスコープで export。
   - `shared_params_loader.load` に物理補助量（例: `Sigma_ref`, `gas_scale`）を含めたデータクラスを整備。
   - `migrate_v1_to_v2` に実データからの換算（`tau0 = alpha·Σ_ref`, `eta = δτ·L_if/λ_D`, `g = β/(1+β)` 等）を組み込む。必要情報が v1 JSON に無い場合は学習クラスタから補完。

2. **媒質物理 (`physics/medium.py`)**
   - 入力: Σ_g(kpc^-2), gas 温度 T, 電子数密度 n_e（X線/HI/Hα 由来）。
   - 出力: プラズマ周波数 `ω_p`, デバイ長 `λ_D`, 界面幅 `L_if ≈ 1/|∇ ln ω_p|` をマルチスケール平滑後に計算。
   - 保守値も baseline JSON へ保存し、クラスタ・銀河共通の参照を可能にする。

3. **輸送カーネル (`physics/transport.py`)**
   - 参照式: `W_eff = e^{-τ0 Σ_e/Σ_ref} + ω0·Ξ(Σ_e, p, q_knee, ξ_sat)` 等、指示の物理解釈に沿った散乱・再放射モデルを実装。
   - 既存 `MinKernelParams` を `theta_opt/theta_if/theta_aniso` へマッピングし直し、旧 API は互換モードで維持。

4. **異方性 (`kernels/aniso.py`)**
   - Henyey–Greenstein 位相関数 `P(cosθ; g)` を実装し、β→g の換算（`g = β / (1 + β)` のような変換を検討）。Lambert項との整合を再評価。

5. **宇宙論 (`cosmo/mu_ak.py`)**
   - 7パラモデル `μ(a,k) = 1 + ε · f(a; s, q, n) · S(k; k0, m, k_c)` を整理し、既存 `mu_late` から置換。
   - 早期/UV極限 (`μ→1`) を明示的にテストできるよう analytic limit を併記。

6. **テスト**
   - `tests/physics_spec.py`（新規）で curl=0, 球対称極限, UV/Early limit を数値検証。
   - 旧 `test_mu_late.py` を `test_mu_ak.py` として書き換え、パラ新仕様をカバー。
   - 既存ベンチ・クラスタの数値比較テストに `to_legacy_dict` を通じた下位互換確認を追加。

7. **データ更新**
   - `data/shared_params.json` を v2 スキーマに再生成し、旧キーは `scripts/migrate_params_v1_to_v2.py` で自動書換。
   - Baseline JSON (`config/baseline_conditions.json`) に L_if, λ_D, Σ_ref, gas_scale など必須パラを追加。

## 未解決点 / 調査課題
- Σ_ref の標準値（例: 1 M⊙ pc⁻²？）の定義ソース。既存コードでは 1.0 を仮定しているが、文献・データの裏付けを要確認。
- 学習クラスタ FITS から n_e, T を安定的に抽出するパイプライン有無（X-rayスペクトル解析結果が既にあるか調査）。
- β→g の正確な換算：Lambert補正 `1+β cosθ` を HG 位相関数に置換する場合の物理整合。
- μ(a,k) の新パラが既存テーブル（cv_shared_summary 等）と矛盾しないよう、共通インターフェースを設計する必要がある。

## 次アクション候補
1. Σ_ref / L_if / λ_D の文献値・データ由来を確認し、`physics/medium.py` の仕様を確定。
2. `params/schema_v2.py` のクラス設計と `shared_params_loader` のデータクラス化を改修し、単純な I/O テストを追加。
3. 旧パラとの互換性維持方針（`to_legacy_dict` など）の詳細を決めた上で、`MinKernelParams` → 新パラ変換のスケッチを作成。


### 旧→新パラ換算案（初稿）
| 旧パラ | 新パラ | 換算式 / 備考 |
|--------|--------|----------------|
| α | τ₀ | `τ0 = α · Σ_ref`。Σ_ref は銀河/クラスタごとの代表面密度（デフォルト 1 M⊙ pc⁻²、後で実測に差し替え）。|
| ξ | ω₀ | 単散乱アルベド。現状 ξ∈[0,∞) → σ散の確率に正規化し、`ω0 = ξ / (1 + ξ)` など確率化を検討。|
| p | p | そのまま移行。既定 0.5–1.5。|
| τ_q, δτ/τ, L_if, λ_D | η | `η = (δτ/τ) · (L_if / λ_D)`。τ_q 自体は界面ゲート閾値として残すが、新スキーマには含めない方針（baseline 条件で別管理）。|
| s_gate | s_gate | スケーリング係数を引き続き保持。|
| q_knee | q_knee | そのまま。|
| β | g | HG 位相関数 `P(cosθ; g)` に合わせて `g = β / (1 + β)` を暫定採用（β∈[0,1) → g∈[0,1)）。|
| μ(k) パラ (ε, k₀, m, …) | θ_cos | 既存 `mu_late` のパラを `θ_cos = {ε, s, k0, q, m, k_c, n}` に拡張。旧 JSON では ε, k0, m のみなので、残りは baseline/事前で補完。|

- アルベド ω₀ の飽和処理（ξ_sat）や knee の扱いは `transport` モジュール側で従来機能を保持しつつ、新スキーマから導入できる可変引数として整理する。
- τ_q は共有パラセットではなく評価条件（baseline JSON）に移し、各解析で共通化する。

## 実装タスクリスト（草案）
1. **スキーマとローダ整備**
   - `params/schema_v2.py` を修正（Pydantic BaseModel、`ThetaOpt` 等を export）。
   - `scripts/fdb/shared_params_loader.py`
     - `ParameterSet` を dataclass から Pydantic モデル/NamedTuple へ整理。
     - `load()` が `gas_scale` など追加情報も返せるように拡張。
     - `to_legacy_dict()` で旧 API 互換の値を算出。
   - `scripts/migrate_params_v1_to_v2.py` に実データ換算を導入し、コマンドラインで v1 JSON → v2 JSON を生成可能にする。
2. **物理モジュールの追加**
   - `physics/medium.py`: Σ_g, n_e, T から `omega_p`, `lambda_D`, `L_if` を計算する関数群と CLI 補助。
   - `physics/transport.py`: `theta_opt/theta_if/theta_aniso` を受けて `W_eff`, `S_gate`, `transport_kernel` を構築する関数を実装。
   - `kernels/aniso.py`: Henyey–Greenstein 位相関数と関連補助関数。
   - `cosmo/mu_ak.py`: 7 パラモデル `μ(a,k)` の実装、旧 `mu_late` 呼び出し箇所を差し替え。
3. **既存コードとの接続**
   - `scripts/cluster/min_kernel.py` を新モジュール呼び出しにリファクタし、互換モード（旧 MinKernelParams → 新パラ）を保持。
   - `scripts/reports/make_bullet_holdout.py`／bench スクリプト／SOTA ビルダーを新パラセットに沿って修正。
   - `data/shared_params.json` を v2 スキーマに更新し、`baseline_conditions.json` に関連物理量を追記。
4. **テストとCI**
   - `tests/physics_spec.py` を追加し、curl=0 / 球対称 / UV/Early limit を検証。
   - `tests/test_mu_ak.py`（旧 `test_mu_late`）で新パラをカバー。
   - `scripts/qa/audit_shared_params.py` を v2 対応に更新、CI での共有パラ検証を強化。
5. **ドキュメント・監査**
   - `docs/state-of-the-art.md` と runbook に新パラ説明と再現手順を追記。
   - ページ脚注に旧→新換算式・Σ_ref・L_if/λ_D の出典を固定。

## 想定テストカバレッジ
- 単体: medium/transport/aniso/mu_ak のユニットテスト。
- 統合: `make_bullet_holdout.py` のスモーク（小さな FITS で pipeline を一周させる軽量モード）を検討。
- QA: shared_params 監査スクリプト、SOTA ビルド差分比較、通知テンプレを含む。


## 今回の実装メモ
- `params/schema_v2.py` を dataclass ベースへ再実装し、外部依存なく `Theta*` 系を構築できるようにした。
- `scripts/fdb/shared_params_loader.py` を v2 スキーマ対応へ更新し、互換出力 (`to_legacy_dict`) は ω₀・g から旧 ξ・β を復元するように調整。
- `scripts/migrate_params_v1_to_v2.py` を学習クラスタ既定 (`data/cluster/params_cluster.json`) と旧 shared JSON を利用して v2 パラへ変換する実データ仕様に改修。`gas_scale` も保持。
- `python scripts/migrate_params_v1_to_v2.py data/shared_params.json -o data/shared_params_v2.json` を実行し、v2 形式の共有JSONを生成した。

## 確認
- `python - <<'PY'` 経由で `load()` が旧形式（migrate 経由）・新形式（v2 JSON）いずれもロード出来ることを確認。
- `pytest tests/test_mu_late.py` は PYTHONPATH 未設定により `ModuleNotFoundError: src` で停止（テスト環境整備が必要）。

## TODO/フォローアップ
- `data/shared_params.json` を v2 へ正式移行する前に、SOTA/bench/報告スクリプトが新フィールドを参照するよう全面改修する。
- `theta_if.eta` の物理換算（L_if, λ_D 取得）と `tau_q` の参照先を baseline JSON へ分離する。
- μ(a,k) 拡張パラ (`s, q, k_c, n`) の事前分布・ドキュメント化。

## 2025-09-17 追加作業ログ
- 単一銀河ベンチ（NGC 3198/2403）と SOTA ビルダーを v2 パラメタで直接表示するよう改修し、θ_opt/θ_if/θ_aniso の要約値をカードに追記。
- 論文用変数生成 (`scripts/paper/generate_vars.py`) と共有パラ監査 (`scripts/qa/audit_shared_params.py`) を新ローダ仕様へ更新し、どこから実行しても import エラーにならないよう `PYTHONPATH` 設定を内包。
- `scripts/migrate_params_v1_to_v2.py` の出力に `mu_k`, `tau0`, `omega0`, `eta`, `g` を同梱し、旧UIが要求する互換プロパティを維持しつつ v2 スキーマへ移行。
- `data/shared_params.json` を v2 スキーマで再生成（mu_k/gas_scale 等は従来キーも保持）し、ローダ経由での互換性を確認。
