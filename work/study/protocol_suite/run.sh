#!/usr/bin/env bash
set -euo pipefail
suite_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd -- "$suite_dir/../../.." && pwd)"
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export TMPDIR="$suite_dir/tmp" MPLCONFIGDIR="$suite_dir/cache/matplotlib"
export XDG_CACHE_HOME="$suite_dir/cache" GIT_OPTIONAL_LOCKS=0
mkdir -p "$TMPDIR" "$MPLCONFIGDIR"
cd -- "$repo_dir"
exec work/study/.venv/bin/python -B "$@"
