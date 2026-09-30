from __future__ import annotations

import copy
import json

import pymupdf

from knowledge_base.philosophy import chunking
from knowledge_base.philosophy.alignment import Section, aligned_language_set
from knowledge_base.philosophy.sectioning import (
    _Line, _cells, _contents_pages, _merge_lines, _normalize_chinese_spacing,
    _toc_anchors, split_sections, web_shell_reason,
)
from scripts.ingest_philosophy_b import compose_registry


def _save_pdf(path, pages: list[list[tuple[str, str, float, float, float]]], toc=None) -> None:
    doc = pymupdf.open()
    for page_items in pages:
        page = doc.new_page(width=600, height=800)
        for text, font, size, x, y in page_items:
            page.insert_text((x, y), text, fontname=font, fontsize=size)
    if toc:
        doc.set_toc(toc)
    doc.save(path)
    doc.close()


def test_splitter_uses_pdf_outline_and_drops_contents_page(tmp_path) -> None:
    path = tmp_path / "outline.pdf"
    _save_pdf(path, [
        [("Contents", "helv", 16, 50, 70), ("Alpha ........ 2", "helv", 10, 50, 110),
         ("Beta ........ 3", "helv", 10, 50, 140)],
        [("Alpha", "helv", 16, 50, 70), ("Alpha body paragraph.", "helv", 10, 50, 110)],
        [("Beta", "helv", 16, 50, 70), ("Beta body paragraph.", "helv", 10, 50, 110)],
    ], [[1, "Alpha", 2], [1, "Beta", 3]])

    sections, info = split_sections(path, "en", document_title="Test Work")

    assert [section.section_title for section in sections] == ["Alpha", "Beta"]
    assert "Contents" not in " ".join(section.text for section in sections)
    assert "Alpha body" in sections[0].text
    assert "Beta body" in sections[1].text
    assert info.outline_used is True
    assert info.contents_pages_removed == 1


def test_splitter_finds_document_headings_without_outline(tmp_path) -> None:
    path = tmp_path / "headings.pdf"
    _save_pdf(path, [
        [("Chapter 1", "hebo", 18, 50, 70), ("First chapter text.", "helv", 10, 50, 110)],
        [("Chapter 2", "hebo", 18, 50, 70), ("Second chapter text.", "helv", 10, 50, 110)],
    ])

    sections, _ = split_sections(path, "en", document_title="Test Work")

    assert [section.section_title for section in sections] == ["Chapter 1", "Chapter 2"]
    assert "First chapter text" in sections[0].text
    assert "Second chapter text" in sections[1].text


def test_splitter_removes_a_single_line_contents_list(tmp_path) -> None:
    path = tmp_path / "single-line-contents.pdf"
    _save_pdf(path, [
        [("Opening section ........ 2 Second section ........ 3 Third section ........ 4 Fourth section ........ 5",
          "helv", 10, 50, 70)],
        [("Opening section", "hebo", 16, 50, 70), ("Opening body text.", "helv", 10, 50, 110)],
        [("Second section", "hebo", 16, 50, 70), ("Second body text.", "helv", 10, 50, 110)],
        [("Third section", "hebo", 16, 50, 70), ("Third body text.", "helv", 10, 50, 110)],
        [("Fourth section", "hebo", 16, 50, 70), ("Fourth body text.", "helv", 10, 50, 110)],
    ])

    sections, info = split_sections(path, "en", document_title="Test Work")

    assert info.contents_pages_removed == 1
    assert [section.section_title for section in sections] == [
        "Opening section", "Second section", "Third section", "Fourth section",
    ]


def test_splitter_drops_undotted_contents_list_before_article_text(tmp_path) -> None:
    path = tmp_path / "undotted-contents.pdf"
    lines = [
        "First lecture", "January 1, 2000", "Li Hongzhi", "Second lecture",
        "March 3, 2001", "Li Hongzhi",
        "The actual article begins here and continues in a long paragraph with enough text to be unmistakably prose.",
    ]
    _save_pdf(path, [[(line, "helv", 10, 50, 70 + index * 28) for index, line in enumerate(lines)]])

    sections, _ = split_sections(path, "en", document_title="Mixed Edition")

    assert len(sections) == 1
    assert sections[0].text.startswith("The actual article begins here")
    assert "First lecture" not in sections[0].text


