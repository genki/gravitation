# run_2025-11-24_ja_structure
## TL;DR
- main.ja.md を章構成から書き直し: 0章まえがき・観点整理・重力再定義・四作用再配置・GR対比の骨子を作成
- H1/BTFR セクションの式と判定基準を本文ボックス＆図説明で明示、2π 規約と PASS 窓を再確認
- Data & Code 節と参考文献を新構成に合わせて整理し、再現手順と主要文献を列挙

## Details
- TODO.md を導入し、Task 1〜5 を順次処理。図刷新タスクは一旦スキップ。
- main.ja.md の序文/§1〜§4 を「GRとの併存」「情報ドリフト」「4→3 力」「観測的検証」へ改稿し、導入を充実。
- H1 セクションに定義ボックス (R=θ'_E c^2/(2π v_c^2), PASS 窓) を追加、BTFR 節では軸・切片・±0.1 dex を明記。
- データとコードの公開節に再実行手順（git clone→make）とスクリプト/ディレクトリを列挙。参考文献に Rubin/Tully/Milgrom/NFW/Verlinde など基礎文献を追加。
- Makefile へ `pdf-ja` ターゲットを追加し、`make` で `build/main.pdf` `build/main.ja.pdf` が同時生成されるよう変更。

## Next Actions
- 図刷新タスク (GR vs FDB 模式図等) の実施可否を判断し、必要なら別コミットで対応。
