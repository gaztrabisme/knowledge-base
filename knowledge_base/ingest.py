"""EPUB → clean markdown pipeline using markitdown."""

import re
from pathlib import Path

from markitdown import MarkItDown

from .headings import (
    apply_heading_map,
    evaluate,
    normalize_heading_text,
    parse_epub_navigation_documents,
    recover_epub_headings,
    recover_pdf_headings,
)

from .config import MARKDOWN_DIR, SOURCE_DIRS, BOOKS

_converter = MarkItDown()


def convert_epub(epub_path: Path) -> str:
    result = _converter.convert(str(epub_path))
    return result.text_content


def clean_markdown(text: str, repair_extraction_artifacts: bool = False, repair_unclosed_fence: bool = False) -> str:
    # Strip markitdown metadata header (Title/Authors/Publisher/etc.)
    text = re.sub(r"^\*\*(?:Title|Authors?|Language|Publisher|Date|Description|Identifier)\*\*:.*\n", "", text, flags=re.MULTILINE)

    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)

    # Strip backslash escapes that markitdown adds
    text = text.replace("\\-", "-")
    text = text.replace("\\*", "*")
    text = text.replace("\\_", "_")
    text = text.replace("\\.", ".")
    text = text.replace("\\[", "[")
    text = text.replace("\\]", "]")

    if repair_extraction_artifacts:
        # Some PDF text layers encode a missing glyph as backspace. It has no
        # meaning in extracted prose and leaks through MarkItDown unchanged.
        text = text.replace("\x08", "")

        # A drop cap can be split from the rest of a short opening word. Keep
        # the repair narrow so initials and list markers remain separate.
        drop_cap_starts = set(
            "do the this that these those then there their think through they them "
            "when where what which while who why would with we were will your you "
            "in into is it if its on one only our out for from as at an and are "
            "be by but can could had has have he her here how my no not of".split()
        )
        text = re.sub(
            r"(?m)^([A-Z])\n([a-z]{1,3})(?=\s)",
            lambda m: m.group(1) + m.group(2)
            if (m.group(1) + m.group(2)).lower() in drop_cap_starts else m.group(0),
            text,
        )

    text = re.sub(r"</?span[^>]*>", "", text)
    text = re.sub(r"</?div[^>]*>", "", text)

    text = re.sub(r"\n{4,}", "\n\n\n", text)

    # MarkItDown occasionally leaves one code fence open through the rest of a
    # PDF's text layer. Close an unmatched fence so later chapter headings stay
    # visible to the chunker and markdown auditors.
    if repair_unclosed_fence and sum(line.strip().startswith("```") for line in text.splitlines()) % 2:
        text = text.rstrip() + "\n\n```\n"
    return text.strip() + "\n"


def strip_front_back_matter(text: str, *, recovery_pass: bool = False) -> str:
    lines = text.split("\n")

    # A chapter/part opener marks the first real chapter — but only if it appears
    # early. Some books reserve numbered headings for answer keys at the end.
    numeric_cap = int(len(lines) * 0.4)
    chapter_candidates = []
    front_positions = []
    for i, line in enumerate(lines):
        if i > numeric_cap:
            break
        heading = bool(re.match(r"^#{1,3}\s+", line))
        candidate = line if heading else line.strip()
        if not heading:
            continue
        if _is_front_matter_heading(candidate):
            front_positions.append(i)
            continue
        embedded_chapter = bool(
            re.match(r"^#{3}\s+", line)
            and re.search(r"(?i)\bchapter\s+(?:\d+|[a-z]+|[ivxlcdm]+)\b", candidate)
        )
        if _is_chapter_heading(candidate) or embedded_chapter:
            chapter_candidates.append(i)

    content_start = None
    if chapter_candidates:
        last_front = max(front_positions, default=-1)
        after_front = [i for i in chapter_candidates if i > last_front]
        content_start = min(after_front or chapter_candidates)

    if content_start is None:
        # A subset of EPUBs leaves the first chapter opener as plain text.
        # Accept a short, explicit Chapter 1 title; linked contents entries and
        # prose such as "Part 3 explores ..." are intentionally excluded.
        for i, line in enumerate(lines[:numeric_cap + 1]):
            candidate = line.strip()
            if "[" in candidate or "](" in candidate or len(candidate) > 160:
                continue
            if re.match(r"(?i)^chapter\s+1(?:[.:]\s*|\s+)[A-Z]", candidate):
                content_start = i
                lines[i] = "# " + candidate
                break

    recovery_title = None
    if content_start is None:
        if recovery_pass and front_positions:
            # Recovery can restore a contents/foreword/preface sequence without
            # restoring an explicit "Chapter 1" label. In that case the first
            # non-front heading before the sequence is often just the book title.
            first_front = min(front_positions)
            title_before_front = next((
                line for line in lines[:first_front]
                if re.match(r"^#\s+", line) and not _is_front_matter_heading(line)
            ), None)
            last_front = max(front_positions)
            for i in range(last_front + 1, len(lines)):
                if (re.match(r"^#{1,3}\s+", lines[i])
                        and not _is_front_matter_heading(lines[i])):
                    content_start = i
                    break
            if content_start is not None:
                recovery_title = title_before_front

    if content_start is None:
        for i, line in enumerate(lines):
            if not re.match(r"^#{1,3}\s+", line):
                continue
            if not _is_front_matter_heading(line):
                content_start = i
                break

    if content_start is None:
        content_start = 0

    content = _strip_back_matter(lines, content_start)
    if recovery_title:
        return recovery_title + "\n\n" + content.lstrip("\n")
    return content


