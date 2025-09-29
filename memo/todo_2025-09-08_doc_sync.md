# メモ: 用語同期（ULM/対照検証）

目的: 表示/文書/図ラベルを ULW→ULM(P/D)、ヌルテスト→対照検証へ統一。
旧称は初出脚注にのみ残す。

受け入れ条件(DoD)
- SOTAトップ・Prospective・代表6ページで新用語が統一表示。
- 旧称の脚注が初出に1回のみ存在。

実行手順
1) `rg -n "ULW|ヌル" site server docs src` で残存箇所を洗い出し。
2) テンプレ/描画ラベルを置換。脚注テンプレを `assets/templates/footnotes.md` に。
3) `make build-sota docs` で再生成、差分確認。

