"""Validate a catalog.json written by build_catalog.py.

Checks every entry's domain against SOURCE_DIRS and tags against build_catalog.TAGS,
requires a non-empty summary and _meta.enforcement == "json_schema", and (with
--expect N) the entry count. Prints one line per failing entry; exits 0 only if
everything passes.

Usage:
  .venv/bin/python scripts/check_catalog.py data/catalog.json [--expect 126]
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))    # knowledge_base

from knowledge_base.config import SOURCE_DIRS

import build_catalog


def entry_problems(slug: str, entry) -> list[str]:
    if not isinstance(entry, dict):
        return ["entry is not an object (error record?)"]
    problems = []
    if entry.get("domain") not in SOURCE_DIRS:
        problems.append(f"domain {entry.get('domain')!r} is not a SOURCE_DIRS key")
    tags = entry.get("tags")
    if not isinstance(tags, list) or not 6 <= len(tags) <= 10:
        problems.append(f"tags {tags!r} is not a list of 6-10")
    elif len(set(tags)) != len(tags):
        problems.append("tags contain duplicates")
    elif any(t not in build_catalog.TAGS for t in tags):
        bad = [t for t in tags if t not in build_catalog.TAGS]
        problems.append(f"tags outside TAGS: {bad}")
    summary = entry.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        problems.append("summary missing or empty")
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path")
    ap.add_argument("--expect", type=int, help="required number of entries")
    args = ap.parse_args()

    catalog = json.loads(Path(args.path).read_text())
    entries = {k: v for k, v in catalog.items() if k != "_meta"}

    failures = []
    for slug in sorted(entries):
        problems = entry_problems(slug, entries[slug])
        if problems:
            failures.append(f"{slug}: {'; '.join(problems)}")

    enforcement = catalog.get("_meta", {}).get("enforcement")
    if enforcement != "json_schema":
        failures.append(f"_meta: enforcement {enforcement!r} != 'json_schema'")

    if args.expect is not None and len(entries) != args.expect:
        failures.append(f"entry count {len(entries)} != expected {args.expect}")

    for line in failures:
        print(line)
    if failures:
        sys.exit(1)
    print(f"OK: {len(entries)} entries pass")


if __name__ == "__main__":
    main()
