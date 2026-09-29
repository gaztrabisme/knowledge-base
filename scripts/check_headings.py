#!/usr/bin/env python3
"""Feature-based quality checks for headings in Markdown books."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge_base.headings import evaluate


DEFAULT_EXCEPTIONS = Path("data/intake/heading-exceptions.json")


def _load_exceptions(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    contents = path.read_text(encoding="utf-8").strip()
    if not contents:
        return {}
    raw = json.loads(contents)
    if not isinstance(raw, dict) or any(not isinstance(value, str) for value in raw.values()):
        raise ValueError(f"exceptions file must be a JSON object of slug-to-reason strings: {path}")
    return raw


def _paths(arguments: list[str]) -> list[Path]:
    paths: list[Path] = []
    for argument in arguments:
        path = Path(argument)
        if path.is_dir():
            paths.extend(sorted(path.glob("*.md")))
        else:
            paths.append(path)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Markdown files or directories (top-level *.md)")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    parser.add_argument("--exceptions", type=Path, default=DEFAULT_EXCEPTIONS)
    args = parser.parse_args(argv)

    try:
        exceptions = _load_exceptions(args.exceptions)
        rows = []
        for path in _paths(args.paths):
            result = evaluate(path.read_text(encoding="utf-8", errors="replace"))
            slug = path.stem
            rows.append({"path": str(path), "slug": slug, **result, "exception": exceptions.get(slug)})
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))

    if args.json:
        print(json.dumps({"books": rows}, ensure_ascii=False))
    else:
        for row in rows:
            status = "FLAGGED" if row["flagged"] else "PASS"
            suffix = f" [exception: {row['exception']}]" if row["exception"] else ""
            print(f"{status} {row['path']}{suffix}")
            for reason in row["reasons"]:
                print(f"  - {reason}")
        unexcepted = [row for row in rows if row["flagged"] and not row["exception"]]
        if not unexcepted:
            print(f"{len(rows)} book(s): no unexcepted heading-quality flags")
    return 1 if any(row["flagged"] and not row["exception"] for row in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
