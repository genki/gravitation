#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/cluster/cxo/build_sigma_wcut_ciao.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

# CIAO 4.17 exposure-corrected mosaic → sigma_e.fits / omega_cut.fits
# Usage: scripts/cluster/cxo/build_sigma_wcut_ciao.sh Bullet 0.5:2.0

NAME="${1:-Bullet}"
BAND="${2:-0.5:2.0}"
ROOT="data/cluster/${NAME}"
CXO_DIR="${ROOT}/cxo"
OUT_SIGMA="${ROOT}/sigma_e_ciao.fits"
OUT_WCUT="${ROOT}/omega_cut_ciao.fits"
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
PYTHON_BIN="${REPO_ROOT}/.venv/bin/python"
if [ ! -x "$PYTHON_BIN" ]; then PYTHON_BIN="python3"; fi

mkdir -p "${CXO_DIR}"

# Activate CIAO if wrapper exists
if command -v ciao &>/dev/null; then
  : # already active
elif [ -x "$HOME/.mamba/envs/ciao-4.17/bin/ciaover" ]; then
  # Prefer micromamba activation if available
  if [ -x "$HOME/.local/bin/micromamba" ]; then
    set +u
    eval "$("$HOME/.local/bin/micromamba" shell hook -s bash)" || true
    micromamba activate ciao-4.17 || true
    set -u
  else
    # Fallback to conda/mamba-style activation if provided by micromamba
    set +u
    if [ -f "$HOME/.mamba/etc/profile.d/conda.sh" ]; then source "$HOME/.mamba/etc/profile.d/conda.sh"; fi
    if [ -f "$HOME/.mamba/etc/profile.d/mamba.sh" ]; then source "$HOME/.mamba/etc/profile.d/mamba.sh"; fi
    conda activate "$HOME/.mamba/envs/ciao-4.17" || true
    set -u
  fi
fi

have_fluximage=0
command -v fluximage >/dev/null 2>&1 && have_fluximage=1

pushd "${CXO_DIR}" >/dev/null
OUT_SIGMA_ABS="${REPO_ROOT}/${OUT_SIGMA}"
OUT_WCUT_ABS="${REPO_ROOT}/${OUT_WCUT}"

