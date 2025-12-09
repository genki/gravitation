# 宇宙型「学習なし」ディフュージョン最小デモ

`demo/univ/universe_diffusion_demo.py` は学習済みモデルやデータセットを使わず、手作りエネルギー関数の勾配降下＋減衰ノイズだけでノイズ画像から「滑らかで中心に円がある」パターンを出現させるデモです。

## 使い方

```bash
pip install torch numpy matplotlib
python demo/univ/universe_diffusion_demo.py
```

- 64×64 のグレースケール画像を生成し、`demo/univ/outputs/` に途中経過と `final.png` を保存します。
- GPU があれば自動で使用します（`device` を dataclass で指定可）。

## 仕組み（概要）

- BigBang: 標準正規ノイズから開始。
- エネルギー関数 E(x) = 平滑項 + 中心集中項 + 円リング項。時間ステップに応じて重みをスケジューリング。
- 逆拡散更新: `x_{t-1} = x_t - α(t)∇E + β(t)noise` を T=400 ステップで実行。

パラメータは `UniverseConfig` で調整できます。中心を暗くしたい／リングを強調したい場合は重みや `circle_radius` を変更してください。
