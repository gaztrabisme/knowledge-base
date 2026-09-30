"""Source extraction and aligned-section discovery for the phase-A corpus."""

from __future__ import annotations

import re
from bisect import bisect_left
from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from math import sqrt
from pathlib import Path

import pymupdf


@dataclass
class Section:
    section_key: str
    section_title: str
    text: str


_HAN_DIGITS = dict(zip("〇零一二三四五六七八九", "00123456789"))
_HAN_SMALL = {"十": 10, "百": 100}


def _chinese_number(value: str) -> str:
    if value and all(char in _HAN_DIGITS for char in value):
        return "".join(_HAN_DIGITS[char] for char in value).lstrip("0") or "0"
    total, current = 0, 0
    for char in value:
        if char in _HAN_DIGITS:
            current = int(_HAN_DIGITS[char])
        elif char in _HAN_SMALL:
            total += (current or 1) * _HAN_SMALL[char]
            current = 0
        else:
            return ""
    return str(total + current) if total + current else ""


def _section_numbers(section: Section) -> set[str]:
    source = f"{section.section_title} {section.text[:900]}"
    found = set(re.findall(r"(?<!\d)(?:19|20)\d{2}(?!\d)", source))
    found.update(re.findall(r"(?<!\d)\d{1,3}(?!\d)", section.section_title))
    for value in re.findall(r"(?i)\b(?:chapter|lecture|poem|verse|part|section)\s+(\d+)\b",
                            section.section_title):
        found.add(f"n:{int(value)}")
    for value in re.findall(r"第([〇零一二三四五六七八九十百\d]+)[章节讲篇卷]", section.section_title):
        normalized = _chinese_number(value) if not value.isdigit() else value
        if normalized:
            found.add(f"n:{normalized}")
    for value in re.findall(r"([〇零一二三四五六七八九\d]{4})年", source):
        normalized = "".join(_HAN_DIGITS.get(char, char) for char in value)
        if normalized.isdigit():
            found.add(normalized)
    return found


