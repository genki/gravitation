#!/usr/bin/env bash
# Do not source; execute only
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run $0" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

usage(){
  echo "Usage: $0 [-s SIZE]" >&2
  echo "  SIZE: swap size like 8G, 6G (default 8G)" >&2
}

SIZE="8G"
while getopts s:h opt; do
  case "$opt" in
    s) SIZE="$OPTARG" ;;
    h) usage; exit 0 ;;
    *) usage; exit 2 ;;
  esac
done

if [ "${EUID:-$(id -u)}" -ne 0 ]; then
  if command -v sudo >/dev/null 2>&1; then
    exec sudo -n "$0" -s "$SIZE" || { echo "sudo failed; run manually as root: $0 -s $SIZE" >&2; exit 1; }
  else
    echo "This script requires root. Re-run as root." >&2
    exit 1
  fi
fi

target_bytes() { num=$(echo "$1" | tr '[:lower:]' '[:upper:]');
  case "$num" in
    *G) echo $(( ${num%G} * 1024 * 1024 * 1024 )) ;;
    *M) echo $(( ${num%M} * 1024 * 1024 )) ;;
    *K) echo $(( ${num%K} * 1024 )) ;;
    * ) echo "$num" ;;
  esac
}

cur_swap_mb=$(LC_ALL=C /sbin/swapon --show --bytes 2>/dev/null | awk 'NR>1{sum+=$3} END{printf("%d", sum/1024/1024)}')
[ -z "$cur_swap_mb" ] && cur_swap_mb=0
want_bytes=$(target_bytes "$SIZE")
want_mb=$(( want_bytes / 1024 / 1024 ))

if [ "$cur_swap_mb" -ge "$want_mb" ]; then
  echo "swap already >= ${want_mb}MiB (current ${cur_swap_mb}MiB). Skipping."
  exit 0
fi

SWAPF=/swap.img
active=$(awk '$1=="/swap.img"{print 1}' /proc/swaps || true)
# Try to deactivate swap unconditionally; ignore failure if already off
/sbin/swapoff "$SWAPF" 2>/dev/null || true

echo "Allocating $SIZE at $SWAPF ..."
if command -v fallocate >/dev/null 2>&1; then
  rm -f "$SWAPF" || true
  fallocate -l "$SIZE" "$SWAPF" || dd if=/dev/zero of="$SWAPF" bs=1M count=$((want_mb)) status=progress
else
  dd if=/dev/zero of="$SWAPF" bs=1M count=$((want_mb)) status=progress
fi
chmod 600 "$SWAPF"
/sbin/mkswap "$SWAPF" >/dev/null
/sbin/swapon "$SWAPF"

if ! grep -q '^/swap.img\s' /etc/fstab; then
  echo '/swap.img none swap sw 0 0' >> /etc/fstab
fi

echo "Swap extended. Current:"
/sbin/swapon --show
