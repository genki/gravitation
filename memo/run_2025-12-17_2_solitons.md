# 2025-12-17 2ソリトン共鳴ノート追加

## 結果サマリ
- 縮小宇宙（共形時間）で advanced 解が「計算場」として意味を持つ理由を、物質ソリトン×情報ソリトンの2ソリトン共鳴・局所収束として整理し、`2-solitons.md` にまとめた。
- `scripts/check-math.js` で数式マーカーを確認し、GitHub Wiki ページ `2-Solitons` として追加（Home からリンク追加、check-math で raw math なしを確認）。
- 数式が `pre` にならないよう、Wiki 側は `$$...$$` の GitHub 数式記法に統一し、`\\eta_\\star` 等の記法で check-math 上もレンダリングされることを確認した。

## 主要変更点
- 追加: `2-solitons.md`
- Wiki: `2-Solitons.md`（新規）、`Home.md`（リンク追加）

## 次の一手
- Wikiにも載せるなら、数式表記をWiki向け（raw LaTeX回避）にした版を `2-Solitons` として追加し、Homeからリンクする。

## 通知
- `make notify-done` が Makefile に無く、自動通知手順は実行できない（代替手段の整備が必要）。
