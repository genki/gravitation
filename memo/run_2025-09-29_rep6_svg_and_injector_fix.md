# rep6: SVG出力とインジェクタ重複防止（マーカー置換）

## 結果サマリ
- `plot_rep6.py` に **SVG出力**（`<metadata id="rep6">{N,k,rχ²,AICc,seed,shared_sha}</metadata>`）を追加。PNG同様のメタが埋め込みに。
- `inject_rep6_figs.py` に **マーカー挿入**（`<!-- REP6_FIGS_BEGIN/END -->`）と**レガシーブロック削除**の置換ロジックを実装。再注入時も**常に1ブロック**に整列。
- `make rep6` 実行で **PNG+SVG（6×2件）** を生成し、HTMLに**重複なし**でタイルを注入することを確認。

## 生成物
- 図: `assets/rep6/{gal}_rep6.png`, `assets/rep6/{gal}_rep6.svg`（各6枚）
- HTML: `server/public/reports/ws_vs_phieta_rep6.html`（`<!-- REP6_FIGS_BEGIN/END -->` で囲まれた1ブロック）

## 次アクション
- ベンチ図のSVG版も追加予定（必要なら）。
- 代表6のフォント警告（CJKグリフ）については `scripts/utils/mpl_fonts.py` の既定に依存。必要であれば Noto CJK セット導入を検討。