def strip_back_matter(text: str) -> str:
    """Apply the existing trailing index/promotion cut without a front cut."""
    return _strip_back_matter(text.split("\n"), 0)


def _strip_back_matter(lines: list[str], content_start: int) -> str:
    content_end = len(lines)
    content_headings = []
    back_headings = []
    for i in range(content_start, len(lines)):
        if not re.match(r"^#{1,3}\s+", lines[i]):
            continue
        if _is_back_matter_heading(lines[i]):
            back_headings.append(i)
        elif _is_auxiliary_index_trailer(lines[i]) and any(
            _is_back_matter_heading(lines[index])
            and re.sub(r"^#{1,6}\s+", "", lines[index]).strip().lower()
            in ("index", "subject index", "author index")
            for index in range(content_start, i)
        ):
            back_headings.append(i)
        elif not _is_front_matter_heading(lines[i]):
            content_headings.append(i)
    if back_headings:
        # A back-of-book index may be followed by Packt promotions or review
        # pages. Start at the first back-matter heading after the last real
        # content heading, while preserving a genuine mid-book "Index" chapter.
        last_content = max(content_headings, default=content_start - 1)
        tail_candidates = [i for i in back_headings if i > last_content]
        # Some EPUBs append the alphabetical index before a repeated contents
        # page or an inside-back-cover page. Treat a late Index heading as the
        # tail when no later chapter opener follows it; an Index section near
        # the front of a book (for example, an API object index) remains content.
        tail_index = next((
            i for i in back_headings
            if i >= int(len(lines) * 0.65)
            and re.sub(r"^#{1,6}\s+", "", lines[i]).strip().lower()
                in ("index", "subject index", "author index")
            and not any(
                re.match(r"^#{1,3}\s+", lines[j]) and _is_chapter_heading(lines[j])
                for j in range(i + 1, len(lines))
            )
        ), None)
        if tail_index is not None:
            tail_candidates.append(tail_index)
        if tail_candidates:
            content_end = min(tail_candidates)

    return "\n".join(lines[content_start:content_end]).strip() + "\n"


def _is_front_matter_heading(line: str) -> bool:
    heading = re.sub(r"^#{1,6}\s+", "", line).strip().lower()
    heading = re.sub(r"\s+", " ", heading)
    front_starts = (
        "table of contents", "brief contents", "copyright", "dedication",
        "what will you learn", "what you'll learn", "why this book",
        "a word from the author", "from the author", "overview of the chapters",
        "overview of the book", "who is this book for", "target audience",
        "prerequisites", "overview of this book", "about the author",
        "about the reviewer", "about the technical", "preface", "acknowledgment",
        "foreword", "contributor", "join our community", "discord", "who this book is for",
        "what this book covers", "what you need for this book", "conventions used",
        "get in touch", "download the example", "packt.link", "to get the most out",
        "reviews", "leave a review", "making the most out", "unlock your book",
        "how to unlock", "running a jupyter", "conventions", "code in action",
        "why subscribe", "packtpub", "packt.com", "subscribe", "praise for",
        "revision history", "reilly online learning", "how to contact us",
        "using code examples", "about this book", "who should read this book",
        "why i wrote this book", "navigating the book", "staying up-to-date", "safari",
    )
    exact = {
        "contents", "cover", "landmarks", "sections", "notice", "title",
        "list of figures", "list of tables", "list of illustrations",
        "list of maps", "list of abbreviations", "list of acronyms",
    }
    return heading in exact or heading.startswith(front_starts)


