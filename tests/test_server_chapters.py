"""Printed chapter numbers, markdown boundaries, and legacy title lookup."""

import pytest

from knowledge_base import books, server
from knowledge_base.config import MARKDOWN_DIR


@pytest.fixture
def markdown_books(monkeypatch, tmp_path):
    fixtures = {
        "parts": """# Part I: Basics
Part introduction.
## [Chapter 1: Getting Started](chapter1.html)
First chapter body.
## Chapter 12: ARM Internals
Twelfth chapter body.
### 12.1 Registers
Register details.
````markdown
# Chapter 99: Code Example
```
## Chapter 88: Still Code
````
After the code example.
# Part II: Advanced
Second part introduction.
## CHAPTER 22: Advanced ARM
Twenty-second chapter body.
## Chapter 23: Conclusion
Last chapter body.
""",
        "front-matter": """# Title Page
Title page body.
# Copyright
Copyright body.
# Preface
Preface body.
# Chapter 1: Getting Started
First chapter body.
# 2 Ghidra Processors
Second chapter body.
# 22. Patching Programs
Twenty-second chapter body.
## 22.1 Details
Patching details.
# CHAPTER 23
Last chapter body.
""",
        "plain": """# [Introduction](intro.html)
Introduction body.
## Details
Introduction details.
~~~markdown
# Fake Chapter
~~~
# Working with Tools
Tools body.
## Usage
Tools usage.
# Conclusion
Conclusion body.
""",
    }
    for slug, text in fixtures.items():
        (tmp_path / f"{slug}.md").write_text(text, encoding="utf-8")
    monkeypatch.setattr(books, "MARKDOWN_DIR", tmp_path)
    monkeypatch.setattr(server, "MARKDOWN_DIR", tmp_path)
    monkeypatch.setattr(books, "BOOKS", {slug: slug for slug in fixtures})
    monkeypatch.setattr(server, "BOOKS", books.BOOKS)
    books.book_chapters.cache_clear()
    yield tmp_path
    books.book_chapters.cache_clear()


@pytest.mark.parametrize("query", [12, "12", " 12 "])
def test_chapter_number_reaches_chapters_under_parts(markdown_books, query):
    result = server.get_chapter("parts", query)

    assert result.startswith("## Chapter 12: ARM Internals\n")
    assert "Register details." in result
    assert "After the code example." in result
    assert "# Part II: Advanced" not in result
    assert "positional" not in result


@pytest.mark.parametrize("query", [1, "1", 2, "2"])
def test_chapter_printed_number_takes_priority_over_front_matter_position(markdown_books, query):
    result = server.get_chapter("front-matter", query)

    expected = "# Chapter 1: Getting Started" if int(query) == 1 else "# 2 Ghidra Processors"
    assert result.startswith(expected + "\n")
    assert "positional" not in result


@pytest.mark.parametrize("label", ["Chapter 2", "2 Title", "2. Title", "CHAPTER 2: Title"])
def test_chapter_printed_label_formats_precede_position(markdown_books, label):
    (markdown_books / "plain.md").write_text(
        f"# Preface\nPreface.\n# Other\nWrong position.\n# {label}\nCorrect body.\n",
        encoding="utf-8",
    )

    assert server.get_chapter("plain", 2) == f"# {label}\nCorrect body."


@pytest.mark.parametrize("query", [2, "2"])
def test_chapter_without_printed_number_reports_positional_fallback(markdown_books, query):
    result = server.get_chapter("plain", query)

    assert "Used positional index 2" in result
    assert "# Working with Tools\nTools body.\n## Usage\nTools usage." in result
    assert "# Conclusion" not in result


@pytest.mark.parametrize(
    ("slug", "query", "heading"),
    [
        ("plain", "Introduction", "# [Introduction](intro.html)"),
        ("plain", "working with", "# Working with Tools"),
        ("plain", "Tools", "# Working with Tools"),
        ("parts", "chapter 12", "## Chapter 12: ARM Internals"),
        ("parts", "ARM Internals", "## Chapter 12: ARM Internals"),
        ("parts", "Part I:", "# Part I: Basics"),
    ],
)
def test_chapter_title_and_prefix_queries_keep_working(markdown_books, slug, query, heading):
    result = server.get_chapter(slug, query)

    assert result.startswith(heading + "\n")
    assert "Used positional" not in result
    if query == "Part I:":
        assert "Twelfth chapter body." in result
        assert "Second part introduction." not in result


