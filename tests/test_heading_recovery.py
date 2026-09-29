import pytest

from knowledge_base import ingest
from knowledge_base.headings import (
    NavigationEntry,
    PdfLine,
    _markdown_page_spans,
    _place_pdf_candidates,
    _place_pdf_page_candidates,
    apply_heading_map,
    parse_contents_pages,
    parse_epub_navigation_documents,
    recover_epub_headings,
    suppress_pdf_artifact_headings,
)


def test_epub_navigation_prefers_the_document_with_more_entries_and_keeps_depth_and_targets():
    nav = """<?xml version="1.0"?>
    <html xmlns="http://www.w3.org/1999/xhtml"
          xmlns:epub="http://www.idpf.org/2007/ops">
      <body><nav epub:type="toc"><ol>
        <li><a href="Text/part.xhtml#part">Part One</a>
          <ol><li><a href="Text/ch01.xhtml#intro">Plain title</a></li>
               <li><a href="Text/ch02.xhtml#next">Another title</a></li></ol>
        </li>
      </ol></nav></body>
    </html>"""
    ncx = """<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/">
      <navMap><navPoint id="n1"><navLabel><text>Only NCX entry</text></navLabel>
        <content src="Text/old.xhtml#old"/>
      </navPoint></navMap>
    </ncx>"""

    entries = parse_epub_navigation_documents(nav, ncx, nav_path="EPUB/nav.xhtml")

    assert entries == [
        NavigationEntry("Part One", "EPUB/Text/part.xhtml#part", 0),
        NavigationEntry("Plain title", "EPUB/Text/ch01.xhtml#intro", 1),
        NavigationEntry("Another title", "EPUB/Text/ch02.xhtml#next", 1),
    ]


def test_epub_navigation_uses_ncx_when_nav_xhtml_is_absent():
    ncx = """<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/">
      <navMap>
        <navPoint id="n1"><navLabel><text>Opening</text></navLabel>
          <content src="chapter1.xhtml#opening"/>
          <navPoint id="n2"><navLabel><text>Details</text></navLabel>
            <content src="chapter1.xhtml#details"/></navPoint>
        </navPoint>
      </navMap>
    </ncx>"""

    entries = parse_epub_navigation_documents(None, ncx)

    assert entries == [
        NavigationEntry("Opening", "chapter1.xhtml#opening", 0),
        NavigationEntry("Details", "chapter1.xhtml#details", 1),
    ]


def test_epub_target_matching_ignores_inline_forward_cross_reference():
    body = "The source [link](Text/chapter.xhtml#target) is discussed in this paragraph."
    entry = NavigationEntry("Target section", "EPUB/Text/chapter.xhtml#target", 0)

    result = recover_epub_headings(body, [entry])

    assert result == body


def test_epub_bare_numbered_navigation_titles_match_unnumbered_body_titles():
    toc = (
        "1. [Why care about ethics?](ch0001.xlink.html)\n\n"
        "2. [Ethical approaches](ch0002.xlink.html)\n\n"
    )
    text = (
        toc
        + "Why Care About Ethics?\nChapter one begins.\n\n"
        + "Ethical Approaches\nChapter two begins.\n"
    )
    entries = [
        NavigationEntry("1 Why Care About Ethics?", "Text/ch0001.xlink.html", 0),
        NavigationEntry("2 Ethical Approaches", "Text/ch0002.xlink.html", 0),
    ]

    result = recover_epub_headings(text, entries)

    assert result.splitlines() == [
        "1. [Why care about ethics?](ch0001.xlink.html)",
        "",
        "2. [Ethical approaches](ch0002.xlink.html)",
        "",
        "## 1 Why Care About Ethics?",
        "Why Care About Ethics?",
        "Chapter one begins.",
        "",
        "## 2 Ethical Approaches",
        "Ethical Approaches",
        "Chapter two begins.",
    ]


