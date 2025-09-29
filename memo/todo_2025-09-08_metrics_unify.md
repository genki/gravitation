# メモ: 指標の恒常化（AICc/(N,k)/rχ² 常設＋誤差床脚注）

目的: SOTA/ベンチ/Prospective/一覧の全ページで AICc, (N,k), rχ² を常設表示し、
誤差床の式を脚注として明記。極小 rχ² は診断用注記を自動付与。

受け入れ条件(DoD)
- 任意3ページ抜き打ちで AICc/(N,k)/rχ² が確認できる。
- 誤差床の式（例: `σ_floor = clip(0.03×Vobs, 3..7 km/s)`）が脚注にある。
- Prospective/CV でも同一表記（χ²のみ表示は残っていない）。

実行手順
1) `scripts/build_state_of_the_art.py` と `scripts/build_report.py` に共通の出力
   テンプレを使用。`shared/metrics.py` に整形関数を追加/利用。
2) ページテンプレの脚注に誤差床式を注入（TOML/JSONから取得可）。
3) `make build-sota` で再生成し目検（3ページ）。