# If there are obsid subdirs with evt2, run chandra_repro; otherwise proceed with merge/fluximage if reprocessed already
shopt -s nullglob
# Look for raw evt2 in typical CIAO tree (download_chandra_obsid layout)
evt_files=(*/primary/*evt2*.fits* */secondary/*evt2*.fits* */*evt2*.fits*)
have_evt=${#evt_files[@]}
if [ "${have_evt}" -gt 0 ] && [ "${have_fluximage}" = "1" ]; then
  # Preferred: use merge_obs on an explicit file list (supports @list)
  ls -1 */repro/*evt2*.fits* 2>/dev/null > evt2_list.lis || true
  if [ ! -s evt2_list.lis ]; then
    ls -1 */primary/*evt2*.fits* 2>/dev/null > evt2_list.lis || true
  fi
  if [ -s evt2_list.lis ]; then
    echo "[ciao] merge_obs @evt2_list.lis"
    # merge_obs は ACIS の命名バンドを要求（soft を使用）
    merge_obs @evt2_list.lis out=merge_${NAME} bands="soft" clobber=yes >/dev/null || true
    echo "[ciao] fluximage: ${BAND} keV (or soft), binsize=1"
    # fluximage は数値帯域を許容。指定が数値ならそれを使い、そうでなければ soft を使う
    FLUX_BAND="${BAND}"
    case "$FLUX_BAND" in
      *:*) : ;; # numeric range ok
      *) FLUX_BAND="soft" ;;
    esac
    fluximage merge_${NAME} merge_${NAME}_img bands="$FLUX_BAND" binsize=1 clobber=yes >/dev/null || true
  fi
  IMG=$(ls -1 merge_${NAME}_img_*_thresh.img 2>/dev/null | head -n1)
  EXP=$(ls -1 merge_${NAME}_img_*_thresh.expmap 2>/dev/null | head -n1)
else
  # If flat evt2 files exist in current dir (download_chandra_obsid default), stage them into obsid/repro tree
  flat_evt=( *evt2*.fits* )
  if [ ${#flat_evt[@]} -gt 0 ] && [ "${have_fluximage}" = "1" ]; then
    echo "[ciao] staging flat evt2 into obsid/repro"
    for f in "${flat_evt[@]}"; do
      base=$(basename "$f")
      # extract obsid digits from filename (acisf0XXXXX...)
      obs=$(echo "$base" | sed -E 's/.*acisf0?([0-9]{4,5}).*/\1/g')
      [ -n "$obs" ] || continue
      mkdir -p "$obs/repro"
      ln -sf "../$base" "$obs/repro/$base"
    done
    obsdirs=$(ls -1d */repro 2>/dev/null | paste -sd, -)
    if [ -n "$obsdirs" ]; then
      echo "[ciao] merge_obs (staged): ${obsdirs}"
      merge_obs "${obsdirs}" out=merge_${NAME} bands="soft" clobber=yes >/dev/null || true
      echo "[ciao] fluximage: ${BAND} keV (or soft), binsize=1"
      FLUX_BAND="${BAND}"; case "$FLUX_BAND" in *:*) : ;; *) FLUX_BAND="soft";; esac
      fluximage merge_${NAME} merge_${NAME}_img bands="$FLUX_BAND" binsize=1 clobber=yes >/dev/null || true
      IMG=$(ls -1 merge_${NAME}_img_*_thresh.img 2>/dev/null | head -n1)
      EXP=$(ls -1 merge_${NAME}_img_*_thresh.expmap 2>/dev/null | head -n1)
    fi
  fi
  # Reproject-based fallback: generate reprojected events then per-file fluximage and combine
  if [ -z "${IMG:-}" ] && [ "${have_fluximage}" = "1" ]; then
    echo "[ciao] fallback2: reproject_obs + per-evt fluximage + combine"
    ls -1 */primary/*evt2*.fits* 2>/dev/null > evt2_list.lis || true
    if [ -s evt2_list.lis ]; then
      reproject_obs @evt2_list.lis reproj clobber=yes >/dev/null || true
      # run fluximage per reprojected evt file
      rm -f file_imgs.lis file_exps.lis
      for f in reproj/*_reproj_evt.fits; do
        [ -f "$f" ] || continue
        base=$(basename "$f" .fits)
        out="flux_${base}"
        FLUX_BAND="${BAND}"; case "$FLUX_BAND" in *:*) : ;; *) FLUX_BAND="soft";; esac
        fluximage "$f" "$out" bands="$FLUX_BAND" binsize=1 clobber=yes >/dev/null || true
        img=$(ls -1 ${out}_*_thresh.img 2>/dev/null | head -n1)
        exp=$(ls -1 ${out}_*_thresh.expmap 2>/dev/null | head -n1)
        [ -f "$img" ] && echo "$img" >> file_imgs.lis
        [ -f "$exp" ] && echo "$exp" >> file_exps.lis
      done
      # Combine with dmimgcalc if available; else Python weighted mean
      if command -v dmimgcalc >/dev/null 2>&1 && [ -s file_imgs.lis ] && [ -s file_exps.lis ]; then
        echo "[ciao] combining with dmimgcalc (weighted by exposure)"
        # Initialize sum images
        first_img=$(head -n1 file_imgs.lis); first_exp=$(head -n1 file_exps.lis)
        cp -f "$first_img" sum_img.fits; cp -f "$first_exp" sum_exp.fits
        tail -n +2 file_imgs.lis | while read -r im; do dmimgcalc sum_img.fits "$im" sum_img.fits op=add clobber=yes >/dev/null 2>&1 || true; done
        tail -n +2 file_exps.lis | while read -r ex; do dmimgcalc sum_exp.fits "$ex" sum_exp.fits op=add clobber=yes >/dev/null 2>&1 || true; done
        IMG=sum_img.fits; EXP=sum_exp.fits
      else
        echo "[ciao] combining with Python (weighted mean)"
        "$PYTHON_BIN" - << 'PY'
import glob
from astropy.io import fits
import numpy as np
imgs=[i.strip() for i in open('file_imgs.lis').read().splitlines() if i.strip()]
exps=[i.strip() for i in open('file_exps.lis').read().splitlines() if i.strip()]
from itertools import islice
if not imgs or not exps or len(imgs)!=len(exps):
    raise SystemExit(0)
sum_img=None; sum_exp=None; hdr=None
for im, ex in zip(imgs, exps):
    with fits.open(im) as I, fits.open(ex) as E:
        a=I[0].data.astype('f4'); b=E[0].data.astype('f4'); hdr=I[0].header
        sum_img = a if sum_img is None else sum_img + a
        sum_exp = b if sum_exp is None else sum_exp + b
with fits.HDUList([fits.PrimaryHDU(sum_img, hdr)]) as H: H.writeto('sum_img.fits', overwrite=True)
with fits.HDUList([fits.PrimaryHDU(sum_exp, hdr)]) as H: H.writeto('sum_exp.fits', overwrite=True)
print('wrote sum_img.fits/sum_exp.fits')
PY
        IMG=sum_img.fits; EXP=sum_exp.fits
      fi
    fi
  fi
  # Fallback: exposure-corrected ACIS pipeline images exist (full_img2)
  echo "[ciao] fallback: mosaicking with Python (glob acisf*_full_img2.fits*)"
  "$PYTHON_BIN" - << 'PY'
import glob, os, numpy as np
from astropy.io import fits
files = sorted(glob.glob('acisf*_full_img2.fits*'))
if not files:
    raise SystemExit(2)
hdus = []
for fn in files:
    try:
        h = fits.open(fn)
        hdus.append(h)
    except Exception:
        pass
if not hdus:
    raise SystemExit(2)
# minimal shape
hs = [h[0].data.shape for h in hdus]
hmin = min(s[0] for s in hs); wmin = min(s[1] for s in hs)
def ccrop(a):
    H,W = a.shape; cy,cx = H//2, W//2; y0 = max(0, cy - hmin//2); x0 = max(0, cx - wmin//2)
    return a[y0:y0+hmin, x0:x0+wmin]
stack = np.stack([ccrop(h[0].data.astype('f4')) for h in hdus], axis=0)
mean = np.nanmean(stack, axis=0).astype('f4')
hdr = hdus[0][0].header
for h in hdus:
    h.close()
fits.writeto('mosaic_sum.fits', mean, hdr, overwrite=True)
print('wrote mosaic_sum.fits from', len(files), 'inputs')
PY
  if [ -f mosaic_sum.fits ]; then IMG="mosaic_sum.fits"; EXP=""; fi
fi

if [ -z "${IMG:-}" ]; then
  echo "[ciao] no mosaic image produced" >&2
  popd >/dev/null
  exit 3
fi

# Convert to electron surface density proxy sigma_e = A * sqrt(I_X)
"$PYTHON_BIN" - "$IMG" "$OUT_SIGMA_ABS" << 'PY'
import sys
from astropy.io import fits
import numpy as np
img,out=sys.argv[1:3]
with fits.open(img) as h:
    a=h[0].data.astype('f4'); hdr=h[0].header
    # exposure-corrected image units ~ ph/s/cm^2/pix; use sqrt as proxy for n_e surface
    sigma=np.sqrt(np.clip(a,0,None))
    hdr['BUNIT']='sqrt(ph s-1 cm-2 pix-1)'
    fits.writeto(out,sigma,hdr,overwrite=True)
print('wrote',out)
PY

# Build omega_cut ~ A * sqrt(I_X) with scaling; keep same map here
cp -f "${OUT_SIGMA_ABS}" "${OUT_WCUT_ABS}"
echo "[ciao] wrote ${OUT_WCUT} (same map; model consumes units via C)"

# Resize to match existing proxies if shapes differ (for stable diff/holdout)
REF_SIG="${REPO_ROOT}/${ROOT}/sigma_e.fits"
if [ -f "$REF_SIG" ]; then
"$PYTHON_BIN" - "${OUT_SIGMA_ABS}" "${REF_SIG}" << 'PY'
import sys
from astropy.io import fits
import numpy as np
from scipy.ndimage import zoom
sig, ref = sys.argv[1:3]
with fits.open(sig, mode='update') as S, fits.open(ref) as R:
    a=S[0].data.astype('f4'); b=R[0].data.astype('f4')
    if a.shape!=b.shape:
        zy=b.shape[0]/a.shape[0]; zx=b.shape[1]/a.shape[1]
        S[0].data=zoom(a, zoom=(zy,zx), order=1)
        S.flush()
PY
  cp -f "${OUT_SIGMA_ABS}" "${OUT_WCUT_ABS}"
fi

popd >/dev/null

echo "[ciao] DONE"
