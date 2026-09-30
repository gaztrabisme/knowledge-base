"""Small offline fixture for the Phase B grouping and selection rules."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import build_philosophy_selection as builder
from knowledge_base.philosophy.textcheck import TextCheck


def output(output_id, language, title, kind, pdf_name, *, edition="", layout="primary"):
    return {
        "output_id": output_id,
        "source_item_id": output_id,
        "language": language,
        "title": title,
        "kind": kind,
        "edition": edition,
        "layout_or_variant": layout,
        "pdf_path": pdf_name,
        "pages": 10,
    }


def check(lang, share, *, count=100):
    outside = round(count * share)
    return TextCheck(lang, count, outside, outside / count, outside / count < 0.10,
                     reason="fixture result")


def test_grouping_editions_layouts_and_chinese_fallback(monkeypatch, tmp_path):
    manifest = {"outputs": [
        output("en-old", "en", "Example Work", "book", "en-old.pdf", edition="2005 translation"),
        output("en-new", "en", "Example Work", "book", "en-new.pdf", edition="2025 translation"),
        output("en-alias", "en", "Former Title", "book", "en-alias.pdf"),
        output("gb-two", "gb", "简体作品", "book", "two.pdf", layout="2合1"),
        output("gb-four", "gb", "简体作品", "book", "four.pdf", layout="4合1"),
        output("big5-example", "big5", "繁體作品", "book", "trad.pdf"),
        output("gb-priority-one", "gb", "优先排版", "book", "one.pdf", layout="one-page-per-sheet"),
        output("gb-priority-two", "gb", "优先排版", "book", "priority-two.pdf", layout="2合1"),
        output("gb-priority-four", "gb", "优先排版", "book", "priority-four.pdf", layout="4合1"),
        output("gb-bad-two", "gb", "乱码作品", "book", "bad-two.pdf", layout="2合1"),
        output("gb-bad-four", "gb", "乱码作品", "book", "bad-four.pdf", layout="4合1"),
        output("big5-bad", "big5", "繁體乱码", "book", "bad-trad.pdf"),
        output("big5-only", "big5", "孤立繁體", "book", "alone.pdf"),
    ]}
    title_map = {"groups": [
        {
            "work_id": "example-work", "kind": "book",
            "titles": {"en": "Example Work", "zh-Hans": "简体作品", "zh-Hant": "繁體作品"},
            "other_titles": {"en": [{"title": "Former Title", "reason": "Earlier catalogue title for the same work."}]},
            "edition_choices": {"en": {"output_id": "en-new", "reason": "Newest official English translation (2025)."}},
            "basis": "Fixture title map basis.",
        },
        {
            "work_id": "layout-priority", "kind": "book", "titles": {"zh-Hans": "优先排版"},
            "basis": "Fixture title map basis.",
        },
        {
            "work_id": "all-fail", "kind": "book", "titles": {"zh-Hans": "乱码作品", "zh-Hant": "繁體乱码"},
            "basis": "Fixture title map basis.",
        },
        {
            "work_id": "traditional-only", "kind": "book", "titles": {"zh-Hant": "孤立繁體"},
            "basis": "Fixture title map basis.",
        },
    ]}
    checks = {
        ("two.pdf", "zh-Hans"): check("zh-Hans", 0.20),
        ("four.pdf", "zh-Hans"): check("zh-Hans", 0.02),
        ("trad.pdf", "zh-Hant"): check("zh-Hant", 0.20),
        ("one.pdf", "zh-Hans"): check("zh-Hans", 0.01),
        ("priority-two.pdf", "zh-Hans"): check("zh-Hans", 0.02),
        ("priority-four.pdf", "zh-Hans"): check("zh-Hans", 0.03),
        ("bad-two.pdf", "zh-Hans"): check("zh-Hans", 0.20),
        ("bad-four.pdf", "zh-Hans"): check("zh-Hans", 0.30),
        ("bad-trad.pdf", "zh-Hant"): check("zh-Hant", 0.20),
        ("alone.pdf", "zh-Hant"): check("zh-Hant", 0.20),
    }

    def fake_check(path, lang):
        return checks[(Path(path).name, lang)]

    monkeypatch.setattr(builder, "check_pdf", fake_check)
    result = builder.build_selection(manifest, title_map, tmp_path)
    groups = {group["work_id"]: group for group in result["groups"]}

    example = groups["example-work"]
    assert example["languages"]["en"]["output_id"] == "en-new"
    assert example["languages"]["en"]["edition_reason"] == "Newest official English translation (2025)."
    assert example["languages"]["en"]["other_titles"] == [
        {"title": "Former Title", "reason": "Earlier catalogue title for the same work."}
    ]
    hans = example["languages"]["zh-Hans"]
    assert hans["status"] == "included"
    assert hans["output_id"] == "gb-four"  # the 2-up layout failed; the passing 4-up layout is eligible
    assert [candidate["output_id"] for candidate in hans["candidates"]] == ["gb-two", "gb-four"]
    assert [candidate["text_check"]["passed"] for candidate in hans["candidates"]] == [False, True]
    hant = example["languages"]["zh-Hant"]
    assert hant["status"] == "derive"
    assert hant["derive_from_output_id"] == "gb-four"
    assert "0.200000" in hant["reason"]

    priority = groups["layout-priority"]["languages"]["zh-Hans"]
    assert priority["output_id"] == "gb-priority-one"
    assert len(priority["candidates"]) == 3

    failed = groups["all-fail"]["languages"]
    assert failed["zh-Hans"]["status"] == "skipped"
    assert len(failed["zh-Hans"]["candidates"]) == 2
    assert failed["zh-Hant"]["status"] == "skipped"
    assert "No included Simplified edition" in failed["zh-Hant"]["reason"]
    assert groups["traditional-only"]["languages"]["zh-Hant"]["status"] == "skipped"
    assert "No included Simplified edition" in groups["traditional-only"]["languages"]["zh-Hant"]["reason"]
