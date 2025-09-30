# A-3（膝）サマリページ生成とSOTA導線の追加

## 結果サマリ
- A-3 FAST/FULL の結果を自動集計するサマライザを実装し、AbellS1063/MACSJ0416のランキングHTMLを生成。
- SOTAトップのQuick LinksにA-3サマリへの導線を追加（存在時に自動表示）。

## 生成物
- サマリスクリプト: `scripts/reports/summarize_knee_runs.py`
- HTML: `server/public/reports/AbellS1063_a3_summary.html`, `server/public/reports/MACSJ0416_a3_summary.html`
- SOTA更新: `scripts/build_state_of_the_art.py`（Quick LinksへのA-3リンク拡張）

## 次アクション
- AbellS1063 FULLの完了後にサマリを再実行し、S_shadowとΔAICcで上位を確定→文言をSOTAへ反映。
- MACSJ0416 FAST終了後に同様のランキングからFULL候補を選抜し投入。