_WORD_NUMERALS = (
    "zero|one|two|three|four|five|six|seven|eight|nine|ten|"
    "first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth"
)
_PART_NUMERALS = rf"(?:\d+|{_WORD_NUMERALS}|[ivxlcdm]+)"


def _is_chapter_heading(line: str) -> bool:
    """Recognize chapter and part openers with numeric or written ordinals."""
    heading = re.sub(r"^#{1,6}\s+", "", line).strip()
    return bool(re.match(
        rf"^(?:chapter\s+{_PART_NUMERALS}|part\s+{_PART_NUMERALS}|"
        r"\d+(?:\s+\S|[.:](?!\d)\s*\S)|\d+)(?=$|\s|[.:—–-])",
        heading,
        re.IGNORECASE,
    ))


def _is_back_matter_heading(line: str) -> bool:
    heading = re.sub(r"^#{1,6}\s+", "", line).strip().lower()
    # Exact matches: the book index ("Index") is huge page-number noise, but
    # "Index Scans"/"Indexing" mid-book must not trigger the cut.
    if heading in ("index", "subject index", "author index"):
        return True
    back_patterns = [
        "other books you may enjoy", "packt page", "download a free pdf",
        "inside back cover",
    ]
    return any(p in heading for p in back_patterns)


def _is_auxiliary_index_trailer(line: str) -> bool:
    heading = re.sub(r"^#{1,6}\s+", "", line).strip().lower()
    return any(p in heading for p in (
        "colophon", "eula", "share your thoughts",
        "packt is searching for authors like you",
    ))


def normalize_heading_levels(text: str) -> str:
    lines = text.split("\n")
    heading_levels = []
    for line in lines:
        m = re.match(r"^(#{1,6})\s+", line)
        if m:
            heading_levels.append(len(m.group(1)))

    if not heading_levels:
        return text

    min_level = min(heading_levels)
    if min_level == 1:
        return text

    chapter_count = sum(_is_chapter_heading(line) for line in lines)
    shift = min_level - 2 if min_level == 3 and chapter_count >= 5 else min_level - 1
    result = []
    in_code = False
    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
        if not in_code:
            m = re.match(r"^(#{1,6})(\s+.*)", line)
            if m:
                new_level = max(1, len(m.group(1)) - shift)
                line = "#" * new_level + m.group(2)
        result.append(line)
    return "\n".join(result)


def _epub_navigation_entries(epub_path: Path):
    import zipfile

    try:
        with zipfile.ZipFile(epub_path) as archive:
            names = archive.namelist()
            nav_name = next((name for name in names if name.casefold().endswith("/nav.xhtml")), None)
            if nav_name is None:
                nav_name = next((name for name in names if name.casefold() == "nav.xhtml"), None)
            ncx_name = next((name for name in names if name.casefold().endswith(".ncx")), None)
            nav = archive.read(nav_name).decode("utf-8", errors="replace") if nav_name else None
            ncx = archive.read(ncx_name).decode("utf-8", errors="replace") if ncx_name else None
    except (OSError, zipfile.BadZipFile):
        return []
    return parse_epub_navigation_documents(
        nav, ncx, nav_path=nav_name or "", ncx_path=ncx_name or ""
    )


def _epub_book_title(epub_path: Path) -> str | None:
    import xml.etree.ElementTree as ET
    import zipfile

    try:
        with zipfile.ZipFile(epub_path) as archive:
            opf_name = next(
                (name for name in archive.namelist() if name.casefold().endswith(".opf")),
                None,
            )
            if opf_name is None:
                return None
            root = ET.fromstring(archive.read(opf_name))
    except (OSError, zipfile.BadZipFile, ET.ParseError):
        return None
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1].casefold() == "title":
            title = " ".join("".join(element.itertext()).split())
            if title:
                return title
    return None


