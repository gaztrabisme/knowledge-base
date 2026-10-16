#!/usr/bin/env bash
# Shared by the connected checker and pytest's baseline-case subprocesses.
set -euo pipefail
FP_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export PYTHONDONTWRITEBYTECODE=1
exec "${FP_PYTHON:-python3}" "$FP_REPO_ROOT/scripts/fp/baseline_runtime.py" "$@"