def test_contents_continuation_requires_list_evidence() -> None:
    def page(texts: list[str]) -> list[_Line]:
        return [_Line(text, 10 + index * 12, 0, 20 + index * 12, 100, 10, False)
                for index, text in enumerate(texts)]

    contents_first = page(["目錄", "Lecture One", "...............", "Lecture Two", "..............."])
    contents_next = page(["Lecture Three", "...............", "Lecture Four", "...............",
                          "Lecture Five", "...............", "Lecture Six", "..............."])
    actual_poem = page(["Steadfast", "The first line of a poem", "The second line of a poem",
                        "Third line follows", "Fourth line follows", "Fifth line follows",
                        "Sixth line follows", "Seventh line follows"])

    assert _contents_pages([contents_first, contents_next, actual_poem], 90) == [True, True, False]


def test_contents_continuation_accepts_unnumbered_title_list_only() -> None:
    def page(texts: list[str]) -> list[_Line]:
        return [_Line(text, 10 + index * 12, 0, 20 + index * 12, 100, 10, False)
                for index, text in enumerate(texts)]

    first = page(["Mục lục", "Giàu mà có đức", "Rộng lớn"])
    continuation = page([
        "Chân tu", "Minh trí", "Ngộ", "Vì sao không được thấy", "Học Pháp",
        "Phụ đạo như thế nào", "Khung", "Cảnh giới", "Thế nào là Không", "Kiên định",
        "Thánh giả", "Bái Sư",
    ])
    article = page([
        "Giàu mà có đức", "Người xưa dạy tiền là vật ngoại thân.",
        "Ai ai cũng biết và ai ai cũng truy cầu.", "Kẻ tráng niên vì thoả chữ dục.",
        "Đàn bà đẹp vì vinh hoa.", "Người già vì giải quyết vấn đề cuối đời.",
        "Kẻ trí vì danh tiếng.", "Quan lại vì làm tốt chức trách.", "Đều truy cầu nó.",
    ])

    assert _contents_pages([first, continuation, article], 70) == [True, True, False]


def test_toc_anchor_matches_accented_heading_and_rejects_prefix_word() -> None:
    text = "Ngoại trừ chấp trước hơn nữa.\n\nGiàu mà có đức\nBody starts here.\n\nRộng lớn\nMore body."

    anchors = _toc_anchors(text, ["Ngộ", "Giàu mà có đức", "Rộng lớn"])

    assert [title for _, title in anchors] == ["Giàu mà có đức", "Rộng lớn"]


def test_contents_and_revision_tail_are_removed() -> None:
    def page(texts: list[str]) -> list[_Line]:
        return [_Line(text, 10 + index * 12, 0, 20 + index * 12, 100, 10, False)
                for index, text in enumerate(texts)]

    pages = [[] for _ in range(7)]
    pages += [
        page(["各地講法一", "李洪志"]),
        page(["更新日期更新内容", "格式说明：页数-行数", "3-19"]),
        page(["简体字《各地讲法一》网络版更新备注", "根据新版校对改字。"]),
    ]

    flags = _contents_pages(pages, 100)

    assert flags[:7] == [False] * 7
    assert flags[7:] == [True, True, True]


def test_splitter_keeps_unstructured_document_as_one_section(tmp_path) -> None:
    path = tmp_path / "plain.pdf"
    _save_pdf(path, [[("A plain title", "hebo", 16, 50, 70),
                      ("One continuous article with no internal headings.", "helv", 10, 50, 110)]])

    sections, _ = split_sections(path, "en", document_title="Plain Work")

    assert len(sections) == 1
    assert sections[0].section_title == "Plain Work"
    assert "continuous article" in sections[0].text


def test_splitter_reads_two_up_logical_page_order(tmp_path) -> None:
    path = tmp_path / "two-up.pdf"
    _save_pdf(path, [[
        ("2", "helv", 10, 40, 40), ("Second logical page", "helv", 12, 40, 80),
        ("second column line two", "helv", 10, 40, 120),
        ("1", "helv", 10, 340, 40), ("First logical page", "helv", 12, 340, 80),
        ("first column line two", "helv", 10, 340, 120),
    ]])

    sections, _ = split_sections(path, "zh-Hans", "2合1", document_title="Two Up")

    assert len(sections) == 1
    assert sections[0].text.index("First logical page") < sections[0].text.index("Second logical page")
    assert sections[0].text.index("first column line two") < sections[0].text.index("Second logical page")