_UNLOADED_HEADING_MAP = object()


def _load_output_heading_map(output_path: Path):
    import json

    map_path = Path(__file__).resolve().parents[1] / "data" / "intake" / "heading-maps" / f"{output_path.stem}.json"
    if not map_path.is_file():
        return None
    try:
        heading_map = json.loads(map_path.read_text(encoding="utf-8"))
        if isinstance(heading_map, list):
            entries = heading_map
        elif (
            isinstance(heading_map, dict)
            and isinstance(heading_map.get("replace_existing"), bool)
            and isinstance(heading_map.get("entries"), list)
        ):
            entries = heading_map["entries"]
        else:
            raise ValueError("map must be a JSON list or an object with replace_existing and entries")
        if any(not isinstance(entry, dict) for entry in entries):
            raise ValueError("map entries must be JSON objects")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"  Invalid heading map {map_path}: {error}")
        return None
    return heading_map


def _is_authoritative_heading_map(heading_map) -> bool:
    return isinstance(heading_map, dict) and heading_map.get("replace_existing") is True


def _apply_output_heading_map(
    text: str,
    output_path: Path,
    heading_map=_UNLOADED_HEADING_MAP,
) -> str:
    if heading_map is _UNLOADED_HEADING_MAP:
        heading_map = _load_output_heading_map(output_path)
    if heading_map is None:
        return text
    apply_map = heading_map if isinstance(heading_map, dict) else heading_map
    text, unmatched = apply_heading_map(text, apply_map)
    if unmatched:
        print(f"  Unmatched heading-map titles for {output_path.stem}: {', '.join(unmatched)}")
    return text


def _book_title(output_path: Path) -> str | None:
    title = BOOKS.get(output_path.stem)
    if not title:
        return None
    return re.sub(r"\s+\([^()]*\)$", "", title).strip()


def _trim_to_first_map_heading(text: str, heading_map: dict, output_path: Path) -> str:
    entries = heading_map.get("entries", [])
    if not entries:
        print(f"  Empty authoritative heading map for {output_path.stem}; preserving extracted text")
        return strip_back_matter(text)

    first = entries[0]
    title = str(first.get("title", "")).strip()
    try:
        level = max(1, min(6, int(first.get("level", 2))))
    except (TypeError, ValueError):
        level = 2
    mapped_line = "#" * level + " " + title
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.strip() == mapped_line), None)
    if not title or start is None:
        print(f"  First heading-map entry was not placed for {output_path.stem}: {title or '<untitled>'}")
        return strip_back_matter(text)

    expected_title = _book_title(output_path)
    title_line = None
    if expected_title:
        expected_normalized = normalize_heading_text(expected_title)
        for line in lines[:start]:
            match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
            if not match:
                continue
            candidate = normalize_heading_text(match.group(1))
            if candidate == expected_normalized or (
                len(candidate) >= 5 and expected_normalized.startswith(candidate)
            ):
                title_line = "# " + match.group(1).strip()
                break
        if title_line is None:
            title_line = "# " + expected_title

    # Use the original line span for index heuristics so its 65% threshold and
    # all other trailing-cut decisions remain identical to the pre-map pass.
    content = _strip_back_matter(lines, start)
    if title_line:
        return title_line + "\n\n" + content.lstrip("\n")
    return content


