# GitHub 運用メモ（token / gh / Release 更新）

FDB 論文リポジトリ `genki/gravitation` での GitHub 関連の運用ルールと具体的なコマンドをまとめる。

---

## 1. 認証とトークン

- このリポジトリでは GitHub CLI (`gh`) を使う。
- 認証は `.env` 内の `GITHUB_TOKEN` を利用して行う。

### 1.1 `.env` の構造（ローカル専用）

`./.env` の中に以下のような行がある:

```env
GITHUB_TOKEN=github_pat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

- **注意**: `.env` 自体は `.gitignore` で除外されており、リポジトリにはコミットしない。
- `AGENT_TOKEN` など他のトークンと並んでいるが、GitHub 関連で使うのは `GITHUB_TOKEN` のみ。

### 1.2 `gh` での利用方法

`gh` は `GH_TOKEN` 環境変数を見て認証するので、コマンド実行時に `.env` から流し込む:

```sh
GH_TOKEN=$(grep '^GITHUB_TOKEN=' .env | sed 's/^GITHUB_TOKEN=//') gh release list
```

他の `gh` サブコマンドも同様に `GH_TOKEN=...` を前に付けて実行する。

---

## 2. Release の一覧・内容確認

### 2.1 リリース一覧

```sh
GH_TOKEN=$(grep '^GITHUB_TOKEN=' .env | sed 's/^GITHUB_TOKEN=//') \
  gh release list --limit 5
```

出力例:

```txt
FDB docs 2025-11-30  Latest  v2025-11-30  2025-11-29T21:32:00Z
FDB docs 2025-11-26          v2025-11-26  2025-11-26T05:06:56Z
```

### 2.2 個別リリースの詳細

```sh
GH_TOKEN=$(grep '^GITHUB_TOKEN=' .env | sed 's/^GITHUB_TOKEN=//') \
  gh release view v2025-11-30
```

出力には title, tag, URL, asset 一覧などが含まれる:

```txt
title:  FDB docs 2025-11-30
tag:    v2025-11-30
url:    https://github.com/genki/gravitation/releases/tag/v2025-11-30
asset:  main.ja.pdf
asset:  main.pdf
-- 説明文 --
```

---

## 3. PDF のビルドと Release 更新手順

### 3.1 PDF のビルド

ルートで:

```sh
make pdf
```

生成物:

- 英語版: `build/main.pdf`
- 日本語版: `build/main.ja.pdf`

### 3.2 既存 Release の PDF を上書き更新する

1. まずどのタグを使うか決める（例: `v2025-11-30`）。
2. 最新の PDF をビルドしてから、次でアセットを上書きする:

```sh
GH_TOKEN=$(grep '^GITHUB_TOKEN=' .env | sed 's/^GITHUB_TOKEN=//') \
  gh release upload v2025-11-30 \
    build/main.pdf build/main.ja.pdf \
    --clobber
```

ポイント:

- `--clobber` を付けることで同名アセットを上書きできる。
- Release の「作成日時」は変わらないが、ダウンロードされる PDF の中身は更新される。

### 3.3 新しい Release を作成する場合

タグを新たに切って Release を作る場合:

```sh
TAG=v2025-12-01
TITLE="FDB docs 2025-12-01"
GH_TOKEN=$(grep '^GITHUB_TOKEN=' .env | sed 's/^GITHUB_TOKEN=//') \
  gh release create "$TAG" \
    build/main.pdf build/main.ja.pdf \
    --title "$TITLE" \
    --notes "Updated main/main.ja with shell-scale & λ_eff geometry changes."
```

---

## 4. Pages / gh-pages の更新メモ（将来用）

現時点では、Wiki や PDFs をそのまま GitHub Pages に連携する構成は取っていないが、必要になった場合の簡単な方針:

1. `gh-pages` ブランチで `build/main.pdf` や HTML 化した Wiki コンテンツを配置。
2. Settings → Pages で `gh-pages` を公開ブランチに指定。
3. 更新時には通常の git push または CI で `gh-pages` を再構築。

CLI で `gh-pages` を push するスクリプトを用意する場合は、必ず `GH_TOKEN` 経由で `git push` を行うか、事前に `gh auth login` しておく。

---

## 5. 注意点

- `.env` 内の `GITHUB_TOKEN` は**絶対にコミットしない**（すでに `.gitignore` で除外されているが念のため）。
- Release の説明文には「何を変更した PDF か」（例: λ_eff/殻構造アップデート、v2 カーネルなど）を短く書いておくと後で追跡しやすい。
- CLI が使えない環境では、GitHub の Web UI から Release ページを開き、手動で `main.pdf` / `main.ja.pdf` をドラッグ＆ドロップで差し替えてもよい。