def test_rotated_two_up_cells_keep_their_own_column_lines() -> None:
    # The coordinates mirror a 90-degree turned two-up sheet: each printed
    # page occupies a separate y band, while text lines advance along x.
    lines = [
        _Line("second one", 500, 20, 520, 790, 10, False),
        _Line("first one", 80, 20, 100, 790, 10, False),
        _Line("second two", 500, 40, 520, 790, 10, False),
        _Line("first two", 80, 40, 100, 790, 10, False),
    ]

    cells = _cells(lines, pymupdf.Rect(0, 0, 600, 800), "2合1", 90)

    assert len(cells) == 2
    assert [line.text for line in cells[0]] == ["first one", "first two"]
    assert [line.text for line in cells[1]] == ["second one", "second two"]


def test_splitter_reads_rotated_two_up_pdf_in_printed_page_order(tmp_path) -> None:
    path = tmp_path / "rotated-two-up.pdf"
    doc = pymupdf.open()
    page = doc.new_page(width=600, height=800)
    for text, y in [
        ("2", 120), ("Second logical page", 140), ("second column body", 160),
        ("1", 530), ("First logical page", 550), ("first column body", 570),
    ]:
        page.insert_text((50, y), text, fontsize=12, rotate=90)
    page.set_rotation(90)
    doc.save(path)
    doc.close()

    sections, _ = split_sections(path, "en", "2合1", document_title="Two Up")

    text = sections[0].text
    assert text.index("First logical page") < text.index("first column body")
    assert text.index("first column body") < text.index("Second logical page")
    assert text.index("Second logical page") < text.index("second column body")


def test_vertical_writing_rebuilds_whole_columns_in_reading_order() -> None:
    # Coordinates mirror a rotated vertical CJK page: y selects a column and x
    # advances from its top to its bottom. Columns are read right to left.
    lines = [
        _Line("以", 100, 30, 115, 45, 15, False, 1),
        _Line("經", 200, 10, 215, 25, 15, False, 1),
        _Line("師", 100, 10, 115, 25, 15, False, 1),
        _Line("文", 200, 30, 215, 45, 15, False, 1),
        _Line("可", 100, 20, 115, 35, 15, False, 1),
    ]

    merged = _merge_lines(lines, rotation=90)

    assert [line.text for line in merged] == ["師可以", "經文"]


def test_splitter_removes_letter_spacing_between_chinese_characters(tmp_path) -> None:
    path = tmp_path / "letter-spaced.pdf"
    _save_pdf(path, [[("師 ： 可 以 這 個 經 文。", "china-s", 12, 50, 100)]])

    sections, _ = split_sections(path, "zh-Hant", document_title="測試文章")

    assert len(sections) == 1
    assert "師：可以這個經文。" in sections[0].text


def test_letter_spaced_vertical_page_normalizes_titles_and_body(tmp_path) -> None:
    path = tmp_path / "vertical-letter-spaced.pdf"
    doc = pymupdf.open()
    page = doc.new_page(width=600, height=800)
    page.insert_text((300, 180), "修 ： 煉 者 心 篤 圓 滿。", fontsize=12,
                     fontname="china-s", rotate=90)
    page.set_rotation(90)
    doc.save(path)
    doc.close()

    sections, _ = split_sections(path, "zh-Hant", document_title="測試文章")

    assert len(sections) == 1
    assert "修：煉者心篤圓滿" in _normalize_chinese_spacing(sections[0].text)


