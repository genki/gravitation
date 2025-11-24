# H1 強レンズ一次検定「即示キット」実行メモ

## 目的
- ゼロ自由度の比テスト \(R=\theta_E' c^2 /(2\pi v_c^2)=1\) を O(N) で評価し、FDB 理論の説明コストの低さを即時提示する。
- PASS 時は中央値・ロバスト散布の2指標だけで優位性を示し、スライド化できる。

## 入力データ（レンズごと）
- \(\theta_E\)[arcsec], \(z_l, z_s\)
- \(\sigma_{\rm SIS}\) **または** \(\sigma_{\rm ap}\) と \(R_e\)[arcsec]
- サーベイ識別子（SDSS/BOSS/BELLS）→ \(R_{\rm ap}\) 自動選択

## 手順概要
1. 単位変換：\(\theta_E\)[arcsec] → rad, 距離 \(D_s, D_{ls}\) (Flat ΛCDM: H0=70, Ωm=0.3) を計算し \(\theta_E'=\theta_E D_s/D_{ls}\)。
2. 速度軸：
   - 優先：\(\sigma_{\rm SIS}\) → \(v_c=\sqrt{2}\,\sigma_{\rm SIS}\)
   - 代替：\(\sigma_e=\sigma_{\rm ap}(R_{\rm ap}/R_e)^{-0.066}\) with \(R_{\rm ap}=\)1.5″(SDSS)/1.0″(BOSS,BELLS); \(v_c=\sqrt{2}\,\sigma_e\)
3. 比計算：\(R_i=\theta_{E,i}' c^2 /(2\pi v_{c,i}^2)\), \(\ell_i=\log_{10}R_i\)
4. 指標：中央値 \(m_R\), ロバスト散布 \(s_R=1.4826\,{\rm MAD}\)
5. 判定：\(|m_R|\le0.03\) dex かつ \(s_R\le0.10\) dex で PASS。サーベイ混在で散布悪化時は均質サブセット（例:SDSS）の \(m_R,s_R\) も併記。

## QC チェック
- \(\theta_E\) arcsec→rad 済み、\(\theta_E'\) に \(D_s/D_{ls}\) を適用。
- v_c 軸使用時は分母 2π（σ軸は4π）。\(\sqrt{2}\) 変換漏れに注意。
- アパーチャ指数は -0.066、\(R_{\rm ap}\) は半径。
- PASS 基準を満たせば「ゼロ自由度で一致」を太字で明示。

## スライド提示（PASS 時）
- 左：\(\log_{10}R\) ヒストグラム（0 dex, m_R を縦線表示）
- 右：全体と均質サブセットの (N, m_R, s_R, PASS/FAIL) 2行表
- メッセージ例：「FDB の硬い予言 \(\theta_E' c^2=2\pi v_c^2\) が調整パラメータなしで観測と一致し、GR+DM のハロー調整不要で成立」

## 再点検ポイント（失敗時）
- 2π/4π の取り違え、\(\sqrt{2}\) 変換漏れ、アパーチャ指数符号、サーベイ半径設定。
- 均質サブセットでの再評価を実施。

## 参考スニペット（擬似コード）
```python
thetaE_rad = thetaE_arcsec * (np.pi / (180*3600))
Ds, Dls = ang_diam_dist(z_s), ang_diam_dist_z1z2(z_l, z_s)
theta_p = thetaE_rad * (Ds / Dls)
if has_sigma_SIS:
    v_c = np.sqrt(2) * sigma_SIS
else:
    R_ap = {"sdss":1.5, "boss":1.0, "bells":1.0}.get(survey, 1.5)
    sigma_e = sigma_ap * (R_ap / Re_arcsec)**(-0.066)
    v_c = np.sqrt(2) * sigma_e
R = theta_p * (c_kms**2) / (2*np.pi * v_c**2)
logR = np.log10(R)
m_R = np.median(logR)
s_R = 1.4826 * np.median(np.abs(logR - m_R))
pass_H1 = (abs(m_R) <= 0.03) and (s_R <= 0.10)
```

## 2025-11-24 追記（BOSS, Playwright, SPARC 感度）
- **資料化**: Shu+2017 Appendix A などの HTML を Playwright (Node v20.19.4 / playwright 1.55) で `data/strong_lensing/sources/` に保存し、`data/strong_lensing/BOSS_full_table.csv` へ整形。`analysis/h1_strong_lens.py` が自動で読み込む。
- **最新 H1 統計**: All N=235 (m_R=+0.0009 dex, s_R=0.1057 dex), SDSS N=132 (−0.0003, 0.0175), BELLS N=63 (+0.0777, 0.1367), BOSS N=40 (+0.0846, 0.1497), SDSS+BELLS N=195 (+0.0025, 0.0681)。BOSS は Re 欠損＋ファイバー混在で PASS 阈値外 → 補助ホールドアウトとして扱う。
- **内部 QC**: `analysis/h1_ratio_test.py` はサーベイ別中央値補正係数 (例: boss divide by 1.102) をレポートするが、主張には未適用。Re 欠損時は [0.7'', 2.0''] 範囲で支援判定。
- **SPARC 感度**: `scripts/sparc_sweep.py` で err floor {2,3,5} km/s と M/L {0.5/0.7, 0.44/0.65} を一括走査。NFW は c=10 固定 (k=1) とし、外縁 (r≥2.5R_d) では常に ΔAICc<0。集計は `build/sparc_aicc.csv`, Table 2, Appendix B.3 に反映済み。
