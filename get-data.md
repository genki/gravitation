# 研究指示（単一MD版・要承認）— A1689/CL0024 の κ 整備と X 線モザイク正式化
**日時**: 2025‑09‑12 JST  
**本ドキュメントは最新・唯一の指示書です（以後の更新は本ファイルを全置換）。**

---

## 0. 前提（現状）
- 在庫
  - **Bullet**: `sigma_e.fits` / `omega_cut.fits`（ACIS 由来・`PIXKPC` あり）, `kappa_obs.fits`（Wayback 由来）, ACIS primary 多数。
  - **Abell1689 / CL0024**: `sigma_e.fits` / `omega_cut.fits`（`PIXKPC` あり）。**`kappa_obs.fits` が未整備**。
- ブロッカー
  - Lenstool 公式 **モデル tarball（a1689, cl0024）要ログイン**のため無人取得不可。
  - **CIAO 未導入**（0.5–2 keV 露光補正モザイクが正式手順で未生成）。

---

## 1. ご提供・許可の依頼（要アクション）
- **モデル tarball の提供（推奨・主経路）**
  - `a1689.tar.gz` と `cl0024.tar.gz` をご提供ください（または Files ページの直リンク／添付 ID）。
  - 受領後は **展開 → lenstool 実行 → κ FITS 生成 → `PIXKPC` 付与 → 所定パス配置** まで即対応します。
- **CIAO 導入の許可**
  - 許可いただければ micromamba/conda で CIAO を導入し、`chandra_repro → merge_obs → fluximage` を実施します。
- **暫定（二次手段）: Wayback 強化**
  - 追加 SEEDS/URL をご提示いただくか、こちらから候補 SEEDS/PATTERN 案を提示して探索を強化します。

---

## 2. 実行方針の選択（いずれか一つ以上）
1. **モデル tarball を先に受領** → κ 生成を先行。  
2. **CIAO の導入と X 線モザイク** を先に実施。  
3. **Wayback 探索の追加 SEEDS**（候補提示 → 即実行）。

---

## 3. 推奨プラン（優先度）
1. **Option 1: tarball 受領 → lenstool κ 生成**（最短で学習を成立）  
2. **Option 2: CIAO 導入 → 0.5–2 keV 露光補正モザイク正式生成**（`sigma_e/omega_cut` を正規化）  
3. **Option 3: Wayback 強化**（tarball が入手困難な場合の暫定）

---

## 4. 実行手順

### 4.1 Option 1 — tarball 受領 → κ FITS 生成（学習用）
**入力**: `a1689.tar.gz`, `cl0024.tar.gz`（または直リンク／添付 ID）  
**出力**:
- `gravitation/data/cluster/Abell1689/kappa_obs.fits`
- `gravitation/data/cluster/CL0024/kappa_obs.fits`
- WCS 完備・`BUNIT=dimensionless`・`PIXKPC`（kpc/pix）付与。

**手順**
1. 受領ファイルを所定パスへ保存し `sha256` 検証 → 展開。  
2. 付属 `par` を用い **lenstool** の `runmode mass` で κ を出力（規格は **Dls/Ds=1**）。  
3. WCS を確認／整備。角径距離から `PIXKPC` を計算して FITS ヘッダに追記。  
4. 必要に応じ κ(Dls/Ds=1) → κ(z_s) へリスケール。  
5. 所定パスへ配置し、**再現メタ（URL/sha/コマンド）** を `used_ids.csv` 等に追記。

**DoD‑1**
- 両クラスターの `kappa_obs.fits` が存在（WCS/`PIXKPC`/`BUNIT` 整備済み）。  
- κ ピーク位置が既報中心から許容内。  
- (α,β,C) 学習が収束。

---

### 4.2 Option 2 — CIAO 導入 → 0.5–2 keV 露光補正モザイク正式生成
**入力**: Bullet（必要なら学習クラスタ）の ACIS 観測データ  
**出力**: 露光補正モザイク（0.5–2 keV）→ `sigma_e.fits` / `omega_cut.fits`（正式版）

