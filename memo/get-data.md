以下は、2025‑09‑12 JST 時点で確認できる情報に基づく、現状在庫と未達事項を踏まえた 最新のデータ入手・生成手順（Abell 1689 / CL0024 の κ 観測マップ相当の整備、Chandra/CIAO によるX線モザイク生成） の指示書です。
（前提：URL 到達性やバージョンは随時変動し得ます。リンク切れ時は、同ドメインのトップから辿るか、Wayback を用いた代替手順を併記しています。）

⸻

目的と全体像
	•	不足データ
	•	Abell 1689 と CL0024（ZwCl 0024+1652）の 観測 κ（kappa_obs.fits）。
	•	CIAO 未導入に起因する 露光補正モザイク（0.5–2 keV） の正式生成。
	•	方針
	1.	公開レンズモデル（Lenstool 公式配布） を取得し、自前で κ（収束）マップ FITS を生成する。
	•	A1689/CL0024 ともに 公式配布 tarball が存在（要ログインの場合あり）。 ￼
	•	生成は Lenstool の runmode「mass/shear」 を用いて κ/γ を直接 FITS 出力。 ￼
	•	参考：CL0024 の Lenstool/GRALE 再構成比較（κマップ差異の注意）。 [oai_citation:2‡A&A

](https://www.aanda.org/articles/aa/full_html/2018/04/aa31932-17/aa31932-17.html?utm_source=chatgpt.com)
2) CIAO 4.17 + CALDB を公式手順で導入し、chandra_repro→merge_obs→fluximage により 0.5–2 keV 露光補正画像 を作成。 ￼
3) Wayback での κ 直接取得は二次手段（著者個人配布の変動大）。まずは 公式モデル→κ生成 を主経路とする。

⸻

1) A1689 / CL0024：Lenstool 公式モデル→κ FITS 生成

1‑A. モデル取得（Lenstool 公式配布）
	•	公式 Wiki（Files）に A1689 / CL0024 の tarball が掲示：
	•	a1689.tar.gz（Limousin+2007 系列）
	•	cl0024.tar.gz
ページ：Lenstool » Files（Login が必要な場合あり、未ログインでも一覧は閲覧可のことが多い）
	•	一覧に a1689.tar.gz / cl0024.tar.gz の存在を明示。 ￼

備考：A1689 の強レンズモデルの代表例（Coe+2010, Limousin+2007 など）。モデル系統差は κ の大域形状に影響し得るため、複数モデル比較をセットで準備（下記 QC 参照）。 ￼
# 例: 認証後に直接取得（URL は Files ページからコピー）
curl -L -o a1689.tar.gz "https://projets.lam.fr/attachments/download/<<ID>>/a1689.tar.gz"
curl -L -o cl0024.tar.gz "https://projets.lam.fr/attachments/download/<<ID>>/cl0024.tar.gz"

tar xzf a1689.tar.gz -C gravitation/data/cluster/Abell1689/
tar xzf cl0024.tar.gz -C gravitation/data/cluster/CL0024/
Wayback 代替（必要時）：Lenstool の プロジェクト/添付 URL を Wayback に投げる（https://projets.lam.fr/projects/lenstool/wiki、.../attachments/*）。それでも不可の場合は、著者名 + クラスタ名 + “lenstool model tar.gz” を種に再探索。

1‑B. Lenstool のインストール（conda 推奨）
	•	conda による導入（2025‑08 リリースの現行案内）。 ￼
conda create -n lenstool_env -c conda-forge lenstool astropy numpy matplotlib
conda activate lenstool_env
# 追加で cfitsio, wcstools が必要な場合
conda install -c conda-forge cfitsio wcstools
1‑C. κ（収束）/γ（シア）マップの FITS 出力
	•	runmode 設定（Lenstool 6.8 以降の仕様に合わせる）
	•	mass 行で zlens, zsource を指定して κ FITS 出力。
	•	shear 行で zsource を指定して γ FITS 出力。
	•	参考：ユーザー ML / wiki 記載。 ￼

