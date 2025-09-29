#!/usr/bin/env bash
# PATH/bootstrap for the gravitation repo (vagrant user)
# - Adds project bin, local micromamba, lenstool env, Python venv, and CIAO.
# - Safe to source multiple times (idempotent PATH prepends).

#set -euo pipefail

# Resolve repo root from this file's location: tools/profile.d/ -> repo root
_this_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
GRAV_ROOT="$(cd -- "${_this_dir}/../.." && pwd)"

# Helper: prepend to PATH if the directory exists and not already present
_prepend_path() {
  local d="$1"
  [ -d "$d" ] || return 0
  case ":$PATH:" in
    *":$d:"*) ;; # already present
    *) PATH="$d:${PATH}" ;;
  esac
}

# 1) Project bin
_prepend_path "${GRAV_ROOT}/bin"

# 2) Project-local micromamba and lenstool env
_prepend_path "${GRAV_ROOT}/.mamba/bin"
_prepend_path "${GRAV_ROOT}/.mamba/envs/lenstool_env/bin"

# 3) Python venv
_prepend_path "${GRAV_ROOT}/.venv/bin"

# 4) CIAO (installed under the user-level micromamba by prior setup)
_prepend_path "$HOME/.mamba/envs/ciao-4.17/bin"

export PATH

# Convenience helpers (lazy activation)
# - ciao-on: source CIAO environment when needed
ciao-on() {
  local setup="$HOME/.mamba/envs/ciao-4.17/bin/ciao.bash"
  if [ -r "$setup" ]; then
    # shellcheck disable=SC1090
    source "$setup"
    type ciaover >/dev/null 2>&1 && ciaover || true
  else
    echo "CIAO setup not found: $setup" >&2
    return 1
  fi
}

# - lt (lenstool): run within the bundled conda env if present
lt() {
  if command -v lenstool >/dev/null 2>&1; then
    lenstool "$@"
  elif [ -x "${GRAV_ROOT}/.mamba/bin/micromamba" ] && [ -d "${GRAV_ROOT}/.mamba/envs/lenstool_env" ]; then
    "${GRAV_ROOT}/.mamba/bin/micromamba" run -p "${GRAV_ROOT}/.mamba/envs/lenstool_env" lenstool "$@"
  else
    echo "lenstool not available; install or check env." >&2
    return 127
  fi
}

# Export GRAV_ROOT for helper scripts
export GRAV_ROOT

