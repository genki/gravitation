# 通知運用Runbook

## 概要

`scripts/notice.sh`はAGENTゲートウェイ経由でtalker/noticeに
通知を送信します。任意でSlackにも同内容を投稿できます。

## 前提

- 依存: bash, curl, jq がインストール済み
- 必須環境変数: `AGENT_TOKEN`
- 任意環境変数: `SLACK_WEBHOOK_URL`

### 環境変数の設定

1) `.env.example` を `.env` にコピー
2) `.env` に値を設定（例）

```sh
export AGENT_TOKEN="<提供されたトークン>"
# 任意
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

## 使い方

最小:

```sh
./scripts/notice.sh -m "デプロイ完了" -t "通知"
```

Make経由（.envを自動読込）:

```sh
make notify MSG="デプロイ完了" TITLE="通知"
```

アクションボタンと添付:

```sh
./scripts/notice.sh -m "再起動しますか" -t "メンテ" \
  -S "返答を選択してください" -a "OK,キャンセル" -F ./assets/cap.png
```

Make経由:

```sh
make notify MSG="再起動しますか" TITLE="メンテ" \
  EXTRA="-S '返答を選択してください' -a 'OK,キャンセル' -F ./assets/cap.png"
```

タイムアウト変更（秒）とサウンド:

```sh
./scripts/notice.sh -m "ジョブ完了" -T 120 -s "Tink"
```

## トラブルシュート

- `AGENT_TOKEN が未設定です` と出る
  - シェルに `export AGENT_TOKEN=...` を設定してください。

- 送信後に反応がない
  - スクリプトは既定で非同期送信です。サーバログや
    受信側UIを確認してください。

- Slackに出ない
  - `SLACK_WEBHOOK_URL` の設定と到達性を確認してください。

## ローカル再現(make repro-local)

- 実行コマンド: `make repro-local`
- フロー: NGC3198 フルベンチ → NGC2403 フルベンチ → Early-Universe CLASS 検証 → `scripts/repro_local_checks.py`
- 閾値: `scripts/repro_local_checks.py` が AICc 差 ≤ 1e-3、p 値 2〜3桁一致を検証。逸脱時は AssertionError で停止。
- 環境: `.venv` と `env.lock` を維持し、必要に応じて `pip install -r requirements.txt` または `micromamba` で復元する。

### 通知とサイト更新を同時に行う

進捗が出たら通知と同時にサイトも更新したい場合:

```sh
make notify-done-site
```

または一時的に環境変数で有効化:

```sh
make notify-done AUTO_PUBLISH_SITE=1
```

これにより `publish-site` と `web-deploy` が続けて実行され、
`site/` の再生成と `server/public/state_of_the_art/` の更新、
ローカルHTTPサーバ（http://localhost:3131）の再起動まで行われます。
（Makefileにより `USE_TLS=0` を指定してHTTPで配信します）

## SOTA更新との連携

バレット・ホールドアウトを含む SOTA 更新では、通知ポリシーと再現手順を同期させる。

1. **再現実行**: `docs/state-of-the-art.md` の「バレット・ホールドアウト（1E 0657‑56）再現手順」に従い、
   `scripts/reports/make_bullet_holdout.py` → `scripts/reports/update_sota.py` を実行する。
2. **成果物確認**: `server/public/reports/bullet_holdout.json/.html` と `sota.json/.html` を点検し、ΔAICc と S_shadow の KPI を確認。
3. **メモ記録**: `memo/run_YYYY-MM-DD_*.md` に実行条件（環境変数、WLS パラメタ、結果指標）を必ず追記。
4. **通知送信**: 完了後に `make notify-done`（必要に応じて `make notify-done-site`）で通知ポリシーに従ったサマリを送信。

この手順により、SOTA 更新が行われたことを通知ログから追跡でき、第三者が同じ条件で再現しやすくなる。

## Bulletホールドアウト検証ワークフロー

バレットクラスタのホールドアウト指標は、自動検証で基準値との乖離を監視する。

1. **基準JSON**: `data/baselines/bullet_holdout_reference.json` に AICc、rχ²、S_shadow、Permutation 指標の基準値を保存している。基準更新が必要になった場合は、再現が取れた最新指標を記録する前にレビューを受ける。
2. **検証スクリプト**: `scripts/reports/validate_bullet_holdout.py` が `server/public/reports/cluster/Bullet_holdout.json` から指標を抽出し、基準との差分を以下の許容範囲で比較する。
   - `ΔAICc(FDB−rot)` と `ΔAICc(FDB−shift)`：許容差 1e-3
   - `S_shadow(global)` と `rχ²(FDB)`：許容差 1e-3
   - `p_perm(one-sided)` と `p_fdr`：許容差 1e-4
3. **ログ**: 判定結果は `logs/bullet_holdout_validation.log` に UTC タイムスタンプ付きで `PASS` / `FAIL` を追記する。FAIL 行には超過した項目が列挙される。
4. **実行ポイント**: `make bullet-holdout` と `make kpi-bullet` が `make_bullet_holdout.py` 実行直後に検証スクリプトを呼び出す。手動検証は `PYTHONPATH=. ./.venv/bin/python scripts/reports/validate_bullet_holdout.py` を実行する。
5. **パラメータ**: `make bullet-holdout` では環境変数 `BULLET_PERM_N`（既定 1024）で Permutation 試行数を調整できる。検証は生成済み JSON を参照するため、基準との差異は生成条件の変化を示唆する。

FAIL が記録された場合は、調査結果と暫定対応を直近の `memo/run_*.md` に記入し、基準 JSON の更新を行う際はレビュー承認を得る。
