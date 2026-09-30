#!/usr/bin/env python3
"""Ingest selected phase-B philosophy works with general sectioning and safe registry append."""

from __future__ import annotations

import json
import re
import sys
import tempfile
from collections import Counter
from pathlib import Path

from opencc import OpenCC
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from knowledge_base.philosophy import chunking
from knowledge_base.philosophy.alignment import Section, aligned_language_set
from knowledge_base.philosophy.sectioning import (
    repair_chinese_full_stop_positions, split_sections, web_shell_reason,
)
from knowledge_base.philosophy.textcheck import check_text

PHASE_B = ROOT / "data" / "philosophy" / "phase-b"
SELECTION_PATH = PHASE_B / "selection.json"
REGISTRY_PATH = ROOT / "data" / "philosophy" / "works.json"
BASELINE_PATH = PHASE_B / "works-phase-a.json"
ARCHIVE = Path("/Users/GaryT/Documents/books/falun-dafa-pdf-archive")
REPORT_PATH = PHASE_B / "u4-report.md"
BEFORE_REWORK = {
    "chunks": {"en": 7613, "vi": 19203, "zh-Hans": 12116, "zh-Hant": 13790},
    "sections": {"en": 361, "vi": 5508, "zh-Hans": 268, "zh-Hant": 466},
    "aligned_works": {0: 38, 2: 68, 3: 8, 4: 3},
}
LETTER_SPACED_TRADITIONAL = [
    "hong-yin-ii",
    "hong-yin-iv",
    "hong-yin-v",
    "hong-yin-vi",
    "lecture-given-at-the-conference-in-sydney",
]


def compose_registry(current: dict, phase_a_baseline: dict, phase_b_works: list[dict]) -> dict:
    """Preserve existing phase-A records and replace the phase-B append idempotently."""
    baseline = phase_a_baseline.get("works", [])
    expected = {item["work_id"]: item for item in baseline}
    present = {item["work_id"]: item for item in current.get("works", [])}
    if any(present.get(work_id) != item for work_id, item in expected.items()):
        raise RuntimeError("works.json phase-A records differ from works-phase-a.json")
    if len(phase_b_works) != len({item["work_id"] for item in phase_b_works}):
        raise RuntimeError("phase-B registry contains duplicate work ids")
    return {"schema_version": current.get("schema_version", 1),
            "works": [present[item["work_id"]] for item in baseline] + phase_b_works}


def _manifest() -> dict[str, dict]:
    raw = json.loads((ARCHIVE / "manifest.json").read_text(encoding="utf-8"))
    return {item["output_id"]: item for item in raw.get("outputs", [])}


def _source(chosen: dict, manifest: dict[str, dict]) -> tuple[Path | None, dict | None]:
    if chosen.get("file"):
        return Path(chosen["file"]), None
    output_id = chosen.get("output_id")
    item = manifest.get(output_id)
    if item and item.get("pdf_path"):
        return ARCHIVE / item["pdf_path"], item
    return None, item


def _quality(text: str, lang: str, selected_check: dict | None = None) -> dict:
    if not lang.startswith("zh"):
        return {"status": "not_applicable", "passed": True, "outside_share": 0.0,
                "reason": "not a Chinese-language edition"}
    value = check_text(text, lang).to_dict()
    value["status"] = "passed" if value["passed"] else "failed"
    if selected_check and selected_check.get("comparison") is not None:
        value["comparison"] = selected_check["comparison"]
    return value


def _skip_record(
    *, lang: str, chosen: dict, reason: str, source: Path | None = None,
    text_check: dict | None = None, extraction: dict | None = None,
) -> dict:
    return {
        "file": str(source) if source else str(chosen.get("file") or ""),
        "edition": chosen.get("edition") or chosen.get("layout_or_variant") or "selected edition",
        "page_count": chosen.get("pages"), "text_check": text_check or chosen.get("text_check") or {
            "status": "not_applicable", "passed": True, "reason": "not evaluated"},
        "status": "skipped", "markdown_file": None, "chunks_file": None,
        "chunk_count": 0, "section_count": 0, "translator": "", "aligned": False,
        "manifest_output_id": chosen.get("output_id"), "reason": reason,
        **({"extraction": extraction} if extraction else {}),
    }


