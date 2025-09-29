# 2025-09-26 — MACS J0416 薄層(遷移層)強調・外縁薄帯テスト（FAST）

## 結果サマリ
- 薄層強調（H_kpc=150, χ=0.6）と outer 薄帯（r80–r92）を導入したが、S_shadow が 0.375（outer=0.363）へ低下し、p_perm≈0.15 に悪化。既存ベース（S_shadow≈0.724, p≈0.064）が最良。

## 実施内容
- `BULLET_LAYER_H_KPC=150, BULLET_SHADOW_LAYER_CHI=0.6`、`BULLET_OUTER_Q_LOW=0.80, BULLET_OUTER_Q_HIGH=0.92` を設定し、FAST 再実行。
- 角度核・重み・薄層有無の効果を比較。

## 生成物
- `server/public/reports/MACSJ0416_holdout.html`

## 所見 / 次アクション
- 解析的に強い外縁のみへ過度に集中させると、Permutation の帰無分布が尖り p が下がらない傾向。Σ層の「薄層」よりも、**edge_count の絶対数管理** と **outer帯域の面積（N, N_eff）確保** が重要。
- 以降は薄層強調・外縁薄帯は停止し、ベース outer（r≥r75）・mask 0.85–0.88・edge 640–768 の範囲で **Σ層の角度核 K(θ;χ) の形（物理整合）** に注力する。