def _trim_to_back_matter_anchor(text: str, heading_map: dict, output_path: Path) -> str:
    """Drop mapped books' trailing back matter from its explicit line anchor."""
    if not _is_authoritative_heading_map(heading_map):
        return text
    if "back_matter_anchor" not in heading_map:
        return text

    anchor = heading_map.get("back_matter_anchor")
    if not isinstance(anchor, str) or not anchor.strip():
        print(f"  Invalid back_matter_anchor for {output_path.stem}; preserving extracted text")
        return text
    normalized_anchor = normalize_heading_text(anchor)
    if not normalized_anchor:
        print(f"  Invalid back_matter_anchor for {output_path.stem}; preserving extracted text")
        return text

    entries = heading_map.get("entries", [])
    if entries:
        last_entry = entries[-1]
        title = str(last_entry.get("title", "")).strip()
        try:
            level = max(1, min(6, int(last_entry.get("level", 2))))
        except (TypeError, ValueError):
            level = 2
        last_heading = "#" * level + " " + title
        lines = text.splitlines(keepends=True)
        last_heading_at = next(
            (i for i in range(len(lines) - 1, -1, -1)
             if lines[i].strip() == last_heading),
            None,
        )
        if last_heading_at is None:
            print(
                f"  Back-matter anchor for {output_path.stem} not applied; "
                f"last mapped heading was not placed: {title or '<untitled>'}"
            )
            return text
        search_start = last_heading_at + 1
    else:
        print(f"  Back-matter anchor for {output_path.stem} not applied; heading map is empty")
        return text

    lines = text.splitlines(keepends=True)
    for i in range(search_start, len(lines)):
        line = lines[i].rstrip("\r\n")
        if normalize_heading_text(line).startswith(normalized_anchor):
            return "".join(lines[:i]).rstrip("\r\n") + "\n"

    print(
        f"  Back-matter anchor not found for {output_path.stem}: {anchor!r}; "
        "preserving extracted text"
    )
    return text


def ingest_epub(epub_path: Path, output_path: Path) -> Path:
    heading_map = _load_output_heading_map(output_path)
    authoritative_map = _is_authoritative_heading_map(heading_map)
    text = convert_epub(epub_path)
    text = clean_markdown(
        text,
        repair_extraction_artifacts=epub_path.stem == "storytelling-with-data",
        repair_unclosed_fence=epub_path.stem == "vector-databases-introduction",
    )
    if sum(bool(re.match(r"^#{2,6}\s+", line)) for line in text.splitlines()) < 5:
        text = reconstruct_epub_toc(epub_path, text)
    if not authoritative_map:
        text = strip_front_back_matter(text)
    if sum(bool(re.match(r"^#{2,6}\s+", line)) for line in text.splitlines()) < 5:
        text = reconstruct_epub_toc(epub_path, text, allow_plain_labels=True)
    text = normalize_heading_levels(text)
    if evaluate(text)["flagged"]:
        try:
            recovered = recover_epub_headings(
                text, _epub_navigation_entries(epub_path), _epub_book_title(epub_path)
            )
            if recovered != text:
                recovered = strip_front_back_matter(recovered, recovery_pass=True)
            text = recovered
        except Exception as error:
            print(f"  EPUB heading recovery unavailable ({error}): {epub_path.stem}")
    text = _apply_output_heading_map(text, output_path, heading_map)
    if authoritative_map:
        text = _trim_to_first_map_heading(text, heading_map, output_path)
        text = _trim_to_back_matter_anchor(text, heading_map, output_path)
    output_path.write_text(text, encoding="utf-8")
    return output_path


