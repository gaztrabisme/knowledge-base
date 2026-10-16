#!/usr/bin/env bash
set -euo pipefail
FP_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec bash "$FP_REPO_ROOT/scripts/fp/run-python.sh" "$FP_REPO_ROOT/scripts/fp/check_baseline.py"
