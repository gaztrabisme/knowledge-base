"""General, CPU-only extraction and sectioning for philosophy source PDFs."""

from __future__ import annotations

import re
import statistics
import unicodedata
from bisect import bisect_left
from collections import Counter
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path

import pymupdf

from .alignment import Section


@dataclass
class ExtractionInfo:
    page_count: int = 0
    missing_pages: list[int] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    contents_pages_removed: int = 0
    front_pages_removed: int = 0
    interlinear_pages_removed: int = 0
    glossary_pages_removed: int = 0
    outline_used: bool = False


@dataclass(frozen=True)
class _Line:
    text: str
    y: float
    x: float
    bottom: float
    right: float
    size: float
    bold: bool
    writing_mode: int = 0
    direction: tuple[float, float] = (1.0, 0.0)


_TOC = re.compile(r"(?i)(\bcontents\b|\btable of contents\b|\bmục lục\b|目錄|目录|目次)")
_PAGE_NO = re.compile(r"^[\s\-–—•·]*(?:\d{1,4}|[ivxlcdm]{1,8}|[〇零一二三四五六七八九十百]+)[\s\-–—•·]*$", re.I)
_TOC_LINE = re.compile(r"(?:\.{2,}|…{1,}|·{2,})\s*\d{1,4}(?!\d)|\s{3,}\d{1,4}\s*$")
_HEADING = re.compile(
    r"(?i)^(?:chapter|part|lecture|lesson|talk|section|chapter|chương|phần|bài giảng)\s+[\divxlc]+\b|"
    r"^第[〇零一二三四五六七八九十百\d]+[章节讲篇卷]|^(?:序|前言|引言|序言|后记|後記|结语|結語)$"
)
_NUMBERED_HEADING = re.compile(r"^(?:\d{1,3}|[ivxlcdm]{1,8}|[一二三四五六七八九十百]+)[、.)．:]\s*\S", re.I)
_TALK_TITLE = re.compile(r"(?i)^(?:talk\s+(?:in|at|on)|lecture\s+(?:in|at))\s+\S")
_SHELL_META = re.compile(
    r"(?i)(bài viết của sư phụ|master.?s recent articles|open book reader|back to top|"
    r"falundafa\.org\s*>\s*books|pháp luân đại pháp\s*-\s*minghui\.org|"
    r"bản dịch(?: có thể được hiệu chỉnh[^.]*)?|bản song ngữ|bilingual|translation last updated|this translation last updated|"
    r"lưu ý:|đăng ngày|updated\s+\d|posted\s+\d|liên kết|links?)"
)
_DOWNLOAD_LINK = re.compile(
    r"(?i)(?:简体字|繁体字|正体字|簡體字|繁體字|正體字)\s*(?:A4|Letter)?\s*版\s*[:：]?\s*PDF文件?"
)
_MARGIN = re.compile(r"(?i)(back\s+to\s+top|minghui\.org|falundafa\.org|page\s+\d+)")
_UPDATE_NOTES = re.compile(
    r"(?i)(更新日期.{0,12}更新(?:内容|內容)|格式说明.{0,12}(?:页数|頁數).{0,12}(?:行数|行數)|"
    r"格式說明.{0,12}(?:頁數|页数).{0,12}(?:行數|行数)|"
    r"(?:网络版|網絡版).{0,12}更新(?:备注|備注|注記)|web\s+edition.{0,12}(?:revision|update)\s+notes)"
)
_GLOSSARY_START = re.compile(
    r"(?i)^(?:chú thích(?: của người dịch)?|chú giải|giải nghĩa|bảng thuật ngữ|glossary|"
    r"footnotes?|translation notes|notes on the translation|注释|註釋|词语解释|詞語解釋)$"
)
_NON_SECTION_LABEL = re.compile(r"(?i)^(?:lyrics?|ca\s*từ|歌詞|歌词)$")


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\u200b", "").replace("\xa0", " ")).strip()


def _line_records(page: pymupdf.Page) -> list[_Line]:
    lines = []
    data = page.get_text("dict")
    for block in data.get("blocks", []):
        for line in block.get("lines", []):
            direction = tuple(line.get("dir", (1.0, 0.0)))
            writing_mode = int(line.get("wmode", 0))
            for span in line.get("spans", []):
                text = _clean(span.get("text", ""))
                if not text:
                    continue
                box = span.get("bbox", line.get("bbox", block.get("bbox", (0, 0, 0, 0))))
                lines.append(_Line(
                    text, float(box[1]), float(box[0]), float(box[3]), float(box[2]),
                    float(span.get("size", 0)), bool(int(span.get("flags", 0)) & 16),
                    writing_mode, direction,
                ))
    return lines


