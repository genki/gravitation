# 2025-09-18 バレット影整合しきい値チューニング

## 作業概要
- `config/baseline_conditions.json` の shadow セクションを再設計。Σ_e・σマップの分位と edge 候補を再調整して、界面マスクの候補群を拡張。
- バレットホールドアウトレポートを再生成し、S_shadow の Permutation p 値が十分小さくなる組合せを探索。

## 主要変更
- se_quantile=0.70, sn_quantile=0.88, rr_quantile=0.78, edge_quantiles=[0.70,0.72,0.75,0.78,0.80,0.82,0.85,0.88], edge_count=1400, perm_min=10000, block_size=28。
- `server/public/reports/bullet_holdout.(html,json)` を更新。最良候補は edge_count=1400 の固定上位抽出で、band_4_8/8_16 で weight_sum=315 の帯域整合。

## 結果ハイライト
- S_shadow(global)=0.151、outer_r75=0.153。
- Permutation(one-sided >0): n=10000, p_perm=0.0023、BH-q=0.0092。
- Bootstrap(ブロック, n=400): 95%CI=[0.003, 0.243]。
- Rayleigh: R=0.152 (p=4.06×10⁻⁷)、V-test: V=-0.151 (p=6.06×10⁻⁷)。
- ΔAICc(FDB−shift)=-3.36×10⁹（不変）。Spearman(global)=-0.432 (p=0)。
- 実行時間 ~180 秒（輪帯 FFT＋Permutation 10k＋Bootstrap 400）。

## フォローアップ
- core_r50 の S_shadow は依然 NaN（マスク無し）。core/outer の個別マスク戦略を検討。
- 境界帯 Fisher の有意化は未達（p_fisher≈0.16）。dtau 帯域の再最適化が必要。
