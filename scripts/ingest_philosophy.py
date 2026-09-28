#!/usr/bin/env python3
"""Ingest the phase-A multilingual philosophy collection without touching the technical shelf."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pymupdf
from opencc import OpenCC

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from knowledge_base.philosophy.alignment import (
    Section,
    original_library_sections,
    tao_epub_sections,
    tao_pdf_sections,
    zhuan_falun_sections,
)
from knowledge_base.philosophy.chunking import write_work_chunks
from knowledge_base.philosophy.textcheck import TextCheck, check_pdf, check_text, compare_editions

BOOKS_DIR = Path("/Users/GaryT/Documents/books")
ARCHIVE = BOOKS_DIR / "falun-dafa-pdf-archive"
REGISTRY_PATH = ROOT / "data" / "philosophy" / "works.json"
TTC_BACK_MATTER_HEADINGS = {
    "notes", "endnotes", "commentary", "afterword", "about the translator",
    "about the author", "acknowledgments", "acknowledgements", "bibliography",
}


def _result(check: TextCheck, *, status: str | None = None) -> dict:
    item = check.to_dict()
    item["status"] = status or ("passed" if check.passed else "failed")
    return item


def _pages(path: Path) -> int:
    with pymupdf.open(str(path)) as doc:
        return doc.page_count


def _record(
    *, work_id: str, lang: str, source_file: Path, edition: str, page_count: int | None,
    text_check: dict, sections=None, title: str, translator: str = "", work_group: str | None = None,
    derived: bool = False,
) -> dict:
    work_group = work_group or work_id
    record = {
        "file": str(source_file),
        "edition": edition,
        "page_count": page_count,
        "text_check": text_check,
        "status": "included" if sections is not None else "skipped",
        "markdown_file": None,
        "chunks_file": None,
        "chunk_count": 0,
    }
    if sections is not None:
        markdown_path, chunks_path, count = write_work_chunks(
            work_id=work_id, lang=lang, work_group=work_group, title=title,
            sections=sections, edition=edition, translator=translator, derived=derived,
        )
        record.update({
            "markdown_file": str(markdown_path.relative_to(ROOT)),
            "chunks_file": str(chunks_path.relative_to(ROOT)),
            "chunk_count": count,
            "section_count": len(sections),
            "translator": translator,
        })
    if derived:
        record["derived"] = True
    return record


def _sections_from_markdown(path: Path) -> list[Section]:
    """Read alignment sections from the accepted Hans markdown without changing their keys."""
    text = path.read_text(encoding="utf-8")
    heading = re.compile(r"(?m)^# (?P<key>zfl-[A-Za-z0-9-]+) — (?P<title>.*?)\s*$")
    matches = list(heading.finditer(text))
    sections = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.append(Section(
            match.group("key"), match.group("title"), text[match.end():end].strip(),
        ))
    expected = ["zfl-front-lunyu", *(f"zfl-L{i}" for i in range(1, 10))]
    found = [section.section_key for section in sections]
    if found != expected:
        raise ValueError(f"Expected Zhuan Falun section keys {expected} in {path.name}, got {found}")
    return sections


def _split_tao_back_matter(sections: list[Section]) -> list[Section]:
    """Move chapter 81 back matter to a searchable section outside alignment."""
    chapter = next((section for section in sections if section.section_key == "ttc-081"), None)
    if chapter is None:
        raise ValueError("Tao Te Ching input is missing ttc-081")

    lines = chapter.text.splitlines()
    for index, line in enumerate(lines):
        heading = re.sub(r"^[ \t]{0,3}#{1,6}[ \t]*", "", line).strip()
        heading = re.sub(r"[*`_]", "", heading).strip().rstrip(":").strip()
        if heading.casefold() not in TTC_BACK_MATTER_HEADINGS:
            continue

        chapter_text = "\n".join(lines[:index]).strip()
        back_matter = "\n".join(lines[index + 1:]).strip()
        if not chapter_text or not back_matter:
            raise ValueError(f"Incomplete back matter at {heading!r} in ttc-081")
        split = sections.index(chapter)
        return [
            *sections[:split],
            Section(chapter.section_key, chapter.section_title, chapter_text),
            Section("ttc-notes", heading, back_matter),
            *sections[split + 1:],
        ]
    return sections


def _zfl_candidates(manifest: dict, language: str, title: str) -> list[dict]:
    return [
        item for item in manifest["outputs"]
        if item.get("language") == language and item.get("kind") == "book"
        and item.get("title") == title
    ]


def _manifest_path(item: dict) -> Path:
    return ARCHIVE / item["pdf_path"]


def build() -> dict:
    registry = {"schema_version": 1, "works": []}

    # The PDF bookmark order is the cross-language alignment contract (38 entries).
    original = {
        "work_id": "original-library",
        "work_group": "original-library",
        "titles": {
            "en": "The Original Library",
            "vi": "Thư Viện Bản Nguyên",
            "zh-Hant": "本源圖書館",
        },
        "languages": {},
    }
    original_sources = {
        "en": (BOOKS_DIR / "ORIGINAL LIBRARY - ENGLISH VERSION.docx.pdf", "English source edition"),
        "zh-Hant": (BOOKS_DIR / "本源圖書館 - 繁體中文版.docx.pdf", "Traditional Chinese source edition"),
        "vi": (BOOKS_DIR / "Thư Viện - Master OS .pdf", "Vietnamese source edition"),
    }
    for lang, (source, edition) in original_sources.items():
        sections, page_count = original_library_sections(source)
        if lang == "zh-Hant":
            check = check_pdf(source, lang)
            text_quality = _result(check)
            text_quality["comparison"] = {"peer_count": 0, "note": "only one Traditional Chinese edition was supplied"}
        else:
            text_quality = {"status": "not_applicable", "passed": True, "outside_share": 0.0,
                            "reason": "not a Chinese-language edition"}
        original["languages"][lang] = _record(
            work_id=original["work_id"], lang=lang, source_file=source, edition=edition,
            page_count=page_count, text_check=text_quality, sections=sections,
            title=original["titles"][lang],
        )
    registry["works"].append(original)

    # Three independent translation records keep one edition per work/language,
    # while their identical ttc-NNN keys make the 81 chapter alignment explicit.
    tao_sources = [
        ("tao-te-ching-jonathan-star", "en", BOOKS_DIR / "Tao Te Ching (Lao Tzu, Jonathan Star).epub",
         "Jonathan Star", "Jonathan Star, 2008-01-10 (The Definitive Edition)", True),
        ("tao-te-ching-stephen-mitchell", "en", BOOKS_DIR / "Tao Te Ching (Stephen Mitchell, Lao Tzu).pdf",
         "Stephen Mitchell", "Stephen Mitchell English translation (provided PDF)", False),
        ("tao-te-ching-tse-lao", "es", BOOKS_DIR / "Tao Te Ching (Tse Lao).epub",
         "Tse Lao", "Tse Lao Spanish translation (provided EPUB)", False),
    ]
    for work_id, lang, source, translator, edition, verse_heading in tao_sources:
        if source.suffix.lower() == ".pdf":
            sections, page_count = tao_pdf_sections(source)
        else:
            sections, page_count = tao_epub_sections(source, verse_heading=verse_heading)
        sections = _split_tao_back_matter(sections)
        body_han = sum(1 for section in sections for char in section.text
                       if "\u3400" <= char <= "\u9fff")
        work = {
            "work_id": work_id,
            "work_group": "tao-te-ching",
            "titles": {lang: "Tao Te Ching"},
            "languages": {
                lang: _record(
                    work_id=work_id, lang=lang, source_file=source, edition=edition,
                    page_count=page_count,
                    text_check={"status": "not_present" if body_han == 0 else "present",
                                "passed": True, "cjk_count_in_aligned_text": body_han,
                                "reason": "no Chinese original in the aligned chapter text" if body_han == 0
                                else "Chinese characters present; inspect whether they form the original text"},
                    sections=sections, title="Tao Te Ching", translator=translator,
                    work_group="tao-te-ching",
                ),
            },
            "translator": translator,
        }
        registry["works"].append(work)

    manifest = json.loads((ARCHIVE / "manifest.json").read_text(encoding="utf-8"))
    zfl = {
        "work_id": "zhuan-falun",
        "work_group": "zhuan-falun",
        "titles": {"en": "Zhuan Falun", "vi": "Chuyển Pháp Luân",
                   "zh-Hans": "转法轮", "zh-Hant": "轉法輪"},
        "languages": {},
        "edition_candidates": {"zh-Hans": [], "zh-Hant": []},
    }
    zfl_specs = [
        ("en", "Zhuan Falun (The main text of Falun Dafa)"),
        ("vi", "Chuyển Pháp Luân"),
        ("gb", "转法轮"),
        ("big5", "轉法輪"),
    ]
    candidates = {lang: _zfl_candidates(manifest, lang, title) for lang, title in zfl_specs}
    all_chinese_checks = {}
    for lang in ("gb", "big5"):
        for item in candidates[lang]:
            path = _manifest_path(item)
            all_chinese_checks[item["output_id"]] = check_pdf(path, "zh-Hans" if lang == "gb" else "zh-Hant")
    checked = {}
    # Compare layout variants only within the same script. Hans and Hant are
    # both Chinese, but their common-character sets differ and must not be used
    # as peers for one another.
    for manifest_lang in ("gb", "big5"):
        language_checks = {
            item["output_id"]: all_chinese_checks[item["output_id"]]
            for item in candidates[manifest_lang]
        }
        checked.update(compare_editions(language_checks))
    for source_lang, manifest_lang in (("zh-Hans", "gb"), ("zh-Hant", "big5")):
        other_manifest_lang = "big5" if manifest_lang == "gb" else "gb"
        other_script_shares = [
            check.outside_share for item in candidates[other_manifest_lang]
            if (check := all_chinese_checks[item["output_id"]]).cjk_count
        ]
        for item in candidates[manifest_lang]:
            check = checked[item["output_id"]]
            check_record = _result(check)
            comparison = check_record.setdefault("comparison", {})
            comparison["other_script_reference"] = {
                "peer_count": len(other_script_shares),
                "peer_median_outside_share": (
                    sorted(other_script_shares)[len(other_script_shares) // 2]
                    if len(other_script_shares) % 2 else
                    (sorted(other_script_shares)[len(other_script_shares) // 2 - 1]
                     + sorted(other_script_shares)[len(other_script_shares) // 2]) / 2
                    if other_script_shares else None
                ),
                "note": "reference only; absolute thresholds use the language-specific character set",
            }
            zfl["edition_candidates"][source_lang].append({
                "file": str(_manifest_path(item)),
                "edition": item.get("edition") or item.get("layout_or_variant") or "archive edition",
                "layout_or_variant": item.get("layout_or_variant"),
                "page_count": item.get("pages"),
                "text_check": check_record,
            })

    # Only primary English/Vietnamese editions are eligible; the English manifest
    # labels make the 2018 translation the newest primary version.
    en_primary = [item for item in candidates["en"] if item.get("layout_or_variant") == "primary"]
    vi_primary = [item for item in candidates["vi"] if item.get("layout_or_variant") == "primary"]
    edition_year = lambda item: max(map(int, re.findall(r"\d{4}", item.get("edition", "") or "")), default=0)
    english = max(en_primary, key=edition_year)
    vietnamese = max(vi_primary, key=edition_year)
    for language, item, parse_lang in (("en", english, "en"), ("vi", vietnamese, "vi")):
        source = _manifest_path(item)
        sections, page_count = zhuan_falun_sections(source, parse_lang)
        translator = item.get("edition") or f"{language} translation"
        zfl["languages"][language] = _record(
            work_id="zhuan-falun", lang=language, source_file=source,
            edition=item.get("edition") or "primary archive edition", page_count=page_count,
            text_check={"status": "not_applicable", "passed": True,
                        "reason": "not a Chinese-language edition"},
            sections=sections, title=zfl["titles"][language], translator=translator,
        )

    # The archive has no primary Simplified Chinese layout label. Choose a passing
    # two-up layout only after confirming all nine body headings and maximal page coverage.
    han_candidates = []
    for item in candidates["gb"]:
        quality = checked[item["output_id"]]
        if not quality.passed:
            continue
        try:
            sections, page_count = zhuan_falun_sections(_manifest_path(item), "zh-Hans", two_up=True)
        except (ValueError, RuntimeError):
            continue
        han_candidates.append((len(sections), -page_count, item, sections, page_count, quality))
    if not han_candidates:
        raise RuntimeError("No complete, clean Simplified Chinese Zhuan Falun candidate found")
    _, _, han_item, han_sections, han_page_count, han_quality = max(han_candidates, key=lambda row: (row[0], row[1]))
    zfl["languages"]["zh-Hans"] = _record(
        work_id="zhuan-falun", lang="zh-Hans", source_file=_manifest_path(han_item),
        edition=han_item.get("layout_or_variant") or "archive Simplified Chinese edition",
        page_count=han_page_count, text_check=_result(han_quality), sections=han_sections,
        title=zfl["titles"]["zh-Hans"], translator="Simplified Chinese edition",
    )

    hant_candidates = candidates["big5"]
    hant_item = hant_candidates[0] if hant_candidates else None
    if hant_item is not None:
        quality = checked[hant_item["output_id"]]
        hant_quality = _result(quality)
        hant_quality["comparison"] = next(
            row["text_check"]["comparison"] for row in zfl["edition_candidates"]["zh-Hant"]
            if row["file"] == str(_manifest_path(hant_item))
        )
        zfl["languages"]["zh-Hant"] = _record(
            work_id="zhuan-falun", lang="zh-Hant", source_file=_manifest_path(hant_item),
            edition=hant_item.get("layout_or_variant") or "archive Traditional Chinese edition",
            page_count=hant_item["pages"], text_check=hant_quality, sections=None,
            title=zfl["titles"]["zh-Hant"], translator="Traditional Chinese edition",
        )

    # Supply a clearly labelled script conversion from the accepted Hans text.
    # Keep the rejected PDF's source and text-check record attached for auditability.
    hant_pdf_record = zfl["languages"].get("zh-Hant")
    hans_markdown = ROOT / "data" / "markdown" / "philosophy" / "zhuan-falun.zh-Hans.md"
    converter = OpenCC("s2t")
    derived_sections = [
        Section(section.section_key, converter.convert(section.section_title), converter.convert(section.text))
        for section in _sections_from_markdown(hans_markdown)
    ]
    derived_edition = "derived from zh-Hans via OpenCC s2t"
    derived_text = "\n\n".join(section.text for section in derived_sections)
    derived_check = _result(check_text(derived_text, "zh-Hant"))
    derived_check["reason"] = "script-converted from accepted zh-Hans; common-character check only"
    derived_record = _record(
        work_id="zhuan-falun", lang="zh-Hant", source_file=hans_markdown,
        edition=derived_edition, page_count=None, text_check=derived_check,
        sections=derived_sections, title=zfl["titles"]["zh-Hant"],
        translator="OpenCC s2t (derived from zh-Hans)", derived=True,
    )
    if hant_pdf_record:
        derived_record["rejected_pdf"] = {
            "file": hant_pdf_record["file"],
            "edition": hant_pdf_record["edition"],
            "page_count": hant_pdf_record["page_count"],
            "status": hant_pdf_record["status"],
            "text_check": hant_pdf_record["text_check"],
        }
    zfl["languages"]["zh-Hant"] = derived_record
    registry["works"].append(zfl)

    # Remove stale language outputs for the work ids this ingest owns (for
    # example, if a source is correctly reclassified from English to Spanish).
    owned_ids = {item["work_id"] for item in registry["works"]}
    expected_markdown = {
        Path(record["markdown_file"]).name
        for item in registry["works"] for record in item["languages"].values()
        if record.get("status") == "included" and record.get("markdown_file")
    }
    expected_chunks = {
        Path(record["chunks_file"]).name
        for item in registry["works"] for record in item["languages"].values()
        if record.get("status") == "included" and record.get("chunks_file")
    }
    for directory, expected, suffix in (
        (ROOT / "data" / "markdown" / "philosophy", expected_markdown, ".md"),
        (ROOT / "data" / "chunks" / "philosophy", expected_chunks, ".json"),
    ):
        for path in directory.glob(f"*{suffix}"):
            if path.stem.split(".", 1)[0] in owned_ids and path.name not in expected:
                path.unlink()

    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for work in registry["works"]:
        for lang, record in work["languages"].items():
            if record["status"] == "included":
                path = ROOT / record["chunks_file"]
                chunks = json.loads(path.read_text(encoding="utf-8"))
                keys = {child["metadata"]["section_key"] for child in chunks["children"]}
                if len(keys) != record["section_count"]:
                    raise RuntimeError(f"Incomplete section keys in {path.name}: {len(keys)} of {record['section_count']}")
    return registry


if __name__ == "__main__":
    result = build()
    print(json.dumps({
        work["work_id"]: {
            lang: {"status": record["status"], "chunks": record["chunk_count"],
                  "pages": record["page_count"], "text_check": record["text_check"]["status"]}
            for lang, record in work["languages"].items()
        }
        for work in result["works"]
    }, ensure_ascii=False, indent=2))