@pytest.mark.parametrize("slug", ["parts", "front-matter"])
def test_chapter_not_found_lists_printed_labels_and_nested_chapters(markdown_books, slug):
    result = server.get_chapter(slug, 999)

    assert result.startswith("Chapter '999' not found")
    assert "Available chapters:" in result
    expected = "CHAPTER 22: Advanced ARM" if slug == "parts" else "22. Patching Programs"
    assert expected in result
    assert "Chapter 99: Code Example" not in result
    assert "Chapter 88: Still Code" not in result
    assert "12.1 Registers" not in result


def test_chapter_error_does_not_hide_chapters_after_first_ten(markdown_books):
    (markdown_books / "plain.md").write_text(
        "\n".join(f"# Chapter {number}: Title\nBody." for number in range(1, 26)),
        encoding="utf-8",
    )

    assert "Chapter 22: Title" in server.get_chapter("plain", "missing title")


@pytest.mark.parametrize("query", [0, 99, "99"])
def test_chapter_invalid_number_does_not_match_substrings_or_code(markdown_books, query):
    result = server.get_chapter("parts", query)

    assert result.startswith(f"Chapter '{query}' not found")


def test_chapter_number_does_not_match_larger_printed_number(markdown_books):
    (markdown_books / "plain.md").write_text("# Chapter 120: Other\nBody.\n", encoding="utf-8")

    assert server.get_chapter("plain", 12).startswith("Chapter '12' not found")


@pytest.mark.parametrize("wrapper", ["# Book Title\n", "# Part I\n## Chapters\n"])
def test_chapter_printed_label_survives_intermediate_wrapper_headings(markdown_books, wrapper):
    (markdown_books / "plain.md").write_text(
        wrapper + "### Chapter 1: Opening\nOne.\n### Chapter 2: Methods\nTwo.\n",
        encoding="utf-8",
    )

    assert server.get_chapter("plain", 2) == "### Chapter 2: Methods\nTwo."
    assert "Chapter 2: Methods" in books.book_chapters("plain")


def test_server_list_books_and_book_chapters_share_printed_labels(markdown_books):
    titles = books.book_chapters("parts")
    listed = server.list_books("parts")

    assert "Chapter 12: ARM Internals" in titles
    assert "CHAPTER 22: Advanced ARM" in titles
    assert "Chapter 88: Still Code" not in titles
    assert [row["title"] for row in listed["chapters"]] == titles
    assert [row["index"] for row in listed["chapters"]] == list(range(1, len(titles) + 1))
    assert next(row for row in server.list_books() if row["slug"] == "parts")["chapter_count"] == len(titles)


def test_chapter_empty_and_missing_markdown_errors(markdown_books):
    (markdown_books / "plain.md").write_text("No headings.\n", encoding="utf-8")
    assert server.get_chapter("plain", 1).endswith("No chapters found.")
    (markdown_books / "plain.md").unlink()
    assert server.get_chapter("plain", 1) == "Book markdown not found: plain"


def test_chapter_truncation_keeps_positional_notice(markdown_books):
    (markdown_books / "plain.md").write_text("# Long chapter\n" + "x" * 51000, encoding="utf-8")

    result = server.get_chapter("plain", 1)

    assert "Used positional index 1" in result
    assert result.endswith("[... truncated at 50,000 characters ...]")


@pytest.mark.parametrize(
    ("slug", "number", "heading"),
    [
        ("arm-assembly-internals", 12, "## Chapter 12 Reversing arm64 macOS Malware"),
        ("ghidra-book", 22, "# Chapter 22: Patching Binaries"),
    ],
)
def test_chapter_real_book_printed_number_when_markdown_is_present(slug, number, heading):
    path = MARKDOWN_DIR / f"{slug}.md"
    if not path.is_file():
        pytest.skip(f"Real book markdown is absent: {path}")

    result = server.get_chapter(slug, number)

    assert result.startswith(heading + "\n")
    assert "Used positional" not in result
    assert heading.lstrip("# ") in books.book_chapters(slug)
    assert heading.lstrip("# ") in server.get_chapter(slug, "missing chapter title")
