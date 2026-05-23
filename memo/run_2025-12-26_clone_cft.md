# run_2025-12-26_clone_cft

## 結果サマリ

- `../cft` への `git@github.com:genki/cft.git` クローンを試行したが、GitHub から `Repository not found` が返り失敗した。
- `ssh -T git@github.com` 自体は認証成功しているため、URL/リポジトリ名の誤り、もしくは当該リポジトリへの権限不足の可能性が高い。
- 追加で `.env` の `GITHUB_TOKEN_S21G` を用いて HTTPS + Authorization header で clone を試行したが同じく `Repository not found`。
- GitHub API `GET /repos/genki/cft` も 404（Not Found）。また当該トークンで `GET /user/repos` を走査しても `cft` を含むリポジトリが見つからなかった。
- `GITHUB_TOKEN_S21G` のトークン所有者は `s21g`（`GET /user` が `login: s21g`）であり、`genki/cft` にコラボ追加したアカウントと不一致の可能性がある。

## 実行内容

- `mkdir -p ../cft`
- `git clone git@github.com:genki/cft.git ../cft`
- `GITHUB_TOKEN_S21G` を使い `https://github.com/genki/cft.git` を Authorization header 付きで clone（失敗）
- `https://api.github.com/repos/genki/cft` をトークン付きで確認（404）
- `https://api.github.com/user/repos` をトークン付きで走査して `cft` を検索（0件）

## 次の一手

- リポジトリ名/オーナーを確認（例: `genki/cft` が存在するか、別組織配下か、リネーム済みか）。
- プライベートなら、この環境の SSH 鍵に当該 repo へのアクセス権があるか確認。
- もしくは正しい HTTPS URL（`https://github.com/<owner>/<repo>.git`）を提示。
- `GITHUB_TOKEN_S21G` を使う場合は、**`s21g` を当該リポジトリの collaborator に追加**するか、`genki` アカウントのトークンを用意する。