def test_splitter_ignores_wrapped_book_title_and_contents_outline(tmp_path) -> None:
    path = tmp_path / "wrapped-title.pdf"
    doc = pymupdf.open()
    cover = doc.new_page(width=600, height=800)
    cover.insert_text((50, 70), "Collected Teachings Given Around the World,", fontname="hebo", fontsize=18)
    cover.insert_text((50, 98), "Volume I", fontname="hebo", fontsize=18)
    contents = doc.new_page(width=600, height=800)
    contents.insert_text((50, 70), "CONTENTS", fontname="hebo", fontsize=16)
    contents.insert_text((50, 110), "Talk One ........ 3", fontname="helv", fontsize=10)
    contents.insert_text((50, 140), "Talk Two ........ 4", fontname="helv", fontsize=10)
    one = doc.new_page(width=600, height=800)
    one.insert_text((50, 70), "Talk One", fontname="hebo", fontsize=16)
    one.insert_text((50, 110), "First lecture body text has enough words to be ordinary article prose.", fontsize=10)
    two = doc.new_page(width=600, height=800)
    two.insert_text((50, 70), "Talk Two", fontname="hebo", fontsize=16)
    two.insert_text((50, 110), "Second lecture body text has enough words to be ordinary article prose.", fontsize=10)
    doc.set_toc([
        [1, "Collected Teachings Given Around the World,", 1], [1, "Volume I", 1],
        [1, "CONTENTS", 2], [1, "Talk One", 3], [1, "Talk Two", 4],
    ])
    doc.save(path)
    doc.close()

    sections, _ = split_sections(
        path, "en", document_title="Collected Teachings Given Around the World, Volume I",
    )

    assert [section.section_title for section in sections] == ["Talk One", "Talk Two"]
    assert all("Collected Teachings" not in section.section_title for section in sections)


def test_glossary_bullets_do_not_become_section_titles(tmp_path) -> None:
    path = tmp_path / "glossary.pdf"
    _save_pdf(path, [
        [("Lecture 1", "hebo", 18, 50, 70), ("The first lecture body has a useful amount of prose.", "helv", 10, 50, 110),
         ("▪ glossary entry one", "hebo", 18, 50, 180), ("• glossary entry two", "hebo", 18, 50, 220)],
        [("Lecture 2", "hebo", 18, 50, 70), ("The second lecture body also has a useful amount of prose.", "helv", 10, 50, 110)],
    ])

    sections, _ = split_sections(path, "en", document_title="Test Work")

    assert [section.section_title for section in sections] == ["Lecture 1", "Lecture 2"]


