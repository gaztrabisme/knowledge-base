"""Run every baseline case with the checker's pinned runtime, even from uv's venv."""
import ast
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / 'tests/fp_baseline_cases.py'


def case_ids():
    # Read names without importing the checker into pytest's unrelated runtime.
    tree = ast.parse(CASES.read_text())
    cases = [f'{cls.name}.{method.name}' for cls in tree.body if isinstance(cls, ast.ClassDef)
             for method in cls.body if isinstance(method, ast.FunctionDef) and method.name.startswith('test_')]
    assert cases, 'baseline case inventory must not be empty'
    return cases


@pytest.mark.parametrize('case', case_ids())
def test_baseline(case):
    result = subprocess.run(['bash', str(ROOT / 'scripts/fp/run-python.sh'), str(CASES), case],
                            cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
