# OOM再発防止の実施（tmux異常終了対策）

## 結果サマリ
- メモリ安全デフォルトを Makefile に導入（BLAS/numexprスレッド=1, glibc arena縮小）。
- 重いターゲット（rep6-ab-fast/rep6-ab-full/rep6-fast/rep6-full/progress）に適用。
- `start`/`continue` の codex 起動を `setsid -w` に切替（存在時）し、シグナル伝播を抑制。
- スワップを 8GiB へ拡張済（/swap.img）。

## 生成物
- Makefile: `MEMSAFE_ENV` 追加と各ターゲット適用、`setsid -w` 起動。
- scripts/swap_extend.sh: スワップ拡張ユーティリティを追加（実行専用）。
- .env.example: 推奨メモリ環境変数のコメント例を追記。
- 現在のスワップ: `/swap.img 8G`（/proc/swapsで確認済）。

## 次アクション
- 監視: 代表計算（rep6-*）再実行時のメモリピークとOOMの再発有無を確認。
- 必要に応じて: さらなるスワップ拡張（I/O許容時）、またはFULL実行の分割実行化。
- 継続対策: 追加でOOM兆候があれば、`NUMEXPR_MAX_THREADS`や一時データの保存粒度見直しを検討。