def reconstruct_epub_toc(epub_path: Path, text: str, allow_plain_labels: bool = False) -> str:
    """Rebuild chapter headings from an EPUB's nested navigation document."""
    import zipfile
    import xml.etree.ElementTree as ET

    try:
        with zipfile.ZipFile(epub_path) as archive:
            toc_name = next((name for name in archive.namelist() if name.lower().endswith(".ncx")), None)
            if not toc_name:
                return text
            root = ET.fromstring(archive.read(toc_name))
    except (OSError, zipfile.BadZipFile, ET.ParseError):
        return text

    def local(tag: str) -> str:
        return tag.rsplit("}", 1)[-1]

    def normalized(value: str) -> str:
        value = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", value)
        return re.sub(r"[^\w]+", " ", value.casefold()).strip()

    entries: list[tuple[int, str]] = []

    def visit(parent, depth: int = 0) -> None:
        for node in parent:
            if local(node.tag) != "navPoint":
                visit(node, depth)
                continue
            title = next((child.text or "" for child in node.iter() if local(child.tag) == "text"), "").strip()
            structural = bool(re.match(r"(?i)^(?:chapter|part)\s+", title))
            if allow_plain_labels:
                structural = structural or bool(re.match(r"^(?:\d{1,2}[.:]|[A-Z][.:])\s+\S", title))
            if title and structural:
                entries.append((depth, title))
            visit(node, depth + 1)

    visit(root)
    if not entries:
        return text

    all_top_level = all(depth == 0 for depth, _ in entries)
    flat_numbered_outline = sum(
        depth == 0 and bool(re.match(r"^\d{1,2}[.:]\s+\S", title))
        for depth, title in entries
    ) >= 5
    flat_outline = all_top_level or flat_numbered_outline
    doc_title = next((
        (child.text or "").strip()
        for node in root.iter()
        if local(node.tag) == "docTitle"
        for child in node.iter()
        if local(child.tag) == "text" and (child.text or "").strip()
    ), "")
    lines = text.splitlines()
    cursor = 0
    for depth, title in entries:
        title_match = re.match(r"(?i)^(chapter|part)\s+(?:\d+|[a-z]+|[ivxlcdm]+)\s*[:.\-–—]?\s*(.*)$", title)
        variants = {normalized(title)}
        if title_match and title_match.group(2):
            variants.add(normalized(title_match.group(2)))
        numbered_match = re.match(r"^(\d{1,2})[.:]\s*(.*)$", title)
        if numbered_match and numbered_match.group(2):
            variants.add(normalized(f"Chapter {numbered_match.group(1)} {numbered_match.group(2)}"))
            variants.add(normalized(numbered_match.group(2)))
        match_at = None
        for i in range(cursor, len(lines)):
            if not allow_plain_labels and not ("[" in lines[i] and "](" in lines[i]):
                continue
            candidate = normalized(lines[i])
            if candidate in variants:
                match_at = i
                break
        if match_at is None:
            continue
        # A flat navigation list gives no distinction between book chapters and
        # subheadings. Keep those chapter openers at H2; nested EPUB navigation
        # retains its part/chapter levels.
        level = 2 if flat_outline and depth == 0 else min(3, depth + 1)
        lines[match_at] = "#" * level + " " + title
        cursor = match_at + 1
    if flat_outline and doc_title:
        lines.insert(0, "# " + doc_title)
    return "\n".join(lines)


def convert_pdf_with_toc(pdf_path: Path) -> str | None:
    """Reconstruct markdown headings from a PDF's embedded TOC bookmarks.

    Returns None if the PDF has no usable TOC (caller should fall back to
    markitdown). The body text never contributes headings — we inject only
    the TOC entries and neutralize any body line that looks like a heading,
    so code comments like `# init` can't masquerade as structure.
    """
    import fitz  # PyMuPDF

    doc = fitz.open(str(pdf_path))
    toc = doc.get_toc()  # [[level, title, page], ...]; page is 1-based
    if not toc:
        doc.close()
        return None

    page_headings: dict[int, list[tuple[int, str]]] = {}
    levels = {level for level, title, _ in toc if title.strip()}
    flat_chapter_outline = (
        len(toc) >= 5
        and len(levels) == 1
        and sum(_is_chapter_heading("# " + title) for _, title, _ in toc) >= 5
    )
    for level, title, page in toc:
        title = title.strip()
        if not title:
            continue
        if flat_chapter_outline and _is_chapter_heading("# " + title):
            level = 2
        page_headings.setdefault(page - 1, []).append((level, title))

    parts = []
    for page_index in range(doc.page_count):
        for level, title in page_headings.get(page_index, []):
            parts.append("#" * min(level, 3) + " " + title)
        body = str(doc.load_page(page_index).get_text("text"))
        # Neutralize body lines that would parse as markdown headings.
        body = re.sub(r"(?m)^(#{1,6}\s)", r" \1", body)
        parts.append(body)

    doc.close()
    return "\n\n".join(parts)


