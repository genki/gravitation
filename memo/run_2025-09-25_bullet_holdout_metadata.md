# run_2025-09-25_bullet_holdout_metadata

## 結果サマリ
- `scripts/reports/make_bullet_holdout.py` に `metadata` ブロックを追加し、生成UTC時刻・再現コマンド（`sys.executable` 含む）・fair/shared_params SHA・クラスタ核ハッシュ・rng 情報・環境上書きを JSON に記録するよう改修した。
- `make bullet-holdout` を実行して Bullet ホールドアウトを再生成。`server/public/reports/cluster/Bullet_holdout.json` に `metadata.command="/home/vagrant/gravitation/.venv/bin/python scripts/reports/make_bullet_holdout.py"` 等が埋まり、`logs/bullet_holdout_validation.log` が PASS（ΔAICc/Shadow 差 ≤ 1e-3, p 値一致）で更新された。
- HTML 側の脚注（再現カード）も SHA 表示付きで維持され、JSON→HTML の自動上書きフローが機能することを確認した。

## 生成物
- 更新: `scripts/reports/make_bullet_holdout.py`
- 再生成: `server/public/reports/Bullet_holdout.json`, `server/public/reports/Bullet_holdout.html`, `server/public/reports/cluster/Bullet_holdout.json`
- ログ: `logs/bullet_holdout_validation.log`

## 次アクション
1. metadata を脚注カードへ明示表示する（シャドウ検証ページでもコマンド/rng/sha を露出）か検討する。
2. Bullet 以外（AbellS1063/MACSJ0416）のホールドアウト JSON にも metadata を展開し、SOTA 参照カードで表示を統一する。
