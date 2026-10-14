#!/usr/bin/env bash
set -euo pipefail
FP_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export PYTHONDONTWRITEBYTECODE=1
exec "${FP_PYTHON:-python3}" "$FP_REPO_ROOT/scripts/fp/check_baseline.py"
