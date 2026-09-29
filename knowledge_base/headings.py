#!/usr/bin/env python3
"""Feature-based quality checks for headings in Markdown books."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any
from dataclasses import dataclass
import posixpath
import unicodedata
from urllib.parse import unquote, urlsplit


DEFAULT_EXCEPTIONS = Path("data/intake/heading-exceptions.json")
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
WORD_RE = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?")
LINK_RE = re.compile(r"!?\[([^\]]+)\]\([^)]*\)")
MARKDOWN_LINK_TARGET_RE = re.compile(r"!?\[([^\]]+)\]\(([^)]*)\)")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
INLINE_CODE_RE = re.compile(r"`+[^`]*`+")
NUMBERED_RE = re.compile(r"^\s*(?:\[\d+\]|\d+[.)])\s*[a-z]")
NUMBERED_CONTEXT_RE = re.compile(r"^\s*(?:\d+[.)](?!\d)\s*|\d+\s+)")
CODE_MARKER_RE = re.compile(r"(?:`|::|->|&&|\|\||[=<>;{}])")
CODE_IDENTIFIER_RE = re.compile(
    r"(?<![\w])(?:[A-Za-z_$][A-Za-z0-9_$]*_[A-Za-z0-9_$]*|"
    r"[A-Za-z_$]+[A-Z][A-Za-z0-9_$]*|[A-Za-z_$]+\d[A-Za-z0-9_$]*)(?![\w])"
)
CODE_CHAIN_RE = re.compile(
    r"\b[A-Za-z_$][A-Za-z0-9_$]*(?:(?:::|\.|->)[A-Za-z_$][A-Za-z0-9_$]*)+"
    r"(?:\s*<[^<>]*>)?(?:\s*\([^)]*\))?"
)
SENTENCE_END_RE = re.compile(r"[.!?][\"’')\]]?\s*$")
TERMINAL_PUNCT_RE = re.compile(r"[.!?:][\"’')\]]?\s*$")
TABLE_RULE_RE = re.compile(r"^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*$")
NONWORD_RE = re.compile(r"^[^\w]+$", re.UNICODE)


def _plausible_token(token: str) -> bool:
    """A rough language-shape check; dictionaries and title vocabularies are not used."""
    token = token.lower()
    if len(token) < 3 or re.search(r"(.)\1\1", token):
        return False
    vowels = set("aeiouy")
    vowel_fraction = sum(char in vowels for char in token) / len(token)
    if not 0.16 <= vowel_fraction <= 0.78:
        return False
    if "q" in token and not re.search(r"q[u]", token):
        return False
    consonant_run = vowel_run = max_consonant_run = max_vowel_run = 0
    for char in token:
        if char in vowels:
            vowel_run += 1
            consonant_run = 0
        else:
            consonant_run += 1
            vowel_run = 0
        max_consonant_run = max(max_consonant_run, consonant_run)
        max_vowel_run = max(max_vowel_run, vowel_run)
    return max_consonant_run <= 4 and max_vowel_run <= 3


def _heading_prose(heading: str) -> str:
    """Remove code syntax/spans so code vocabulary is not mistaken for OCR noise."""
    cleaned = INLINE_CODE_RE.sub(" ", heading)
    cleaned = LINK_RE.sub(r"\1", cleaned)
    cleaned = CODE_CHAIN_RE.sub(" ", cleaned)
    cleaned = CODE_IDENTIFIER_RE.sub(" ", cleaned)
    cleaned = re.sub(r"(?<!\w)[A-Za-z_$][A-Za-z0-9_$]*(?:\([^)]*\))", " ", cleaned)
    # Operators and punctuation are legitimate in code headings. Discard their
    # punctuation contribution while retaining surrounding ordinary words.
    if CODE_MARKER_RE.search(cleaned):
        cleaned = CODE_MARKER_RE.sub(" ", cleaned)
    cleaned = re.sub(r"[*_~]", "", cleaned)
    return CONTROL_RE.sub("", cleaned)


def _garbled_heading(heading: str) -> bool:
    cleaned = _heading_prose(heading)
    tokens = WORD_RE.findall(cleaned)
    if not tokens:
        return False
    # One- and two-letter tokens commonly name languages, types, and variables.
    long_tokens = [token for token in tokens if len(token) >= 3]
    if not long_tokens:
        return False
    implausible_share = sum(not _plausible_token(token) for token in long_tokens) / len(long_tokens)
    short_share = sum(len(token) <= 2 for token in tokens) / len(tokens)
    compact_garble = len(tokens) >= 4 and short_share >= 0.45 and implausible_share >= 0.4
    random_wording = len(long_tokens) >= 3 and implausible_share >= 0.65
    return compact_garble or random_wording


def _footnote_like_heading(heading: str, previous_body_line: str, next_body_line: str) -> bool:
    """Find numbered lowercase prose or a heading that visibly splits a sentence."""
    plain = LINK_RE.sub(r"\1", heading).strip()
    tokens = WORD_RE.findall(plain)
    if not tokens:
        return False
    starts_numbered_lowercase_prose = bool(NUMBERED_RE.match(plain)) and len(tokens) >= 4
    if (
        starts_numbered_lowercase_prose
        and not _looks_like_code_line(previous_body_line)
        and not _looks_like_code_line(next_body_line)
    ):
        return True

    previous = previous_body_line.strip()
    following = next_body_line.strip()
    first_heading_alpha = next((char for char in plain if char.isalpha()), "")
    first_next_alpha = next((char for char in following if char.isalpha()), "")
    starts_lowercase = bool(first_heading_alpha and first_heading_alpha.islower())
    starts_numbered = bool(NUMBERED_CONTEXT_RE.match(plain))
    previous_words = WORD_RE.findall(previous)
    previous_ends_mid_wording = bool(previous and previous[-1:].isalpha() and previous[-1:].islower())
    return bool(
        previous
        and following
        and first_next_alpha
        and first_next_alpha.islower()
        and not TERMINAL_PUNCT_RE.search(plain)
        and not _looks_like_code_line(previous)
        and not _looks_like_code_line(following)
        and (
            (
                starts_lowercase
                and len(previous_words) >= 4
                and previous_ends_mid_wording
                and not SENTENCE_END_RE.search(previous)
            )
            or (
                starts_numbered
                and len(previous_words) >= 2
                and not SENTENCE_END_RE.search(previous)
            )
        )
    )


def _looks_like_code_line(line: str) -> bool:
    """Recognize common code-shaped context without matching prose vocabulary."""
    if CODE_MARKER_RE.search(line) and len(WORD_RE.findall(line)) >= 2:
        return True
    if re.match(r"^\s*(?:from\s+\S+\s+import\s+\S+|import\s+\S+)", line):
        return True
    if re.match(r"^\s*(?:async\s+)?def\s+[A-Za-z_$][\w$]*\s*\(", line):
        return True
    if re.match(r"^\s*(?:for|if|while|class|return)\b.*[({=:\[]", line):
        return True
    if re.match(r"^\s*@\w+(?:\.\w+)*(?:\s*\(|\s*$)", line):
        return True
    if re.match(r"^\s*[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*\s*(?:=|\(|\{)", line):
        return True
    if re.match(r"^\s*(?:\$\s+\S+|[A-Za-z_][A-Za-z0-9_]*:\s*)$", line):
        return True
    hex_byte_tokens = re.findall(r"(?<![A-Za-z0-9])(?:0x[0-9a-fA-F]+|[0-9a-fA-F]{2})(?![A-Za-z0-9])", line)
    return len(hex_byte_tokens) >= 3


def _clean_body_line(content: str) -> str:
    cleaned = CONTROL_RE.sub("", INLINE_CODE_RE.sub(" ", content))
    cleaned = LINK_RE.sub(r"\1", cleaned)
    cleaned = re.sub(r"^\s{0,3}(?:[-+*]|\d+[.)])\s+", "", cleaned)
    cleaned = re.sub(r"^\s{0,3}>\s?", "", cleaned)
    return cleaned.strip()


def _measure_body_line(content: str, totals: Counter[str]) -> None:
    cleaned = _clean_body_line(content)
    if not cleaned or TABLE_RULE_RE.fullmatch(cleaned):
        return
    if content.startswith(("    ", "\t")):
        return
    # Unfenced source-code lines have dense operators or braces. They do not
    # contribute to OCR measures; fenced and indented blocks are handled by
    # the caller as well.
    if CODE_MARKER_RE.search(cleaned) and len(WORD_RE.findall(cleaned)) >= 2:
        return

    totals["body_nonblank_line_count"] += 1
    words = WORD_RE.findall(cleaned)
    letter_count = sum(len(word) for word in words)
    if len(words) <= 2 and letter_count <= 8:
        totals["body_fragment_line_count"] += 1
        if any(len(word) >= 3 and not _plausible_token(word) for word in words):
            totals["body_garbled_fragment_line_count"] += 1
    if len(words) == 1 and len(words[0]) <= 2:
        totals["body_short_letter_line_count"] += 1

    units = cleaned.split()
    if units:
        totals["body_token_count"] += len(units)
        totals["body_nonword_token_count"] += sum(bool(NONWORD_RE.fullmatch(unit.strip("*_~`"))) for unit in units)
    totals["body_word_count"] += len(words)
    totals["body_implausible_word_count"] += sum(
        len(word) >= 4 and word.islower() and not _plausible_token(word) for word in words
    )
    if re.fullmatch(r"[^A-Za-z0-9\s]{1,12}", cleaned):
        totals["body_punctuation_line_count"] += 1


def evaluate(text: str) -> dict[str, Any]:
    """Measure heading quality in ``text`` without reading files or global state."""
    headings: list[str] = []
    heading_contexts: list[str] = []
    heading_next_contexts: list[str] = []
    body_chars = 0
    current_heading_free_span = 0
    largest_heading_free_span = 0
    fence_char = ""
    fence_width = 0
    prior_nonblank_body_line = ""
    pending_heading_index: int | None = None
    body_totals: Counter[str] = Counter()

    # This is the only pass over body lines. Heading and adjacency state is
    # collected at the same time so corpus files are not rescanned.
    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        fence = FENCE_RE.match(content)
        if fence_char:
            if fence and fence.group(1)[0] == fence_char and len(fence.group(1)) >= fence_width:
                fence_char = ""
                fence_width = 0
            body_chars += len(line)
            current_heading_free_span += len(line)
            continue
        if fence:
            fence_char = fence.group(1)[0]
            fence_width = len(fence.group(1))
            body_chars += len(line)
            current_heading_free_span += len(line)
            continue

        match = HEADING_RE.match(content)
        if match:
            headings.append(match.group(2).strip())
            heading_contexts.append(prior_nonblank_body_line)
            heading_next_contexts.append("")
            pending_heading_index = len(headings) - 1
            largest_heading_free_span = max(largest_heading_free_span, current_heading_free_span)
            current_heading_free_span = 0
            prior_nonblank_body_line = ""
        else:
            body_chars += len(line)
            current_heading_free_span += len(line)
            if content.strip():
                if not content.startswith(("    ", "\t")):
                    _measure_body_line(content, body_totals)
                if pending_heading_index is not None and not content.startswith(("    ", "\t")):
                    heading_next_contexts[pending_heading_index] = content.strip()
                    pending_heading_index = None
                if not content.startswith(("    ", "\t")):
                    prior_nonblank_body_line = content.strip()

    count = len(headings)
    density = count / max(body_chars / 100_000, 0.01)
    largest_gap_chars = max(largest_heading_free_span, current_heading_free_span)
    frequencies = Counter(re.sub(r"[^a-z0-9]+", " ", heading.lower()).strip() for heading in headings)
    heading_keys = [re.sub(r"[^a-z0-9]+", " ", heading.lower()).strip() for heading in headings]
    duplicate_heading_share = sum(n for n in frequencies.values() if n > 1) / count if count else 0.0
    most_repeated_heading_count = max(frequencies.values(), default=0)
    top_heading_key = max(frequencies, key=frequencies.get, default="")
    top_heading = next((heading for heading in headings if re.sub(r"[^a-z0-9]+", " ", heading.lower()).strip() == top_heading_key), "")
    top_alpha = [char for char in top_heading if char.isalpha()]
    top_uppercase_share = sum(char.isupper() for char in top_alpha) / len(top_alpha) if top_alpha else 0.0
    link_count = sum(bool(LINK_RE.search(heading)) for heading in headings)
    footnote_count = sum(
        _footnote_like_heading(heading, previous, following)
        for heading, previous, following in zip(headings, heading_contexts, heading_next_contexts)
    )
    garbled_count = sum(_garbled_heading(heading) for heading in headings)
    periodic_repeat_share = max(
        (
            sum(heading_keys[index] == heading_keys[index - lag] for index in range(lag, count)) / count
            for lag in range(1, min(5, count))
        ),
        default=0.0,
    )

    body_line_count = body_totals["body_nonblank_line_count"]
    body_fragment_share = body_totals["body_fragment_line_count"] / max(body_line_count, 1)
    body_garbled_fragment_share = body_totals["body_garbled_fragment_line_count"] / max(body_line_count, 1)
    body_short_letter_share = body_totals["body_short_letter_line_count"] / max(body_line_count, 1)
    body_punctuation_share = body_totals["body_punctuation_line_count"] / max(body_line_count, 1)
    body_nonword_share = body_totals["body_nonword_token_count"] / max(body_totals["body_token_count"], 1)
    body_implausible_share = body_totals["body_implausible_word_count"] / max(body_totals["body_word_count"], 1)
    body_ocr_signal = (
        0.20 * body_garbled_fragment_share
        + 0.15 * body_short_letter_share
        + 0.15 * body_nonword_share
        + 0.15 * body_punctuation_share
        + 0.35 * body_implausible_share
    )
    features = {
        "heading_count": count,
        "body_chars": body_chars,
        "body_nonblank_line_count": body_line_count,
        "headings_per_100k_body_chars": round(density, 4),
        "largest_heading_free_span_chars": largest_gap_chars,
        "largest_heading_free_span_share": round(largest_gap_chars / max(body_chars, 1), 4),
        "duplicate_heading_share": round(duplicate_heading_share, 4),
        "most_repeated_heading_count": most_repeated_heading_count,
        "most_repeated_heading_share": round(most_repeated_heading_count / count if count else 0.0, 4),
        "most_repeated_heading_uppercase_share": round(top_uppercase_share, 4),
        "periodic_repeat_share": round(periodic_repeat_share, 4),
        "link_heading_share": round(link_count / count if count else 0.0, 4),
        "footnote_like_heading_count": footnote_count,
        "sentence_like_heading_share": round(footnote_count / count if count else 0.0, 4),
        "garbled_heading_count": garbled_count,
        "garbled_heading_share": round(garbled_count / count if count else 0.0, 4),
        "body_fragment_line_share": round(body_fragment_share, 4),
        "body_garbled_fragment_line_share": round(body_garbled_fragment_share, 4),
        "body_short_letter_line_share": round(body_short_letter_share, 4),
        "body_nonword_token_share": round(body_nonword_share, 4),
        "body_punctuation_line_share": round(body_punctuation_share, 4),
        "body_implausible_word_share": round(body_implausible_share, 4),
        "body_ocr_signal": round(body_ocr_signal, 4),
    }

    reasons: list[str] = []
    gap_share = largest_gap_chars / max(body_chars, 1)
    repeat_share = most_repeated_heading_count / count if count else 0.0
    link_share = link_count / count if count else 0.0
    footnote_share = footnote_count / count if count else 0.0
    garbled_share = garbled_count / count if count else 0.0

    if count == 0 or (density < 0.75 and gap_share > 0.25):
        reasons.append(
            "sparse headings: "
            f"{count} headings, {density:.2f} per 100k body chars, largest gap {gap_share:.1%}"
        )
    if most_repeated_heading_count >= 70 and repeat_share >= 0.08 and top_uppercase_share >= 0.75:
        reasons.append(
            "one heading repeats like a running header: "
            f"{most_repeated_heading_count}/{count} headings ({repeat_share:.1%}), uppercase {top_uppercase_share:.1%}"
        )
    if link_count >= 5 and link_share >= 0.60:
        reasons.append(f"heading link markup: {link_count}/{count} headings ({link_share:.1%})")
    if footnote_count >= 3 and footnote_share >= 0.044:
        reasons.append(
            "footnote-like numbered prose headings: "
            f"{footnote_count}/{count} ({footnote_share:.1%})"
        )
    if garbled_count >= 3 and garbled_share >= 0.05:
        reasons.append(f"garbled headings: {garbled_count}/{count} ({garbled_share:.1%})")
    if (
        body_line_count >= 30
        and body_ocr_signal >= 0.025
        and body_implausible_share >= 0.02
        and (body_nonword_share >= 0.025 or body_punctuation_share >= 0.01 or body_short_letter_share >= 0.015)
    ):
        reasons.append(
            "OCR-like body noise: "
            f"signal {body_ocr_signal:.1%}, garbled fragments {body_garbled_fragment_share:.1%}, "
            f"implausible words {body_implausible_share:.1%}, non-word tokens {body_nonword_share:.1%}, "
            f"punctuation lines {body_punctuation_share:.1%}"
        )
    return {"flagged": bool(reasons), "reasons": reasons, "features": features}



@dataclass(frozen=True)
class NavigationEntry:
    title: str
    target: str
    depth: int


@dataclass(frozen=True)
class PdfLine:
    page: int
    text: str
    y_ratio: float | None = None
    font_size: float | None = None
    bold: bool = False
    starts_block: bool = False


def normalize_heading_text(value: str) -> str:
    """Normalize prose for structural matching without title-specific rules."""
    value = LINK_RE.sub(r"\1", value)
    value = re.sub(r"^\s{0,3}#{1,6}\s+", "", value)
    value = unicodedata.normalize("NFKC", value).casefold()
    value = re.sub(r"[^\w]+", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


def _resolve_epub_target(base_path: str, href: str) -> str:
    href = unquote(href.strip())
    split = urlsplit(href)
    path = posixpath.normpath(posixpath.join(posixpath.dirname(base_path), split.path))
    if path == ".":
        path = ""
    return path + (f"#{split.fragment}" if split.fragment else "")


def _navigation_from_nav(nav_xhtml: str | None, nav_path: str) -> list[NavigationEntry]:
    if not nav_xhtml:
        return []
    import xml.etree.ElementTree as ET

    try:
        root = ET.fromstring(nav_xhtml)
    except ET.ParseError:
        return []

    def local(tag: str) -> str:
        return tag.rsplit("}", 1)[-1].lower()

    nav_nodes = [node for node in root.iter() if local(node.tag) == "nav"]
    toc_nodes = [
        node for node in nav_nodes
        if "toc" in " ".join(str(value) for key, value in node.attrib.items() if key.endswith("type")).casefold()
    ]
    selected = toc_nodes or nav_nodes
    entries: list[NavigationEntry] = []

    def link_data(li) -> tuple[str, str] | None:
        for child in li:
            if local(child.tag) == "a":
                title = " ".join("".join(child.itertext()).split())
                href = next((value for key, value in child.attrib.items() if local(key) == "href"), "")
                if title and href:
                    return title, _resolve_epub_target(nav_path, href)
        return None

    def walk_list(list_node, depth: int) -> None:
        for li in list_node:
            if local(li.tag) != "li":
                continue
            data = link_data(li)
            if data:
                entries.append(NavigationEntry(data[0], data[1], depth))
            for child in li:
                if local(child.tag) in {"ol", "ul"}:
                    walk_list(child, depth + 1)

    for nav in selected:
        for child in nav:
            if local(child.tag) in {"ol", "ul"}:
                walk_list(child, 0)
                if entries:
                    break
        if entries:
            break
    return entries


def _navigation_from_ncx(ncx: str | None, ncx_path: str) -> list[NavigationEntry]:
    if not ncx:
        return []
    import xml.etree.ElementTree as ET

    try:
        root = ET.fromstring(ncx)
    except ET.ParseError:
        return []

    def local(tag: str) -> str:
        return tag.rsplit("}", 1)[-1].lower()

    entries: list[NavigationEntry] = []

    def visit(parent, depth: int = 0) -> None:
        for node in parent:
            if local(node.tag) != "navpoint":
                visit(node, depth)
                continue
            label = next((child for child in node if local(child.tag) == "navlabel"), None)
            title = " ".join(
                " ".join((child.text or "") for child in label.iter() if local(child.tag) == "text").split()
            ) if label is not None else ""
            content = next((child for child in node if local(child.tag) == "content"), None)
            target = next((value for key, value in content.attrib.items() if local(key) == "src"), "") if content is not None else ""
            if title and target:
                entries.append(NavigationEntry(title, _resolve_epub_target(ncx_path, target), depth))
            visit(node, depth + 1)

    visit(root)
    return entries


def parse_epub_navigation_documents(
    nav_xhtml: str | None,
    ncx: str | None,
    nav_path: str = "",
    ncx_path: str = "",
) -> list[NavigationEntry]:
    """Parse EPUB 3 and EPUB 2 navigation; prefer the document with more entries."""
    nav_entries = _navigation_from_nav(nav_xhtml, nav_path)
    ncx_entries = _navigation_from_ncx(ncx, ncx_path)
    return nav_entries if len(nav_entries) >= len(ncx_entries) else ncx_entries


def parse_contents_pages(pages: list[str]) -> list[tuple[str, int]]:
    """Read consistently formatted contents entries with printed page numbers."""
    parsed: list[tuple[str, int]] = []
    inline = re.compile(r"^(.*?)(?:\.{2,}|\s{2,}|\t+)\s*(\d{1,4})\s*$")
    for page in pages:
        lines = [line.strip() for line in page.splitlines()]
        index = 0
        page_entries: list[tuple[str, int]] = []
        while index < len(lines):
            line = re.sub(r"\s+", " ", lines[index]).strip()
            if not line:
                index += 1
                continue
            match_line = re.sub(
                r"(?:\.\s*){2,}",
                lambda leader: re.sub(r"\s+", "", leader.group(0)),
                lines[index].rstrip(),
            )
            match = inline.match(match_line)
            if match:
                title, number = match.groups()
                title = re.sub(r"[.\s]+$", "", title).strip()
                if title and normalize_heading_text(title) not in {"contents", "table of contents"}:
                    page_entries.append((title, int(number)))
                index += 1
                continue
            if index + 1 < len(lines) and re.fullmatch(r"\s*\d{1,4}\s*", lines[index + 1]):
                if line and normalize_heading_text(line) not in {"contents", "table of contents"}:
                    page_entries.append((line, int(lines[index + 1].strip())))
                index += 2
                continue
            index += 1
        parsed.extend(page_entries)
    # Contents pages have repeated entry formatting. Requiring multiple rows
    # across the scanned pages prevents prose ending in a number from becoming
    # a heading while allowing a contents list to span several pages.
    return parsed if len(parsed) >= 2 else []


def _pure_link_heading(line: str) -> bool:
    match = HEADING_RE.match(line)
    if not match:
        return False
    content = match.group(2).strip()
    return bool(re.fullmatch(r"\[([^\]]+)\]\([^)]*\)", content))


def _entry_title_variants(title: str) -> list[str]:
    values = [normalize_heading_text(title)]
    structural = re.match(r"(?i)^(?:chapter|part)\s+(?:\d+|[a-z]+|[ivxlcdm]+)\s*[:.\-–—]?\s+(.+)$", title.strip())
    if structural:
        values.append(normalize_heading_text(structural.group(1)))
    numbered = re.match(r"^(\d{1,3})(?:[.:]\s*|\s+)(.+)$", title.strip())
    if numbered:
        values.extend((
            normalize_heading_text(f"Chapter {numbered.group(1)} {numbered.group(2)}"),
            normalize_heading_text(numbered.group(2)),
        ))
    return [value for value in dict.fromkeys(values) if value]


def _line_target(line: str) -> list[str]:
    return [unquote(href) for _, href in MARKDOWN_LINK_TARGET_RE.findall(line)]


def _target_matches(target: str, href: str) -> bool:
    wanted = urlsplit(target)
    actual = urlsplit(href)
    if wanted.path and actual.path:
        wanted_path = posixpath.normpath(wanted.path)
        actual_path = posixpath.normpath(actual.path)
        same_path = (
            wanted_path == actual_path
            or posixpath.basename(wanted_path) == posixpath.basename(actual_path)
        )
        if not same_path:
            return False
    elif wanted.path or actual.path:
        return False
    else:
        same_path = True

    if wanted.fragment:
        return wanted.fragment == actual.fragment
    # A navigation item without a fragment names the start of the chapter file.
    return bool(wanted.path and same_path)


def _heading_depth_levels(entries: list[NavigationEntry]) -> dict[int, int]:
    roots = [entry for entry in entries if entry.depth == 0]
    has_parts = any(re.match(r"(?i)^part(?:\s+|[.:—–-])", entry.title.strip()) for entry in roots)
    offset = 1 if has_parts else 2
    return {index: min(6, entry.depth + offset) for index, entry in enumerate(entries)}


def _epub_entry_match(
    lines: list[str], entry: NavigationEntry, start: int, end: int
) -> int | None:
    """Find a navigation entry without treating prose links as its destination."""
    variants = _entry_title_variants(entry.title)
    for index in range(start, min(end, len(lines))):
        line = lines[index]
        # Inline links and standalone prose links are often forward
        # cross-references. Only accept a target carried by an actual heading.
        if HEADING_RE.match(line) and entry.target:
            if any(_target_matches(entry.target, href) for href in _line_target(line)):
                return index
        if MARKDOWN_LINK_TARGET_RE.search(line) and not HEADING_RE.match(line):
            continue
        candidate = normalize_heading_text(line)
        if any(candidate == variant or candidate.startswith(variant + " ") for variant in variants):
            return index
    return None


def recover_epub_headings(
    text: str, entries: list[NavigationEntry], book_title: str | None = None
) -> str:
    """Place EPUB navigation entries using link targets, then title matches."""
    if not entries:
        return text
    lines = text.splitlines()
    levels = _heading_depth_levels(entries)
    cursor = 0
    for entry_index, entry in enumerate(entries):
        # A missing repeated title must not consume the same title in a later
        # chapter. Bound this entry at the next navigation entry at the same or
        # shallower depth that can be located after the current cursor.
        end = len(lines)
        for later in entries[entry_index + 1 :]:
            if later.depth > entry.depth:
                continue
            later_match = _epub_entry_match(lines, later, cursor, len(lines))
            if later_match is not None:
                end = later_match
                break
        match_at = _epub_entry_match(lines, entry, cursor, end)
        if match_at is None:
            continue
        title = re.sub(r"\s+", " ", entry.title).strip()
        recovered_heading = "#" * levels[entry_index] + " " + title
        if HEADING_RE.match(lines[match_at]):
            lines[match_at] = recovered_heading
            cursor = match_at + 1
        else:
            # Link targets and title prefixes can occur inside prose. Add the
            # structural marker before that body line and keep its text intact.
            lines.insert(match_at, recovered_heading)
            cursor = match_at + 2

    # Remove destinations from heading text. Headings that are only navigation
    # links and did not match a structural entry are demoted to ordinary text.
    for i, line in enumerate(lines):
        if not HEADING_RE.match(line):
            continue
        stripped = LINK_RE.sub(r"\1", line)
        heading = HEADING_RE.match(stripped)
        if heading and LINK_RE.search(line):
            plain = heading.group(2).strip()
            lines[i] = plain if _pure_link_heading(line) else "#" * len(heading.group(1)) + " " + plain
    has_parts = any(
        entry.depth == 0 and re.match(r"(?i)^part(?:\s+|[.:—–-])", entry.title.strip())
        for entry in entries
    )
    if book_title and not has_parts:
        normalized_title = normalize_heading_text(book_title)
        existing_title_h1 = any(
            (match := HEADING_RE.match(line))
            and len(match.group(1)) == 1
            and normalize_heading_text(match.group(2)) == normalized_title
            for line in lines
        )
        if not existing_title_h1:
            lines.insert(0, "# " + book_title.strip())
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _pdf_line_key(line: str) -> str:
    return normalize_heading_text(line)


def _artifact_line_keys(pdf_lines: list[PdfLine], body_size: float, page_count: int) -> set[str]:
    page_hits: dict[str, set[int]] = {}
    footer_or_header: set[str] = set()
    footnotes: set[str] = set()
    for item in pdf_lines:
        key = _pdf_line_key(item.text)
        if not key:
            continue
        if item.y_ratio is not None and (item.y_ratio <= 0.12 or item.y_ratio >= 0.88):
            page_hits.setdefault(key, set()).add(item.page)
            footer_or_header.add(key)
        numbered_prose = bool(re.match(r"^\s*(?:\[?\d{1,3}\]?)[.)]?\s+[a-z]", item.text))
        small = item.font_size is not None and item.font_size < body_size * 0.92
        at_bottom = item.y_ratio is not None and item.y_ratio >= 0.84
        if numbered_prose and (small or at_bottom):
            footnotes.add(key)
        elif small and at_bottom:
            footnotes.add(key)
    threshold = max(3, int(page_count * 0.2 + 0.999))
    repeated = {key for key, pages in page_hits.items() if len(pages) >= threshold}
    return repeated | footnotes


def _contextual_footnote_heading_indices(text: str) -> set[int]:
    """Return headings flagged by the same adjacency rule used by evaluate()."""
    headings: list[str] = []
    heading_lines: list[int] = []
    previous_contexts: list[str] = []
    next_contexts: list[str] = []
    prior_body_line = ""
    pending_heading_index: int | None = None
    fence_char = ""
    fence_width = 0

    for line_index, line in enumerate(text.splitlines()):
        fence = FENCE_RE.match(line)
        if fence_char:
            if fence and fence.group(1)[0] == fence_char and len(fence.group(1)) >= fence_width:
                fence_char = ""
                fence_width = 0
            continue
        if fence:
            fence_char = fence.group(1)[0]
            fence_width = len(fence.group(1))
            continue

        match = HEADING_RE.match(line)
        if match:
            headings.append(match.group(2).strip())
            heading_lines.append(line_index)
            previous_contexts.append(prior_body_line)
            next_contexts.append("")
            pending_heading_index = len(headings) - 1
            prior_body_line = ""
            continue

        if line.strip() and not line.startswith(("    ", "\t")):
            if pending_heading_index is not None:
                next_contexts[pending_heading_index] = line.strip()
                pending_heading_index = None
            prior_body_line = line.strip()

    return {
        line_index
        for line_index, heading, previous, following in zip(
            heading_lines, headings, previous_contexts, next_contexts
        )
        if _footnote_like_heading(heading, previous, following)
    }


def suppress_pdf_artifact_headings(
    text: str, pdf_lines: list[PdfLine], body_size: float, page_count: int
) -> str:
    """Demote fallback headings that correspond to repeated page furniture or notes."""
    artifacts = _artifact_line_keys(pdf_lines, body_size, page_count)
    footnotes = _contextual_footnote_heading_indices(text)
    if not artifacts and not footnotes:
        return text
    output = []
    fence_char = ""
    fence_width = 0
    for line_index, line in enumerate(text.splitlines()):
        fence = FENCE_RE.match(line)
        if fence_char:
            is_fence_line = True
            if (
                fence
                and fence.group(1)[0] == fence_char
                and len(fence.group(1)) >= fence_width
                and not line[fence.end() :].strip()
            ):
                fence_char = ""
                fence_width = 0
        elif fence:
            fence_char = fence.group(1)[0]
            fence_width = len(fence.group(1))
            is_fence_line = True
        else:
            is_fence_line = False
        match = HEADING_RE.match(line) if not is_fence_line else None
        if match and (line_index in footnotes or _pdf_line_key(match.group(2)) in artifacts):
            line = match.group(2).strip()
        output.append(line)
    return "\n".join(output) + ("\n" if text.endswith("\n") else "")


def _markdown_line_matches(line: str, title: str) -> bool:
    candidate = normalize_heading_text(line)
    variants = _entry_title_variants(title)
    return any(candidate == variant or candidate.startswith(variant + " ") for variant in variants)


def _markdown_line_is_exact_title(line: str, title: str) -> bool:
    candidate = normalize_heading_text(line)
    return candidate in _entry_title_variants(title)


def _place_pdf_candidates(text: str, candidates: list[tuple[str, int]]) -> str:
    lines = text.splitlines()
    cursor = 0
    for title, level in candidates:
        if not title.strip():
            continue
        match_at = next((i for i in range(cursor, len(lines)) if _markdown_line_matches(lines[i], title)), None)
        if match_at is None:
            continue
        heading = "#" * max(1, min(6, level)) + " " + title.strip()
        if _markdown_line_is_exact_title(lines[match_at], title):
            lines[match_at] = heading
            cursor = match_at + 1
        else:
            lines.insert(match_at, heading)
            cursor = match_at + 2
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _pdf_page_lines(doc) -> tuple[list[list[PdfLine]], float, list[dict]]:
    from collections import Counter
    page_dicts = [page.get_text("dict") for page in doc]
    spans = [
        span for page in page_dicts for block in page.get("blocks", [])
        for line in block.get("lines", []) for span in line.get("spans", [])
        if span.get("text", "").strip()
    ]
    body_size = Counter(round(span["size"] * 2) / 2 for span in spans).most_common(1)[0][0] if spans else 0.0
    pages: list[list[PdfLine]] = []
    for page_number, page_dict in enumerate(page_dicts):
        height = page_dict.get("height") or 1
        lines = []
        for block in page_dict.get("blocks", []):
            for line_index, line in enumerate(block.get("lines", [])):
                line_spans = [span for span in line.get("spans", []) if span.get("text", "").strip()]
                if not line_spans:
                    continue
                value = re.sub(r"\s+", " ", "".join(span["text"] for span in line_spans)).strip()
                if not value:
                    continue
                y = min(span.get("bbox", [0, 0, 0, 0])[1] for span in line_spans) / height
                size = max(span.get("size", body_size) for span in line_spans)
                bold = any((span.get("flags", 0) & 16) or "bold" in span.get("font", "").casefold() for span in line_spans)
                lines.append(PdfLine(page_number + 1, value, y, size, bold, line_index == 0))
        pages.append(lines)
    return pages, body_size, page_dicts


def _page_title_matches(page: list[PdfLine], title: str) -> bool:
    variants = _entry_title_variants(title)
    return any(
        (candidate := normalize_heading_text(line.text))
        and any(candidate == variant or candidate.startswith(variant + " ") for variant in variants)
        for line in page
    )


def _contents_candidates(pages: list[list[PdfLine]], page_count: int) -> list[tuple[str, int, int]]:
    contents = parse_contents_pages(["\n".join(line.text for line in page) for page in pages[:30]])
    if not contents:
        return []
    offsets: list[int] = []
    for title, printed_page in contents:
        for physical, page in enumerate(pages, 1):
            if _page_title_matches(page, title):
                offsets.append(physical - printed_page)
    if not offsets:
        return []
    from collections import Counter
    offset, support = Counter(offsets).most_common(1)[0]
    # A contents list is useful only when more than one independent title
    # supports the same physical-to-printed-page offset.
    if support < 2:
        return []
    candidates: list[tuple[str, int, int]] = []
    for title, printed_page in contents:
        physical = printed_page + offset
        if 1 <= physical <= page_count and _page_title_matches(pages[physical - 1], title):
            candidates.append((title, 2, physical))
    return candidates


def _markdown_page_spans(text: str, pages: list[list[PdfLine]]) -> dict[int, tuple[int, int]]:
    """Map source pages to Markdown spans using page-unique source-line anchors."""
    lines = text.splitlines()
    normalized_pages = [
        {key for item in page if (key := normalize_heading_text(item.text))}
        for page in pages
    ]
    page_owners: dict[str, set[int]] = {}
    for page_number, keys in enumerate(normalized_pages, 1):
        for key in keys:
            if len(key) >= 18 and len(key.split()) >= 3:
                page_owners.setdefault(key, set()).add(page_number)

    anchors_by_page: dict[int, set[int]] = {}
    for key, owners in page_owners.items():
        if len(owners) != 1:
            continue
        page_number = next(iter(owners))
        for line_index, line in enumerate(lines):
            candidate = normalize_heading_text(line)
            if candidate == key or f" {key} " in f" {candidate} ":
                anchors_by_page.setdefault(page_number, set()).add(line_index)

    mapped = sorted(
        (page_number, min(indices), max(indices))
        for page_number, indices in anchors_by_page.items()
        if indices
    )
    spans: dict[int, tuple[int, int]] = {}
    for mapped_index, (page_number, first_anchor, last_anchor) in enumerate(mapped):
        start = 0
        if mapped_index:
            _, _, previous_last = mapped[mapped_index - 1]
            start = (previous_last + first_anchor) // 2 + 1
        end = len(lines)
        if mapped_index + 1 < len(mapped):
            _, next_first, _ = mapped[mapped_index + 1]
            end = (last_anchor + next_first) // 2 + 1
        if start < end:
            spans[page_number] = (start, end)
    return spans


def _place_pdf_page_candidates(
    text: str,
    candidates: list[tuple[str, int, int]],
    page_spans: dict[int, tuple[int, int]],
) -> str:
    """Promote contents entries only inside their mapped physical-page span."""
    lines = text.splitlines()
    line_sources: list[int | None] = list(range(len(lines)))
    for title, level, page_number in candidates:
        span = page_spans.get(page_number)
        if span is None:
            continue
        start, end = span
        match_at = next(
            (
                index
                for index, source_index in enumerate(line_sources)
                if source_index is not None
                and start <= source_index < end
                and _markdown_line_matches(lines[index], title)
            ),
            None,
        )
        if match_at is None:
            continue
        heading = "#" * max(1, min(6, level)) + " " + title.strip()
        if _markdown_line_is_exact_title(lines[match_at], title):
            lines[match_at] = heading
        else:
            lines.insert(match_at, heading)
            line_sources.insert(match_at, None)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _typographic_candidates(pages: list[list[PdfLine]], body_size: float) -> list[tuple[str, int]]:
    if body_size <= 0:
        return []
    candidate_rows: list[tuple[str, float, bool]] = []
    for page in pages:
        for index, item in enumerate(page):
            text = item.text.strip()
            if not text or re.fullmatch(r"\d{1,4}", text):
                continue
            if re.match(r"^\s*(?:\[?\d{1,3}\]?)[.)]?\s+[a-z]", text):
                continue
            words = WORD_RE.findall(text)
            if not words or len(words) > 16 or re.search(r"[.!?][\"')\]]?$", text):
                continue
            starts_block = item.starts_block or index == 0
            distinctly_larger = item.font_size is not None and item.font_size >= body_size * 1.18
            clearly_bold = item.bold and item.font_size is not None and item.font_size >= body_size * 0.98
            if starts_block and (distinctly_larger or clearly_bold):
                candidate_rows.append((text, item.font_size or body_size, item.bold))
    tiers = sorted({round(size * 2) / 2 for _, size, _ in candidate_rows}, reverse=True)
    if not tiers:
        return []
    candidates = []
    for title, size, _ in candidate_rows:
        tier = min(range(len(tiers)), key=lambda i: abs(tiers[i] - size))
        candidates.append((title, min(4, tier + 1)))
    return candidates


def _outline_candidates(pdf_path: Path, doc, text: str) -> list[tuple[str, int]]:
    outline = doc.get_toc()
    if not outline:
        return []
    lines = text.splitlines()
    candidates: list[tuple[str, int]] = []
    cursor = 0
    for level, title, page_number in outline:
        title = title.strip()
        if not title:
            continue
        matched = next((
            index for index in range(cursor, len(lines))
            if _markdown_line_matches(lines[index], title)
        ), None)
        if matched is None or not HEADING_RE.match(lines[matched]):
            # A page-zero outline item has no reliable page anchor. Search in
            # order across the full converted text; other entries prefer their
            # physical page's text where possible.
            page = None if page_number <= 0 else page_number - 1
            if page is not None and 0 <= page < doc.page_count:
                page_text = str(doc.load_page(page).get_text("text"))
                if not any(_markdown_line_matches(line, title) for line in page_text.splitlines()):
                    continue
            candidates.append((title, max(1, min(6, level))))
        cursor = (matched + 1) if matched is not None else cursor
    return candidates


def recover_pdf_headings(pdf_path: Path, text: str) -> str:
    """Recover PDF headings from bookmarks, contents pages, or page typography."""
    import fitz

    doc = fitz.open(str(pdf_path))
    try:
        pages, body_size, _ = _pdf_page_lines(doc)
        pdf_lines = [line for page in pages for line in page]
        has_outline = any(
            len(item) >= 2 and str(item[1]).strip()
            for item in doc.get_toc()
        )
        outline = _outline_candidates(pdf_path, doc, text)
        if has_outline:
            recovered = _place_pdf_candidates(text, outline)
            return suppress_pdf_artifact_headings(recovered, pdf_lines, body_size, doc.page_count)
        contents = _contents_candidates(pages, doc.page_count)
        if contents:
            page_spans = _markdown_page_spans(text, pages)
            recovered = _place_pdf_page_candidates(text, contents, page_spans)
        else:
            candidates = _typographic_candidates(pages, body_size)
            recovered = _place_pdf_candidates(text, candidates)
        return suppress_pdf_artifact_headings(recovered, pdf_lines, body_size, doc.page_count)
    finally:
        doc.close()


def _demote_existing_headings(text: str, *, keep_first_h1: bool) -> str:
    """Turn ATX headings into body lines, except an optional book-title H1."""
    output: list[str] = []
    fence_char = ""
    fence_width = 0
    kept_h1 = False
    heading_prefix_re = re.compile(r"^( {0,3})#{1,6}[ \t]+")

    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        fence = FENCE_RE.match(content)
        if fence_char:
            if fence and fence.group(1)[0] == fence_char and len(fence.group(1)) >= fence_width:
                fence_char = ""
                fence_width = 0
            output.append(line)
            continue
        if fence:
            fence_char = fence.group(1)[0]
            fence_width = len(fence.group(1))
            output.append(line)
            continue

        heading = HEADING_RE.match(content)
        if not heading:
            output.append(line)
            continue
        if keep_first_h1 and len(heading.group(1)) == 1 and not kept_h1:
            kept_h1 = True
            output.append(line)
            continue

        prefix = heading_prefix_re.match(content)
        if prefix:
            output.append(prefix.group(1) + content[prefix.end():] + line[len(content):])
        else:
            output.append(line)

    return "".join(output)


def apply_heading_map(
    text: str,
    entries: list[dict[str, Any]] | dict[str, Any],
) -> tuple[str, list[str]]:
    """Insert mapped headings before anchors, optionally replacing source headings."""
    replace_existing = False
    if isinstance(entries, dict):
        replace_existing = entries.get("replace_existing") is True
        entries = entries.get("entries", [])
    if replace_existing:
        has_level_one_entry = False
        for entry in entries:
            try:
                level = int(entry.get("level", 2))
            except (AttributeError, TypeError, ValueError):
                level = 2
            if max(1, min(6, level)) == 1:
                has_level_one_entry = True
                break
        text = _demote_existing_headings(text, keep_first_h1=not has_level_one_entry)

    raw_lines = text.splitlines(keepends=True) if replace_existing else []
    lines = [line.rstrip("\r\n") for line in raw_lines] if replace_existing else text.splitlines()
    fenced_lines: list[bool] = []
    fence_char = ""
    fence_width = 0
    for line in lines:
        fence = FENCE_RE.match(line)
        if fence_char:
            is_fenced = True
            if (
                fence
                and fence.group(1)[0] == fence_char
                and len(fence.group(1)) >= fence_width
                and not line[fence.end() :].strip()
            ):
                fence_char = ""
                fence_width = 0
        elif fence:
            fence_char = fence.group(1)[0]
            fence_width = len(fence.group(1))
            is_fenced = True
        else:
            is_fenced = False
        fenced_lines.append(is_fenced)
    output: list[str] = []
    cursor = 0
    unmatched: list[str] = []
    for entry in entries:
        title = str(entry.get("title", "")).strip()
        anchor = normalize_heading_text(str(entry.get("anchor", "")))
        try:
            level = int(entry.get("level", 2))
        except (TypeError, ValueError):
            level = 2
        level = max(1, min(6, level))
        match_at = None
        for index in range(cursor, len(lines)):
            line = lines[index]
            if fenced_lines[index] or not line.strip() or HEADING_RE.match(line):
                continue
            if normalize_heading_text(line).startswith(anchor) and anchor:
                match_at = index
                break
        if not title or match_at is None:
            unmatched.append(title or "<untitled>")
            continue
        while cursor < match_at:
            output.append(raw_lines[cursor] if replace_existing else lines[cursor])
            cursor += 1
        heading_line = "#" * level + " " + title
        if replace_existing:
            ending = raw_lines[match_at][len(lines[match_at]):]
            output.append(heading_line + (ending or "\n"))
            output.append(raw_lines[match_at])
        else:
            output.append(heading_line)
            output.append(lines[match_at])
        cursor = match_at + 1
    output.extend(raw_lines[cursor:] if replace_existing else lines[cursor:])
    if replace_existing:
        return "".join(output), unmatched
    result = "\n".join(output)
    if text.endswith("\n"):
        result += "\n"
    return result, unmatched