def test_epub_forward_cross_reference_does_not_steal_later_chapter_heading():
    forward_reference = "As discussed in [Chapter 2](Text/ch02.xhtml#ch2), this is important."
    text = (
        "# Chapter 1\n\n"
        "Here is the start of chapter 1.\n"
        f"{forward_reference}\n"
        "More text in chapter 1.\n\n"
        "# Chapter 2\n\n"
        "Here is the actual chapter 2.\n"
    )
    entries = [
        NavigationEntry("Chapter 1", "Text/ch01.xhtml#intro", 0),
        NavigationEntry("Chapter 2", "Text/ch02.xhtml#ch2", 0),
    ]

    result = recover_epub_headings(text, entries)

    lines = result.splitlines()
    assert lines.index(forward_reference) > lines.index("## Chapter 1")
    assert lines.index("## Chapter 2") > lines.index(forward_reference)
    assert sum(line == "## Chapter 2" for line in lines) == 1


def test_epub_duplicate_titles_stay_with_their_chapter_and_do_not_stack():
    text = (
        "# Book Title\n\n"
        "## Chapter 1: Introduction\n\n"
        "We begin here.\n"
        "In summary we can see that this works.\n\n"
        "More prose in chapter 1.\n\n"
        "## Chapter 2: Methods\n\n"
        "Here are the methods.\n\n"
        "### Summary\n\n"
        "Summary of methods.\n\n"
        "## Chapter 3: Results\n\n"
        "Here are results.\n"
    )
    entries = [
        NavigationEntry("Chapter 1: Introduction", "ch1.xhtml", 0),
        NavigationEntry("Summary", "ch1.xhtml#summary", 1),
        NavigationEntry("Chapter 2: Methods", "ch2.xhtml", 0),
        NavigationEntry("Summary", "ch2.xhtml#summary", 1),
        NavigationEntry("Chapter 3: Results", "ch3.xhtml", 0),
    ]

    result = recover_epub_headings(text, entries)

    lines = result.splitlines()
    chapter_two = lines.index("## Chapter 2: Methods")
    summary = lines.index("### Summary")
    chapter_three = lines.index("## Chapter 3: Results")
    assert chapter_two < summary < chapter_three
    assert sum(line == "### Summary" for line in lines) == 1


def test_epub_fragmentless_navigation_target_matches_the_chapter_file():
    entry = NavigationEntry("Chapter title", "EPUB/Text/chapter.xhtml", 0)
    text = "## [Old label](EPUB/Text/chapter.xhtml#section)\n\nChapter body.\n"

    result = recover_epub_headings(text, [entry])

    assert result.splitlines() == ["## Chapter title", "", "Chapter body."]


def test_epub_recovery_strips_link_markup_from_existing_heading():
    entry = NavigationEntry("Target section", "chapter.xhtml#target", 0)

    result = recover_epub_headings(
        "#### [Old label](chapter.xhtml#target)\n\nSection body.\n", [entry]
    )

    assert result.splitlines() == ["## Target section", "", "Section body."]


def test_epub_title_prefix_match_preserves_the_body_line():
    body = "Scope covers all services and their dependencies in this section."
    entry = NavigationEntry("Scope", "", 0)

    result = recover_epub_headings(body, [entry])

    assert result.splitlines() == ["## Scope", body]


def test_contents_parser_reads_dotted_pages_and_titles_followed_by_page_number():
    pages = [
        """CONTENTS

        Preface ................................ 5
        Methods and practice
        13
        Findings . . . . . . . . . . . . . . . 21
        """
    ]

    assert parse_contents_pages(pages) == [
        ("Preface", 5),
        ("Methods and practice", 13),
        ("Findings", 21),
    ]


def test_pdf_contents_match_stays_on_the_physical_body_page_span():
    contents_anchor = "The catalog page contains a distinctive and lengthy navigation summary phrase"
    body_anchor = "The body page begins with a distinctive and lengthy introduction for readers"
    source_pages = [
        [PdfLine(1, "Section One"), PdfLine(1, contents_anchor)],
        [PdfLine(2, "Section One"), PdfLine(2, body_anchor)],
    ]
    markdown = (
        "# Contents\n\n"
        "Section One ..... 1\n"
        f"{contents_anchor}.\n\n"
        "Section One\n"
        f"{body_anchor}.\n"
    )
    spans = _markdown_page_spans(markdown, source_pages)

    result = _place_pdf_page_candidates(markdown, [("Section One", 2, 2)], spans)

    result_lines = result.splitlines()
    assert result_lines[2] == "Section One ..... 1"
    assert result_lines[5] == "## Section One"


