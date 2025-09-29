# 2025-09-18 フェア条件ポリシー同期

## 結果サマリ
- `scripts/build_state_of_the_art.py` に config/fair.json のハッシュと適用内容を読み込み、SOTA バレットカードへフェア条件と主判定ルール（rot/shift）を明記するブロックを追加した。
- 公開ページ `server/public/state_of_the_art/index.html` に「フェア条件: config/fair.json (sha=xxxx) … 主判定は AICc(FDB−rot/shift)」の文言を反映し、shuffle を位相破壊の補助対照として位置付けた。

## 生成物
- 更新: `scripts/build_state_of_the_art.py`
- 更新: `server/public/state_of_the_art/index.html`

## 次アクション
- Bullet ホールドアウト HTML の注記にもフェア条件と主判定ルールを追記し、PDF/サイト双方で説明が一致するようにする。
- `docs/state-of-the-art.md` と通知テンプレにも同文を同期（早期に rot/shift 主判定が伝わるよう整備）。
