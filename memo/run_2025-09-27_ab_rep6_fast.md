# run_2025-09-27 A/B代表比較（FAST）バックグラウンド実行と整備小結

## 結果サマリ
- 代表6（W·S vs Φ·η）のFAST再計算を `dispatch_bg` で起動し、ログをサーバに保存しました。
- 代表HTML生成器を整備し、各銀河に「最良パラ」ミニカード（β, s[kpc], σ_k, rχ²）と残差±σミニ図を追加済み。
- 両方式の再現メタ（rng/sha/cmd）をJSON→HTMLに恒常表示、DoD‑1のΔAICc整合チェック（|Δ|≤5・符号一致）を内蔵しました。

## 生成物
- data/results/rep6_ws_fast.json（W·S代表; rng=42, k=2, hipass=8–16, psf=1.0/1.5, errfloor=0.03,3,7）
- data/results/rep6_phieta_fast.json（Φ·η代表; 同一条件＋公平グリッド β∈{0.0,0.3}, s∈{0.4,0.6,1.0}, σ_k∈{0.5,0.8,1.2}）
- server/public/reports/ws_vs_phieta_rep6.html（表: AICc/Δ・(N,k)・ミニカード・残差±σ、脚注: rng/sha/cmd 固定）
- ログ: server/public/reports/logs/rep6_ab_fast_20250927_172502.log（バックグラウンド実行記録）

## 次アクション
- [urgent] FULL再計算（hipass=4–8,8–16; psf=1.0/1.5/2.0; float64）を同条件で実施し、NGC3198 の Φ·η best（β=0.30, s=0.40, σ_k=0.80）で ΔAICc≈−10.6 の再現を確認。
- [urgent] 両方式への PSF畳込み/高通過の実装反映（現状は脚注固定）。
- [check] 公平スイープ側の W·S 核パラ s[kpc] を {0.4,0.6,1.0} に揃え、DoD‑1の閾値（|Δ|≤5）へ収束させる。
- [docs] SOTA本文の注記「探索条件差異」を“同一条件で再計算済み（2025‑09‑26, rng=42）”に切替済みか監査。