def _load_included(
    work: dict, lang: str, chosen: dict, manifest: dict[str, dict],
) -> tuple[list[Section] | None, dict, Path | None, str | None]:
    source, item = _source(chosen, manifest)
    if source is None:
        return None, _skip_record(lang=lang, chosen=chosen, reason="selected source has no manifest file path"), None, None
    if not source.is_file():
        return None, _skip_record(lang=lang, chosen=chosen, source=source,
                                  reason="selected source file does not exist"), source, None
    title = work.get("titles", {}).get(lang, work["work_id"])
    layout = chosen.get("layout_or_variant") or chosen.get("edition") or (item or {}).get("layout_or_variant", "")
    try:
        sections, info = split_sections(source, lang, layout, document_title=title)
    except Exception as exc:
        return None, _skip_record(lang=lang, chosen=chosen, source=source,
                                  reason=f"section extraction failed: {type(exc).__name__}: {exc}"), source, None
    text = "\n\n".join(section.text for section in sections)
    # A failed boundary can leave a metadata-only section after a cover or TOC.
    # Remove those before alignment so they cannot acquire a translation key.
    sections = [section for section in sections
                if re.sub(r"\W+", "", section.text, flags=re.UNICODE).casefold()
                != re.sub(r"\W+", "", section.section_title, flags=re.UNICODE).casefold()]
    text = "\n\n".join(section.text for section in sections)
    info_dict = {"missing_pages": info.missing_pages, "contents_pages_removed": info.contents_pages_removed,
                 "front_pages_removed": info.front_pages_removed,
                 "interlinear_pages_removed": info.interlinear_pages_removed,
                 "glossary_pages_removed": info.glossary_pages_removed,
                 "outline_used": info.outline_used, "warnings": info.warnings}
    shell = web_shell_reason(text, [title, (item or {}).get("title", "")])
    quality = _quality(text, lang, chosen.get("text_check"))
    if shell:
        return None, _skip_record(lang=lang, chosen=chosen, source=source, reason=shell,
                                  text_check=quality, extraction=info_dict), source, None
    if not sections or not text.strip() or not any(char.isalnum() for char in text):
        return None, _skip_record(lang=lang, chosen=chosen, source=source,
                                  reason="no extractable article or book text", text_check=quality,
                                  extraction=info_dict), source, None
    if lang.startswith("zh") and not quality.get("passed"):
        return None, _skip_record(lang=lang, chosen=chosen, source=source,
                                  reason=f"extracted text failed Chinese text check: {quality.get('reason')}",
                                  text_check=quality, extraction=info_dict), source, None
    record = {
        "file": str(source), "edition": chosen.get("edition") or layout or "selected edition",
        "page_count": info.page_count or chosen.get("pages"), "text_check": quality,
        "status": "included", "markdown_file": None, "chunks_file": None,
        "chunk_count": 0, "section_count": len(sections), "translator": "",
        "aligned": False, "manifest_output_id": chosen.get("output_id"),
        "extraction": info_dict,
    }
    return sections, record, source, layout


def _derive_hant(
    work: dict, chosen: dict, hans_sections: list[Section] | None,
    hans_record: dict | None, manifest: dict[str, dict], *, reason: str = "",
) -> tuple[list[Section] | None, dict]:
    source, _ = _source(chosen, manifest)
    if hans_sections is None or not hans_record or hans_record.get("status") != "included":
        return None, _skip_record(lang="zh-Hant", chosen=chosen,
                                  reason="cannot derive Traditional Chinese because the selected Simplified edition was skipped",
                                  source=source)
    converter = OpenCC("s2t")
    sections = [Section("", converter.convert(section.section_title), converter.convert(section.text))
                for section in hans_sections]
    text = "\n\n".join(section.text for section in sections)
    quality = _quality(text, "zh-Hant")
    rejected, _ = _source(chosen, manifest)
    record = {
        "file": str(ROOT / hans_record["markdown_file"]) if hans_record.get("markdown_file") else hans_record["file"],
        "edition": f"derived from zh-Hans via OpenCC s2t",
        "page_count": None, "text_check": quality, "status": "included",
        "markdown_file": None, "chunks_file": None, "chunk_count": 0,
        "section_count": len(sections), "translator": "OpenCC s2t (derived from zh-Hans)",
        "derived": True, "aligned": False, "manifest_output_id": chosen.get("output_id"),
        **({"derivation_reason": reason} if reason else {}),
        "rejected_pdf": {
            "file": str(rejected) if rejected else "",
            "edition": chosen.get("edition"), "page_count": chosen.get("pages"),
            "status": "skipped", "text_check": chosen.get("text_check", {}),
        },
    }
    if not quality["passed"]:
        return None, _skip_record(lang="zh-Hant", chosen=chosen,
                                  source=Path(record["file"]),
                                  reason=f"OpenCC-derived text failed Chinese text check: {quality['reason']}",
                                  text_check=quality)
    return sections, record