**手順**
1. **許可取得** → micromamba/conda で CIAO（＋CALDB）導入、`ciaover` で確認。  
2. `chandra_repro`（各 ObsID）→ `merge_obs`（0.5–2 keV）→ 必要に応じ `fluximage`。  
3. `Σ_e ≈ A·√S_X(0.5–2 keV)` から `n_e`・`ω_p`・`ω_cut` を導出し FITS 化（`PIXKPC` 付与）。  
4. 既存ファイルと差し替え、**相対差（中央値）< 10%** を確認・記録。

**DoD‑2**
- `ciaover` 実行可。0.5–2 keV 露光補正モザイクが生成済み。  
- `sigma_e/omega_cut` 正式フローで更新・検証済み。  
- Bullet ホールドアウトの三指標（κ残差×Σ_e 含む）が更新。

---

### 4.3 Option 3 — Wayback 強化（暫定 κ 取得）
**入力**: 追加 SEEDS/URL（または本案の承認）  
**出力**: `kappa_obs_wayback_*.fits`（WCS／`PIXKPC` 付与）

**手順**
1. ルート候補（Lenstool Files/Wiki・著者サイト・`attachments/` 階層）と PATTERN（`kappa*.fits`, `convergence*.fits`, `a1689*.tar.gz`, `cl0024*.tar.gz`）を確定。  
2. `fetch_kappa_wayback.sh` に SEEDS/PATTERN を追加し一括探索。  
3. 取得物を検証（形状・中心・外延）。WCS／`PIXKPC` を整備。  
4. 所定パスに配置（tarball 由来 κ と併存管理）。

**DoD‑3**
- 追加 SEEDS での探索結果を記録し、入手可否が明確。  
- 取得した κ が形状検査を通過し、**学習の暫定代替**として利用可能。

---

## 5. 実行後の統合（共通）
1. **学習 → 固定**: （Option 1/3 で κ が整い次第）A1689/CL0024 で (α,β,C) を学習し固定。  
2. **Bullet ホールドアウト**: 固定パラで適用し、**ΔAICc** と **三指標**（κピーク—銀河/ICL/X線距離、剪断位相、κ残差×Σ_e 負相関）を更新。  
3. **監査メタ**: 取得元 URL・sha256・実行コマンド・`ciaover` 等を `used_ids.csv` 等に追記。

---

## 6. セキュリティ / 運用
- ログイン資格情報の提示は不要。tarball はファイル提供または直リンク／添付 ID 指定で対応。  
- CIAO はローカル環境のみ導入。環境追加以外の設定変更は行いません。  
- 取得ファイルは **sha256** と **取得日時** を記録し、再現性を確保します。

---

## 7. 返信テンプレート（該当行のみ残して返答）
```text
[選択] 次で進めてください：
  ☐ 1. モデル tarball を先に受領 → κ 生成を先行
      添付: a1689.tar.gz / cl0024.tar.gz
      （または）直リンク/添付ID:
        - A1689: <URL または ID>
        - CL0024: <URL または ID>

  ☐ 2. CIAO の導入と X 線モザイクを先に実施
      許可: ☐ 承認する
      （任意）導入方式: ☐ conda正攻法 / ☐ offline(conda-pack) / ☐ Docker暫定

  ☐ 3. Wayback 探索の追加 SEEDS（候補提示 → 即実行）
      ご提供 SEEDS/URL（任意）:
        - <seed 1>
        - <seed 2>
      （または）こちらの候補案で開始: ☐ 承認する
8. 受け入れ基準（全体 DoD）
	•	DoD‑1 または DoD‑3 を満たし、(α,β,C) 学習が収束している。
	•	DoD‑2 を満たし、sigma_e/omega_cut の正式再生成が完了。
	•	Bullet ホールドアウトの ΔAICc と三指標 がページで非空・更新済み。
```

