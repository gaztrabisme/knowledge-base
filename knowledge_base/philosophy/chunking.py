"""Per-alignment-unit chunking built from the repository's chunk primitives."""

from __future__ import annotations

import json
import re
from pathlib import Path

from ..chunk import create_children, split_large_section
from ..config import CHUNKS_DIR, MARKDOWN_DIR
from .alignment import Section


def write_work_chunks(
    *, work_id: str, lang: str, work_group: str, title: str,
    sections: list[Section], edition: str, translator: str = "", derived: bool = False,
) -> tuple[Path, Path, int]:
    """Write markdown and chunk JSON while keeping each section key isolated."""
    markdown_dir = MARKDOWN_DIR / "philosophy"
    chunks_dir = CHUNKS_DIR / "philosophy"
    markdown_dir.mkdir(parents=True, exist_ok=True)
    chunks_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = markdown_dir / f"{work_id}.{lang}.md"
    chunks_path = chunks_dir / f"{work_id}.{lang}.json"
    md_sections = []
    parents, children = [], []

    for section_index, section in enumerate(sections, start=1):
        heading = f"# {section.section_key} — {section.section_title}"
        body = section.text.strip()
        compact_body = re.sub(r"\s+", "", body)
        compact_title = re.sub(r"\s+", "", section.section_title)
        if not compact_body or compact_body == compact_title:
            continue
        section_text = f"{heading}\n\n{body}".strip()
        md_sections.append(section_text)
        split_input = {
            # Keep the heading in markdown and chunk metadata, but split only
            # the body. Otherwise a large section with ### headings can emit a
            # heading-only parent before its first subsection.
            "text": body,
            "chapter": section.section_title,
            "section": "",
            "heading_path": section.section_title,
        }
        parts = split_large_section(split_input)
        # Keep alignment sections isolated. The shared overlap helper is English
        # punctuation based; on Chinese text it can treat an entire preceding
        # part as one sentence, causing repeated text to grow exponentially.
        for part in parts:
            part_body = part["text"].strip()
            if not part_body:
                continue
            part["text"] = f"{heading}\n\n{part_body}"
            parent_id = f"{work_id}.{lang}-p{len(parents)}"
            meta = {
                "book": work_id,
                "book_title": title,
                "work_id": work_id,
                "work_group": work_group,
                "lang": lang,
                "section_key": section.section_key,
                "section_title": section.section_title,
                "translator": translator,
                "edition": edition,
                "derived": derived,
                "chapter": str(section_index),
                "chapter_title": section.section_title,
                "section": "",
                "heading_path": section.section_title,
            }
            parents.append({"parent_id": parent_id, "text": part["text"], "metadata": meta.copy()})
            children_for_part = create_children(part_body, parent_id)
            for child_index, child in enumerate(children_for_part):
                # Keep the section heading with its first body child. Feeding
                # the parent heading into the paragraph splitter can produce
                # a child containing only the heading when the title is long.
                if child_index == 0:
                    child["text"] = f"{heading}\n\n{child['text']}"
                child_meta = meta.copy()
                child_meta["chunk_type"] = child.pop("chunk_type")
                child["metadata"] = child_meta
                children.append(child)

    markdown_path.write_text("\n\n".join(md_sections) + "\n", encoding="utf-8")
    chunks_path.write_text(json.dumps({
        "work_id": work_id,
        "work_group": work_group,
        "lang": lang,
        "title": title,
        "translator": translator,
        "edition": edition,
        "derived": derived,
        "parents": parents,
        "children": children,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return markdown_path, chunks_path, len(children)
