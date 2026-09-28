"""Build the v8 source intake manifest from the checked-in curation data.

Run with: .venv/bin/python scripts/build_intake_manifest.py
"""
from __future__ import annotations

import ast
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from knowledge_base.config import SOURCE_DIRS  # noqa: E402

SOURCE_DIR = Path("/Users/GaryT/Documents/books")
CURATION = ROOT / "data" / "intake" / "v8-curation.json"
OUTPUT = ROOT / "data" / "intake" / "v8-manifest.json"
ACTIONS = {"ingest", "skip-duplicate", "skip-indexed", "philosophy"}
REQUIRED = {"file", "slug", "title", "domain", "action", "reason", "summary", "tags"}


def catalog_tags() -> set[str]:
    source = (ROOT / "scripts" / "build_catalog.py").read_text()
    module = ast.parse(source)
    assignment = next(n for n in module.body if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == "TAGS" for t in n.targets))
    return set(ast.literal_eval(assignment.value))


def main() -> int:
    if not SOURCE_DIR.is_dir():
        raise SystemExit(f"Source folder does not exist: {SOURCE_DIR}")
    sources = sorted(p.name for p in SOURCE_DIR.iterdir()
                     if p.is_file() and p.name != ".DS_Store")
    rows = json.loads(CURATION.read_text(encoding="utf-8"))
    names = [row.get("file") for row in rows]
    counts = Counter(names)
    errors = []
    if set(sources) != set(names):
        errors.append(f"inventory mismatch: missing={sorted(set(sources)-set(names))}; extra={sorted(set(names)-set(sources))}")
    duplicates = sorted(name for name, count in counts.items() if count != 1)
    if duplicates:
        errors.append(f"curation rows not unique: {duplicates}")
    allowed_tags = catalog_tags()
    for row in rows:
        if set(row) != REQUIRED:
            errors.append(f"{row.get('file')}: expected exactly {sorted(REQUIRED)} fields")
        if row.get("action") not in ACTIONS:
            errors.append(f"{row.get('file')}: invalid action {row.get('action')!r}")
        if row.get("domain") not in SOURCE_DIRS:
            errors.append(f"{row.get('file')}: unknown domain {row.get('domain')!r}")
        if not row.get("slug") or "/" in row["slug"] or "\\" in row["slug"]:
            errors.append(f"{row.get('file')}: invalid slug {row.get('slug')!r}")
        if not row.get("title", "").strip():
            errors.append(f"{row.get('file')}: title is empty")
        if len(row.get("summary", "")) > 200:
            errors.append(f"{row.get('file')}: summary exceeds 200 characters")
        tags = row.get("tags", [])
        if not isinstance(tags, list) or not 6 <= len(tags) <= 10 or len(tags) != len(set(tags)):
            errors.append(f"{row.get('file')}: tags must be 6-10 unique values")
        elif any(tag not in allowed_tags for tag in tags):
            errors.append(f"{row.get('file')}: unknown tag(s) {sorted(set(tags)-allowed_tags)}")
        if row.get("action") != "ingest" and not row.get("reason", "").strip():
            errors.append(f"{row.get('file')}: skip reason is empty")
    if errors:
        raise SystemExit("Manifest not written:\n" + "\n".join(errors))
    by_name = {row["file"]: row for row in rows}
    rows = [by_name[name] for name in sources]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    actions = Counter(row["action"] for row in rows)
    print(json.dumps({"manifest": str(OUTPUT), "sources": len(rows), "actions": dict(sorted(actions.items()))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
