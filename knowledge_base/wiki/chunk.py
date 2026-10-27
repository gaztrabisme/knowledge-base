"""Heading-aware wiki chunks with a simple ~1,500-token character budget."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

MAX_CHARS = 6000  # Approximation: four characters/token, no tokenizer/model download.
_HEADING = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")


@dataclass(frozen=True)
class Heading:
    start: int
    level: int
    title: str
    path: str


def headings(text: str) -> list[Heading]:
    """Locate ATX headings outside fenced code, retaining their full hierarchy."""
    result = []
    stack: list[tuple[int, str]] = []
    fence = ""
    offset = 0
    for line in text.splitlines(keepends=True):
        marker = _FENCE.match(line)
        if marker:
            run = marker.group(1)
            if not fence:
                fence = run
            elif run[0] == fence[0] and len(run) >= len(fence) and not line[marker.end():].strip():
                fence = ""
        elif not fence and (match := _HEADING.match(line.rstrip("\r\n"))):
            level, title = len(match.group(1)), match.group(2).strip()
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))
            result.append(Heading(offset, level, title, " > ".join(t for _, t in stack)))
        offset += len(line)
    return result


def _split_paragraphs(text: str, max_chars: int):
    pending = ""
    for paragraph in re.split(r"\n[ \t]*\n", text.strip()):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if pending and len(pending) + 2 + len(paragraph) > max_chars:
            yield pending
            pending = ""
        # Oversized single paragraphs (including long tables/code) still obey the cap.
        while len(paragraph) > max_chars:
            yield paragraph[:max_chars]
            paragraph = paragraph[max_chars:]
        pending = "\n\n".join(part for part in (pending, paragraph) if part)
    if pending:
        yield pending


def chunk_page(path: Path, text: str | None = None, max_chars: int = MAX_CHARS) -> list[dict]:
    """Split at H1/H2 boundaries; log entries never merge across their H2 headings."""
    if max_chars < 1:
        raise ValueError("max_chars must be positive")
    path = Path(path)
    if text is None:
        text = path.read_text(encoding="utf-8")
    boundaries = [h for h in headings(text) if h.level <= 2]
    spans = [(0, "")] if not boundaries or boundaries[0].start else []
    spans.extend((h.start, h.path) for h in boundaries)
    chunks = []
    for i, (start, heading) in enumerate(spans):
        end = spans[i + 1][0] if i + 1 < len(spans) else len(text)
        section = text[start:end].strip()
        # A bare page title is context for the following sections, not a log entry.
        if not section or all(_HEADING.match(line) for line in section.splitlines() if line.strip()):
            continue
        date = _DATE.search(heading) or _DATE.search(path.name)
        for part in _split_paragraphs(section, max_chars):
            chunks.append({"heading": heading, "date": date.group(0) if date else None, "text": part})
    return chunks
