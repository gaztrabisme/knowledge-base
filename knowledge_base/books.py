"""Book metadata and name resolution shared by the MCP tools."""

import difflib
import re
from functools import lru_cache

from .config import BOOKS, MARKDOWN_DIR, SOURCE_DIRS


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


@lru_cache(maxsize=None)
def book_chapters(slug: str) -> list[str]:
    """Read cleaned H1 chapter titles, excluding fenced code blocks."""
    path = MARKDOWN_DIR / f"{slug}.md"
    if not path.exists():
        return []

    chapters = []
    in_fence = False
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        title = _chapter_title(line)
        if title:
            chapters.append(title)
    return chapters


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
