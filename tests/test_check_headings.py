from scripts.check_headings import evaluate


def reason_text(result):
    return " ".join(result["reasons"])


def test_flags_a_book_with_no_headings():
    result = evaluate("A long body without structural markers. " * 100)
    assert result["flagged"]
    assert "sparse headings" in reason_text(result)


def test_flags_repeated_uppercase_running_headers():
    text = "\n".join(["# BARGAINING", "# ADVANTAGE"] * 80)
    result = evaluate(text)
    assert result["flagged"]
    assert "running header" in reason_text(result)


def test_flags_heading_link_markup():
    text = "\n".join(f"## [Section {i}](toc.xhtml#s{i})" for i in range(12))
    result = evaluate(text)
    assert result["flagged"]
    assert "heading link markup" in reason_text(result)


def test_flags_numbered_prose_promoted_from_a_paragraph():
    text = "\n\n".join(
        f"The list continues:\n# {i}.draw a diagram of the system and label every component\n"
        "continued on the next line"
        for i in range(1, 9)
    )
    result = evaluate(text)
    assert result["flagged"]
    assert "footnote-like numbered prose headings" in reason_text(result)


def test_flags_a_heading_that_splits_an_ongoing_paragraph():
    result = evaluate(
        "The discussion continues without a completed sentence\n"
        "# and the next thought\n"
        "continues in lowercase on this line.\n" * 4
    )
    assert "footnote-like numbered prose headings" in reason_text(result)


def test_flags_repeated_garbled_headings():
    text = "\n".join(f"## xqzvl brgtx qqqzz vvvth {i}" for i in range(10))
    result = evaluate(text)
    assert result["flagged"]
    assert "garbled headings" in reason_text(result)


def test_flags_ocr_like_body_noise():
    text = "\n".join(
        "xqzvl brgtx qqqzz vvvth a x i q §¤§" for _ in range(40)
    )
    result = evaluate(text)
    assert result["flagged"]
    assert "OCR-like body noise" in reason_text(result)


def test_fenced_code_is_not_heading_text_or_body_prose():
    result = evaluate("```python\n# xqzvl brgtx\n```\n\n# Real heading\n\nReadable prose.")
    assert result["features"]["heading_count"] == 1
    assert not result["flagged"]


def test_code_like_heading_tokens_are_not_garbled():
    text = "\n".join(
        [
            "## C++ operators: std::vector<int> and foo.bar()",
            "## pandas.DataFrame.groupby() with x == y",
            "## `torch.nn.Linear(32, 64)` and CMakeLists.txt",
        ]
    )
    result = evaluate(text)
    assert result["features"]["garbled_heading_share"] == 0
    assert "garbled headings" not in reason_text(result)


def test_long_descriptive_headings_are_not_footnotes():
    text = "\n".join(
        f"## Building resilient systems through careful review of service boundaries {i}"
        for i in range(30)
    )
    result = evaluate(text)
    assert result["features"]["footnote_like_heading_count"] == 0
    assert "footnote-like numbered prose headings" not in reason_text(result)
