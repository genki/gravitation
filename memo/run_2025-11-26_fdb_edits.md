# run_2025-11-26_fdb_edits

## Result summary
- Updated `main.md` abstract and introduction with reader-facing map, zero-parameter H1 emphasis, and GR/FDB equivalence overview.
- Added terminology unification (\Gamma monitoring rate, ULE-EM), footnote on 2\pi vs 4\pi, and clarified BOSS as a supplementary QC set.
- Inserted new concept schematic (`figures/fdb_concept.png`) and SPARC AICc heatmap (`figures/sparc_aicc_grid.png`); aligned figure numbering so BTFR is Figure 4.
- Strengthened captions/table notes (outer \Delta v^2 definition, Table 2 outer metric, BTFR axis units) and added redshift/energy upper-bound clarifications.
- Reproducibility text now points to Table 1 & Figure 1 (H1) and Table 2 & Figures 2–4 (SPARC/BTFR), referencing machine-readable sources.

## Next actions
- Build `main.pdf` to confirm figure numbering and new schematics render as expected.
- Run `make notify-done-site` after verification unless `JOB_CLASS=fast`/`SUPPRESS_NOTIFY` is set.

## Final tweaks (arXiv preflight)
- BTFRキャプションを軸定義と基準線まで含む自給自足形に修正。
- BOSS補助セットの数値 (m_R=+0.0846 dex, s_R=0.1497 dex) を本文に明記。
- ΔAICc定義のBoxを追加し、outer判定を強調。
- Appendix表をTable B1として本文から相互参照。
- 長尺URLを\url{}短縮し、narrow no-break spaceを除去；make pdf警告なし。
- make pdf を再実行し build/main.pdf 更新。

## Final tweaks (arXiv preflight)
- BTFRキャプションを軸定義と基準線まで含む自給自足形に修正。
- BOSS補助セットの数値 (m_R=+0.0846 dex, s_R=0.1497 dex) を本文に明記。
- ΔAICc定義のBoxを追加し、outer判定を強調。
- Appendix表をTable B1として本文から相互参照。
- 長尺URLを\url{}短縮し、narrow no-break spaceを除去；make pdf警告なし。
- make pdf を再実行し build/main.pdf を更新。
- main.ja.md を最終調整（GR↔FDBの明示、定義1追加、H1チェックリスト、BOSS補助数値、ΔAICc設定の明記、図キャプションでΓを説明、再現コミットをc429a17に更新）。