def test_pdf_outline_prefix_match_inserts_heading_and_preserves_body_line():
    body = "Introduction to the methodology is presented here in this sentence.\n\nNext paragraph.\n"

    result = _place_pdf_candidates(body, [("Introduction", 2)])

    assert result.splitlines() == [
        "## Introduction",
        "Introduction to the methodology is presented here in this sentence.",
        "",
        "Next paragraph.",
    ]


def test_pdf_page_prefix_match_inserts_heading_and_preserves_body_line():
    body = "Introduction to the methodology is presented here in this sentence.\nBody follows.\n"

    result = _place_pdf_page_candidates(
        body, [("Introduction", 2, 1)], {1: (0, 2)}
    )

    assert result.splitlines() == [
        "## Introduction",
        "Introduction to the methodology is presented here in this sentence.",
        "Body follows.",
    ]


def test_pdf_suppression_demotes_repeated_headers_and_numbered_footnote_heading():
    markdown_parts = []
    pdf_lines = []
    for page in range(1, 11):
        header = "BARGAINING" if page % 2 else "ADVANTAGE"
        markdown_parts.extend(
            [f"# {header}", f"Narrative body for physical page {page}."]
        )
        pdf_lines.extend(
            [
                PdfLine(page, header, y_ratio=0.04, font_size=16.0),
                PdfLine(page, f"Narrative body for physical page {page}.", y_ratio=0.3),
            ]
        )

    footnote = "12. this note explains the method in more detail and continues as prose"
    markdown_parts.extend(
        [f"# {footnote}", "## Chapter 1: A sound section heading", "Chapter body."]
    )
    pdf_lines.extend(
        [
            PdfLine(3, footnote, y_ratio=0.97, font_size=9.0),
            PdfLine(3, "Chapter 1: A sound section heading", y_ratio=0.22, font_size=18.0),
            PdfLine(3, "Chapter body.", y_ratio=0.35, font_size=12.0),
        ]
    )

    result = suppress_pdf_artifact_headings(
        "\n\n".join(markdown_parts), pdf_lines, body_size=12.0, page_count=10
    )
    heading_lines = [line for line in result.splitlines() if line.startswith("#")]

    assert "BARGAINING" in result
    assert "ADVANTAGE" in result
    assert footnote in result
    assert not any("BARGAINING" in line or "ADVANTAGE" in line for line in heading_lines)
    assert not any(footnote in line for line in heading_lines)
    assert "## Chapter 1: A sound section heading" in heading_lines


def test_pdf_suppression_tracks_fence_character_and_length():
    markdown = (
        "# Header 1\n"
        "Body 1.\n\n"
        "````markdown\n"
        "# BARGAINING\n"
        "To start a Python code block, write:\n"
        "```python\n"
        "and then write code.\n"
        "````\n\n"
        "# BARGAINING\n"
        "Repeated page header that should be suppressed.\n"
    )
    pdf_lines = [
        PdfLine(page, "BARGAINING", y_ratio=0.05, font_size=14.0)
        for page in range(1, 4)
    ]

    result = suppress_pdf_artifact_headings(
        markdown, pdf_lines, body_size=12.0, page_count=3
    )

    assert "````markdown\n# BARGAINING\n" in result
    assert result.count("# BARGAINING") == 1
    assert "\nBARGAINING\nRepeated page header" in result


def test_heading_map_inserts_before_anchors_preserves_body_and_reports_unmatched_titles():
    body = (
        "Front matter remains exactly as written.\n\n"
        "The system scope begins with one clear question.\n\n"
        "More detail follows in the next paragraph.\n"
    )
    entries = [
        {"title": "Scope", "level": 2, "anchor": "the system scope begins"},
        {"title": "Detail", "level": 3, "anchor": "More detail follows"},
        {"title": "Missing section", "level": 2, "anchor": "This anchor is not present"},
    ]

    result, unmatched = apply_heading_map(body, entries)

    result_lines = result.splitlines()
    scope_body_index = result_lines.index("The system scope begins with one clear question.")
    detail_body_index = result_lines.index("More detail follows in the next paragraph.")
    assert result_lines[scope_body_index - 1] == "## Scope"
    assert result_lines[detail_body_index - 1] == "### Detail"
    assert unmatched == ["Missing section"]
    assert "\n".join(
        line for line in result_lines if not line.startswith("#")
    ) == "\n".join(body.splitlines())