テンプレ（例：A1689, z_lens ≃ 0.183；CL0024, z_lens ≃ 0.395）
runmode
  # 出力グリッド（例）：512^2, 1 pixel = 0.5 arcsec 相当の視野に調整
  # 単位・範囲はモデルに付属の README / par に合わせて設定
  grid 512 512  -128.0 -128.0  128.0 128.0   # [arcsec] 左下/右上

  # κマップ（D_ls/D_s=1 規格での収束、出力ファイル名は任意）
  mass   1  512  0.183  2.0  kappa_a1689_zs2p0.fits   # A1689
  #mass  1  512  0.395  2.0  kappa_cl0024_zs2p0.fits   # CL0024

  # γマップ（必要なら）
  shear  1  512  2.0    gamma_a1689_zs2p0.fits
end
注1：zsource は規格化のための値（既定は Dls/Ds=1 での κ が一般的）。外部マップ規格の要件（Dls/Ds=1）も参照。 ￼
注2：実データで比較する際は、観測の有効 z_s へリスケール：
\kappa(z_s) = \kappa(D_{ls}/D_s=1)\times \frac{D_{ls}(z_l,z_s)}{D_s(z_s)}
（宇宙論は SOTA 既定に合わせ、astropy.cosmologyで算出）
lenstool model.par
# 出力された kappa_*.fits / gamma_*.fits を検収用にコピー
1‑D. WCS/スケールの標準化と PIXKPC 付与
	•	WCS：Lenstool 出力の FITS には WCS が書かれていることが多いが、なければ 基準天球座標（RA/Dec など）を par に明示し、出力に反映。
	•	PIXKPC：クラスターの 角径距離から 1 pixel [arcsec] → kpc/pixel を算出し、FITS ヘッダに追加（既存 Bullet, Abell1689/CL0024 の sigma_e.fits/omega_cut.fits と整合）。

⸻

2) CIAO 4.17 の導入と 0.5–2 keV 露光補正モザイク生成

2‑A. インストール（2025‑08/19 リリース）
	•	CIAO 4.17 / CALDB 4.12.x：公式「Download」ページの conda あるいは ciao-install に従う（macOS/Linux。Windows/WSL は非推奨）。 ￼
	•	Quick Start と contributed scripts（4.17.1, 2025‑04）の更新も参照。 ￼

conda 例
# Miniconda/Conda が前提
conda create -n ciao_4_17 -c conda-forge ciao=4.17
conda activate ciao_4_17
ciaover   # バージョン確認
2‑B. 標準スレッド
	1.	再処理（obsid ごと）
chandra_repro indir=<obsid>/ outdir=<obsid>/repro
	2.	多観測合成（露光補正モザイク）
merge_obs "*/repro/" out=merged bands="0.5:2.0:1.0"
# → exposure-corrected 画像が out/ 以下に生成
参照：merge_obs Ahelp。 ￼

	3.	単観測の露光補正画像（必要に応じて）
fluximage <evt2.fits> out=<outdir> bands="0.5:2.0:1.0"
4.	成果物配置
	•	server/public/reports/... など、SOTA が参照する既定パスへ配置。

⸻

