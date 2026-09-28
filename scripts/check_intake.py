"""Check v8 intake inventory, configuration, catalog, and hard links."""
from __future__ import annotations

import ast
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from knowledge_base.config import SOURCE_DIRS  # noqa: E402

SOURCE_DIR = Path("/Users/GaryT/Documents/books")
MANIFEST = ROOT / "data" / "intake" / "v8-manifest.json"
CATALOG = ROOT / "data" / "catalog.json"
ACTIONS = {"ingest", "skip-duplicate", "skip-indexed", "philosophy"}


def books_from(path: Path, baseline: bool = False) -> dict[str, str]:
    source = path.read_text(encoding="utf-8")
    if baseline:
        source, count = re.subn(
            r"^\s*# v8 technical shelf START\s*$.*?^\s*# v8 technical shelf END\s*$\n?",
            "", source, flags=re.M | re.S,
        )
        if count != 1:
            raise ValueError(f"Expected one v8 BOOKS block in {path}; found {count}")
    tree = ast.parse(source, filename=str(path))
    assignment = next(n for n in tree.body if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == "BOOKS" for t in n.targets))
    return ast.literal_eval(assignment.value)


def main() -> int:
    errors: list[str] = []
    rows = json.loads(MANIFEST.read_text(encoding="utf-8"))
    names = [row.get("file") for row in rows]
    sources = sorted(p.name for p in SOURCE_DIR.iterdir()
                     if p.is_file() and p.name != ".DS_Store")
    counts = Counter(names)
    if set(sources) != set(names) or any(counts[name] != 1 for name in sources):
        errors.append(f"manifest inventory mismatch: source_count={len(sources)} manifest_count={len(rows)}")
    if any(action not in ACTIONS for action in (r.get("action") for r in rows)):
        errors.append("manifest contains an unknown action")
    for row in rows:
        if row.get("domain") not in SOURCE_DIRS:
            errors.append(f"{row.get('file')}: unknown domain {row.get('domain')!r}")
        if row.get("action") != "ingest" and not row.get("reason", "").strip():
            errors.append(f"{row.get('file')}: missing skip reason")
    config_path = ROOT / "knowledge_base" / "config.py"
    remote_path = ROOT / "scripts" / "remote_index.py"
    config_books = books_from(config_path)
    remote_books = books_from(remote_path)
    old_config = books_from(config_path, baseline=True)
    old_remote = books_from(remote_path, baseline=True)
    preexisting = set(old_config) | set(old_remote)
    ingest = [row for row in rows if row["action"] == "ingest"]
    slugs = [row["slug"] for row in ingest]
    if len(slugs) != len(set(slugs)):
        errors.append("ingest slugs are not unique")
    collisions = sorted(set(slugs) & preexisting)
    if collisions:
        errors.append(f"ingest slugs collide with pre-existing BOOKS keys: {collisions}")
    for path, books in ((config_path, config_books), (remote_path, remote_books)):
        block_keys = set(books) - set(preexisting)
        expected = set(slugs)
        if block_keys != expected:
            errors.append(f"{path.name}: v8 BOOKS keys mismatch: missing={sorted(expected-block_keys)} extra={sorted(block_keys-expected)}")
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    link_errors: list[str] = []
    for row in ingest:
        slug = row["slug"]
        for label, books in (("config.py", config_books), ("remote_index.py", remote_books)):
            if books.get(slug) != row["title"]:
                errors.append(f"{label}: {slug} title mismatch or missing")
        entry = catalog.get(slug)
        expected = {key: row[key] for key in ("title", "domain", "summary", "tags")}
        if not isinstance(entry, dict) or any(entry.get(key) != value for key, value in expected.items()):
            errors.append(f"catalog: {slug} entry missing or does not match manifest")
        source = SOURCE_DIR / row["file"]
        target = SOURCE_DIRS[row["domain"]] / f"{slug}{source.suffix.lower()}"
        if not source.exists():
            link_errors.append(f"source missing: {source}")
        elif not target.exists() or target.is_symlink():
            link_errors.append(f"hard link missing or is symlink: {target}")
        else:
            src_stat, dst_stat = source.stat(), target.stat()
            if (src_stat.st_dev, src_stat.st_ino) != (dst_stat.st_dev, dst_stat.st_ino):
                link_errors.append(f"inode mismatch: {target}")
    if link_errors:
        examples = "; ".join(link_errors[:5])
        more = f" (+{len(link_errors)-5} more)" if len(link_errors) > 5 else ""
        errors.append(f"hard link verification failed for {len(link_errors)}/{len(ingest)} rows: {examples}{more}")
    summary = Counter(row["action"] for row in rows)
    domains = Counter(row["domain"] for row in rows if row["action"] == "ingest")
    result = {"sources": len(sources), "manifest_rows": len(rows), "ingest": len(ingest),
              "actions": dict(sorted(summary.items())), "ingest_domains": dict(sorted(domains.items())),
              "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