def test_heading_map_skips_anchors_inside_fenced_code():
    body = (
        "# Book Title\n\n"
        "Introduction text.\n\n"
        "```python\n"
        "# System initialization\n"
        "def init():\n"
        "    print('starting')\n"
        "```\n\n"
        "The system initialization continues in real text.\n"
    )
    entries = [
        {"title": "Initialization", "level": 2, "anchor": "def init"},
        {"title": "Real initialization", "level": 2, "anchor": "The system initialization continues"},
    ]

    result, unmatched = apply_heading_map(body, entries)

    assert unmatched == ["Initialization"]
    assert "```python\n# System initialization\ndef init():" in result
    assert "## Initialization\ndef init():" not in result
    assert "## Real initialization\nThe system initialization continues in real text." in result


def test_heading_map_reports_out_of_order_and_missing_entries_as_unmatched():
    body = "First section body text.\n\nSecond section body text.\n"
    entries = [
        {"title": "Second Section", "level": 2, "anchor": "Second section body"},
        {"title": "First Section", "level": 2, "anchor": "First section body"},
        {"title": "Missing Section", "level": 2, "anchor": "Anchor absent from this text"},
    ]

    result, unmatched = apply_heading_map(body, entries)

    assert "## Second Section\nSecond section body text." in result
    assert unmatched == ["First Section", "Missing Section"]


def test_ingest_epub_keeps_original_text_when_heading_recovery_raises(tmp_path, monkeypatch, capsys):
    source_text = "# Book title\n\nThe original extracted text remains intact.\n"
    epub_path = tmp_path / "broken-navigation.epub"
    output_path = tmp_path / "book.md"

    monkeypatch.setattr(ingest, "convert_epub", lambda _path: source_text)
    monkeypatch.setattr(ingest, "clean_markdown", lambda text, **_kwargs: text)
    monkeypatch.setattr(
        ingest, "reconstruct_epub_toc", lambda _path, text, allow_plain_labels=False: text
    )
    monkeypatch.setattr(ingest, "strip_front_back_matter", lambda text: text)
    monkeypatch.setattr(ingest, "normalize_heading_levels", lambda text: text)
    monkeypatch.setattr(ingest, "evaluate", lambda _text: {"flagged": True})
    monkeypatch.setattr(ingest, "_epub_navigation_entries", lambda _path: [])
    monkeypatch.setattr(ingest, "_epub_book_title", lambda _path: None)
    monkeypatch.setattr(
        ingest,
        "recover_epub_headings",
        lambda *_args: (_ for _ in ()).throw(ValueError("bad navigation")),
    )
    monkeypatch.setattr(
        ingest, "_apply_output_heading_map", lambda text, _path, _map=None: text
    )

    result_path = ingest.ingest_epub(epub_path, output_path)

    assert result_path == output_path
    assert output_path.read_text(encoding="utf-8") == source_text
    assert "EPUB heading recovery unavailable (bad navigation): broken-navigation" in capsys.readouterr().out