3) 品質管理（QC）と受け入れ基準
	•	κ マップの妥当性チェック
	•	公開図との形状整合：A1689/CL0024 の既報図（HST プレス・論文図）で中心・等高線形状を目視整合。 ￼
	•	モデル差の把握：CL0024 は Lenstool vs GRALE で κ の大域差が大きい可能性（Wagner+2018）。2系統出力（可能なら GRALE も）で 不確かさ帯を可視化。 [oai_citation:13‡A&A

](https://www.aanda.org/articles/aa/full_html/2018/04/aa31932-17/aa31932-17.html?utm_source=chatgpt.com)
	•	X線（0.5–2 keV）との相関：κ の主峰と X線輝度ピークのオフセットを測定。
	•	ヘッダ/スケール
	•	BUNIT, CTYPE*, CDELT*, CRVAL*, CRPIX*、独自 PIXKPC を必須。
	•	受け入れ
	•	κ のピーク位置が既報中心から ≲10″ ずれ以内。
	•	κ 等高線の外延が参考図（強レンズ拘束域）と 一貫。
	•	X線ピークとの相対オフセットが既報のレンジ内（CL0024 は議論多し、要注記）。 ￼

⸻

4) 追加：学習用クラスタ（Abell 1689 / CL0024）の κ_obs.fits 命名と配置
	•	命名例：
	•	gravitation/data/cluster/Abell1689/kappa_obs_lenstool_zs1p0.fits
	•	gravitation/data/cluster/CL0024/kappa_obs_lenstool_zs1p0.fits
	•	Wayback 由来の “観測κ” が別経路で得られた場合は、
	•	kappa_obs_wayback_<source>.fits とし、モデル由来と 観測由来を併存管理。

⸻

5) 参考・背景（確認用）
	•	A1689 の強レンズモデル代表（Coe+2010; Limousin+2007） ￼
	•	CL0024 の再解析・モデル比較（Wagner+2018） [oai_citation:16‡A&A

](https://www.aanda.org/articles/aa/full_html/2018/04/aa31932-17/aa31932-17.html?utm_source=chatgpt.com)
	•	HST HLSP（一般例）：SGAS では κ/γ FITS を HLSP として提供（形式の参考）。 ￼

⸻

6) 想定される詰まりポイントと回避策
	•	Lenstool Files の直リンクが 403/要認証
	•	公式ページに サインインしてから Files を開き、「Download」ボタン経由で取得。リファラ必須の場合はブラウザで保存 → サーバに持込み。 ￼
	•	κ 出力のスケーリング（z_s 依存）
	•	外部規格（Dls/Ds=1）で出した κ を 任意 z_s へ変換（上式）。
	•	モデル系統差
	•	CL0024 はモデルの仮定で κ の外延が変わる；モデル間バンドを可視化し、解析では 中央値/分位で扱う。 [oai_citation:19‡A&A

](https://www.aanda.org/articles/aa/full_html/2018/04/aa31932-17/aa31932-17.html?utm_source=chatgpt.com)

⸻

7) 実行順チェックリスト
	1.	Lenstool 公式から a1689.tar.gz / cl0024.tar.gz を取得し、展開。 ￼
	2.	conda で Lenstool 環境を作成。 ￼
	3.	model.par の zlens と runmode を確認・設定（mass/shear 出力）。 ￼
	4.	lenstool model.par → κ/γ FITS を生成。
	5.	PIXKPC をヘッダに追記、WCS 整合。
	6.	CIAO 4.17 を導入し、merge_obs で 0.5–2 keV 露光補正モザイクを生成。 ￼
	7.	κ と X線の相関・既報図との形状整合で QC。 ￼
	8.	kappa_obs.fits を所定パスへ配置、SOTA を「学習κ整備済み」に更新。
付録：コマンド断片

κ の z_s リスケール（Astropy）
from astropy.cosmology import Planck18 as cosmo
import astropy.units as u
import numpy as np
from astropy.io import fits

z_l, z_s = 0.183, 1.0   # 例：A1689
D_s  = cosmo.angular_diameter_distance(z_s)
D_l  = cosmo.angular_diameter_distance(z_l)
D_ls = cosmo.angular_diameter_distance_z1z2(z_l, z_s)
scale = (D_ls/D_s).value   # 無次元

with fits.open('kappa_a1689_DlsDs1.fits', mode='readonly') as hdul:
    data = hdul[0].data * scale
    hdul[0].data = data
    hdul.writeto('kappa_a1689_zs1p0.fits', overwrite=True)

