"""Fail closed on runtime drift before running the checker or its unit cases."""
import importlib.metadata
import platform
import runpy
import sys

from jsonschema import FormatChecker

from baseline_io import BASE, compare, load


def verify_runtime():
    baseline = load(BASE / 'baseline.json')
    compare('validator.python', baseline['mac']['machine']['python_checker'], platform.python_version())
    compare('validator.jsonschema', baseline['validator']['jsonschema'], importlib.metadata.version('jsonschema'))
    checker = FormatChecker()
    for name, valid in [('date', '2026-10-16'), ('date-time', '2026-10-16T00:00:00Z'),
                        ('uri', 'https://example.invalid/source')]:
        if name not in checker.checkers or not checker.conforms(valid, name) or checker.conforms('invalid date', name):
            raise ValueError(f'changed baseline: validator.format.{name}')


if __name__ == '__main__':
    try:
        verify_runtime()
    except Exception as error:
        print(f'FAIL: {error}', file=sys.stderr)
        sys.exit(1)
    print(f'INFO: checker runtime {sys.executable}; Python {platform.python_version()}; '
          f'jsonschema {importlib.metadata.version("jsonschema")}; formats date/date-time/uri', flush=True)
    sys.argv = sys.argv[1:]
    if sys.argv[0] == '-m':
        sys.argv = sys.argv[1:]
        runpy.run_module(sys.argv[0], run_name='__main__', alter_sys=True)
    else:
        runpy.run_path(sys.argv[0], run_name='__main__')
