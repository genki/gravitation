# 2025-09-18 SOTAページ BAO統計掲載

## 結果サマリ
- `scripts/build_state_of_the_art.py` に BAO 尤度サマリ生成ロジックを追加し、Fig‑EU1c カードへ χ²/AICc/p 値と観測セットを表示するブロックを挿入。
- `python scripts/build_state_of_the_art.py` を再実行し、SOTA ページに SDSS BOSS DR12 (D_M, H) 対 Late‑FDB の数値比較を反映。
- ページには χ²=3.87, dof=6, AICc=3.87, p=0.694、最大|pull|≲1.46 の記載が追加され、ソース YAML (`bao_points.yml`) を脚注的に明示した。

## 生成物
- 更新: `scripts/build_state_of_the_art.py`
- 更新: `server/public/state_of_the_art/index.html`

## 次アクション
- BAO サマリを docs/state-of-the-art.md（テキスト版）にも同期するか検討。
- DESI/eBOSS など他サンプルを追加した際は同様のサマリが正しく並ぶか確認。