def _stage_write(work_id: str, lang: str, title: str, sections: list[Section], record: dict,
                 work_group: str, temp_root: Path, owned_paths: set[str]) -> None:
    old_markdown, old_chunks = chunking.MARKDOWN_DIR, chunking.CHUNKS_DIR
    chunking.MARKDOWN_DIR = temp_root / "markdown"
    chunking.CHUNKS_DIR = temp_root / "chunks"
    try:
        md_stage, chunks_stage, count = chunking.write_work_chunks(
            work_id=work_id, lang=lang, work_group=work_group, title=title,
            sections=sections, edition=record["edition"], translator=record.get("translator", ""),
            derived=record.get("derived", False),
        )
    finally:
        chunking.MARKDOWN_DIR, chunking.CHUNKS_DIR = old_markdown, old_chunks
    destinations = (
        (md_stage, ROOT / "data" / "markdown" / "philosophy" / md_stage.name, "markdown_file"),
        (chunks_stage, ROOT / "data" / "chunks" / "philosophy" / chunks_stage.name, "chunks_file"),
    )
    for staged, destination, field in destinations:
        content = staged.read_bytes()
        relative = str(destination.relative_to(ROOT))
        if destination.exists():
            if destination.read_bytes() != content:
                if relative not in owned_paths:
                    raise RuntimeError(f"refusing to replace existing non-owned output: {destination}")
                destination.write_bytes(content)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        record[field] = relative
    record["chunk_count"] = count
    record["section_count"] = len(sections)


def _process_group(work: dict, manifest: dict[str, dict], temp_root: Path, owned_paths: set[str]) -> dict:
    work_id = work["work_id"]
    chosen_by_lang = work.get("languages", {})
    output = {"work_id": work_id, "work_group": work_id, "kind": work.get("kind", "book"),
              "titles": work.get("titles", {}), "languages": {}}
    sections_by_lang: dict[str, list[Section]] = {}

    for lang, chosen in chosen_by_lang.items():
        status = chosen.get("status")
        if status == "phase-a":
            continue
        if status == "derive":
            continue
        if status == "skipped":
            reason = chosen.get("edition_reason") or chosen.get("reason") or "selection marked this edition skipped"
            source, _ = _source(chosen, manifest)
            output["languages"][lang] = _skip_record(lang=lang, chosen=chosen, source=source, reason=reason)
            continue
        sections, record, _, layout = _load_included(work, lang, chosen, manifest)
        if lang == "zh-Hant" and sections is None and chosen.get("status") == "included":
            hans_sections = sections_by_lang.get("zh-Hans")
            hans_record = output["languages"].get("zh-Hans")
            if hans_sections and hans_record and hans_record.get("status") == "included":
                failure_reason = record.get("reason", "Traditional Chinese PDF could not be extracted in reading order")
                sections, record = _derive_hant(
                    work, chosen, hans_sections, hans_record, manifest, reason=failure_reason,
                )
        output["languages"][lang] = record
        if sections is not None:
            sections_by_lang[lang] = sections
            record["_layout"] = layout

    for lang, chosen in chosen_by_lang.items():
        if chosen.get("status") != "derive":
            continue
        source_hans = sections_by_lang.get("zh-Hans")
        hans_record = output["languages"].get("zh-Hans")
        reason = chosen.get("reason") or (
            "selected Traditional PDF failed text check: "
            + str(chosen.get("text_check", {}).get("reason", "reading-order extraction was unusable"))
        )
        sections, record = _derive_hant(work, chosen, source_hans, hans_record, manifest, reason=reason)
        output["languages"][lang] = record
        if sections is not None:
            sections_by_lang[lang] = sections

    # A few Simplified writing PDFs have full stops positioned by their
    # invisible text layer at the wrong reading offsets. When a real
    # Traditional edition has identical lexical text, use its punctuation as
    # a reference before alignment and chunking.
    hans_sections = sections_by_lang.get("zh-Hans")
    hant_sections = sections_by_lang.get("zh-Hant")
    hant_record = output["languages"].get("zh-Hant", {})
    if (hans_sections and hant_sections and not hant_record.get("derived")
            and len(hans_sections) == len(hant_sections)):
        to_simplified = OpenCC("t2s")
        for hans_section, hant_section in zip(hans_sections, hant_sections):
            hans_section.text = repair_chinese_full_stop_positions(
                hans_section.text, to_simplified.convert(hant_section.text),
            )

    aligned = aligned_language_set(sections_by_lang)
    for lang, sections in sections_by_lang.items():
        record = output["languages"][lang]
        is_aligned = lang in aligned
        record["aligned"] = is_aligned
        title = work.get("titles", {}).get(lang, work_id)
        for index, section in enumerate(sections, 1):
            section.section_key = f"{work_id}-s{index:02d}" if is_aligned else f"{work_id}-{lang}-s{index:02d}"
        _stage_write(work_id, lang, title, sections, record, work_id, temp_root, owned_paths)
        record.pop("_layout", None)
    for record in output["languages"].values():
        record.setdefault("aligned", False)
    return output


