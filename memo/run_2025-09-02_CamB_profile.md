# Cam B プロファイルの詳細調査と更新

- 実行日: 2025-09-02
- 目的: Cam B (Camelopardalis B) の素性を一次情報で精査し、
  銀河プロファイルを研究に足る水準へ更新。

## 実行
- 主要ソース: Begum, Chengalur & Hopp (2003, NewA 8, 267) GMRT H I + 光学解析。
  - arXiv: https://arxiv.org/abs/astro-ph/0301194
  - ADS: https://ui.adsabs.harvard.edu/abs/2003NewA....8..267B/abstract
- 反映: `memo/galaxies/CamB.md` に基礎量（距離, v_sys, i, M_HI, M_B, h_B/V）,
  回転曲線（非対称ドリフト補正）, ハロー適合（等温 vs NFW）を追記。
- BL方針: dIrr/LSBの系統差回避のためBL対象で維持。

## 結果サマリ
- Cam B は dIrr/LSB, D≈2.2 Mpc, v_sys≈77.5 km/s, i≈65°, M_HI≈5.3e6 M☉,
  V_max(補正)≈20 km/s。等温ハロー適合良好, NFWは不適。
- 相互作用兆候は弱く、整った剛体回転の速度場を示す孤立系。

## 生成物
- 更新: `memo/galaxies/CamB.md`

## 次アクション
- NED/SIMBADの同定子・別名を補完（自動抽出スクリプトの候補）。
- BL反映版CV/ブートストラップで Cam B 除外の影響度を要約に追記。
