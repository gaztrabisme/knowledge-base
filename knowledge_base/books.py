"""Book metadata and name resolution shared by the MCP tools."""

import difflib
import re
from dataclasses import dataclass
from functools import lru_cache

from .config import BOOKS, MARKDOWN_DIR, ROOT, SOURCE_DIRS


@lru_cache(maxsize=1)
def load_catalog() -> dict[str, dict]:
    """Load the generated book catalog, omitting its metadata row."""
    path = ROOT / "data" / "catalog.json"
    if not path.exists():
        return {}
    import json

    raw = json.loads(path.read_text(encoding="utf-8"))
    return {slug: value for slug, value in raw.items() if slug != "_meta"}


def _normalise(value: str) -> str:
    return "".join(char.lower() for char in value if char.isalnum())


def _chapter_title(line: str) -> str | None:
    """Return the cleaned title for an H1 line, or None for non-H1 lines."""
    if not line.startswith("# "):
        return None
    title = line[2:].replace("\u00a0", " ").strip()
    link = re.fullmatch(r"\[([^\]]+)\]\([^)]*\)", title)
    if link:
        title = link.group(1)
    return title.replace("\u00a0", " ").strip()


def chapter_number(title: str) -> int | None:
    """Read a printed chapter label, without mistaking 12.1 for chapter 12."""
    match = re.match(r"^(?:chapter\s+)?(\d+)(?=\s|$|[.:](?:\s|$))", title, re.IGNORECASE)
    return int(match.group(1)) if match else None


@dataclass
class ChapterSection:
    title: str
    level: int
    start: int
    end: int


def chapter_sections(text: str) -> list[ChapterSection]:
    """Locate top-level headings and printed chapters, outside fences.

    Keep part containers addressable by title. Each section ends at its next
    sibling or ancestor heading, so reading a nested chapter cannot spill into
    the next chapter or part. Explicit "Chapter N" labels also survive book
    title headings or intermediate wrappers beneath a part.
    """
    lines = text.splitlines()
    headings: list[tuple[ChapterSection, bool]] = []
    parents: list[ChapterSection] = []
    fence = None
    for index, line in enumerate(lines):
        marker = re.match(r" {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence is not None:
            if (
                marker and marker[1][0] == fence[0]
                and len(marker[1]) >= len(fence) and not marker[2].strip()
            ):
                fence = None
            continue
        if marker:
            fence = marker[1]
            continue

        heading = re.match(r"^(#{1,6})[ \t]+(.+)$", line)
        if not heading:
            continue
        level = len(heading[1])
        title = _chapter_title("# " + re.sub(r"\s+#+\s*$", "", heading[2]))
        if not title:
            continue
        while parents and parents[-1].level >= level:
            parents.pop().end = index
        under_part = bool(parents and re.match(r"^part\s+", parents[-1].title, re.IGNORECASE))
        labelled_chapter = bool(re.match(r"^chapter\s+", title, re.IGNORECASE)) and chapter_number(title) is not None
        section = ChapterSection(title, level, index, len(lines))
        headings.append((section, under_part or labelled_chapter))
        parents.append(section)

    top_level = min((section.level for section, _ in headings), default=1)
    return [section for section, is_chapter in headings if section.level == top_level or is_chapter]


@lru_cache(maxsize=1)
def _source_domains() -> dict[str, str]:
    domains: dict[str, str] = {}
    for domain, root in SOURCE_DIRS.items():
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file():
                domains.setdefault(path.stem, domain)
            elif path.is_dir() and path.name == "owasp-cheat-sheets":
                domains.setdefault(path.name, domain)
    return domains


@lru_cache(maxsize=None)
def book_domain(slug: str) -> str:
    """Return the configured source directory key for a book, or "unknown"."""
    return _source_domains().get(slug, "unknown")


_catalog = load_catalog()
DOMAINS = sorted({
    (_catalog.get(slug, {}).get("domain") or book_domain(slug))
    for slug in BOOKS
    if (_catalog.get(slug, {}).get("domain") or book_domain(slug)) != "unknown"
})


@lru_cache(maxsize=None)
def book_chapters(slug: str) -> list[str]:
    """Read printed chapter titles, including chapters beneath part headings."""
    path = MARKDOWN_DIR / f"{slug}.md"
    if not path.exists():
        return []

    return [section.title for section in chapter_sections(path.read_text(encoding="utf-8"))]


def resolve_book(name: str) -> tuple[str | None, list[str]]:
    """Resolve a slug/title and return up to five nearby slugs on failure."""
    if name in BOOKS:
        return name, []

    lowered = name.casefold()
    for slug, title in BOOKS.items():
        if title.casefold() == lowered:
            return slug, []

    target = _normalise(name)
    normalized_names: list[tuple[str, str]] = []
    for slug, title in BOOKS.items():
        normalized_names.extend(((_normalise(slug), slug), (_normalise(title), slug)))
    for normalized, slug in normalized_names:
        if normalized == target:
            return slug, []

    close = difflib.get_close_matches(
        target, [normalized for normalized, _ in normalized_names], n=1, cutoff=0.75,
    )
    if close:
        return next(slug for normalized, slug in normalized_names if normalized == close[0]), []

    suggestions = sorted(
        BOOKS,
        key=lambda slug: difflib.SequenceMatcher(None, target, _normalise(slug)).ratio(),
        reverse=True,
    )[:5]
    return None, suggestions
