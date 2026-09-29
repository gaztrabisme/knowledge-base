"""Strip book back-of-book index pages that survived front/back-matter stripping.

The child must have a top-level index heading such as `Index (part N)`, `Names Index`,
`Subject Index`, `Author Index`, or `Index of ...`. The expanded named-heading cleanup is
used for the v9 ingest set via `--slugs-from data/intake/v9-manifest.json`; that scope keeps
unrelated books such as joy-of-cryptography's curated `Index of Security Definitions` intact.

Removes flagged index children and any parent left with no surviving child (back-of-book index
parents are dropped as orphans). Writes cleaned chunk files in place; back up with --backup.

Usage:
  .venv/bin/python scripts/strip_index_backmatter.py --dry-run --slugs-from data/intake/v9-manifest.json
  .venv/bin/python scripts/strip_index_backmatter.py --slugs-from data/intake/v9-manifest.json
"""

import argparse
import json
import re
import shutil
from pathlib import Path

CHUNKS = Path("data/chunks")
INDEX_PART_SUFFIX = re.compile(r"(?:\s+\(part\s+\d+\))+$", re.IGNORECASE)


def is_index_child(ch: dict) -> bool:
    top = (ch.get("metadata", {}).get("heading_path", "") or "").split(">")[0].strip()
    top = INDEX_PART_SUFFIX.sub("", top).strip().casefold()
    return (
        top == "index"
        or top in {"names index", "subject index", "author index"}
        or top.startswith("index of ")
    )


def page_of(cid: str) -> int:
    m = re.search(r"-p(\d+)-", cid)
    return int(m.group(1)) if m else -1


def load_ingest_slugs(manifest_path: Path) -> set[str]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = data if isinstance(data, list) else data.get("books", [])
    return {row["slug"] for row in rows if row.get("action") == "ingest"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--backup", default="")
    ap.add_argument("--slugs-from", type=Path,
                    help="manifest JSON; only its ingest rows are processed")
    args = ap.parse_args()
    slugs = load_ingest_slugs(args.slugs_from) if args.slugs_from else None
    if slugs is not None:
        print(f"Scoped to {len(slugs)} ingest slugs from {args.slugs_from}\n")

    if args.backup and not args.dry_run:
        bdir = Path(args.backup)
        if not bdir.exists():
            shutil.copytree(CHUNKS, bdir)
            print(f"backed up {CHUNKS} -> {bdir}\n")
        else:
            print(f"(backup {bdir} already exists — reusing)\n")

    tot_c = tot_p = tot_books = 0
    for f in sorted(CHUNKS.glob("*.json")):
        if slugs is not None and f.stem not in slugs:
            continue
        data = json.loads(f.read_text())
        flagged = [c for c in data["children"] if is_index_child(c)]
        if not flagged:
            continue
        flagged_ids = {c["child_id"] for c in flagged}
        kept_children = [c for c in data["children"] if c["child_id"] not in flagged_ids]
        used_parents = {c["parent_id"] for c in kept_children}
        kept_parents = [p for p in data["parents"] if p["parent_id"] in used_parents]
        # safety: index chunks must be a contiguous tail (max kept page <= min flagged page, loosely)
        fp = [page_of(c["child_id"]) for c in flagged if page_of(c["child_id"]) >= 0]
        kp = [page_of(c["child_id"]) for c in kept_children if page_of(c["child_id"]) >= 0]
        tail_note = ""
        if fp and kp and min(fp) < max(kp) * 0.5:
            tail_note = "  !! WARN: flagged pages not in tail — REVIEW"
        dc, dp = len(flagged), len(data["parents"]) - len(kept_parents)
        tot_c += dc
        tot_p += dp
        tot_books += 1
        rng = f"{min(fp)}-{max(fp)}" if fp else "?"
        print(f"  {f.stem:52s}  -{dc:4d} ch  -{dp:3d} par  (index pp {rng}){tail_note}")
        if not args.dry_run:
            data["children"] = kept_children
            data["parents"] = kept_parents
            f.write_text(json.dumps(data))

    mode = "DRY-RUN" if args.dry_run else "STRIPPED"
    print(f"\n{mode}: {tot_c} index children + {tot_p} index parents across {tot_books} books")


if __name__ == "__main__":
    main()
