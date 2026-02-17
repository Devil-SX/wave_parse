#!/usr/bin/env bash
# setup_envs.sh -- Create isolated Python virtual environments for benchmarking.
#
# Creates three uv-managed venvs under benchmarks/python/:
#   .venv_vcdvcd   -- vcdvcd (VCD reader) + pyvcd (VCD writer)
#   .venv_pylibfst -- pylibfst (FST reader/writer via C API)
#   .venv_pywellen -- pywellen (Rust-based waveform parser via maturin)
#
# Usage:
#   bash benchmarks/python/setup_envs.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYWELLEN_DIR="/home/sdu/wave_parse/wellen/pywellen"

# ---------------------------------------------------------------------------
# Preflight check
# ---------------------------------------------------------------------------
if ! command -v uv &>/dev/null; then
    echo "ERROR: 'uv' is not installed or not on PATH."
    echo "       Install it from https://github.com/astral-sh/uv"
    exit 1
fi

echo "============================================================"
echo "Setting up Python benchmark environments"
echo "  Base directory : ${SCRIPT_DIR}"
echo "  uv version     : $(uv --version)"
echo "============================================================"

# ---------------------------------------------------------------------------
# 1. vcdvcd + pyvcd
# ---------------------------------------------------------------------------
echo ""
echo "--- [1/3] Creating .venv_vcdvcd (vcdvcd + pyvcd) ---"
VENV_VCDVCD="${SCRIPT_DIR}/.venv_vcdvcd"
uv venv "${VENV_VCDVCD}"
uv pip install --python "${VENV_VCDVCD}/bin/python" vcdvcd pyvcd
echo "  Installed vcdvcd + pyvcd into ${VENV_VCDVCD}"

# ---------------------------------------------------------------------------
# 2. pylibfst
# ---------------------------------------------------------------------------
echo ""
echo "--- [2/3] Creating .venv_pylibfst (pylibfst) ---"
VENV_PYLIBFST="${SCRIPT_DIR}/.venv_pylibfst"
uv venv "${VENV_PYLIBFST}"
uv pip install --python "${VENV_PYLIBFST}/bin/python" pylibfst
echo "  Installed pylibfst into ${VENV_PYLIBFST}"

# ---------------------------------------------------------------------------
# 3. pywellen (Rust, built via maturin)
# ---------------------------------------------------------------------------
echo ""
echo "--- [3/3] Creating .venv_pywellen (pywellen via maturin) ---"
VENV_PYWELLEN="${SCRIPT_DIR}/.venv_pywellen"
uv venv "${VENV_PYWELLEN}"
uv pip install --python "${VENV_PYWELLEN}/bin/python" maturin

if [ -d "${PYWELLEN_DIR}" ]; then
    echo "  Building pywellen from ${PYWELLEN_DIR} ..."
    (
        cd "${PYWELLEN_DIR}"
        # Activate the venv so maturin develop installs into it
        source "${VENV_PYWELLEN}/bin/activate"
        maturin develop --release
    ) || {
        echo "  WARNING: pywellen build failed. The pywellen benchmark will be skipped."
        echo "           You can retry manually:"
        echo "             source ${VENV_PYWELLEN}/bin/activate"
        echo "             cd ${PYWELLEN_DIR} && maturin develop --release"
    }
else
    echo "  WARNING: pywellen source not found at ${PYWELLEN_DIR}"
    echo "           Skipping pywellen build."
fi

echo "  pywellen venv at ${VENV_PYWELLEN}"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "============================================================"
echo "Environment setup complete."
echo ""
echo "  .venv_vcdvcd   : ${VENV_VCDVCD}"
echo "  .venv_pylibfst : ${VENV_PYLIBFST}"
echo "  .venv_pywellen : ${VENV_PYWELLEN}"
echo ""
echo "To generate test data, run:"
echo "  ${VENV_PYLIBFST}/bin/python ${SCRIPT_DIR}/../generate_testdata.py --scale all"
echo "============================================================"