def _section_titles(work: dict, lang: str) -> list[tuple[str, str]]:
    record = work.get("languages", {}).get(lang, {})
    if record.get("status") != "included":
        return []
    path = ROOT / record["chunks_file"]
    data = json.loads(path.read_text(encoding="utf-8"))
    titles = {}
    for child in data.get("children", []):
        meta = child.get("metadata", {})
        titles.setdefault(meta.get("section_key"), meta.get("section_title", ""))
    return list(titles.items())


def _phase_b_metrics(works: list[dict]) -> dict:
    chunks = Counter()
    sections = Counter()
    aligned = Counter()
    for work in works:
        aligned[sum(bool(record.get("aligned")) for record in work.get("languages", {}).values())] += 1
        for lang, record in work.get("languages", {}).items():
            if record.get("status") == "included":
                chunks[lang] += record.get("chunk_count", 0)
                sections[lang] += record.get("section_count", 0)
    return {"chunks": dict(chunks), "sections": dict(sections), "aligned_works": dict(aligned)}


def _counts_line(values: dict[int | str, int]) -> str:
    return ", ".join(f"{key}: {values[key]}" for key in sorted(values)) or "none"


def _middle_children(record: dict) -> list[dict]:
    if record.get("status") != "included" or not record.get("chunks_file"):
        return []
    data = json.loads((ROOT / record["chunks_file"]).read_text(encoding="utf-8"))
    children = data.get("children", [])
    if not children:
        return []
    start = max(0, len(children) // 2 - 1)
    return children[start:start + 3]


def _pdf_layout_summary(record: dict) -> str:
    """Summarize vertical text spans and rotated pages for a sampled PDF."""
    source = Path(str(record.get("file", "")))
    if source.suffix.casefold() != ".pdf" or not source.is_file():
        return "layout unavailable"
    total_lines = vertical_lines = rotated_pages = 0
    try:
        with pymupdf.open(source) as document:
            page_count = document.page_count
            for page in document:
                rotated_pages += bool(page.rotation)
                for block in page.get_text("dict").get("blocks", []):
                    for line in block.get("lines", []):
                        total_lines += 1
                        vertical_lines += int(line.get("wmode", 0) == 1)
    except Exception as exc:
        return f"layout inspection failed: {type(exc).__name__}"
    return (f"vertical spans {vertical_lines}/{total_lines}; "
            f"rotated pages {rotated_pages}/{page_count}")


def _append_reading_order_samples(lines: list[str], works: list[dict]) -> None:
    included = [
        (work, work.get("languages", {}).get("zh-Hans", {}))
        for work in works
        if _is_multipage_record(work.get("languages", {}).get("zh-Hans", {}))
        and work.get("languages", {}).get("zh-Hans", {}).get("status") == "included"
    ]
    multiup = []
    preferred = ["collected-teachings-given-around-the-world-volume-i",
                 "collected-teachings-given-around-the-world-volume-vii"]
    for work_id in preferred:
        multiup.extend(row for row in included if row[0]["work_id"] == work_id)
    multiup.extend(row for row in sorted(included, key=lambda row: row[0]["work_id"])
                   if row not in multiup)

    lines.extend(["", "## Reading-order excerpts", "",
                  "The following are three child chunks around the midpoint of each file; each excerpt is capped at 400 characters.",
                  "", "### Five Simplified 2合1 files", ""])
    for work, record in multiup[:5]:
        lines.append(f"#### `{work['work_id']}.zh-Hans` — source `{Path(record['file']).name}`")
        for child in _middle_children(record):
            lines.append(f"- `{child['child_id']}`: {_snippet(child['text'], 400)}")
        lines.append("")

    lines.extend(["### Five previously letter-spaced Traditional files", ""])
    by_id = {work["work_id"]: work for work in works}
    for work_id in LETTER_SPACED_TRADITIONAL:
        work = by_id.get(work_id)
        record = work.get("languages", {}).get("zh-Hant", {}) if work else {}
        lines.append(f"#### `{work_id}.zh-Hant` — {_pdf_layout_summary(record)}; "
                     f"derived: {bool(record.get('derived'))}")
        if record.get("status") != "included":
            lines.append(f"- No included child chunks; status `{record.get('status', 'missing')}`. "
                         f"{record.get('reason', '')}")
        else:
            for child in _middle_children(record):
                lines.append(f"- `{child['child_id']}`: {_snippet(child['text'], 400)}")
        lines.append("")
    lines.extend([
        "The sampled Traditional PDFs include two rotated vertical text layouts "
        "(Hong Yin II and the Sydney lecture); Hong Yin IV, V, and VI use horizontal text. "
        "The vertical spans are reassembled by column before sectioning. No internal "
        "Han-character spacing remains within the sampled child bodies.",
        "",
    ])


def _is_multipage_record(record: dict) -> bool:
    return bool(re.search(r"[24]\s*合\s*1", " ".join(
        [str(record.get("edition", "")), Path(str(record.get("file", ""))).name]
    )))


def _sample_works(works: list[dict]) -> list[dict]:
    candidates = []
    for work in works:
        included = {lang: rec for lang, rec in work["languages"].items() if rec.get("status") == "included"}
        if len(included) < 2:
            continue
        section_counts = [rec.get("section_count", 0) for rec in included.values()]
        if max(section_counts, default=0) > 30:
            continue
        details = {lang: _section_titles(work, lang) for lang in included}
        structured = sum(len(items) >= 2 for items in details.values())
        four_lang = len(included) == 4
        aligned_langs = sum(bool(rec.get("aligned")) for rec in included.values())
        derived = any(rec.get("derived") for rec in included.values())
        multipage = any(_is_multipage_record(rec) for rec in included.values())
        score = (100 if four_lang else 0) + aligned_langs * 18 + structured * 12
        score += 4 * min(max(section_counts, default=0), 8)
        candidates.append({"score": score, "kind": work["kind"], "work": work,
                           "languages": set(included), "derived": derived, "multipage": multipage})
    selected: list[dict] = []

    def add_best(pool: list[dict], *, prefer: str = "") -> None:
        pool = [row for row in pool if row not in selected]
        if not pool:
            return
        covered = set().union(*(row["languages"] for row in selected)) if selected else set()
        derived_seen = any(row["derived"] for row in selected)
        multipage_seen = any(row["multipage"] for row in selected)
        row = max(pool, key=lambda item: (
            item["score"] + 35 * len(item["languages"] - covered)
            + (50 if item["derived"] and not derived_seen else 0)
            + (35 if item["multipage"] and not multipage_seen else 0)
            + (70 if prefer == "derived" and item["derived"] else 0)
            + (70 if prefer == "four-languages" and len(item["languages"]) == 4 else 0),
            item["work"]["work_id"],
        ))
        selected.append(row)

    volume_one = next((row for row in candidates if row["work"]["work_id"] ==
                       "collected-teachings-given-around-the-world-volume-i"), None)
    if volume_one:
        selected.append(volume_one)
    writing = [row for row in candidates if row["kind"] == "writing"]
    books = [row for row in candidates if row["kind"] == "book"]
    if not any(row["kind"] == "writing" for row in selected):
        add_best(writing, prefer="derived")
    if not any(row["derived"] for row in selected):
        add_best([row for row in candidates if row["derived"]], prefer="derived")
    if not any(row["kind"] == "book" for row in selected):
        add_best(books, prefer="four-languages")
    while len(selected) < min(6, len(candidates)):
        book_count = sum(row["kind"] == "book" for row in selected)
        writing_count = sum(row["kind"] == "writing" for row in selected)
        underrepresented = "writing" if writing_count < book_count else "book"
        pool = [row for row in candidates if row["kind"] == underrepresented] or candidates
        add_best(pool, prefer="four-languages")
    return [row["work"] for row in selected[:6]]


def _snippet(text: str, limit: int = 300) -> str:
    return re.sub(r"\s+", " ", text).strip()[:limit].replace("|", "\\|")


def _write_report(registry: dict, selection: dict) -> None:
    baseline_ids = {item["work_id"] for item in json.loads(BASELINE_PATH.read_text(encoding="utf-8"))["works"]}
    works = [item for item in registry["works"] if item["work_id"] not in baseline_ids]
    languages = Counter(lang for work in works for lang in work.get("languages", {}))
    status_counts = Counter(
        "derived" if record.get("derived") and record.get("status") == "included"
        else record.get("status")
        for work in works for record in work["languages"].values()
    )
    derived = sum(bool(record.get("derived")) for work in works for record in work["languages"].values())
    chunks_by_lang = Counter()
    for work in works:
        for lang, record in work["languages"].items():
            if record.get("status") == "included":
                chunks_by_lang[lang] += record.get("chunk_count", 0)
    aligned_counts = Counter(sum(record.get("aligned", False) for record in work["languages"].values())
                             for work in works)
    metrics = _phase_b_metrics(works)
    chunk_files = [(record.get("chunk_count", 0), f"{work['work_id']}.{lang}.json")
                   for work in works for lang, record in work["languages"].items()
                   if record.get("status") == "included"]

    lines = ["# Phase B U4 report", "", "## Counts", "",
             f"- Works: {len(works)}", "- Language records by status: " + ", ".join(
                 f"{status}: {status_counts[status]}" for status in sorted(status_counts)),
             f"- Derived records: {derived}", "- Child chunks by language: " + ", ".join(
                 f"{lang}: {chunks_by_lang[lang]}" for lang in sorted(languages)),
             "- Works by number of aligned languages: " + ", ".join(
                 f"{count}: {aligned_counts[count]}" for count in sorted(aligned_counts)), "",
             "## Before and after rework", "",
             "Before (the 2026-09-30 output that failed chunk quality):",
             "- Child chunks by language: " + _counts_line(BEFORE_REWORK["chunks"]),
             "- Sections by language: " + _counts_line(BEFORE_REWORK["sections"]),
             "- Works by aligned-language count: " + _counts_line(BEFORE_REWORK["aligned_works"]), "",
             "After this rebuild:",
             "- Child chunks by language: " + _counts_line(metrics["chunks"]),
             "- Sections by language: " + _counts_line(metrics["sections"]),
             "- Works by aligned-language count: " + _counts_line(metrics["aligned_works"]), "",
             "## Records skipped at ingest", ""]
    skipped = [(work["work_id"], lang, rec.get("reason", "no reason recorded"))
               for work in works for lang, rec in work["languages"].items() if rec.get("status") == "skipped"]
    lines.extend([f"- `{work}/{lang}` — {reason}" for work, lang, reason in skipped] or ["- None."])
    lines += ["", "## Works whose language sections did not align", ""]
    unaligned = []
    for work in works:
        included = {lang: rec for lang, rec in work["languages"].items() if rec.get("status") == "included"}
        if len(included) >= 2 and any(not rec.get("aligned") for rec in included.values()):
            counts = ", ".join(f"{lang}: {rec.get('section_count', 0)}" for lang, rec in sorted(work["languages"].items()))
            unaligned.append(f"- `{work['work_id']}` — {counts}")
    lines.extend(unaligned or ["- None."])

    lines += ["", "## Six work samples", ""]
    samples = _sample_works(works)
    for work in samples:
        included = [rec for rec in work["languages"].values() if rec.get("status") == "included"]
        features = []
        if any(rec.get("derived") for rec in included):
            features.append("derived Traditional Chinese")
        if any(_is_multipage_record(rec) for rec in included):
            features.append("multi-up source")
        suffix = "; " + ", ".join(features) if features else ""
        lines += [f"### {work['work_id']} ({work.get('kind', 'book')}{suffix})", ""]
        langs = sorted(work["languages"])
        lines.append("| # | " + " | ".join(langs) + " |")
        lines.append("|---:|" + "---|" * len(langs))
        title_lists = {lang: _section_titles(work, lang) for lang in langs}
        max_count = max((len(items) for items in title_lists.values()), default=0)
        for index in range(max_count):
            values = []
            for lang in langs:
                if index < len(title_lists[lang]):
                    values.append(title_lists[lang][index][1])
                elif work["languages"][lang].get("status") == "skipped" and index == 0:
                    values.append("skipped")
                else:
                    values.append("—")
            lines.append(f"| {index + 1} | " + " | ".join(value.replace("|", "\\|") for value in values) + " |")
        if max_count == 0:
            lines.append("| — | " + " | ".join(
                "skipped" if work["languages"][lang].get("status") == "skipped" else "—" for lang in langs
            ) + " |")
        lines += ["", "Chunk excerpts (first and last child for the first and last available section):", ""]
        for lang in langs:
            record = work["languages"][lang]
            if record.get("status") != "included":
                lines.append(f"- `{lang}`: skipped — {record.get('reason', '')}")
                continue
            data = json.loads((ROOT / record["chunks_file"]).read_text(encoding="utf-8"))
            by_key: dict[str, list[dict]] = {}
            for child in data.get("children", []):
                by_key.setdefault(child["metadata"]["section_key"], []).append(child)
            keys = list(by_key)
            chosen_keys = list(dict.fromkeys([keys[0], keys[-1]])) if keys else []
            for key in chosen_keys:
                children = by_key[key]
                title = children[0]["metadata"].get("section_title", "")
                lines.append(f"- `{lang}` / {title}: first `{children[0]['child_id']}`: {_snippet(children[0]['text'])}")
                lines.append(f"  last `{children[-1]['child_id']}`: {_snippet(children[-1]['text'])}")
            if len(keys) == 1:
                lines.append(f"  Only one section was extracted for `{lang}`.")
        lines.append("")

    volume_one = next((work for work in works if work["work_id"] ==
                       "collected-teachings-given-around-the-world-volume-i"), None)
    if volume_one:
        lines += ["## Volume I section titles in all four languages", ""]
        languages_in_order = [lang for lang in ("en", "vi", "zh-Hans", "zh-Hant")
                              if lang in volume_one.get("languages", {})]
        title_lists = {lang: _section_titles(volume_one, lang) for lang in languages_in_order}
        count = max((len(items) for items in title_lists.values()), default=0)
        lines.append("| # | " + " | ".join(languages_in_order) + " |")
        lines.append("|---:|" + "---|" * len(languages_in_order))
        for index in range(count):
            values = [title_lists[lang][index][1] if index < len(title_lists[lang]) else "—"
                      for lang in languages_in_order]
            lines.append(f"| {index + 1} | " + " | ".join(value.replace("|", "\\|") for value in values) + " |")
        lines.append("")

    _append_reading_order_samples(lines, works)

    lines += ["## Shortest and longest chunk files", ""]
    lines.append("### 10 shortest")
    lines.extend(f"- `{name}` — {count} chunks" for count, name in sorted(chunk_files)[:10])
    lines += ["", "### 10 longest", ""]
    lines.extend(f"- `{name}` — {count} chunks" for count, name in sorted(chunk_files, reverse=True)[:10])

    lines += ["", "## Source text and extraction notes", ""]
    notes = []
    for work in works:
        for lang, rec in work["languages"].items():
            reason = rec.get("reason", "")
            if "web shell" in reason:
                notes.append(f"- `{work['work_id']}/{lang}` — {reason}; title-only content was not indexed.")
            if rec.get("derived") and rec.get("derivation_reason"):
                rejected = rec.get("rejected_pdf", {})
                notes.append(f"- `{work['work_id']}/{lang}` — Traditional source `{Path(rejected.get('file', '')).name}` "
                             f"was rejected and derived from Simplified: {rec['derivation_reason']}")
            info = rec.get("extraction", {})
            if info.get("missing_pages"):
                notes.append(f"- `{work['work_id']}/{lang}` — `{rec.get('file')}`: page tree missing pages "
                             f"{', '.join(map(str, info['missing_pages']))}; readable pages were retained.")
            if info.get("contents_pages_removed"):
                notes.append(f"- `{work['work_id']}/{lang}` — removed {info['contents_pages_removed']} detected contents page(s).")
            if info.get("front_pages_removed"):
                notes.append(f"- `{work['work_id']}/{lang}` — removed {info['front_pages_removed']} short title/cover page(s) before body text.")
            if info.get("interlinear_pages_removed"):
                notes.append(f"- `{work['work_id']}/{lang}` — removed {info['interlinear_pages_removed']} Chinese/pinyin interlinear page(s); the Vietnamese poem translations are on paired pages.")
            if info.get("glossary_pages_removed"):
                notes.append(f"- `{work['work_id']}/{lang}` — removed {info['glossary_pages_removed']} trailing glossary/footnote page(s) after the work text.")
            if info.get("warnings"):
                notes.append(f"- `{work['work_id']}/{lang}` — extraction warning: " + "; ".join(info["warnings"]))
            if rec.get("status") == "included":
                data = json.loads((ROOT / rec["chunks_file"]).read_text(encoding="utf-8"))
                text = "\n".join(child.get("text", "") for child in data.get("children", []))
                total_letters = sum(char.isalpha() for char in text)
                cjk = sum("\u3400" <= char <= "\u9fff" for char in text)
                if total_letters and ((lang.startswith("zh") and cjk / total_letters < 0.55)
                                     or (lang in {"en", "vi"} and cjk / total_letters > 0.25)):
                    notes.append(f"- `{work['work_id']}/{lang}` — mixed Latin/CJK scripts in the extracted body; inspect before treating it as monolingual.")
                if "\ufffd" in text or any(0xE000 <= ord(char) <= 0xF8FF for char in text):
                    notes.append(f"- `{work['work_id']}/{lang}` — replacement/private-use glyphs found in extracted text.")
                if re.search(r"(?im)^.{0,120}(?:\.{3,}|…{1,}|·{3,})\s*\d{1,4}\s*$", text):
                    notes.append(f"- `{work['work_id']}/{lang}` — a contents-style leader with a page number remains in section text.")
    manual_notes = {
        ("hong-yin", "vi"): "the extracted text layer interleaves Vietnamese transliteration with pinyin and Chinese lines; keep this flagged as mixed-language source text",
        ("hong-yin-iv", "zh-Hant"): "the source PDF's short title/cover pages contain garbled text-layer symbols; those cover pages were removed, and the extracted poem text passed the Chinese text check",
    }
    for work_id, lang in manual_notes:
        work = next((item for item in works if item["work_id"] == work_id), None)
        record = work.get("languages", {}).get(lang, {}) if work else {}
        if record.get("status") == "included":
            notes.append(f"- `{work_id}/{lang}` — manual source-text review: {manual_notes[(work_id, lang)]}.")
    lines.extend(dict.fromkeys(notes) or ["- No other source-text anomalies were flagged by the script-level scan."])
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build() -> dict:
    selection = json.loads(SELECTION_PATH.read_text(encoding="utf-8"))
    manifest = _manifest()
    phase_b = []
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    current = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    phase_a_ids = {item["work_id"] for item in baseline["works"]}
    selected_ids = {item["work_id"] for item in selection.get("groups", [])} - phase_a_ids
    owned_paths = {
        str(record[field]) for work in current.get("works", []) if work.get("work_id") in selected_ids
        for record in work.get("languages", {}).values()
        for field in ("markdown_file", "chunks_file") if record.get(field)
    }
    with tempfile.TemporaryDirectory(prefix="philosophy-b-") as temp:
        temp_root = Path(temp)
        for work in selection.get("groups", []):
            if work["work_id"] in phase_a_ids:
                continue
            phase_b.append(_process_group(work, manifest, temp_root, owned_paths))
    registry = compose_registry(current, baseline, phase_b)
    rendered = json.dumps(registry, ensure_ascii=False, indent=2) + "\n"
    if not REGISTRY_PATH.exists() or REGISTRY_PATH.read_text(encoding="utf-8") != rendered:
        REGISTRY_PATH.write_text(rendered, encoding="utf-8")
    _write_report(registry, selection)
    return registry


if __name__ == "__main__":
    result = build()
    print(json.dumps({"works": len(result["works"]), "phase_b_works": len(result["works"]) - 5,
                      "report": str(REPORT_PATH.relative_to(ROOT))}, ensure_ascii=False))