def _merge_lines(lines: list[_Line], rotation: int = 0) -> list[_Line]:
    rotation %= 360
    vertical = sum(line.writing_mode == 1 for line in lines) > len(lines) / 2
    if vertical:
        # CJK vertical-writing PDFs often store one glyph per line. With a
        # quarter-turned page, columns lie at a common media-box y coordinate
        # and the glyphs progress along x; sorting line boxes by their usual y
        # baseline interleaves adjacent columns one character at a time.
        if rotation == 90:
            column = lambda line: (line.y + line.bottom) / 2
            progress = lambda line: (line.x + line.right) / 2
            reverse_columns = False
            reverse_progress = False
        elif rotation == 180:
            column = lambda line: (line.x + line.right) / 2
            progress = lambda line: (line.y + line.bottom) / 2
            reverse_columns = True
            reverse_progress = True
        elif rotation == 270:
            column = lambda line: (line.y + line.bottom) / 2
            progress = lambda line: (line.x + line.right) / 2
            reverse_columns = True
            reverse_progress = True
        else:
            column = lambda line: (line.x + line.right) / 2
            progress = lambda line: (line.y + line.bottom) / 2
            reverse_columns = True
            reverse_progress = False
        ordered = sorted(lines, key=column, reverse=reverse_columns)
        groups: list[list[_Line]] = []
        tolerance = max(2.5, statistics.median([line.size for line in lines if line.size > 0] or [10]) * 0.22)
        for line in ordered:
            if groups and abs(column(line) - column(groups[-1][0])) <= tolerance:
                groups[-1].append(line)
            else:
                groups.append([line])
        merged = []
        for group in groups:
            group.sort(key=progress, reverse=reverse_progress)
            merged.append(_Line(
                "".join(line.text for line in group),
                min(line.y for line in group), min(line.x for line in group),
                max(line.bottom for line in group), max(line.right for line in group),
                max(line.size for line in group), any(line.bold for line in group),
                1, group[0].direction,
            ))
        return merged
    if rotation == 90:
        ordered = sorted(lines, key=lambda line: (line.x, line.y))
        baseline = lambda line: line.x
        within_group = lambda line: line.y
        reverse_within = True
    elif rotation == 270:
        ordered = sorted(lines, key=lambda line: (-line.x, -line.y))
        baseline = lambda line: -line.x
        within_group = lambda line: line.y
        reverse_within = False
    elif rotation == 180:
        ordered = sorted(lines, key=lambda line: (-line.y, -line.x))
        baseline = lambda line: -line.y
        within_group = lambda line: -line.x
        reverse_within = False
    else:
        ordered = sorted(lines, key=lambda line: (line.y, line.x))
        baseline = lambda line: line.y
        within_group = lambda line: line.x
        reverse_within = False
    groups: list[list[_Line]] = []
    for line in ordered:
        if (_PAGE_NO.fullmatch(line.text.strip()) and line.text.strip().isdigit()) or not groups:
            groups.append([line])
        elif abs(baseline(line) - baseline(groups[-1][0])) <= 2.5 and not any(
                _PAGE_NO.fullmatch(item.text.strip()) and item.text.strip().isdigit() for item in groups[-1]):
            same_rotated_line = rotation not in (90, 270) or abs(
                within_group(line) - within_group(groups[-1][0])
            ) <= 2.5
            if same_rotated_line:
                groups[-1].append(line)
            else:
                groups.append([line])
        else:
            groups.append([line])
    merged = []
    for group in groups:
        group.sort(key=within_group, reverse=reverse_within)
        value = ""
        for line in group:
            if value and value[-1].isascii() and value[-1].isalnum() and line.text[0].isascii() and line.text[0].isalnum():
                value += " "
            value += line.text
        merged.append(_Line(value, min(item.y for item in group), min(item.x for item in group),
                             max(item.bottom for item in group), max(item.right for item in group),
                             max(item.size for item in group), any(item.bold for item in group),
                             group[0].writing_mode, group[0].direction))
    return merged


def _cells(lines: list[_Line], rect: pymupdf.Rect, layout: str, rotation: int) -> list[list[_Line]]:
    match = re.search(r"([24])\s*合\s*1", layout)
    if not match:
        return [_merge_lines(lines, rotation)]
    count = int(match.group(1))
    cells = [[] for _ in range(count)]
    for line in lines:
        x_mid = (line.x + line.right) / 2
        y_mid = (line.y + line.bottom) / 2
        if count == 2 and rotation in (90, 270):
            index = min(1, max(0, int((y_mid / max(rect.height, 1)) * 2)))
        elif count == 2:
            index = min(1, max(0, int((x_mid / max(rect.width, 1)) * 2)))
        else:
            col = min(1, max(0, int((x_mid / max(rect.width, 1)) * 2)))
            row = min(1, max(0, int((y_mid / max(rect.height, 1)) * 2)))
            index = row * 2 + col
        cells[index].append(line)
    return [_merge_lines(cell, rotation) for cell in cells]


