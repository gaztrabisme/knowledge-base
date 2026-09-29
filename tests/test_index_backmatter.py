from knowledge_base import ingest
from knowledge_base.headings import apply_heading_map
from scripts.strip_index_backmatter import is_index_child


def test_back_matter_anchor_trims_from_its_line_after_the_last_mapped_heading(tmp_path):
    heading_map = {
        "replace_existing": True,
        "back_matter_anchor": "Index",
        "entries": [
            {"title": "Chapter One", "level": 2, "anchor": "Chapter one body"},
            {"title": "Appendix B", "level": 2, "anchor": "Appendix B starts here"},
        ],
    }
    source = (
        "# Example Book\n\n"
        "Chapter one body begins here.\n"
        "Index entries are discussed in this chapter.\n"
        "Appendix B starts here.\n"
        "The full appendix remains content.\n"
        "Index\n"
        "A page-number entry, 14\n"
    )

    mapped, unmatched = apply_heading_map(source, heading_map)
    assert unmatched == []
    content = ingest._trim_to_first_map_heading(mapped, heading_map, tmp_path / "example.md")
    result = ingest._trim_to_back_matter_anchor(content, heading_map, tmp_path / "example.md")

    assert "## Chapter One" in result
    assert "Index entries are discussed in this chapter." in result
    assert "## Appendix B" in result
    assert "The full appendix remains content." in result
    assert "A page-number entry" not in result
    assert not result.rstrip().endswith("Index")


def test_missing_back_matter_anchor_reports_and_preserves_text(tmp_path, capsys):
    heading_map = {
        "replace_existing": True,
        "back_matter_anchor": "Notes",
        "entries": [{"title": "Appendix", "level": 2, "anchor": "Appendix starts"}],
    }
    text = "# Example Book\n\n## Appendix\nAppendix starts here.\nKeep this text.\n"

    result = ingest._trim_to_back_matter_anchor(text, heading_map, tmp_path / "example.md")

    assert result == text
    assert "Back-matter anchor not found for example: 'Notes'" in capsys.readouterr().out


def test_map_without_back_matter_anchor_keeps_existing_text_unchanged(tmp_path):
    heading_map = {
        "replace_existing": True,
        "entries": [{"title": "Chapter", "level": 2, "anchor": "Chapter starts"}],
    }
    text = "# Example Book\n\n## Chapter\nChapter starts.\nIndex\nIndex contents.\n"

    assert ingest._trim_to_back_matter_anchor(text, heading_map, tmp_path / "example.md") == text


def test_is_index_child_recognizes_top_level_named_index_headings():
    for heading in (
        "Index (part 1)",
        "Names Index",
        "Names Index (part 2) (part 1)",
        "Subject Index",
        "Author Index",
        "Index of Terms",
    ):
        assert is_index_child({"metadata": {"heading_path": heading}}), heading

    assert not is_index_child({"metadata": {"heading_path": "Chapter 1 > Names Index"}})
    assert not is_index_child({"metadata": {"heading_path": "Pandas Index object"}})