def convert_pdf_with_layout(pdf_path: Path) -> str:
    """Use PDF typography to recover headings when bookmarks are absent."""
    import fitz  # PyMuPDF
    from collections import Counter

    doc = fitz.open(str(pdf_path))
    page_dicts = [page.get_text("dict") for page in doc]
    spans = [
        span for page in page_dicts for block in page["blocks"]
        for line in block.get("lines", []) for span in line["spans"]
        if span["text"].strip()
    ]
    if not spans:
        doc.close()
        raise ValueError("PDF has no extractable text layer")

    body_size = Counter(round(span["size"] * 2) / 2 for span in spans).most_common(1)[0][0]
    parts = []
    for page_number, page in enumerate(page_dicts):
        extracted = []
        for block in page["blocks"]:
            for line in block.get("lines", []):
                items = [span for span in line["spans"] if span["text"].strip()]
                if not items:
                    continue
                body = re.sub(r"\s+", " ", "".join(s["text"] for s in items)).strip()
                if not body or re.fullmatch(r"\d{1,4}", body):
                    continue
                size = max(s["size"] for s in items)
                bold = any((s["flags"] & 16) or "bold" in s["font"].lower() for s in items)
                extracted.append((body, size, bold))

        page_lines = []
        i = 0
        while i < len(extracted):
            body, size, bold = extracted[i]
            number = re.fullmatch(r"\d{1,2}(?:\.\d{1,2}){1,3}", body)
            if page_number >= 3 and number and i + 1 < len(extracted):
                title = extracted[i + 1][0]
                level = min(3, body.count(".") + 1)
                page_lines.append("#" * level + " " + body + " " + title)
                i += 2
                continue
            chapter = _is_chapter_heading("# " + body)
            if page_number >= 3 and (size >= body_size * 1.75 or chapter):
                page_lines.append("# " + body)
            elif page_number >= 3 and (
                    size >= body_size * 1.25 or (bold and size >= body_size * 1.05)
            ):
                page_lines.append("## " + body)
            else:
                page_lines.append(" " + body if re.match(r"^#{1,6}\s", body) else body)
            i += 1
        if page_lines:
            parts.append("\n".join(page_lines))

    doc.close()
    text = "\n\n".join(parts)
    if len(text.strip()) < 500:
        raise ValueError("PDF text layer is too small to form usable markdown")
    return text


# Glyphs that should never appear in English technical PDFs. Some PDFs embed
# subset fonts with no ToUnicode CMap, so PyMuPDF maps glyphs to garbage in the
# Armenian/Hebrew/extended-Cyrillic ranges (e.g. "PostgreSQL" → "PostgreԯԭԨ",
# "2022" → "ҁѿҁ҂"). When that happens we lose the body text, so we discard the
# TOC headings and fall back to markitdown, which extracts these PDFs cleanly.
_GARBLE_RE = re.compile(r"[԰-֏֐-׿Ҁ-ӿ]")
_GARBLE_RATIO_THRESHOLD = 0.002  # clean PDFs ~0%; the one bad book ran ~0.88%


def _garble_ratio(text: str) -> float:
    if not text:
        return 0.0
    return len(_GARBLE_RE.findall(text)) / len(text)


def ingest_pdf(pdf_path: Path, output_path: Path) -> Path:
    heading_map = _load_output_heading_map(output_path)
    authoritative_map = _is_authoritative_heading_map(heading_map)
    text = convert_pdf_with_toc(pdf_path)
    if text is not None and _garble_ratio(text) > _GARBLE_RATIO_THRESHOLD:
        # CID-font subset with no ToUnicode map: PyMuPDF text is corrupt. Headings
        # come from the TOC (clean) but the body is unusable — markitdown wins here.
        print(f"  PyMuPDF text garbled ({_garble_ratio(text):.2%}); falling back to markitdown: {pdf_path.stem}")
        text = None
    if text is None:
        try:
            text = convert_epub(pdf_path)
        except Exception as error:
            print(f"  MarkItDown PDF fallback unavailable ({error}); using PyMuPDF layout: {pdf_path.stem}")
            text = convert_pdf_with_layout(pdf_path)
            text = clean_markdown(
                text,
                repair_extraction_artifacts=pdf_path.stem == "storytelling-with-data",
                repair_unclosed_fence=pdf_path.stem == "vector-databases-introduction",
            )
            if not authoritative_map:
                text = strip_front_back_matter(text)
            text = normalize_heading_levels(text)
        else:
            text = clean_markdown(
                text,
                repair_extraction_artifacts=pdf_path.stem == "storytelling-with-data",
                repair_unclosed_fence=pdf_path.stem == "vector-databases-introduction",
            )
            text = normalize_heading_levels(text)
    else:
        text = clean_markdown(
            text,
            repair_extraction_artifacts=pdf_path.stem == "storytelling-with-data",
            repair_unclosed_fence=pdf_path.stem == "vector-databases-introduction",
        )
        if not authoritative_map:
            text = strip_front_back_matter(text)
        text = normalize_heading_levels(text)
    if evaluate(text)["flagged"]:
        try:
            recovered = recover_pdf_headings(pdf_path, text)
            if recovered != text:
                recovered = strip_front_back_matter(recovered, recovery_pass=True)
            text = recovered
        except Exception as error:
            print(f"  PDF heading recovery unavailable ({error}): {pdf_path.stem}")
    text = _apply_output_heading_map(text, output_path, heading_map)
    if authoritative_map:
        text = _trim_to_first_map_heading(text, heading_map, output_path)
        text = _trim_to_back_matter_anchor(text, heading_map, output_path)
    output_path.write_text(text, encoding="utf-8")
    return output_path