@pytest.mark.parametrize("kind", ["epub", "pdf"])
@pytest.mark.parametrize("recovery_changes_text", [False, True])
def test_heading_recovery_reapplies_matter_rules_only_when_text_changes(
    kind, recovery_changes_text, tmp_path, monkeypatch
):
    body = "\n".join(f"Chapter body line {i}." for i in range(40))
    source_text = f"# Book title\n\n# Chapter 1 Opening\n{body}\n"
    recovered_text = (
        f"# Book title\n\n## Copyright\nCopyright block.\n\n"
        f"# Chapter 1 Opening\n{body}\n"
    )
    output_path = tmp_path / "book.md"
    initial_clean = ingest.strip_front_back_matter(source_text)
    recovery_result = recovered_text if recovery_changes_text else initial_clean
    strip_calls = []
    real_strip = ingest.strip_front_back_matter

    def track_strip(text, **kwargs):
        strip_calls.append(text)
        return real_strip(text, **kwargs)

    monkeypatch.setattr(ingest, "_load_output_heading_map", lambda _path: None)
    monkeypatch.setattr(ingest, "_apply_output_heading_map", lambda text, *_args: text)
    monkeypatch.setattr(ingest, "clean_markdown", lambda text, **_kwargs: text)
    monkeypatch.setattr(ingest, "normalize_heading_levels", lambda text: text)
    monkeypatch.setattr(ingest, "strip_front_back_matter", track_strip)
    monkeypatch.setattr(ingest, "evaluate", lambda _text: {"flagged": True})

    if kind == "epub":
        monkeypatch.setattr(ingest, "convert_epub", lambda _path: source_text)
        monkeypatch.setattr(
            ingest, "reconstruct_epub_toc", lambda _path, text, allow_plain_labels=False: text
        )
        monkeypatch.setattr(ingest, "_epub_navigation_entries", lambda _path: [])
        monkeypatch.setattr(ingest, "_epub_book_title", lambda _path: None)
        monkeypatch.setattr(ingest, "recover_epub_headings", lambda *_args: recovery_result)
        ingest.ingest_epub(tmp_path / "book.epub", output_path)
    else:
        monkeypatch.setattr(ingest, "convert_pdf_with_toc", lambda _path: source_text)
        monkeypatch.setattr(ingest, "recover_pdf_headings", lambda *_args: recovery_result)
        ingest.ingest_pdf(tmp_path / "book.pdf", output_path)

    result = output_path.read_text(encoding="utf-8")
    assert len(strip_calls) == (2 if recovery_changes_text else 1)
    if recovery_changes_text:
        assert "Copyright block" not in result
        assert result.startswith("# Chapter 1 Opening")
    else:
        assert result == initial_clean


def test_recovery_front_matter_cut_uses_first_heading_after_front_sequence():
    recovered = (
        "# MEDDICC\n\nCopyright © 2020 Publisher\n\n"
        "## Acknowledgments\nThanks.\n\n"
        "## Foreword\nForeword text.\n\n"
        "## Preface\nPreface text.\n\n"
        "## Introduction\nMain text starts here.\n"
    )

    original_behavior = ingest.strip_front_back_matter(recovered)
    recovery_behavior = ingest.strip_front_back_matter(recovered, recovery_pass=True)

    assert original_behavior.startswith("# MEDDICC")
    assert recovery_behavior.startswith("# MEDDICC\n\n## Introduction")
    assert "Main text starts here." in recovery_behavior
    assert "Copyright © 2020 Publisher" not in recovery_behavior


def test_replacement_heading_map_demotes_junk_and_keeps_book_title_and_fenced_code():
    body = (
        "# Book title\n\n"
        "# 16 In our experience, an average software engineer works this way\n"
        "The following paragraph remains exactly as extracted.\n\n"
        "## 3.For passwords that you do not need to remember use this approach\n"
        "A second body paragraph remains exactly as extracted.\n\n"
        "### NG\n"
        "An OCR fragment is followed by its original body line.\n\n"
        "```markdown\n"
        "# This heading is code content\n"
        "```\n"
    )
    heading_map = {
        "replace_existing": True,
        "entries": [
            {"title": "Experience note", "level": 2, "anchor": "16 In our experience"},
            {"title": "Password guidance", "level": 3, "anchor": "3.For passwords"},
            {"title": "OCR note", "level": 2, "anchor": "NG"},
        ],
    }

    result, unmatched = apply_heading_map(body, heading_map)

    assert unmatched == []
    assert result == (
        "# Book title\n\n"
        "## Experience note\n"
        "16 In our experience, an average software engineer works this way\n"
        "The following paragraph remains exactly as extracted.\n\n"
        "### Password guidance\n"
        "3.For passwords that you do not need to remember use this approach\n"
        "A second body paragraph remains exactly as extracted.\n\n"
        "## OCR note\n"
        "NG\n"
        "An OCR fragment is followed by its original body line.\n\n"
        "```markdown\n"
        "# This heading is code content\n"
        "```\n"
    )


