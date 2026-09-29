#!/usr/bin/env python3
"""Audit v8 markdown and parent/child chunks without loading retrieval models."""

import argparse
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from knowledge_base import ingest
from knowledge_base.chunk import estimate_tokens
from knowledge_base.config import BOOKS, CHUNKS_DIR, MARKDOWN_DIR, SOURCE_DIRS
from strip_index_backmatter import is_index_child

DEFAULT_EXCEPTIONS = ROOT / "data" / "intake" / "audit-exceptions.json"
PAGE_FLOOR_PERCENTILE = 0.05
FRONT_TEXT = re.compile(
    r"(?im)^\s*(?:#{1,6}\s*)?(?:copyright\b|all rights reserved\b|"
    r"dedication\b|table of contents\b|brief contents\b|praise for\b|"
    r"about the author\b|©\s*\d{4})"
)


def source_for(slug: str, row: dict | None = None) -> Path | None:
    if row:
        suffix = Path(row.get("file", "")).suffix.lower()
        candidate = SOURCE_DIRS.get(row.get("domain"), ROOT) / f"{slug}{suffix}"
        return candidate if candidate.exists() else None
    matches = sorted(Path(SOURCE_DIRS["applied-ml"]).parent.glob(f"*/{slug}.*"))
    return matches[0] if matches else None


def pdf_pages(source: Path | None) -> int | None:
    if not source or source.suffix.lower() != ".pdf":
        return None
    import fitz

    with fitz.open(source) as doc:
        return doc.page_count


def calibrate_page_floor(excluded: set[str]) -> tuple[int | None, list[tuple[str, float]]]:
    observations = []
    for slug in BOOKS:
        if slug in excluded:
            continue
        source = source_for(slug)
        md = MARKDOWN_DIR / f"{slug}.md"
        pages = pdf_pages(source)
        if pages and md.exists():
            observations.append((slug, len(md.read_text(encoding="utf-8")) / pages))
    if not observations:
        return None, []
    ordered = sorted(value for _, value in observations)
    rank = max(1, math.ceil(PAGE_FLOOR_PERCENTILE * len(ordered)))
    return math.floor(ordered[rank - 1]), observations


def heading_rows(text: str) -> list[tuple[int, int, str]]:
    found = []
    in_code = False
    for line_no, line in enumerate(text.splitlines()):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            found.append((line_no, len(match.group(1)), line))
    return found