def ingest_all() -> list[Path]:
    MARKDOWN_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    for source_dir in SOURCE_DIRS.values():
        for epub_file in sorted(source_dir.glob("*.epub")):
            stem = epub_file.stem
            if stem not in BOOKS:
                print(f"  Skipping unknown book: {stem}")
                continue
            output = MARKDOWN_DIR / f"{stem}.md"
            if output.exists():
                print(f"  Skipping (exists): {stem}")
                results.append(output)
                continue
            print(f"  Converting: {stem}")
            ingest_epub(epub_file, output)
            results.append(output)

    # PDFs from domain directories
    for domain, source_dir in SOURCE_DIRS.items():
        for pdf_file in sorted(source_dir.glob("*.pdf")):
            stem = pdf_file.stem
            if stem not in BOOKS:
                print(f"  Skipping unknown PDF: {stem}")
                continue
            output = MARKDOWN_DIR / f"{stem}.md"
            if output.exists():
                print(f"  Skipping (exists): {stem}")
                results.append(output)
                continue
            print(f"  Converting PDF: {stem}")
            try:
                ingest_pdf(pdf_file, output)
                results.append(output)
            except Exception as e:
                print(f"  ERROR converting {stem}: {e}")
                if output.exists():
                    output.unlink()  # remove partial output

    # HTML files (special case: distributed-systems-fun-profit.html)
    for domain, source_dir in SOURCE_DIRS.items():
        for html_file in sorted(source_dir.glob("*.html")):
            stem = html_file.stem
            if stem not in BOOKS:
                continue
            output = MARKDOWN_DIR / f"{stem}.md"
            if output.exists():
                print(f"  Skipping (exists): {stem}")
                results.append(output)
                continue
            print(f"  Converting HTML: {stem}")
            try:
                text = convert_epub(html_file)  # markitdown handles HTML too
                text = clean_markdown(text)
                text = normalize_heading_levels(text)
                text = _apply_output_heading_map(text, output)
                output.write_text(text, encoding="utf-8")
                results.append(output)
            except Exception as e:
                print(f"  ERROR converting {stem}: {e}")
                if output.exists():
                    output.unlink()

    # Plain markdown sources (scraped web books, pre-built sheet collections).
    # Already markdown — just normalise heading levels (like the HTML path); no
    # markitdown conversion and no front/back-matter strip (tuned for Packt PDFs).
    for source_dir in SOURCE_DIRS.values():
        for md_file in sorted(source_dir.glob("*.md")):
            stem = md_file.stem
            if stem not in BOOKS:
                continue
            output = MARKDOWN_DIR / f"{stem}.md"
            if output.exists():
                print(f"  Skipping (exists): {stem}")
                results.append(output)
                continue
            print(f"  Copying markdown: {stem}")
            text = md_file.read_text(encoding="utf-8")
            text = normalize_heading_levels(text)
            text = _apply_output_heading_map(text, output)
            output.write_text(text, encoding="utf-8")
            results.append(output)

    return results


if __name__ == "__main__":
    print("Ingesting EPUBs → markdown...")
    paths = ingest_all()
    print(f"Done. {len(paths)} files in {MARKDOWN_DIR}")