def _alignment_evidence(left: list[Section], right: list[Section]) -> float | None:
    """Return a pair score only when equal counts have corroborating text evidence."""
    if not left or len(left) != len(right):
        return None
    conflicts = 0
    shared = 0
    for a, b in zip(left, right):
        marks_a, marks_b = _section_numbers(a), _section_numbers(b)
        if marks_a and marks_b:
            if marks_a & marks_b:
                shared += 1
            else:
                conflicts += 1
    if conflicts > max(0, len(left) // 5):
        return None

    lengths_a = [max(1, len(section.text.strip())) for section in left]
    lengths_b = [max(1, len(section.text.strip())) for section in right]
    if len(left) == 1:
        ratio = lengths_a[0] / lengths_b[0]
        # A single section has a trivial length profile. Require an independent
        # shared date/number as well, so equal counts alone cannot align whole
        # articles with unrelated section boundaries.
        if not 0.3 <= ratio <= 3.0 or not shared or conflicts:
            return None
        return 0.8 + min(shared, 1) * 0.15

    total_a, total_b = sum(lengths_a), sum(lengths_b)
    total_ratio = total_b / max(1, total_a)
    profile_outliers = sum(
        not (total_ratio / 3 <= size_b / max(1, size_a) <= total_ratio * 3)
        for size_a, size_b in zip(lengths_a, lengths_b)
    )
    if profile_outliers / len(left) > 0.10:
        return None
    profile_a = [value / total_a for value in lengths_a]
    profile_b = [value / total_b for value in lengths_b]
    cosine = sum(a * b for a, b in zip(profile_a, profile_b)) / (
        sqrt(sum(a * a for a in profile_a)) * sqrt(sum(b * b for b in profile_b))
    )
    threshold = 0.78 if len(left) == 2 else 0.86
    if cosine < threshold and shared < max(2, len(left) // 2):
        return None
    return cosine + min(shared / max(1, len(left)), 1.0) * 0.15 - conflicts * 0.1


def aligned_language_set(sections_by_language: dict[str, list[Section]]) -> set[str]:
    """Choose the largest mutually supported language set; singletons stay unaligned."""
    languages = sorted(lang for lang, sections in sections_by_language.items() if sections)
    best: tuple[float, tuple[str, ...]] = (-1.0, ())
    for size in range(len(languages), 1, -1):
        candidates = []
        for subset in combinations(languages, size):
            scores = [
                _alignment_evidence(sections_by_language[a], sections_by_language[b])
                for a, b in combinations(subset, 2)
            ]
            if all(score is not None for score in scores):
                candidates.append((sum(float(score) for score in scores), subset))
        if candidates:
            best = max(candidates, key=lambda item: (item[0], item[1]))
            break
    return set(best[1])


def _clean_title(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\u200b", "").replace("\xa0", " ")).strip()


def _normal(value: str) -> str:
    return "".join(char.casefold() for char in value if char.isalnum())


def _normal_with_map(text: str) -> tuple[str, list[int]]:
    chars, offsets = [], []
    for index, char in enumerate(text):
        if char.isalnum():
            chars.append(char.casefold())
            offsets.append(index)
    return "".join(chars), offsets


def _heading_offset(page_text: str, title: str, cursor: int = 0) -> int | None:
    normalized, offsets = _normal_with_map(page_text)
    target = _normal(title)
    if not target:
        return None
    normalized_cursor = bisect_left(offsets, cursor)
    minimum = min(6, len(target))
    for length in range(len(target), minimum - 1, -1):
        match = normalized.find(target[:length], normalized_cursor)
        if match >= 0:
            return offsets[match]
    return None


def original_library_sections(path: Path) -> tuple[list[Section], int]:
    """Use the 38 PDF bookmarks, including its empty first cover bookmark."""
    with pymupdf.open(str(path)) as document:
        toc = document.get_toc()
        pages = [page.get_text("text") for page in document]
        page_count = document.page_count
    if len(toc) != 38:
        raise ValueError(f"Expected 38 Original Library bookmarks in {path.name}, got {len(toc)}")

    titles = [_clean_title(entry[1]) or "Front matter" for entry in toc]
    title = titles[1]
    first_page = pages[0] if pages else ""
    title_offset = _heading_offset(first_page, title) or 0
    _, offset_map = _normal_with_map(first_page)
    normalized_title, _ = _normal_with_map(first_page)
    title_norm = _normal(title)
    position = normalized_title.find(title_norm)
    title_offset = offset_map[position] if position >= 0 else title_offset
    markers = ("SYSTEM DIRECTORY", "系統目錄", "MỤC LỤC HỆ THỐNG")
    marker_positions = [first_page.casefold().find(marker.casefold()) for marker in markers]
    end = min((index for index in marker_positions if index >= 0), default=len(first_page))
    cover_text = first_page[title_offset:end].strip()

    # The first PDF bookmark is intentionally blank. Give it the actual system
    # directory represented by the bookmark list, so the 38th alignment key is useful.
    front_lines = ["System directory"] + [item for item in titles[1:] if item]
    result = [Section("ol-01", "Front matter", "\n".join(front_lines))]
    result.append(Section("ol-02", title, cover_text or title))

    anchor_positions: dict[int, tuple[int, int]] = {}
    by_page: dict[int, list[tuple[int, str]]] = defaultdict(list)
    for toc_index, (level, toc_title, page) in enumerate(toc):
        if toc_index < 2:
            continue
        by_page[page - 1].append((toc_index, _clean_title(toc_title)))
    for page_index, entries in by_page.items():
        if not 0 <= page_index < len(pages):
            continue
        cursor = 0
        for toc_index, toc_title in entries:
            offset = _heading_offset(pages[page_index], toc_title, cursor)
            if offset is None:
                offset = _heading_offset(pages[page_index], toc_title)
            if offset is None:
                raise ValueError(f"Could not align Original Library bookmark {toc_index + 1}: {toc_title}")
            anchor_positions[toc_index] = (page_index, offset)
            cursor = offset + max(1, len(toc_title))

    global_starts: list[tuple[int, int, int]] = []
    page_starts, total = [], 0
    for page_text in pages:
        page_starts.append(total)
        total += len(page_text) + 1
    for toc_index in range(2, len(toc)):
        if toc_index not in anchor_positions:
            raise ValueError(f"Original Library bookmark {toc_index + 1} has no body anchor")
        page_index, offset = anchor_positions[toc_index]
        global_starts.append((toc_index, page_starts[page_index] + offset, page_index))
    flattened = "\n".join(pages)
    for index, (toc_index, start, _) in enumerate(global_starts):
        end = global_starts[index + 1][1] if index + 1 < len(global_starts) else len(flattened)
        text = flattened[start:end].strip()
        result.append(Section(f"ol-{toc_index + 1:02d}", titles[toc_index], text or titles[toc_index]))
    if len(result) != 38:
        raise ValueError(f"Original Library alignment produced {len(result)} sections, expected 38")
    return result, page_count


def _pdf_pages(path: Path) -> tuple[list[str], int]:
    with pymupdf.open(str(path)) as document:
        return [page.get_text("text") for page in document], document.page_count


def tao_pdf_sections(path: Path) -> tuple[list[Section], int]:
    pages, page_count = _pdf_pages(path)
    with pymupdf.open(str(path)) as document:
        toc = document.get_toc()
    starts = []
    for _, title, page in toc:
        match = re.fullmatch(r"Chapter\s+(\d+)", title.strip(), re.IGNORECASE)
        if match:
            number = int(match.group(1))
            if 1 <= number <= 81:
                starts.append((number, max(0, page - 1)))
    starts = sorted(dict(starts).items())
    if [number for number, _ in starts] != list(range(1, 82)):
        raise ValueError(f"Expected Chapter 1–81 bookmarks in {path.name}")
    result = []
    for index, (number, start_page) in enumerate(starts):
        end_page = starts[index + 1][1] if index + 1 < len(starts) else len(pages)
        body = "\n\n".join(pages[start_page:end_page]).strip()
        result.append(Section(f"ttc-{number:03d}", f"Chapter {number}", body or f"Chapter {number}"))
    return result, page_count


def tao_epub_sections(path: Path, *, verse_heading: bool) -> tuple[list[Section], None]:
    """Convert an EPUB through the repository converter and split its numbered units."""
    from markitdown import MarkItDown

    text = MarkItDown().convert(str(path)).text_content
    lines = text.splitlines()
    found = []
    for index, line in enumerate(lines):
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if not match:
            continue
        heading = re.sub(r"[*`_]", "", match.group(1)).strip()
        if verse_heading:
            number_match = re.fullmatch(r"(?:Verse|Chapter)\s+(\d{1,2})", heading, re.IGNORECASE)
        else:
            number_match = re.fullmatch(r"0*(\d{1,2})", heading)
        if number_match:
            number = int(number_match.group(1))
            if 1 <= number <= 81:
                found.append((index, number, heading))
    if [number for _, number, _ in found] != list(range(1, 82)):
        raise ValueError(f"Expected numbered EPUB sections 1–81 in {path.name}; found {len(found)}")
    sections = []
    for i, (line_index, number, title) in enumerate(found):
        end = found[i + 1][0] if i + 1 < len(found) else len(lines)
        body = "\n".join(lines[line_index:end]).strip()
        sections.append(Section(f"ttc-{number:03d}", title, body or title))
    return sections, None


def _page_number(text: str) -> int | None:
    matches = re.findall(r"(?m)^\s*(?:[-–—•·]\s*)?(\d{1,3})(?:\s*[-–—•·])?\s*$", text)
    return int(matches[-1]) if matches else None


def two_up_logical_pages(path: Path) -> tuple[list[str], int]:
    """Split a two-up Chinese PDF into logical pages and sort by printed page number."""
    with pymupdf.open(str(path)) as document:
        physical_count = document.page_count
        numbered: dict[int, tuple[int, str]] = {}
        unnumbered: list[tuple[int, str]] = []
        for physical_index, page in enumerate(document):
            halves = [[], []]
            midpoint = page.rect.width / 2
            for block in page.get_text("blocks"):
                side = 0 if (block[0] + block[2]) / 2 < midpoint else 1
                halves[side].append((block[1], block[4]))
            for side, blocks in enumerate(halves):
                content = "\n".join(value for _, value in sorted(blocks)).strip()
                if not content:
                    continue
                page_number = _page_number(content)
                if page_number is None:
                    unnumbered.append((physical_index * 2 + side, content))
                elif page_number not in numbered or len(content) > len(numbered[page_number][1]):
                    numbered[page_number] = (physical_index * 2 + side, content)
    pages = [text for _, text in sorted(unnumbered)]
    pages.extend(numbered[number][1] for number in sorted(numbered))
    if len(numbered) < 250:
        raise ValueError(f"Two-up PDF page labels incomplete in {path.name}: {len(numbered)} logical pages")
    return pages, physical_count


_EN_ORDINALS = ("first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth")
_VI_ORDINALS = ("nhất", "hai", "ba", "tư", "năm", "sáu", "bảy", "tám", "chín")
_ZH_NUMERALS = "一二三四五六七八九"


def _lecture_marker(text: str, lang: str, number: int) -> bool:
    folded = re.sub(r"\s+", " ", text).casefold()
    if lang == "en":
        return bool(re.search(rf"\bthe\s+{_EN_ORDINALS[number - 1]}\s+talk\b", folded))
    if lang == "vi":
        return f"bài giảng thứ {_VI_ORDINALS[number - 1]}" in folded
    compact = re.sub(r"\s+", "", text)
    marker = f"第{_ZH_NUMERALS[number - 1]}讲"
    return marker in compact


def zhuan_falun_sections(path: Path, lang: str, *, two_up: bool = False) -> tuple[list[Section], int]:
    if two_up:
        pages, page_count = two_up_logical_pages(path)
    else:
        pages, page_count = _pdf_pages(path)
    starts: dict[int, int] = {}
    for number in range(1, 10):
        candidates = [i for i, page in enumerate(pages) if _lecture_marker(page, lang, number)]
        if candidates:
            starts[number] = candidates[-1]  # discard the earlier table-of-contents occurrence
    if sorted(starts) != list(range(1, 10)):
        raise ValueError(f"Could not find all nine lecture starts in {path.name}: {sorted(starts)}")
    positions = [starts[number] for number in range(1, 10)]
    if positions != sorted(positions):
        raise ValueError(f"Lecture markers are out of reading order in {path.name}: {positions}")

    front_title = {"en": "On Dafa", "vi": "Luận ngữ", "zh-Hans": "论语"}[lang]
    front = "\n\n".join(pages[:starts[1]]).strip()
    sections = [Section("zfl-front-lunyu", front_title, front or front_title)]
    for number in range(1, 10):
        end = starts[number + 1] if number < 9 else len(pages)
        body = "\n\n".join(pages[starts[number]:end]).strip()
        title = {
            "en": f"The {_EN_ORDINALS[number - 1].title()} Talk",
            "vi": f"Bài giảng thứ {_VI_ORDINALS[number - 1]}",
            "zh-Hans": f"第{_ZH_NUMERALS[number - 1]}讲",
        }[lang]
        sections.append(Section(f"zfl-L{number}", title, body or title))
    return sections, page_count
