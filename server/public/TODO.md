# TODO

このファイルは、作業中に見つけた別タスクを素早く記録するための常設リストです。

記入ルール:
- 各タスクは1行で簡潔に書く（80桁目安）。
- 詳細や長文は `memo/` 配下にメモを作成し、行内にそのファイル名のみを記載する。
  - 例: `APIのリトライ方針検討 — memo/api_retry_memo.md`
- 状態管理が必要な場合のみ、先頭に任意のタグ等を付けてよい（例: `[low]`, `[urgent]`）。

例:
APIのリトライ方針検討 — memo/api_retry_memo.md
ログローテーション設計の見直し

---

Backlog:

（空）

# 2025-09-29 追加（HO並列安全化とバッチ実行）
[urgent] StageResume を digest付きファイルへ移行し並列安全化（旧ファイル互換読み込み済） — memo/run_2025-09-29_stage_resume_and_batches.md
[high] A-3 (W_eff膝) グリッド用ジョブスクリプト追加・運用 — scripts/jobs/batch_w_eff_knee.sh
[high] A-4 (Σ変換×PSF×高通過) グリッド用ジョブスクリプト追加・運用 — scripts/jobs/batch_se_psf_grid.sh
[check] A-5 可視化（S_shadow・境界帯域）パネルはHOページへ常設済（再検証） — memo/run_2025-09-29_stage_resume_and_batches.md

# 2025-09-06 追加（単一銀河ベンチ後のフォローアップ）
NGC3198 残差×Hα相関図の自動生成（データ在時のみ描画） — memo/todo_2025-09-06_ha_overlay.md
εのH_cut結合（境界スケール推定→line-epsに反映）と監査ログ出力 — memo/todo_2025-09-06_eps_policy.md
GR+DM(NFW)のc–M事前（σ_lnc≈0.35）導入とμ同時最適化の確認、脚注整備 — memo/todo_2025-09-06_grdm_prior.md
全ページの表記をAIC→AICcへ統一（SOTA/ベンチ/一覧）

# 2025-09-08 追加（D+2 反映）
[urgent] ULW→ULM 表記の抜け漏れ洗い出し（残存UI文言・図ラベル） — memo/todo_2025-09-08_ulm_label_sweep.md
SOTA/CIでの“数値一致”強制の拡張（合計χ²一致・代表6表の存在） — memo/todo_2025-09-08_ci_numeric.md
data_links.json の参照配線（取得スクリプトに導入） — memo/todo_2025-09-08_data_links.md

# 2025-09-08 追加（SOTAカード実行）
[urgent] WEB-AUDIT: notifications/・used_ids.csv を200応答、監査バッジ自動OFF/ON — memo/todo_2025-09-08_web_audit.md
指標の恒常化: AICc/(N,k)/rχ²常設＋誤差床脚注 — memo/todo_2025-09-08_metrics_unify.md
用語同期: ULW→ULM(P/D)・ヌル→対照検証（初出脚注のみ旧称） — memo/todo_2025-09-08_doc_sync.md
銀河ベンチ仕上げ: 外縁1/r²の傾き95%CI・Hα等高線・脚注テンプレ — memo/todo_2025-09-08_bench_finish.md
代表6再計算: Σ vs 体積（実測）AICc/(N,k)/rχ²/ΔAICc/勝率/md5 — memo/todo_2025-09-08_rep6_recalc.md
対照検証の定量公開: ΔAICc中央値[IQR]・効果量d・n 図表 — memo/todo_2025-09-08_ctrl_tests.md
バレット薄レンズFDB: W/S/核→共有3パラ学習→ホールドアウト — memo/todo_2025-09-08_bullet_fdb.md
Early‑Universe(Late‑FDB): mu_late実装→稀少尾倍率→CMB/BAO整合 — memo/todo_2025-09-08_eu_late.md

# 2025-09-23 追加（証明完了ギャップ指示）
Bullet HO legacy同期実装 — memo/directive_2025-09-23_gap_to_proof.md
AbellS1063 permutation拡張と帯域走査 — memo/directive_2025-09-23_gap_to_proof.md
MACSJ0416 WCS調整とΔAICc負化 — memo/directive_2025-09-23_gap_to_proof.md
弱レンズ/CMB 軽量尤度の実装とSOTA掲示 — memo/directive_2025-09-23_gap_to_proof.md
IRAC1取得・lenstools導入・envログ補完 — memo/directive_2025-09-23_gap_to_proof.md

# 2025-09-24 追加（AbellS1063再評価）
S_shadow候補がedge_count=256固定になる原因調査・切替オプション実装 — memo/run_2025-09-24_abells1063_mask075_psf15_hp15_w0_n2k.md
AbellS1063用 block_pix/weight_power スイープ（512 permutation体制） — memo/run_2025-09-24_abells1063_mask075_psf15_hp15_w0_n2k.md

# 2025-09-25 追加（SOTAフォント整備）
SVG用 Webフォント(WOFF2)の同梱と `svg.fonttype=none` 移行計画 — memo/run_2025-09-25_sota_font_hardening.md
SOTA画像の srcset/@2x 整備＋画像サイズLint導入 — memo/run_2025-09-25_sota_font_hardening.md
FDB-volume geometryカタログ拡充（SPARC noBLの i/PA/h_z 埋め） — memo/todo_2025-09-25_fdb_volume_geometry.md
[high] MatplotlibのCJKグリフ欠落対応（Noto Sans CJK 同梱＋登録） — memo/todo_2025-09-25_fonts_cjk.md
[urgent] AbellS1063 S_shadow >0.1達成に向けたedge/mask/weight再探索 — memo/run_2025-09-25_abells1063_sweep.md, memo/run_2025-09-25_abells1063_fast_followup.md
[urgent] MACSJ0416 Σ層/角度核の再設計と FAST→FULL p_perm<0.02 達成計画 — memo/run_2025-09-26_macsj0416_reproject.md
[low] MOND代表図の旧PNGと現行PNGの差分キャプチャ — memo/run_2025-09-25_mond_recheck.md
[low] GR+DM図のgas_scale整合性レビュー — memo/run_2025-09-25_mond_recheck.md
[low] tri_compare SVGのMOND表記統一（PNG移行含む） — memo/run_2025-09-25_mond_recheck.md

# 2025-09-26 追加（代表比較A/B整合）
[urgent] PSF/高通過処理の実装を両方式へ反映（rep6系） — memo/run_2025-09-26_ab_rep6.md
[urgent] 公平スイープ側の W·S 核 s[kpc] を {0.4,0.6,1.0} に揃える — memo/run_2025-09-26_ab_rep6.md
[check] NGC3198 の Φ·η best(β=0.30, s=0.40, σ_k=0.80) で ΔAICc≈−10.6 を FULL で再確認 — memo/run_2025-09-26_ab_rep6.md
[nice] 代表図本体へ (N,k)/AICc/rχ² の図中オーバレイ実装 — memo/run_2025-09-26_ab_rep6.md

# 2025-09-27 追加（tmux異常終了の追跡）
[urgent] OOM再発防止: SWAPを8GiBへ拡張検討（I/O許容時） — memo/run_2025-09-27_tmux_codex_termination.md
[high] BLASスレッド抑制・glibc arena抑制の実運用（環境変数） — memo/run_2025-09-27_tmux_codex_termination.md
[low] `make start` の `codex` を `setsid -w` 等で独立PG起動しシグナル伝播を抑制 — memo/run_2025-09-27_tmux_codex_termination.md