def _is_contents_page(lines: list[_Line], index: int, total: int) -> bool:
    text = " ".join(line.text for line in lines)
    front = index < min(8, max(3, total // 15))
    # Some PDF text layers merge a short label with the adjacent running header
    # (for example, “目录 法輪大法”). Keep the match short and at a line start
    # so prose that mentions contents cannot turn an interior page into a TOC.
    toc_label = any(
        _TOC.fullmatch(line.text.strip())
        or (len(_norm(line.text)) <= 20 and _TOC.match(line.text.strip()))
        for line in lines
    )
    references = sum(len(_TOC_LINE.findall(line.text)) for line in lines)
    numbered = sum(bool(re.search(r"\s\d{1,4}\s*$", line.text)) for line in lines)
    dense = max(references, numbered) >= max(4, int(len(lines) * 0.45))
    update_index = bool(_UPDATE_NOTES.search(text))
    indexed = update_index
    toc_like = references >= 4 or (references >= 2 and len(lines) >= 7)
    date_line = re.compile(
        r"(?i)(?:[〇零一二三四五六七八九十\d]{2,4}年.{0,10}[〇零一二三四五六七八九十\d]{1,3}月|"
        r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2})"
    )
    date_lines = sum(bool(date_line.search(line.text)) for line in lines)
    author_lines = sum(bool(re.search(r"(?i)(李洪志|li\s+hongzhi|hongzhi\s+li|lý\s+hồng\s+chí)", line.text))
                        for line in lines)
    heading_lines = sum(
        1 for line in lines if 5 <= len(_norm(line.text)) <= 90
        and not re.search(r"[.!?。！？]$", line.text)
        and not date_line.search(line.text)
        and not re.search(r"(?i)(李洪志|li\s+hongzhi|hongzhi\s+li|lý\s+hồng\s+chí)", line.text)
    )
    long_lines = sum(len(line.text) > 110 for line in lines)
    sentence_ends = sum(bool(re.search(r"[.!?。！？]$", line.text)) for line in lines)
    opening_list = (
        index < min(24, max(8, total // 8)) and len(lines) >= 6
        and long_lines <= 1 and sentence_ends <= 1 and heading_lines >= 3
        and date_lines >= 2 and author_lines >= 2
    )
    return ((toc_label and len(lines) >= 2) or indexed or toc_like
            or (front and dense and len(lines) >= 7) or opening_list)


def _contents_pages(pages: list[list[_Line]], source_page_count: int) -> list[bool]:
    flags = [_is_contents_page(lines, i, len(pages)) for i, lines in enumerate(pages)]
    # Scanned web editions sometimes append a revision index and its correction
    # log after the final chapter. These pages belong to the edition wrapper,
    # not to the work. Drop the tail run, plus an adjacent short title/author
    # page when it immediately precedes that material.
    update_tail = next((i for i, lines in enumerate(pages)
                        if i >= len(pages) * 0.70 and _UPDATE_NOTES.search(_text(lines))), None)
    if update_tail is not None:
        flags[update_tail:] = [True] * (len(flags) - update_tail)
        if update_tail > 0:
            previous = pages[update_tail - 1]
            previous_text = _text(previous)
            has_author = bool(re.search(r"(?i)(李洪志|li\s+hongzhi|hongzhi\s+li|lý\s+hồng\s+chí)", previous_text))
            if has_author and len(previous) <= 6 and len(_norm(previous_text)) < 180:
                flags[update_tail - 1] = True
    marker = next((i for i, lines in enumerate(pages[:min(20, max(10, source_page_count // 10))])
                   if any(_TOC.fullmatch(line.text.strip()) or
                          (len(_norm(line.text)) <= 20 and _TOC.match(line.text.strip()))
                          for line in lines)), None)
    if marker is not None:
        flags[marker] = True
        for index in range(marker + 1, min(len(pages), marker + 8)):
            lines = [line.text.strip() for line in pages[index] if line.text.strip()]
            if len(lines) < 8:
                sentence_ends = sum(bool(re.search(r"[!?。！？]$", line)) for line in lines)
                long_lines = sum(len(line) > 110 for line in lines)
                date_or_author = any(re.search(
                    r"(?i)(?:[〇零一二三四五六七八九十\d]{2,4}年|"
                    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}|"
                    r"李洪志|li\s+hongzhi|hongzhi\s+li|lý\s+hồng\s+chí)", line,
                ) for line in lines)
                meaningful = any(
                    not _PAGE_NO.fullmatch(line) and not _TOC_LINE.search(line)
                    and not re.fullmatch(r"[.·…\s]{3,}", line)
                    for line in lines
                )
                if sentence_ends > 1 or long_lines > 1 or (meaningful and date_or_author):
                    break
                continue
            refs = sum(len(_TOC_LINE.findall(line)) + bool(re.search(r"\s\d{1,4}\s*$", line))
                       for line in lines)
            leader_lines = sum(bool(re.fullmatch(r"[.·…\s]{3,}", line)) for line in lines)
            sentence_ends = sum(
                (bool(re.search(r"[!?。！？]$", line))
                 or (bool(re.search(r"\.$", line)) and not re.fullmatch(r"[.·…\s]{3,}", line)))
                and not (_NUMBERED_HEADING.search(line) or _HEADING.search(line))
                for line in lines
            )
            long_lines = sum(len(line) > 110 and not re.fullmatch(r"[.·…\s]{3,}", line)
                             for line in lines)
            average = sum(len(line) for line in lines) / len(lines)
            short_lines = sum(len(_norm(line)) <= 80 for line in lines)
            headings = sum(bool(_NUMBERED_HEADING.search(line) or _HEADING.search(line))
                           and len(line) <= 90 for line in lines)
            if ((refs >= 2 and sentence_ends <= 1 and long_lines <= 1)
                    or leader_lines >= 2
                    or (headings >= 4 and sentence_ends <= 1 and long_lines <= 1)
                    # Several scanned editions put a plain, unnumbered list
                    # on continuation pages after a labeled contents page.
                    # Accept it only while the lines still look like a title
                    # list, before the first prose page.
                    or (len(lines) >= 12 and sentence_ends <= 1 and long_lines <= 1
                        and short_lines / len(lines) >= 0.85 and average <= 42)):
                flags[index] = True
            else:
                break
    # Some contents sections have no label, and other books place the label on
    # the cover before several numbered list pages. Detect only an opening run
    # with several numbered items and no prose so the label is not required.
    if source_page_count >= 20:
        started = False
        for index, page in enumerate(pages[:8]):
            if flags[index]:
                started = True
                continue
            texts = [line.text.strip() for line in page if line.text.strip()]
            if len(texts) < 8:
                if started:
                    break
                continue
            endings = sum(bool(re.search(r"[.!?。！？]$", line))
                          and not _NUMBERED_HEADING.search(line) for line in texts)
            leaders = sum(bool(re.fullmatch(r"[.·…\s]{3,}", line)) for line in texts)
            refs = sum(len(_TOC_LINE.findall(line)) + bool(re.search(r"\s\d{1,3}\s*$", line))
                       for line in texts)
            headings = sum(bool(_HEADING.search(line) or (_NUMBERED_HEADING.search(line) and len(line) < 65))
                           for line in texts)
            long_lines = sum(len(line) > 110 and not re.fullmatch(r"[.·…\s]{3,}", line)
                             for line in texts)
            if endings <= 1 and long_lines <= 1 and (refs >= 2 or leaders >= 2 or headings >= 4):
                flags[index] = True
                started = True
            elif started and endings <= 1 and long_lines <= 1 and (refs >= 1 or leaders >= 1):
                flags[index] = True
            elif started:
                break
    return flags


def _front_pages(pages: list[list[_Line]], flags: list[bool], source_page_count: int) -> list[bool]:
    front = [False] * len(pages)
    if source_page_count < 20:
        return front
    for index, lines in enumerate(pages[:8]):
        if flags[index]:
            continue
        text = _text(lines)
        # A short, dated page inside the opening run is often the title/date
        # page for the first lecture, especially after a contents section.
        # Treating every short page as a book cover loses that lecture's start.
        has_date = bool(re.search(
            r"(?i)(?:[〇零一二三四五六七八九十\d]{2,4}年|"
            r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2})",
            text,
        ))
        if has_date:
            continue
        if len(_norm(text)) < 180 and len(lines) <= 6:
            front[index] = True
    return front


def _strip_repeated_margins(pages: list[list[_Line]]) -> list[list[_Line]]:
    def is_leader(text: str) -> bool:
        return bool(re.fullmatch(r"[.·…\s]{3,}", text))

    samples = []
    for lines in pages:
        samples.extend(_clean(line.text).casefold() for line in (lines[:2] + lines[-2:])
                       if line.text and not is_leader(_clean(line.text)))
    counts = Counter(samples)
    threshold = max(3, int(len(pages) * 0.2))
    repeated = {text for text, count in counts.items() if count >= threshold and len(text) < 100}
    result = []
    for lines in pages:
        kept = []
        for i, line in enumerate(lines):
            text = _clean(line.text)
            if _PAGE_NO.fullmatch(text):
                continue
            if _MARGIN.search(text):
                continue
            if is_leader(text):
                kept.append(line)
                continue
            if text.casefold() in repeated:
                continue
            kept.append(line)
        result.append(kept)
    return result


def _trim_trailing_glossary(pages: list[list[_Line]]) -> tuple[list[list[_Line]], int]:
    """Drop a back matter glossary/footnote section after the work's body."""
    if len(pages) < 2:
        return pages, 0
    threshold = int(len(pages) * 0.65)
    for page_index in range(threshold, len(pages)):
        for line_index, line in enumerate(pages[page_index]):
            if _GLOSSARY_START.fullmatch(_clean(line.text).strip(" :：.-—–")):
                kept = pages[:page_index]
                if line_index:
                    kept.append(pages[page_index][:line_index])
                return kept, len(pages) - len(kept)
    return pages, 0


def _text(lines: list[_Line]) -> str:
    return "\n".join(line.text for line in lines if line.text).strip()


def _joined_page_offsets(page_texts: list[str]) -> list[int]:
    """Return offsets matching the nonempty-page join used for section text."""
    offsets = []
    total = 0
    for text in page_texts:
        offsets.append(total)
        if text:
            total += len(text) + 2
    return offsets


def _is_vietnamese_interlinear_page(lines: list[_Line], language: str) -> bool:
    """Identify paired Chinese/pinyin sheets in Vietnamese poem editions."""
    if language != "vi":
        return False
    han_lines = [sum("\u3400" <= char <= "\u9fff" for char in line.text) for line in lines]
    latin_lines = [sum(char.isalpha() and not "\u3400" <= char <= "\u9fff" for char in line.text)
                   for line in lines]
    han_total, latin_total = sum(han_lines), sum(latin_lines)
    han_rows = sum(count >= 2 for count in han_lines)
    latin_rows = sum(count >= 8 for count in latin_lines)
    if han_total < 12 or latin_total < 80 or han_rows < 4 or latin_rows < 4:
        return False
    # Interlinear sheets alternate short pinyin/Han/Vietnamese rows. A page of
    # prose with an occasional Chinese quotation does not have this pattern.
    row_categories = [
        "han" if han and not latin else "latin" if latin and not han else "mixed"
        for han, latin in zip(han_lines, latin_lines) if han or latin
    ]
    switches = sum(a != b for a, b in zip(row_categories, row_categories[1:]))
    return switches >= 3


def _printed_page_number(lines: list[_Line]) -> int | None:
    labels = [int(match.group(1)) for line in lines
              if (match := re.fullmatch(r"\s*(\d{1,4})\s*", line.text))]
    return labels[-1] if labels else None


def _vietnamese_interlinear_flags(pages: list[list[_Line]], language: str) -> list[bool]:
    flags = [_is_vietnamese_interlinear_page(page, language) for page in pages]
    if language != "vi":
        return flags
    labels = [_printed_page_number(page) for page in pages]
    for index, (page, following) in enumerate(zip(pages, pages[1:])):
        current_number, next_number = labels[index], labels[index + 1]
        if current_number is None or next_number != current_number + 1:
            continue
        han_current = sum("\u3400" <= char <= "\u9fff" for line in page for char in line.text)
        latin_current = sum(char.isalpha() and not "\u3400" <= char <= "\u9fff"
                            for line in page for char in line.text)
        han_rows = sum(sum("\u3400" <= char <= "\u9fff" for char in line.text) >= 2 for line in page)
        latin_rows = sum(sum(char.isalpha() and not "\u3400" <= char <= "\u9fff"
                             for char in line.text) >= 3 for line in page)
        han_next = sum("\u3400" <= char <= "\u9fff" for line in following for char in line.text)
        latin_next = sum(char.isalpha() and not "\u3400" <= char <= "\u9fff"
                         for line in following for char in line.text)
        if (han_current >= 2 and latin_current >= 8 and han_rows >= 2 and latin_rows >= 3
                and han_next < 4 and latin_next >= 20):
            flags[index] = True
    return flags


def repair_chinese_full_stop_positions(text: str, reference: str) -> str:
    """Move misplaced Chinese full stops using a matching edition as evidence.

    A few Simplified PDFs have invisible text-layer full stops with incorrect
    coordinates. When the Traditional counterpart has the same lexical text
    and the same number of full stops, its punctuation positions provide a
    safe alignment anchor while all Simplified characters and line breaks stay
    intact.
    """
    def lexical(value: str) -> tuple[str, list[int]]:
        chars, offsets = [], []
        for offset, char in enumerate(value):
            if char.isalnum() or "\u3400" <= char <= "\u9fff":
                chars.append(char)
                offsets.append(offset)
        return "".join(chars), offsets

    source_lexical, _ = lexical(text)
    reference_lexical, _ = lexical(reference)
    matcher = SequenceMatcher(None, source_lexical, reference_lexical, autojunk=False)
    if matcher.ratio() < 0.98 or abs(len(source_lexical) - len(reference_lexical)) > 24:
        return text

    def positions(value: str) -> list[int]:
        index = 0
        found = []
        for char in value:
            if char == "。":
                found.append(index)
            elif char.isalnum() or "\u3400" <= char <= "\u9fff":
                index += 1
        return found

    reference_positions = positions(reference)
    if len(reference_positions) != text.count("。"):
        return text
    blocks = matcher.get_matching_blocks()

    def map_boundary(reference_offset: int) -> int:
        previous = following = None
        for source_start, reference_start, length in blocks:
            if reference_start <= reference_offset <= reference_start + length:
                return source_start + min(reference_offset - reference_start, length)
            if reference_start + length < reference_offset:
                previous = (source_start + length, reference_start + length)
            elif reference_start > reference_offset:
                following = (source_start, reference_start)
                break
        if previous is None:
            return following[0] if following else 0
        if following is None:
            return previous[0]
        source_gap = following[0] - previous[0]
        reference_gap = following[1] - previous[1]
        if reference_gap <= 0:
            return previous[0]
        fraction = (reference_offset - previous[1]) / reference_gap
        return max(previous[0], min(following[0], round(previous[0] + fraction * source_gap)))

    target_counts = Counter(map_boundary(offset) for offset in reference_positions)
    if positions(text) == sorted(target_counts.elements()):
        return text
    output = []
    lexical_index = 0
    if target_counts.get(0):
        output.extend("。" * target_counts.pop(0))
    for char in text:
        if char == "。":
            continue
        output.append(char)
        if char.isalnum() or "\u3400" <= char <= "\u9fff":
            lexical_index += 1
            if target_counts.get(lexical_index):
                output.extend("。" * target_counts.pop(lexical_index))
    return "".join(output)


def _norm(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text).casefold().replace("đ", "d")
    return "".join(char for char in decomposed if char.isalnum() and not unicodedata.combining(char))


_CJK = r"\u3400-\u9fff"


def _normalize_chinese_spacing(text: str) -> str:
    # Traditional scans often put a literal space between every glyph. Chinese
    # does not use those word spaces, so join only Han-to-Han and punctuation
    # boundaries; preserve spaces around Latin words and numerals.
    value = re.sub(rf"(?<=[{_CJK}])\s+(?=[{_CJK}])", "", text)
    value = re.sub(rf"(?<=[{_CJK}])\s+([，。！？：；、])", r"\1", value)
    value = re.sub(rf"([，。！？：；、])\s+(?=[{_CJK}])", r"\1", value)
    return value


def _find(text: str, title: str, start_at: int = 0) -> int | None:
    target = _norm(title)
    if not target:
        return None
    chars, offsets = [], []
    for i, char in enumerate(text):
        for normalized in unicodedata.normalize("NFKD", char).casefold().replace("đ", "d"):
            if normalized.isalnum() and not unicodedata.combining(normalized):
                chars.append(normalized)
                offsets.append(i)
    normalized = "".join(chars)
    found = normalized.find(target, bisect_left(offsets, start_at))
    if found >= 0:
        return offsets[found]
    # Bookmark text often differs by punctuation or a short subtitle.
    for size in range(len(target) - 1, min(7, len(target)), -1):
        found = normalized.find(target[:size], bisect_left(offsets, start_at))
        if found >= 0:
            return offsets[found]
    return None


def _toc_titles(pages: list[list[_Line]], flags: list[bool], document_title: str) -> list[str]:
    titles = []
    leaders = re.compile(r"(?:\.{2,}|…+|·{2,})")
    continuation_end = re.compile(r"(?i)(?:,|\b(?:at|of|the|in|for|to|with|given|and|or))\s*$")
    date_or_author = re.compile(
        r"(?i)^(?:李洪志|li\s+hongzhi|hongzhi\s+li|lý\s+hồng\s+chí|"
        r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}\b|"
        r"[〇零一二三四五六七八九\d]{2,4}年.{0,12}[〇零一二三四五六七八九\d]{1,3}月)"
    )
    for page, is_contents in zip(pages, flags):
        if not is_contents:
            continue
        page_text = " ".join(line.text for line in page)
        if re.search(r"(?i)(更新日期.{0,12}更新内容|更新內容|格式说明.{0,8}页数.{0,8}行数)", page_text):
            continue
        page_parts = []
        for line in page:
            value = line.text.strip()
            if not value or _TOC.fullmatch(value):
                continue
            parts = leaders.split(value)
            for part_index, part in enumerate(parts):
                part = part.strip(" .·—–-\t")
                numbered_entry = bool(re.match(r"^\d{1,3}[.)、:]\s*\S", part))
                if date_or_author.search(part.strip()):
                    continue
                if len(parts) > 1:
                    part = re.sub(r"\s+\d{1,4}\s*$", "", part).strip()
                    if part_index > 0:
                        part = re.sub(r"^\d{1,4}[.)、:]?\s+", "", part).strip()
                if numbered_entry:
                    part = re.sub(r"^\d{1,3}[.)、:]\s*", "", part).strip()
                part = re.sub(r"[〇零一二三四五六七八九十百○]+$", "", part).strip()
                if part and not re.fullmatch(r"[.·…\s]{3,}", part):
                    continues_wrapped_title = (
                        not numbered_entry
                        and (continuation_end.search(page_parts[-1])
                             or (part[:1].islower() and part[:1].isascii()))
                    ) if page_parts else False
                    if continues_wrapped_title:
                        page_parts[-1] = f"{page_parts[-1].rstrip()} {part.lstrip()}"
                    else:
                        page_parts.append(part)
        for part in page_parts:
            compact = _norm(part)
            document_compact = _norm(document_title)
            has_cjk_title = bool(re.search(r"[\u3400-\u9fff]", part))
            if (not 1 <= len(compact) <= 90 or compact == document_compact
                    or (len(compact) >= 5 and (compact in document_compact
                                               or document_compact in compact))):
                continue
            if compact in {"lyhongchi", "hongzhili", "master", "sufu", "nam", "year", "falundafa"}:
                continue
            if date_or_author.search(part.strip()):
                continue
            if len(compact) < 3 and not has_cjk_title:
                continue
            if _norm(document_title) in compact or len(part.split()) > 14 or re.search(r"[.!?。！？]$", part):
                continue
            if (_SHELL_META.search(part) or _MARGIN.search(part) or _PAGE_NO.fullmatch(part)
                    or _NON_SECTION_LABEL.fullmatch(part)
                    or compact in {"hongzhili", "lihongzhi", "lyhongchi"}
                    or re.search(r"(?i)(translated|translation|copyright|pre-publication|edition|updated|revision)", part)):
                continue
            titles.append(_normalize_chinese_spacing(part))
    seen = set()
    return [title for title in titles if not (_norm(title) in seen or seen.add(_norm(title)))]


def _toc_anchors(text: str, titles: list[str]) -> list[tuple[int, str]]:
    # Find exact title lines first, then retain the largest title-ordered,
    # document-ordered subset. Some editions move a preface such as “Lunyu”
    # to the back; accepting that one late match must not hide the intervening
    # chapters whose headings are in their normal order.
    candidates: list[tuple[int, int, str]] = []
    for title_index, title in enumerate(titles):
        title_norm = _norm(title)
        has_latin = any(char.isascii() and char.isalnum() for char in title)
        if not title_norm:
            continue
        line_offset = 0
        for raw_line in text.splitlines(keepends=True):
            line = raw_line.rstrip("\r\n")
            line_norm, offsets = [], []
            for index, char in enumerate(line):
                for normalized in unicodedata.normalize("NFKD", char).casefold().replace("đ", "d"):
                    if normalized.isalnum() and not unicodedata.combining(normalized):
                        line_norm.append(normalized)
                        offsets.append(index)
            normalized_line = "".join(line_norm)
            candidate = normalized_line.find(title_norm)
            while candidate >= 0:
                offset_in_line = offsets[candidate]
                end_in_line = offsets[candidate + len(title_norm) - 1] + 1
                prefix = line[:offset_in_line].strip(" \t\u3000-—–:：·•『「“\"'([{（【《")
                suffix = line[end_in_line:]
                # TOC anchors must be headings at the start of a line. This
                # prevents a short Vietnamese title such as "Ngộ" from
                # matching the beginning of the prose word "ngoại".
                at_start = not prefix
                boundary = not suffix or not suffix[0].isalnum()
                tail_norm = normalized_line[candidate + len(title_norm):]
                exact_heading = not tail_norm or tail_norm.isdigit() and len(tail_norm) <= 4
                if at_start and boundary and exact_heading:
                    heading_norm = _norm(line.strip())
                    if len(title_norm) > 2 or has_latin or heading_norm == title_norm:
                        candidates.append((title_index, line_offset + offset_in_line, line.strip()))
                candidate = normalized_line.find(title_norm, candidate + 1)
            line_offset += len(raw_line)

    if not candidates:
        return []
    candidates.sort(key=lambda item: (item[0], item[1]))
    lengths = [1] * len(candidates)
    previous: list[int | None] = [None] * len(candidates)
    for right, (title_index, offset, _) in enumerate(candidates):
        for left in range(right):
            prev_title, prev_offset, _ = candidates[left]
            if (prev_title < title_index and prev_offset < offset
                    and lengths[left] + 1 > lengths[right]):
                lengths[right] = lengths[left] + 1
                previous[right] = left
    best = max(range(len(candidates)), key=lambda index: lengths[index])
    ordered = []
    while best is not None:
        title_index, offset, title = candidates[best]
        ordered.append((offset, title))
        best = previous[best]
    ordered.reverse()
    return ordered


def _headings(
    pages: list[list[_Line]], document_title: str = "", language: str = "",
) -> list[tuple[int, int, str]]:
    sizes = [line.size for page in pages for line in page if line.size > 0]
    typical = statistics.median(sizes) if sizes else 0
    found = []
    for page_index, lines in enumerate(pages):
        page_sizes = [line.size for line in lines if line.size > 0]
        body_size = statistics.median(page_sizes) if page_sizes else typical
        consumed: set[int] = set()
        for line_index, line in enumerate(lines):
            if line_index in consumed:
                continue
            value = _normalize_chinese_spacing(line.text.strip())
            if not value or len(value) > 110 or len(value.split()) > 15 or _norm(value) == _norm(document_title):
                continue
            if _NON_SECTION_LABEL.fullmatch(value):
                continue
            if _PAGE_NO.fullmatch(value) or _TOC_LINE.search(value):
                continue
            if _MARGIN.search(value) or _SHELL_META.search(value):
                continue
            folded = value.casefold()
            if (_TOC.fullmatch(value) or value.lstrip().startswith(("▪", "•", "●", "■", "◆", "※"))
                    or folded in {"hongzhi li", "li hongzhi", "lý hồng chí", "ly hong chi", "contents",
                                  "table of contents", "năm", "year"}):
                continue
            normalized_value = _norm(value)
            if len(normalized_value) <= 1:
                continue
            normalized_document_title = _norm(document_title)
            if (page_index < 4 and len(normalized_value) >= 5 and normalized_document_title
                    and (normalized_value in normalized_document_title
                         or normalized_document_title.startswith(normalized_value))):
                continue
            if re.fullmatch(r"(?i)(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?", value):
                continue
            if re.match(r"(?i)^ngày\s+\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4}", value):
                continue
            numbered = bool(_NUMBERED_HEADING.search(value)) and len(value) <= 65 and len(value.split()) <= 10
            if (numbered and re.search(r"[\u3400-\u9fff]", value)
                    and len(_norm(value)) > 20 and not _HEADING.search(value)):
                numbered = False
            talk_title = bool(_TALK_TITLE.search(value))
            explicit = bool(_HEADING.search(value) or numbered or talk_title)
            style_heading = line.size >= max(body_size * 1.30, typical * 1.30)
            bold_vietnamese_title = (
                language == "vi" and line.bold and len(normalized_value) <= 90
                and not re.search(r"[.!?。！？]$", value)
            )
            if explicit or style_heading or bold_vietnamese_title:
                if talk_title:
                    # Talk titles often wrap one phrase over several large
                    # lines. Keep the title together and start the section at
                    # its first line; date/byline rows remain body metadata.
                    pieces = [value]
                    previous = line
                    for following_index in range(line_index + 1, min(len(lines), line_index + 5)):
                        following = lines[following_index]
                        next_value = _normalize_chinese_spacing(following.text.strip())
                        if (not next_value or abs(following.size - line.size) > max(1.0, line.size * 0.08)
                                or following.y - previous.bottom > max(14, line.size * 1.1)
                                or _PAGE_NO.fullmatch(next_value)
                                or re.search(r"(?i)(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}", next_value)):
                            break
                        pieces.append(next_value)
                        consumed.add(following_index)
                        previous = following
                    value = " ".join(pieces)
                found.append((page_index, line_index, value))
    # Repeated styled headers are not section boundaries.
    counts = Counter(title.casefold() for _, _, title in found)
    unique = [row for row in found if counts[row[2].casefold()] == 1]
    merged = []
    index = 0
    while index < len(unique):
        page_index, line_index, title = unique[index]
        end_line = line_index
        while index + 1 < len(unique):
            next_page, next_line, next_title = unique[index + 1]
            if next_page != page_index or next_line != end_line + 1:
                break
            previous = pages[page_index][end_line]
            following = pages[next_page][next_line]
            if following.y - previous.bottom > 14:
                break
            separator = "" if (title[-1:] and next_title[:1]
                                 and "\u3400" <= title[-1] <= "\u9fff"
                                 and "\u3400" <= next_title[0] <= "\u9fff") else " "
            title = f"{title}{separator}{next_title}"
            end_line = next_line
            index += 1
        merged.append((page_index, line_index, title))
        index += 1
    return merged


def _shell_body(text: str, titles: list[str]) -> str:
    body = re.sub(r"(?m)^\s*#.*$", " ", text)
    # Remove wrapper phrases in place. Dropping any line that contains one of
    # them can erase a short but real article when a PDF text layer joins the
    # article and its translation notice into a single line.
    body = _SHELL_META.sub(" ", body)
    body = _MARGIN.sub(" ", body)
    body = re.sub(
        r"(?i)(?:简体字|繁体字|正体字|簡體字|繁體字|正體字)\s*(?:A4|Letter)?\s*版\s*[:：]?\s*PDF文件?",
        " ", body,
    )
    body = re.sub(r"(?i)PDF文件?", " ", body)
    body = re.sub(
        r"[〇零一二三四五六七八九十\d]{1,4}年[〇零一二三四五六七八九十\d]{1,3}月[〇零一二三四五六七八九十\d]{1,3}日",
        " ", body,
    )
    body_lines = []
    for line in body.splitlines():
        value = _clean(line)
        if not value or _PAGE_NO.fullmatch(value):
            continue
        if re.fullmatch(r"[〇零一二三四五六七八九十\d年月日\s：:—–.-]{4,}", value):
            continue
        normalized_line = _norm(value)
        if normalized_line in {"lyhongchi", "hongzhili", "lihongzhi", "李洪志", "師父", "师父"}:
            continue
        if len(normalized_line) <= 4 and any(char in value for char in "李洪志師父"):
            continue
        body_lines.append(value)
    value = _norm(" ".join(body_lines))
    for title in titles:
        compact_title = _norm(title)
        value = value.replace(compact_title, " ")
        # Text layers on title sheets sometimes truncate the final word or
        # drop a date, leaving most of the title behind as apparent body text.
        minimum = max(8, int(len(compact_title) * 0.7))
        for length in range(len(compact_title) - 1, minimum - 1, -1):
            value = value.replace(compact_title[:length], " ")
    for phrase in (
        "bai viet cua su phu ly hong chi", "master s recent articles", "hongzhi li",
        "ban dich tieng viet", "ban dich song ngu trung viet chi de tham khao",
        "ban dich song ngu trung viet", "ban song ngu chi de tham khao", "ban song ngu",
        "translation last updated", "this translation last updated", "open book reader",
        "falundafa org books", "phap luan dai phap minghui org", "back to top",
        "luu y", "dang ngay", "updated", "posted", "links",
        "ban dich tieng viet", "ban dich song ngu", "ban song ngu trung viet",
        "ban song ngu", "tieng viet", "song ngu trung viet chi de tham khao",
        "chi de tham khao", "song ngu", "alternate editions", "pdf file", "day la ban draft",
        "cap nhat", "draft", "phap luan dai phap minghui org",
        "ban dich co the duoc hieu chinh trong tuong lai", "ban dich co the duoc hieu chinh",
    ):
        value = value.replace(_norm(phrase), " ")
    return re.sub(r"\d+", " ", value)


def _section_text(text: str, title: str) -> str:
    lines = []
    for line in text.splitlines():
        value = _normalize_chinese_spacing(_clean(line))
        if not value or _PAGE_NO.fullmatch(value) or _TOC_LINE.search(value):
            continue
        if _NON_SECTION_LABEL.fullmatch(value):
            continue
        if _MARGIN.search(value):
            continue
        lines.append(value)
    normalized_title = _norm(title)
    for count in range(1, min(4, len(lines)) + 1):
        candidate = _norm(" ".join(lines[:count]))
        if candidate == normalized_title:
            del lines[:count]
            break
        if not normalized_title.startswith(candidate):
            break
    # Some reviewed scan layers place an undotted contents list directly
    # before the first article paragraph. Only remove it when it has multiple
    # date/byline pairs. Wrapped opening paragraphs can look like short title
    # lines when a PDF text layer breaks every sentence across physical lines;
    # a count of short lines alone is not evidence of a contents list.
    cjk_date = re.compile(r"[〇零一二三四五六七八九十\d]{2,4}年.{0,12}[〇零一二三四五六七八九十\d]{1,3}月")
    latin_date = re.compile(
        r"(?i)(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}"
    )
    author = re.compile(r"(?i)(?:^|\s)(?:李洪志|li\s+hongzhi|hongzhi\s+li|lý\s+hồng\s+chí)(?:$|\s)")
    body_index = next((index for index, line in enumerate(lines[:20])
                       if len(line) > 110 or (len(line) > 28 and re.search(r"[.!?。！？]$", line))), None)
    if body_index is not None and body_index >= 6:
        prefix = lines[:body_index]
        dates = sum(bool(cjk_date.search(line) or latin_date.search(line)) for line in prefix)
        authors = sum(bool(author.search(line)) for line in prefix)
        headings = sum(1 for line in prefix if 5 <= len(_norm(line)) <= 90
                       and not cjk_date.search(line) and not latin_date.search(line)
                       and not author.search(line) and not re.search(r"[.!?。！？]$", line))
        if dates >= 2 and authors >= 2 and headings >= 2:
            del lines[:body_index]
    body = _normalize_chinese_spacing("\n".join(lines).strip())
    body = _DOWNLOAD_LINK.sub("", body)
    body = re.sub(r"(?i)PDF文件?", "", body)
    if not _shell_body(body, [title]):
        return ""
    return body


def web_shell_reason(text: str, titles: list[str]) -> str | None:
    """Return a reason only when page text is a title/link shell without article body."""
    normalized = _norm(text)
    markers = ("backtotop", "openbookreader", "falundafaorgbooks", "minghuiorg")
    has_navigation = any(marker in normalized for marker in markers)
    has_translation_notice = bool(re.search(r"(?i)(bản dịch|bản song ngữ|translation)", text))
    has_link_notice = bool(re.search(
        r"(?i)(?:pdf\s*文件?|(?:简体字|繁体字|正体字|簡體字|繁體字|正體字).{0,18}版|alternate editions)", text,
    ))
    residual = _shell_body(text, titles)
    body_letters = sum(char.isalpha() for char in residual)
    has_shell_metadata = has_navigation or has_translation_notice or has_link_notice or bool(
        re.search(r"(?i)(master.?s recent articles|bài viết của sư phụ)", text)
    )
    if body_letters < 20 and (has_shell_metadata or not residual):
        return "one-page web shell contains title, translation/link notices, and navigation but no article body"
    return None


def split_sections(
    path: str | Path, language: str, layout: str = "", *, document_title: str = "",
) -> tuple[list[Section], ExtractionInfo]:
    """Extract ordered sections from a PDF, preferring usable bookmarks to headings."""
    source = Path(path)
    info = ExtractionInfo()
    physical: list[list[list[_Line]]] = []
    with pymupdf.open(str(source)) as document:
        info.page_count = document.page_count
        try:
            toc = document.get_toc()
        except Exception as exc:
            toc = []
            info.warnings.append(f"outline unavailable: {exc}")
        for page_index in range(document.page_count):
            try:
                page = document.load_page(page_index)
                lines = _line_records(page)
                physical.append(_cells(lines, page.mediabox, layout, page.rotation))
            except Exception as exc:
                physical.append([[]])
                info.missing_pages.append(page_index + 1)
                info.warnings.append(f"page {page_index + 1} extraction failed: {exc}")
            warnings = pymupdf.TOOLS.mupdf_warnings(reset=True) or ""
            for match in re.finditer(r"cannot find page (\d+) in page tree", warnings, re.I):
                info.missing_pages.append(int(match.group(1)))
    info.missing_pages = sorted(set(info.missing_pages))

    multipage = bool(re.search(r"[24]\s*合\s*1", layout))
    multipage_unlabelled_removed = 0
    if multipage:
        # Print sheets are read as cells, then ordered by printed page labels when present.
        pages = [cell for sheet in physical for cell in sheet if cell]
        numbered = []
        unnumbered = []
        for order, lines in enumerate(pages):
            label = next((int(m.group(1)) for line in reversed(lines)
                          if (m := re.fullmatch(r"\s*(\d{1,4})\s*", line.text))), None)
            (numbered if label is not None else unnumbered).append((label, order, lines))
        ordered = sorted(numbered, key=lambda row: (row[0], row[1]))
        # Some archive PDFs contain a second copy of the imposed pages in the
        # text layer. Keep one copy of a printed page when its extracted body
        # is identical; retaining both doubles sections and breaks alignment.
        unique_numbered = []
        fingerprints: set[tuple[int, str]] = set()
        for label, order, lines in ordered:
            body = "\n".join(line.text for line in lines
                              if not re.fullmatch(r"\s*\d{1,4}\s*", line.text))
            fingerprint = (label, _norm(body))
            if fingerprint in fingerprints:
                continue
            fingerprints.add(fingerprint)
            unique_numbered.append((label, order, lines))
        # Unnumbered cells in the imposed books are covers, section title
        # pages, and blank panels. When the document has a substantial run of
        # printed page labels they cannot be placed reliably in book order,
        # so keep only numbered logical pages. For small synthetic/partial
        # layouts retain unnumbered cells in their physical position.
        if len(unique_numbered) >= 8 and len(unique_numbered) >= len(pages) * 0.5:
            ordered = unique_numbered
            multipage_unlabelled_removed = len(unnumbered)
        else:
            ordered = unique_numbered
            for row in sorted(unnumbered, key=lambda item: item[1]):
                insertion = next((i for i, item in enumerate(ordered) if item[1] > row[1]), len(ordered))
                ordered.insert(insertion, row)
        pages = [row[2] for row in ordered]
    else:
        pages = [sheet[0] if sheet else [] for sheet in physical]

    interlinear_flags = _vietnamese_interlinear_flags(pages, language)
    info.interlinear_pages_removed = sum(interlinear_flags)
    if info.interlinear_pages_removed:
        pages = [page for page, interlinear in zip(pages, interlinear_flags) if not interlinear]
    pages = _strip_repeated_margins(pages)
    pages, info.glossary_pages_removed = _trim_trailing_glossary(pages)
    layout_match = re.search(r"([24])\s*合\s*1", layout)
    logical_page_count = info.page_count * (int(layout_match.group(1)) if layout_match else 1)
    contents = _contents_pages(pages, logical_page_count)
    front = _front_pages(pages, contents, logical_page_count)
    info.contents_pages_removed = sum(contents)
    info.front_pages_removed = sum(front) + multipage_unlabelled_removed
    contents_titles = _toc_titles(pages, contents, document_title)
    removed = [contents[i] or front[i] for i in range(len(pages))]
    kept_indices = [i for i, is_removed in enumerate(removed) if not is_removed]
    physical_to_kept = {physical: kept for kept, physical in enumerate(kept_indices)}
    kept_pages = [pages[i] for i in kept_indices]
    page_texts = [_text(lines) for lines in kept_pages]
    flattened = "\n\n".join(text for text in page_texts if text)
    starts: list[tuple[int, str]] = []

    if toc and not multipage:
        usable = []
        normalized_document_title = _norm(document_title)
        for level, title, page_number in toc:
            title = _clean(title)
            normalized_title = _norm(title)
            if (not title or _TOC.fullmatch(title) or normalized_title in {"contents", "tableofcontents"}
                    or (len(normalized_title) >= 5 and normalized_document_title
                        and normalized_title in normalized_document_title)):
                continue
            physical_page = page_number - 1
            if title and physical_page in physical_to_kept:
                usable.append((level, title, physical_to_kept[physical_page]))
        anchors = []
        for _, title, page_index in usable:
            offset = _find(page_texts[page_index], title)
            if offset is not None:
                anchors.append((page_index, offset, title))
        if len(anchors) >= 2 and len(anchors) / max(1, len(usable)) >= 0.5:
            page_offsets = _joined_page_offsets(page_texts)
            starts = [(page_offsets[p] + off, title) for p, off, title in anchors]
            info.outline_used = True

    if not starts:
        toc_starts = _toc_anchors(flattened, contents_titles)
        if len(toc_starts) >= 2:
            starts = toc_starts

    heading_rows = _headings(kept_pages, document_title, language)
    if heading_rows:
        page_offsets = _joined_page_offsets(page_texts)
        line_offsets = []
        for lines, page_offset in zip(kept_pages, page_offsets):
            offset = page_offset
            page_line_offsets = []
            for line in lines:
                page_line_offsets.append(offset)
                offset += len(line.text) + 1
            line_offsets.append(page_line_offsets)
        heading_starts = []
        for page_index, line_index, title in heading_rows:
            # Explicit talk/chapter headings supplement sparse TOC anchors;
            # style-only lines remain a fallback when no usable anchors exist.
            explicit = bool(_TALK_TITLE.search(title) or _HEADING.search(title)
                            or _NUMBERED_HEADING.search(title))
            if explicit or language == "vi" or not starts:
                heading_starts.append((line_offsets[page_index][line_index], title))
        starts.extend(heading_starts)

    starts.sort(key=lambda row: row[0])
    deduped = []
    for offset, title in starts:
        if deduped and (offset <= deduped[-1][0] or _norm(title) == _norm(deduped[-1][1])):
            continue
        deduped.append((offset, title))
    if len(deduped) < 2:
        title = document_title or source.stem.replace("_", " ")
        body = _section_text(flattened, _clean(title)) or _normalize_chinese_spacing(flattened.strip())
        return [Section("", _normalize_chinese_spacing(_clean(title)), body)], info

    sections = []
    for index, (start, title) in enumerate(deduped):
        end = deduped[index + 1][0] if index + 1 < len(deduped) else len(flattened)
        body = _section_text(flattened[start:end], title)
        if body:
            section_title = _normalize_chinese_spacing(title)
            if (language.startswith("zh") and 0 < len(_norm(section_title)) <= 2
                    and all("\u3400" <= char <= "\u9fff" for char in section_title)):
                section_title = f"詩：{section_title}"
            sections.append(Section("", section_title, body))
    if not sections:
        title = _clean(document_title or source.stem)
        body = _section_text(flattened, title) or _normalize_chinese_spacing(flattened.strip())
        return [Section("", _normalize_chinese_spacing(title), body)], info
    if len(sections) == 1:
        sections[0].section_title = _normalize_chinese_spacing(
            _clean(document_title or sections[0].section_title or source.stem),
        )
    return sections, info


__all__ = ["ExtractionInfo", "split_sections", "web_shell_reason"]