def audit_book(row: dict, page_floor: int | None) -> dict:
    slug = row["slug"]
    md_path = MARKDOWN_DIR / f"{slug}.md"
    chunk_path = CHUNKS_DIR / f"{slug}.json"
    source = source_for(slug, row)
    text = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
    headings = heading_rows(text)
    h2_plus = sum(level >= 2 for _, level, _ in headings)
    h1 = [item for item in headings if item[1] == 1]
    chapter_headings = [
        item for item in headings
        if ingest._is_chapter_heading(item[2])
    ]
    plain_chapters = [
        (line_no, 0, line.strip())
        for line_no, line in enumerate(text.splitlines())
        if re.match(r"(?i)^(?:chapter|part)\s+(?:\d+|[a-z]+|[ivxlcdm]+)(?=$|\s|[.:—–-])", line.strip())
    ]
    chapter_markers = sorted(chapter_headings + plain_chapters)
    has_structure = (
        len(chapter_markers) >= 2 or len(h1) >= 2
        or (len(h1) == 1 and h2_plus >= 5)
    )
    first_major = next((item for item in headings if item[1] == 1 and not ingest._is_front_matter_heading(item[2])), None)
    first_chapter = chapter_markers[0] if chapter_markers else first_major
    prefix = "\n".join(text.splitlines()[:first_chapter[0]]) if first_chapter else text
    front_left = any(
        ingest._is_front_matter_heading(line)
        for line in prefix.splitlines()
        if re.match(r"^#{1,6}\s+", line)
    )
    front_left = front_left or any(FRONT_TEXT.search(line) for line in prefix.splitlines())

    pages = pdf_pages(source)
    char_page = len(text) / pages if pages else None
    flags = []
    if not md_path.exists():
        flags.append("missing markdown")
    if h2_plus < 5:
        flags.append(f"only {h2_plus} headings at level >=2")
    if not has_structure:
        flags.append("no chapter-level structure")
    garble = ingest._garble_ratio(text)
    if garble > ingest._GARBLE_RATIO_THRESHOLD:
        flags.append(f"garble ratio {garble:.3%} exceeds {ingest._GARBLE_RATIO_THRESHOLD:.3%}")
    if pages and page_floor is not None and char_page < page_floor:
        flags.append(f"markdown density {char_page:.1f} chars/page below {page_floor}")
    if front_left:
        flags.append("front matter before first chapter")

    parents = children = 0
    over_child = over_parent = 0
    index_children = 0
    if chunk_path.exists():
        try:
            data = json.loads(chunk_path.read_text(encoding="utf-8"))
            parents, children = len(data.get("parents", [])), len(data.get("children", []))
            over_child = sum(estimate_tokens(c.get("text", "")) > 250 for c in data.get("children", []))
            over_parent = sum(estimate_tokens(p.get("text", "")) > 1900 for p in data.get("parents", []))
            index_children = sum(is_index_child(c) for c in data.get("children", []))
        except (OSError, ValueError, KeyError) as error:
            flags.append(f"invalid chunk file: {error}")
    else:
        flags.append("missing chunks")
    if chunk_path.exists() and children == 0:
        flags.append("zero child chunks")
    if over_child:
        flags.append(f"{over_child} children exceed 250 tokens")
    if over_parent:
        flags.append(f"{over_parent} parents exceed 1900 tokens")
    if index_children:
        flags.append(f"{index_children} back-of-book index children at end")

    return {
        "slug": slug, "domain": row.get("domain", ""), "source": source,
        "pages": pages, "chars": len(text), "headings": len(headings),
        "h2_plus": h2_plus, "chapter_structure": has_structure,
        "parents": parents, "children": children, "char_page": char_page,
        "garble": garble, "index_children": index_children, "flags": flags,
    }


def load_rows(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data if isinstance(data, list) else data.get("books", [])
    return [row for row in rows if row.get("action") == "ingest"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slugs-from", type=Path, help="manifest JSON; only its ingest rows are audited")
    ap.add_argument("--strict", action="store_true", help="fail for any flagged book without an exception")
    args = ap.parse_args()
    rows = load_rows(args.slugs_from) if args.slugs_from else [
        {"slug": slug, "domain": ""} for slug in sorted(BOOKS)
    ]
    slugs = {row["slug"] for row in rows}
    floor, calibration = calibrate_page_floor(slugs)
    print(f"PDF page-density calibration: n={len(calibration)} existing books / 126 registered; "
          f"nearest-rank p05 floor={floor} markdown chars per physical PDF page")
    print("EPUBs have no stable page count; density is reported as n/a for reflowable sources.")
    results = [audit_book(row, floor) for row in rows]
    exceptions = {}
    if DEFAULT_EXCEPTIONS.exists():
        exceptions = json.loads(DEFAULT_EXCEPTIONS.read_text(encoding="utf-8"))
    failed = 0
    for result in results:
        density = f"{result['char_page']:.1f}" if result["char_page"] is not None else "n/a"
        marker = "; ".join(result["flags"]) if result["flags"] else "PASS"
        print(f"{result['slug']}: {result['chars']} chars; pages={result['pages'] or 'n/a'}; "
              f"headings={result['headings']} (H2+ {result['h2_plus']}); "
              f"parents={result['parents']}; children={result['children']}; "
              f"chars/page={density}; {marker}")
        if result["flags"] and result["slug"] not in exceptions:
            failed += 1
    print(f"\nAudited {len(results)} books; flagged {sum(bool(r['flags']) for r in results)}; "
          f"unexcepted flags={failed}.")
    return 1 if args.strict and failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