def test_authoritative_map_skips_a_contents_row_when_placing_its_first_heading():
    body = (
        "# How to Read a Paper\n\n"
        "Why read papers at all?\t\n1\n\n"
        "Why read papers at all?\nChapter 1\n"
        "The actual chapter body starts here.\n"
    )
    heading_map = {
        "replace_existing": True,
        "entries": [
            {"title": "Why read papers at all?", "level": 2, "anchor": "Why read papers at all?"},
        ],
    }

    result, unmatched = apply_heading_map(body, heading_map)

    lines = result.splitlines()
    body_title_positions = [
        i for i, line in enumerate(lines) if line == "Why read papers at all?"
    ]
    assert unmatched == []
    assert len(body_title_positions) == 1
    assert lines.index("## Why read papers at all?") == body_title_positions[0] - 1
    assert lines.index("## Why read papers at all?") > lines.index("1")


def test_authoritative_map_content_start_keeps_chapter_one_and_discards_prefix(tmp_path):
    output_path = tmp_path / "how-to-read-a-paper.md"
    heading_map = {
        "replace_existing": True,
        "entries": [
            {"title": "Chapter 1: Opening", "level": 2, "anchor": "The first chapter body"},
        ],
    }
    extracted = (
        "# How to Read a Paper\n\n"
        "# Contents\n"
        "A contents row that points to later material.\n\n"
        "Preface-only text.\n\n"
        "Chapter 1: Opening\n"
        "The first chapter body starts here and remains in the output.\n"
    )

    mapped, unmatched = apply_heading_map(extracted, heading_map)
    result = ingest._trim_to_first_map_heading(mapped, heading_map, output_path)

    assert unmatched == []
    assert result.startswith("# How to Read a Paper\n\n## Chapter 1: Opening\n")
    assert "Preface-only text" not in result
    assert "The first chapter body starts here" in result


def test_pdf_ingest_without_map_keeps_the_existing_front_matter_cut(tmp_path, monkeypatch):
    source_path = tmp_path / "no-map-source.pdf"
    output_path = tmp_path / "no-map-output.md"
    monkeypatch.setattr(
        ingest,
        "_load_output_heading_map",
        lambda _path: None,
    )
    monkeypatch.setattr(
        ingest,
        "convert_pdf_with_toc",
        lambda _path: "## Preface\nFront matter text.\n\n## Chapter 1 Opening\nChapter one body.\n",
    )
    monkeypatch.setattr(ingest, "evaluate", lambda _text: {"flagged": False})

    ingest.ingest_pdf(source_path, output_path)

    result = output_path.read_text(encoding="utf-8")
    assert "Front matter text" not in result
    assert "Chapter one body" in result
    assert result.lstrip().startswith("# Chapter 1 Opening")


def test_replacement_heading_map_demotes_existing_title_when_map_has_h1():
    body = "# Old title\n\n## Existing section\nBody starts here.\n"
    heading_map = {
        "replace_existing": True,
        "entries": [
            {"title": "Mapped title", "level": 1, "anchor": "Old title"},
        ],
    }

    result, unmatched = apply_heading_map(body, heading_map)

    assert unmatched == []
    assert result.splitlines() == [
        "# Mapped title",
        "Old title",
        "",
        "Existing section",
        "Body starts here.",
    ]


def test_replacement_heading_map_preserves_crlf_body_bytes():
    body = "# Book title\r\n\r\n## Junk heading\r\nBody stays byte-identical.\r\n"
    heading_map = {
        "replace_existing": True,
        "entries": [
            {"title": "Mapped heading", "level": 2, "anchor": "Junk heading"},
        ],
    }

    result, unmatched = apply_heading_map(body, heading_map)

    assert unmatched == []
    assert result == (
        "# Book title\r\n\r\n"
        "## Mapped heading\r\n"
        "Junk heading\r\n"
        "Body stays byte-identical.\r\n"
    )


def test_list_heading_map_does_not_demote_existing_headings():
    body = "# Existing title\n\n## Existing section\nBody starts here.\n"
    entries = [{"title": "Mapped section", "level": 3, "anchor": "Body starts here"}]

    result, unmatched = apply_heading_map(body, entries)

    assert unmatched == []
    assert result.splitlines() == [
        "# Existing title",
        "",
        "## Existing section",
        "### Mapped section",
        "Body starts here.",
    ]
