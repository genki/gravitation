from __future__ import annotations
import numpy as np
import pandas as pd
from pathlib import Path
from astropy.cosmology import FlatLambdaCDM
from astropy import units as u
import analysis.h1_strong_lens as h

COSMO = FlatLambdaCDM(H0=70, Om0=0.3)
ARCSEC_TO_RAD = (1 * u.arcsec).to(u.rad).value
C_KMS = 299792.458
# 理論切片（横軸を v_c とする場合は 2π）
B0_VC = np.log10(2 * np.pi) - 2 * np.log10(C_KMS)
B0_SIGMA = np.log10(4 * np.pi) - 2 * np.log10(C_KMS)

R_AP_MAP = {"sdss": 1.5, "boss": 1.0, "bells": 1.0}
ALPHA_AP = -0.066


def load_all():
    frames = [h.load_slacs(Path("data/strong_lensing/SLACS_table.cat"))]
    loaders = [
        (Path("data/strong_lensing/S4TM_table.csv"), h.load_s4tm),
        (Path("data/strong_lensing/BELLS_GALLERY_SL2S_table.csv"), h.load_bells_sl2s),
    ]
    boss_full_path = Path("data/strong_lensing/BOSS_full_table.csv")
    if boss_full_path.exists():
        loaders.append((boss_full_path, h.load_boss_full))
    else:
        loaders.append((Path("data/strong_lensing/BOSS_LAE_table.csv"), h.load_boss_lae))
    for p, loader in loaders:
        if p.exists():
            frames.append(loader(p))
    df = pd.concat(frames, ignore_index=True)
    sig_path = Path("data/strong_lensing/SLACS_sigSIE_clean.csv")
    if sig_path.exists():
        sig = pd.read_csv(sig_path)
        df["z_l_round"] = df["z_l"].round(3)
        df = df.merge(sig, on="z_l_round", how="left")
        if "sigma_SIS" not in df.columns:
            df["sigma_SIS"] = np.nan
        if "sigma_SIS_y" in df.columns:
            df["sigma_SIS"] = df["sigma_SIS"].combine_first(df["sigma_SIS_y"])
            df.drop(columns=["sigma_SIS_y"], inplace=True)
        if "sigma_SIS_x" in df.columns:
            df["sigma_SIS"] = df["sigma_SIS"].combine_first(df["sigma_SIS_x"])
            df.drop(columns=["sigma_SIS_x"], inplace=True)
        df.drop(columns=["z_l_round"], inplace=True)
    # サーベイ欠損を「unknown」で埋め、文字列に統一
    df["survey"] = df["survey"].fillna("unknown").astype(str)
    return df


def compute_ratio(df: pd.DataFrame, re_range=(0.7, 2.0)):
    Ds = COSMO.angular_diameter_distance(df.z_s).to(u.kpc).value
    Dls = COSMO.angular_diameter_distance_z1z2(df.z_l, df.z_s).to(u.kpc).value
    theta_p = df.theta_Ein * ARCSEC_TO_RAD * (Ds / Dls)
    r_ap = np.array([R_AP_MAP.get(s, 1.5) for s in df.survey])
    Re = df.Reff_arcsec.to_numpy().astype(float)
    # fill missing Re with geometric mean of range for main calculation
    Re_main = Re.copy()
    missing = np.isnan(Re_main)
    Re_main[missing] = (re_range[0] * re_range[1]) ** 0.5
    sigma_corr = df.veldisp * (r_ap / Re_main) ** (ALPHA_AP)
    v_c = np.where(
        df.sigma_SIS.notnull(),
        np.sqrt(2) * df.sigma_SIS,
        np.sqrt(2) * sigma_corr,
    )
    # 横軸を v_c に取るので分母は 2π v_c^2
    R = theta_p * (C_KMS**2) / (2 * np.pi * v_c**2)
    mask = np.isfinite(R) & (R > 0)
    R = R[mask]
    logR = np.log10(R)
    logR_low = np.full_like(logR, np.nan)
    logR_high = np.full_like(logR, np.nan)
    if missing.any():
        Re_low = Re_main.copy()
        Re_high = Re_main.copy()
        Re_low[missing] = re_range[0]
        Re_high[missing] = re_range[1]
        sigma_low = df.veldisp * (r_ap / Re_low) ** (ALPHA_AP)
        sigma_high = df.veldisp * (r_ap / Re_high) ** (ALPHA_AP)
        R_low = theta_p * (C_KMS**2) / (2 * np.pi * (np.sqrt(2) * sigma_low) ** 2)
        R_high = theta_p * (C_KMS**2) / (2 * np.pi * (np.sqrt(2) * sigma_high) ** 2)
        mask = np.isfinite(R_low) & (R_low > 0)
        logR_low[mask] = np.log10(R_low[mask])
        mask = np.isfinite(R_high) & (R_high > 0)
        logR_high[mask] = np.log10(R_high[mask])
    med = np.median(logR)
    mad = np.median(np.abs(logR - med))
    s = 1.4826 * mad
    return med, s, R.size, logR, logR_low, logR_high, missing


def per_survey(df):
    rows = []
    for surv in sorted(df.survey.unique()):
        sub = df[df.survey == surv].copy()
        med, s, n, *_ = compute_ratio(sub)
        rows.append((surv, n, med, s))
    return rows


def main():
    df = load_all()
    med, s, n, logR, logR_low, logR_high, missing = compute_ratio(df)
    print(f"Total N={n}, median(log10 R)={med:.4f} dex, scatter={s:.4f} dex")
    for surv, n_s, med_s, s_s in per_survey(df):
        print(f"  {surv}: N={n_s}, median={med_s:.4f} dex, scatter={s_s:.4f} dex")
    # single scale factor to zero median
    # survey-specific scale suggestions
    scale_factors = {}
    for surv, _, med_s, _ in per_survey(df):
        f = 10 ** (0.5 * med_s)
        scale_factors[surv] = f
        print(f"Suggested v_c scale for {surv}: divide by {f:.3f} (to zero median)")
    # QC: apply BOSS-only scaling
    logR_scaled = logR.copy()
    if "boss" in scale_factors:
        mask_boss = df.survey == "boss"
        logR_scaled[mask_boss] -= 2 * np.log10(scale_factors["boss"])
        med_b = np.median(logR_scaled[mask_boss])
        mad_b = np.median(np.abs(logR_scaled[mask_boss] - med_b))
        s_b = 1.4826 * mad_b
        print(f"BOSS after internal scale: median={med_b:.4f} dex, scatter={s_b:.4f} dex")
    # BOSS missing Re intervals
    if logR_low is not None:
        mask_miss = missing & (df.survey == "boss")
        if mask_miss.any():
            support = ((logR_low[mask_miss] <= 0) & (logR_high[mask_miss] >= 0)).sum()
            total = mask_miss.sum()
            print(f"BOSS Re-missing lenses supportive via interval: {support}/{total}")

if __name__ == "__main__":
    main()
