# 実行メモ: SOTA進捗率の評価と追加研究指示（2025-09-08）

日時: 2025-09-08

## 結果サマリ

- 総合進捗率（重み付き推定）: 約 65% (±7%)。DoD達成で 85–90% 見込み。
- 強み: 二層骨子/共有μ(k)/AICc比較の運用は定着。NGC3198 外縁1/r²の図示、
  NGC2403 配線は概成。
- 未完: リンク200監査と監査バッジ連動、Prospective指標の恒常化、代表6の
  実測再計算表、対照検証の定量化、バレット薄レンズFDB/Early‑Universe最小核。
- 本メモに沿って Quick Wins（48h）→優先スプリント（今週）の順で実施できる
  粒度に分解し、TODO.md を更新した（該当メモへの参照付き）。

## 生成物

- 企画: 本メモ（評価/優先度/DoD定義）。
- メモ: `memo/todo_2025-09-08_*.md`（WEB-AUDIT/BENCH-FINISH/REP6/CTRL/BULLET/EU/DOC）。
- Backlog: `TODO.md` に SOTAカード起点の実行項目を追加（1行/項目）。

## 次アクション

- 48h Quick Wins（順に実行）
  1) リンク健全化: notifications/ と used_ids.csv を200応答へ。復旧まで監査
     バッジ自動OFF（site-audit連動）。— `memo/todo_2025-09-08_web_audit.md`
  2) 指標恒常化: 全ページへ AICc/(N,k)/rχ² を常設し誤差床式を脚注化。
     — `memo/todo_2025-09-08_metrics_unify.md`
  3) 用語同期: ULW→ULM(P/D)、ヌル→対照検証（初出脚注のみ旧称）。
     — `memo/todo_2025-09-08_doc_sync.md`

- 今週スプリント
  4) 銀河ベンチ確定（外縁1/r²の傾き+95%CI、Hα等高線自動化、脚注テンプレ）
     — `memo/todo_2025-09-08_bench_finish.md`
  5) 代表6: Σ vs 体積（実測）で再出力（AICc/(N,k)/rχ²/ΔAICc/勝率/md5）
     — `memo/todo_2025-09-08_rep6_recalc.md`
  6) 対照検証の定量公開（ΔAICc中央値[IQR]・効果量d・n）—
     `memo/todo_2025-09-08_ctrl_tests.md`
  7) バレット薄レンズFDB 最小核（W/S/畳み込み核→共有3パラ学習→ホールドアウト）
     — `memo/todo_2025-09-08_bullet_fdb.md`
  8) Early‑Universe（Late‑FDB）: mu_late(a,k) 実装→稀少尾倍率→CMB/BAO整合
     — `memo/todo_2025-09-08_eu_late.md`

## 備考（DoD 抜粋）

- 公開品質: 監査リンク200/バッジ一致、AICc/(N,k)/rχ²常設、shared_params.json 単一
  ソース（SHA指紋表示）。
- 銀河ベンチ: NGC3198/2403の外縁1/r²の傾き・95%CI明記、Hα等高線オーバーレイ。
- 代表6: 実測再計算表（AICc, (N,k), rχ², ΔAICc, 勝率, md5, 誤差床/マスク）。
- 対照検証: ΔAICc（中央値[IQR]）・効果量d・n を図表で掲示（1枚）。
- 拡張: バレット ΔAICc≤−10＋3指標、Early‑Universe 稀少尾倍率≥2–5かつCMB/BAO整合。