def test_chunk_writer_never_emits_heading_only_parents_or_children(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(chunking, "MARKDOWN_DIR", tmp_path / "markdown")
    monkeypatch.setattr(chunking, "CHUNKS_DIR", tmp_path / "chunks")
    body = "\n\n".join(["### Subsection\n\n" + ("substantive body text. " * 180)] * 8)

    _, chunks_path, _ = chunking.write_work_chunks(
        work_id="chunk-fixture", lang="en", work_group="chunk-fixture", title="Fixture",
        sections=[Section("chunk-fixture-s01", "Fixture title", body)], edition="test",
    )
    data = json.loads(chunks_path.read_text())

    assert data["parents"]
    assert data["children"]
    assert all(not (child["text"].startswith("# ") and len(child["text"].splitlines()) == 1)
               for child in data["children"])
    assert all("\n\n" in parent["text"] for parent in data["parents"])


def test_chunk_writer_keeps_a_long_section_title_with_body(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(chunking, "MARKDOWN_DIR", tmp_path / "markdown")
    monkeypatch.setattr(chunking, "CHUNKS_DIR", tmp_path / "chunks")
    title = "Long title " * 24
    _, chunks_path, _ = chunking.write_work_chunks(
        work_id="long-title-fixture", lang="en", work_group="long-title-fixture", title="Fixture",
        sections=[Section("long-title-fixture-s01", title, "Substantive body paragraph. " * 35)],
        edition="test",
    )
    data = json.loads(chunks_path.read_text())

    assert data["children"]
    assert data["children"][0]["text"].startswith("# long-title-fixture-s01")
    assert "Substantive body paragraph" in data["children"][0]["text"]
    assert all(len([line for line in child["text"].splitlines() if line.strip()]) > 1
               for child in data["children"] if child["text"].startswith("# "))


def test_rotated_two_up_lines_follow_visual_reading_order() -> None:
    lines = [
        _Line("third", 700, 30, 730, 780, 10, False),
        _Line("first", 500, 10, 530, 780, 10, False),
        _Line("second", 400, 20, 430, 780, 10, False),
    ]

    merged = _merge_lines(lines, rotation=90)

    assert [line.text for line in merged] == ["first", "second", "third"]


def test_shell_check_uses_body_and_preserves_short_chinese_article() -> None:
    shell = """Gửi các đệ tử Đại Pháp tham gia Pháp hội Đài Loan
Bài viết của Sư phụ Lý Hồng Chí
Bản dịch Tiếng Việt.
Bản dịch song ngữ Trung Việt (chỉ để tham khảo).
Lưu ý: Đây là bản draft 0. Đăng ngày 10-12-2023; cập nhật 13-12-2023.
Pháp Luân Đại Pháp - Minghui.org
Back to top"""
    short_article = "给欧洲法会的贺词。祝法会圆满成功，大家精進修炼。"

    assert web_shell_reason(shell, ["Gửi các đệ tử Đại Pháp tham gia Pháp hội Đài Loan"])
    assert web_shell_reason(short_article, ["给欧洲法会的贺词"]) is None


def test_shell_check_uses_chinese_link_metadata_but_keeps_short_greeting() -> None:
    shell = """李洪志
二零一六年七月三十一日
简体字A4版：PDF文件
简体字Letter版：PDF文件
正体字A4版：PDF文件"""
    greeting = """参加欧洲法会的大法弟子：大家好！法会中大家会分享修炼中的心得，祝你们的法会圆满成功。
二零二二年九月十一日
简体字A4版：PDF文件"""

    assert web_shell_reason(shell, ["李洪志"])
    assert web_shell_reason(greeting, ["致欧洲法会贺词"]) is None


def _sections(lengths: list[int], prefix: str) -> list[Section]:
    return [Section("", f"Chapter {index}", prefix * length)
            for index, length in enumerate(lengths, start=1)]


def test_alignment_accepts_ordered_numeric_and_length_evidence() -> None:
    hans = [Section("", f"第{i}章", "中" * size) for i, size in enumerate((100, 450, 900), 1)]

    assert aligned_language_set({"en": _sections([110, 430, 930], "a"), "zh-Hans": hans}) == {
        "en", "zh-Hans",
    }


def test_alignment_rejects_equal_counts_with_conflicting_section_evidence() -> None:
    left = [Section("", f"Chapter {i}", "x" * 100) for i in range(1, 4)]
    right = [Section("", f"Chapter {i + 3}", "y" * 100) for i in range(1, 4)]

    assert aligned_language_set({"en": left, "vi": right}) == set()


def test_alignment_rejects_a_conflicting_length_profile() -> None:
    left = _sections([100, 100, 800, 100], "a")
    right = _sections([100, 800, 100, 100], "b")

    assert aligned_language_set({"en": left, "vi": right}) == set()


def test_alignment_selects_largest_supported_language_subset() -> None:
    en = _sections([100, 500, 900], "a")
    hans = [Section("", f"第{i}章", "中" * size) for i, size in enumerate((110, 490, 920), 1)]
    vi = [Section("", f"Chapter {i + 5}", "b" * size)
          for i, size in enumerate((900, 100, 500), 1)]

    assert aligned_language_set({"en": en, "zh-Hans": hans, "vi": vi}) == {"en", "zh-Hans"}


def test_single_section_alignment_needs_a_shared_marker() -> None:
    en = [Section("", "A Greeting", "Greetings to the disciples. 2022-09-11.")]
    vi = [Section("", "Lời chúc", "Gửi lời chúc tới các học viên. 2022-09-11.")]
    no_marker = [Section("", "Bài viết", "Một bài viết ngắn dành cho các học viên.")]

    assert aligned_language_set({"en": en, "vi": vi}) == {"en", "vi"}
    assert aligned_language_set({"vi": no_marker, "zh-Hans": [Section("", "致辞", "祝大家好。" * 8)]}) == set()


def test_registry_append_preserves_phase_a_records_unchanged() -> None:
    phase_a = {"schema_version": 1, "works": [
        {"work_id": "phase-a-one", "languages": {"en": {"status": "included"}}},
        {"work_id": "phase-a-two", "languages": {"vi": {"status": "included"}}},
    ]}
    current = copy.deepcopy(phase_a)
    original = copy.deepcopy(current)
    phase_b = [{"work_id": "new-work", "kind": "writing", "languages": {}}]

    result = compose_registry(current, phase_a, phase_b)

    assert result["works"][:2] == original["works"]
    assert current == original
    assert result["works"][2:] == phase_b
    assert compose_registry(result, phase_a, phase_b) == result
