# run_2025-12-18_2_soliton_shrinking_view

## 結果サマリ

- 縮小宇宙で「中心に集まっていくものがその場に留まって見える」期待に合わせ、2-soliton 可視化に **物理ウィンドウ上の座標写像**を追加した。
- 共形場（conformal E,B）はそのまま計算し、各フレームで `x_comoving = x_phys / a(η)` のみ適用する（場のスケーリングは未実装）。
- 120フレーム（η∈[0,32]）・各フレーム 2544×1008px で GIF を生成できることを確認した。
- advanced が「拡散して見える」要因を切り分けるため、**成分ごとの3D診断出力**と、advanced が「η増加で到来」になる **時刻シフト**を追加した。

## 主要変更点（生成物 / 変更ファイル）

- `sim/2-soliton/simulate_two_solitons.py`
  - `a(η)=η0/(η+η0)` を導入し、固定物理ウィンドウでの描画をデフォルト化（`USE_PHYSICAL_WINDOW=True`）。
  - 出力を `out/2-soliton/two_soliton_V1_hopfion_z0_shrinkphys_120f.gif` に変更。
  - フレーム解像度を `dpi=240` に更新。
  - `MATTER_TIME_SHIFT=eta_end` を導入し、advanced 成分が **η増加で z=0 面へ到来**する表示を可能にした。
  - `PRINT_DIAGNOSTICS=True` で、3Dボックス上のエネルギー重心と `⟨S_z⟩` を出力する診断を追加した。
- `sim/2-soliton/README.md`
  - 縮小宇宙の見え方（座標写像のみ）を追記、出力ファイル名を更新。
  - `MATTER_TIME_SHIFT` と `PRINT_DIAGNOSTICS` の説明を追記。
- 生成物:
  - `out/2-soliton/two_soliton_V1_hopfion_z0_shrinkphys_120f.gif`（120 frames / 2544×1008）

## 次の一手

- この「座標写像のみ」の縮小表示が期待する挙動（中心近傍の“留まり”）を再現できているか確認する。
- 「advanced=収束（可視化上）」の定義を、(i) time reversal による逆向き伝播、(ii) z=0断面への到来、(iii) 物理座標での留まり、のどれで評価するかを明確化する。
- 必要なら、FLRW 上の物理場への変換（例: E,B の `a(η)` スケーリングや観測量定義）を実装して、
  「共形場のまま描く」要求との整合を明確化する。
