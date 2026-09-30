#!/usr/bin/env python3
"""Build the explicit Phase B selection from the reviewed title map."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = Path("/Users/GaryT/Documents/books/falun-dafa-pdf-archive")
LANG = {"en": "en", "vi": "vi", "gb": "zh-Hans", "big5": "zh-Hant"}
PHASE_A = "zhuan-falun"

sys.path.insert(0, str(ROOT))
from knowledge_base.philosophy.textcheck import check_pdf


def _aliases(group: dict, lang: str) -> list[dict]:
    return group.get("other_titles", {}).get(lang, [])


def _manifest_index(manifest: dict) -> tuple[dict, dict]:
    outputs, by_title = {}, defaultdict(list)
    for item in manifest["outputs"]:
        if item["kind"] == "writing_variant":
            continue
        lang = LANG[item["language"]]
        outputs[item["output_id"]] = item
        by_title[(lang, item["title"])].append(item)
    return outputs, by_title


def _validate_map(title_map: dict, by_title: dict) -> None:
    covered: dict[tuple[str, str], str] = {}
    for group in title_map["groups"]:
        if not str(group.get("basis", "")).strip():
            raise ValueError(f"{group.get('work_id', '(unknown work)')}: title map group needs a basis string")
        for lang, title in group.get("titles", {}).items():
            key = (lang, title)
            if key in covered:
                raise ValueError(f"title map duplicate {key}: {covered[key]} and {group['work_id']}")
            covered[key] = group["work_id"]
        for lang, aliases in group.get("other_titles", {}).items():
            for alias in aliases:
                key = (lang, alias["title"])
                if key in covered:
                    raise ValueError(f"title map duplicate alias {key}: {covered[key]} and {group['work_id']}")
                covered[key] = group["work_id"]
    missing = set(by_title) - set(covered)
    extra = set(covered) - set(by_title)
    if missing or extra:
        raise ValueError(f"title map coverage mismatch; missing={sorted(missing)[:8]}, extra={sorted(extra)[:8]}")


def _page_count(item: dict, archive: Path) -> int:
    if item.get("pages") is not None:
        return int(item["pages"])
    with pymupdf.open(str(item["file"] if item.get("file") else archive / item["pdf_path"])) as doc:
        return doc.page_count


def _layout_rank(item: dict) -> int:
    label = (item.get("layout_or_variant") or "").casefold()
    if "2合1" in label:
        return 1
    if "4合1" in label:
        return 2
    return 0


def _english_choice(group: dict, lang: str, items: list[dict]) -> tuple[dict, str]:
    choices = group.get("edition_choices", {}).get(lang)
    if len(items) == 1:
        item = items[0]
        return item, f"Only indexed edition for this title ({item.get('edition') or item.get('layout_or_variant') or 'primary'})."
    if not choices:
        raise ValueError(f"{group['work_id']}/{lang}: multiple editions need an explicit edition_choices entry")
    chosen = next((item for item in items if item["output_id"] == choices["output_id"]), None)
    if chosen is None:
        raise ValueError(f"{group['work_id']}/{lang}: preferred edition is not a candidate")
    return chosen, choices["reason"]


def _retry_candidates(retry_path: Path, title_map: dict) -> dict[int, list[dict]]:
    if not retry_path.is_file():
        return {}
    data = json.loads(retry_path.read_text(encoding="utf-8"))
    result = defaultdict(list)
    rows = data if isinstance(data, list) else data.get("fetched", [])
    slots = {15: 1, 26: 2, 39: 3, 45: 4, 46: 5, 47: 6}
    for row in rows:
        if isinstance(row, str):
            row = {"file": row}
        raw_path = row.get("file") or row.get("path") or row.get("local_path")
        if not raw_path:
            raise ValueError(f"Retry entry has no local file path: {row}")
        path = Path(raw_path)
        if not path.is_absolute():
            path = retry_path.parent / path
        path = path.resolve()
        if not path.is_file():
            raise ValueError(f"Retry file does not exist: {path}")
        hint = " ".join(str(row.get(key, "")) for key in ("title", "volume", "edition", "file", "path", "source_url", "url"))
        source_index = re.search(r"vi_book_(\d{4})_", str(row.get("source_item_id", "")))
        volume = slots.get(int(source_index.group(1))) if source_index else None
        match = re.search(r"(?:Hồng\s*Ngâm|Hong\s*Yin)\s*(VI|IV|V|III|II|I|[1-6])\b", hint, re.I)
        if volume is None and match:
            roman = match.group(1).upper()
            volume = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6}.get(roman, int(roman) if roman.isdigit() else 0)
        if volume is None and re.search(r"hongngam_?2026", hint, re.I):
            volume = 1
        if volume is None:
            raise ValueError(f"Could not identify Hồng Ngâm volume from retry entry: {row}")
        years = [int(year) for year in re.findall(r"(?:19|20)\d{2}", hint)]
        year = max(years, default=0)
        result[volume].append({
            "output_id": None,
            "file": str(path),
            "edition": row.get("edition") or f"Official Vietnamese source edition{f' ({year})' if year else ''}",
            "pages": row.get("pages"),
            "source_note": "Vietnamese Hồng Ngâm edition fetched by data/philosophy-sources/hong-ngam/hong-ngam-retry.json",
            "retry": True,
            "source_url": row.get("source_url") or row.get("url", ""),
            "published_year": year,
        })
    return dict(result)


def build_selection(manifest: dict, title_map: dict, archive: Path = ARCHIVE,
                    retry_path: Path | None = None) -> dict:
    outputs, by_title = _manifest_index(manifest)
    _validate_map(title_map, by_title)
    retry = _retry_candidates(retry_path, title_map) if retry_path else {}
    groups = []
    for spec in title_map["groups"]:
        titles = dict(spec["titles"])
        if spec.get("retry_hong_ngam_volume") in retry and "vi" not in titles:
            titles["vi"] = spec.get("optional_titles", {}).get("vi")
        records = {}
        for lang, title in titles.items():
            if not title:
                continue
            items = list(by_title.get((lang, title), []))
            volume = spec.get("retry_hong_ngam_volume")
            if lang == "vi" and volume in retry:
                items.extend(retry[volume])
            if not items:
                continue
            checked = []
            if lang.startswith("zh"):
                for item in items:
                    path = item["file"] if item.get("file") else archive / item["pdf_path"]
                    checked.append((item, check_pdf(path, lang).to_dict()))
            if spec["work_id"] == PHASE_A:
                record = {"status": "phase-a", "output_id": None,
                          "edition_reason": "Phase A Zhuan Falun record; edition selection is intentionally deferred."}
                if checked:
                    record["candidates"] = [{"output_id": item.get("output_id"), "text_check": check}
                                             for item, check in checked]
                records[lang] = record
                continue

            if lang == "zh-Hans":
                passing = [(item, check) for item, check in checked if check["passed"]]
                if not passing:
                    best, best_check = min(checked, key=lambda pair: (pair[1]["outside_share"], _layout_rank(pair[0])))
                    record = {"status": "skipped", "output_id": best.get("output_id"),
                              "edition": best.get("edition") or best.get("layout_or_variant") or "primary",
                              "pages": _page_count(best, archive), "text_check": best_check,
                              "reason": f"Every Simplified layout failed the common-character check; best candidate outside_share={best_check['outside_share']:.6f}.",
                              "candidates": [{"output_id": item.get("output_id"), "text_check": check} for item, check in checked]}
                else:
                    selected, selected_check = min(passing, key=lambda pair: (_layout_rank(pair[0]), pair[0].get("output_id") or ""))
                    label = selected.get("layout_or_variant") or "one-page-per-sheet"
                    reason = (f"Checked all {len(checked)} layout candidate(s); selected passing {label} by the preference "
                              "one-page-per-sheet, then 2合1, then 4合1.") if len(checked) > 1 else "Only indexed Simplified edition; text check passed."
                    record = {"status": "included", "output_id": selected.get("output_id"),
                              "edition": selected.get("edition") or label, "pages": _page_count(selected, archive),
                              "edition_reason": reason, "text_check": selected_check,
                              "candidates": [{"output_id": item.get("output_id"), "text_check": check} for item, check in checked]}
                records[lang] = record
                continue

            if lang == "zh-Hant":
                selected, check = checked[0]
                item_fields = {"output_id": selected.get("output_id"),
                               "edition": selected.get("edition") or selected.get("layout_or_variant") or "primary",
                               "pages": _page_count(selected, archive), "text_check": check,
                               "candidates": [{"output_id": item.get("output_id"), "text_check": result} for item, result in checked]}
                if check["passed"]:
                    records[lang] = {"status": "included", **item_fields,
                                     "edition_reason": "Only indexed Traditional Chinese edition; text check passed."}
                else:
                    share = check["outside_share"]
                    hans = records.get("zh-Hans", {})
                    measured = (f"Traditional PDF failed with outside_share={share:.6f} "
                                f"({check['outside_count']}/{check['cjk_count']} CJK characters), above the 10% threshold.")
                    if hans.get("status") == "included":
                        records[lang] = {"status": "derive", **item_fields,
                                         "derive_from_output_id": hans["output_id"], "reason": measured + " Derive from this group's accepted Simplified edition."}
                    else:
                        records[lang] = {"status": "skipped", **item_fields,
                                         "reason": measured + " No included Simplified edition exists in this group."}
                continue

            if lang == "en":
                selected, reason = _english_choice(spec, lang, items)
            elif len(items) > 1 and any(item.get("retry") for item in items):
                retry_items = [item for item in items if item.get("retry")]
                selected = max(retry_items, key=lambda item: (item.get("published_year", 0), item.get("pages") or 0))
                if len(retry_items) > 1:
                    reason = (f"Selected the newest official Vietnamese source PDF ({selected.get('published_year') or 'undated'}); "
                              "checked all retry and manifest editions, including the older version(s).")
                else:
                    reason = (f"Selected the official Vietnamese source PDF ({selected.get('published_year') or 'undated'}) over the "
                              "manifest's alternate print edition as the newest official translation available.")
            else:
                selected, reason = _english_choice(spec, lang, items)
            record = {"status": "included", "output_id": selected.get("output_id"),
                      "edition": selected.get("edition") or selected.get("layout_or_variant") or "primary",
                      "pages": _page_count(selected, archive), "edition_reason": reason}
            if selected.get("file"):
                record["file"] = selected["file"]
                record["source_note"] = selected["source_note"]
            if len(items) > 1 and lang == "vi" and any(item.get("retry") for item in items):
                record["candidates"] = [
                    {key: item.get(key) for key in ("output_id", "file", "edition", "pages", "source_url") if item.get(key) is not None}
                    for item in items
                ]
            records[lang] = record

        for lang, aliases in spec.get("other_titles", {}).items():
            if lang in records:
                records[lang]["other_titles"] = aliases
        groups.append({"work_id": spec["work_id"], "kind": spec["kind"], "titles": titles,
                       "match_basis": spec["basis"], "languages": records})
    return {"schema_version": 1, "groups": groups}


def _make_report(selection: dict, manifest: dict) -> str:
    outputs, _ = _manifest_index(manifest)
    groups = selection["groups"]
    lang_counts = Counter(len(group["languages"]) for group in groups)
    statuses = Counter(record["status"] for group in groups for record in group["languages"].values())
    lines = ["# Phase B U2 report", "", "## Counts", "",
             f"- Groups: {len(groups)}", "- Groups by number of languages: " + ", ".join(f"{n} language(s): {lang_counts[n]}" for n in sorted(lang_counts)),
             "- Language records by status: " + ", ".join(f"{status}: {count}" for status, count in sorted(statuses.items())),
             "", "## Single-language groups", ""]
    single = [g for g in groups if len(g["languages"]) == 1]
    lines.extend(f"- {g['titles'].get(next(iter(g['languages'])), '(untitled)')} — {next(iter(g['languages']))} (`{g['work_id']}`)" for g in single)
    lines += ["", "## Chinese files that failed text check", ""]
    failures = {}
    for group in groups:
        for lang, record in group["languages"].items():
            if not lang.startswith("zh"):
                continue
            candidates = record.get("candidates", [])
            if not candidates and record.get("text_check"):
                candidates = [{"output_id": record.get("output_id"), "text_check": record["text_check"]}]
            for candidate in candidates:
                check = candidate.get("text_check", {})
                if check.get("passed") is False:
                    failures[candidate.get("output_id") or f"{group['work_id']}/{lang}"] = (group, lang, candidate, record)
    if failures:
        for output_id, (group, lang, candidate, record) in sorted(failures.items()):
            item = outputs.get(output_id, {})
            check = candidate["text_check"]
            action = record["status"]
            if action == "derive":
                action += f" from {record['derive_from_output_id']}"
            elif action == "phase-a":
                action += "; Phase A retains its prior Traditional-from-Simplified conversion"
            elif action == "included":
                action += " (candidate not selected)"
            lines.append(f"- `{output_id}` — {lang}, {item.get('title', group['titles'].get(lang, ''))}; "
                         f"outside share {check.get('outside_share', 0):.2%} ({check.get('outside_count')}/{check.get('cjk_count')} CJK); action: {action}.")
    else:
        lines.append("- None.")
    lines += ["", "## Edition choices with multiple candidates", ""]
    choice_count = 0
    for group in groups:
        for lang, title in group["titles"].items():
            candidates = [item for item in manifest["outputs"] if item["kind"] != "writing_variant"
                          and LANG[item["language"]] == lang and item["title"] == title]
            record = group["languages"].get(lang, {})
            listed_candidates = record.get("candidates", [])
            if len(candidates) < 2 and len(listed_candidates) < 2:
                continue
            choice_count += 1
            chosen = record.get("output_id")
            if record.get("status") == "phase-a":
                choice = "no edition selected (Phase A)"
                reason = "Phase A edition selection is intentionally deferred"
            elif record.get("status") == "skipped":
                diagnostic = f"; diagnostic candidate `{chosen}`" if chosen else ""
                choice = f"no included edition{diagnostic}"
                reason = record.get("reason", "all candidates were rejected")
            else:
                selected_name = chosen or Path(record.get("file", "retry PDF")).name
                choice = f"selected `{selected_name}` ({record.get('edition') or 'edition not named'})"
                reason = record.get("edition_reason") or record.get("reason") or "selected as the eligible candidate"
            lines.append(f"- `{group['work_id']}` / {lang} — {choice}. "
                         f"Reason: {reason.rstrip('.')}. Candidates:")
            candidate_by_id = {item["output_id"]: item for item in candidates}
            for listed in listed_candidates:
                if listed.get("output_id") is not None:
                    candidate_by_id.setdefault(listed["output_id"], outputs.get(listed["output_id"], listed))
            rendered = []
            for output_id, candidate in candidate_by_id.items():
                check = next((c.get("text_check") for c in listed_candidates if c.get("output_id") == output_id), None)
                name = candidate.get("edition") or candidate.get("layout_or_variant") or "retry file"
                pages = candidate.get("pages")
                detail = f"{name}, {candidate.get('layout_or_variant') or candidate.get('file') or 'standard layout'}, {pages} pages"
                if check:
                    detail += f"; check {check.get('outside_share', 0):.2%} ({'pass' if check.get('passed') else 'fail'})"
                rendered.append(f"  - `{output_id or candidate.get('file')}` — {detail}")
            for listed in listed_candidates:
                if listed.get("output_id") is None:
                    rendered.append(f"  - `{listed.get('file')}` — {listed.get('edition')}, {listed.get('pages')} pages")
            lines.extend(rendered)
    if not choice_count:
        lines.append("- None.")
    lines += ["", "## 20 sample groups", "", "`work_id | en title | vi title | zh-Hans title | zh-Hant title | basis`", ""]
    for group in groups[:20]:
        lines.append(" | ".join([group["work_id"], *(group["titles"].get(lang, "") for lang in ("en", "vi", "zh-Hans", "zh-Hant")), group["match_basis"]]))
    retry_picks = [record for group in groups for lang, record in group["languages"].items()
                   if lang == "vi" and record.get("source_note", "").startswith("Vietnamese Hồng Ngâm")]
    if retry_picks:
        retry_note = (f"The Hồng Ngâm retry source was present; all fetched Vietnamese I–VI files were considered. "
                      f"The selection contains {len(retry_picks)} retry-backed Vietnamese volume record(s), with the newest dated official source edition chosen.")
    else:
        retry_note = "The Vietnamese Hồng Ngâm retry file was absent at build time; no out-of-manifest Vietnamese edition was added."
    lines += ["", "## Uncertainty", "", f"- {retry_note}",
              "- The English Hong Yin and Hong Yin II candidates include one-page Open Book Reader shells and complete Version B PDFs. The complete Version B PDFs were selected; the manifest does not state a publication year for Version B, so its relative translation date cannot be established from this archive alone.",
              "- Hồng Ngâm VI is at Vietnamese local book position 0047 and English/Chinese position 0051; the source titles identify volume VI, while the index offset reflects Vietnamese omission of collected-teachings XII–XV.",
              "- Unlinked titles are kept as language-local groups rather than inferred matches. Writing links use translated titles and article source metadata; book links use aligned catalogue positions plus translated-title evidence.", ""]
    return "\n".join(lines)


def main() -> int:
    phase_dir = ROOT / "data" / "philosophy" / "phase-b"
    archive = ARCHIVE
    manifest = json.loads((archive / "manifest.json").read_text(encoding="utf-8"))
    title_map = json.loads((phase_dir / "title-map.json").read_text(encoding="utf-8"))
    retry_path = ROOT / "data" / "philosophy-sources" / "hong-ngam" / "hong-ngam-retry.json"
    selection = build_selection(manifest, title_map, archive, retry_path)
    selection_path = phase_dir / "selection.json"
    selection_path.write_text(json.dumps(selection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path = phase_dir / "u2-report.md"
    report_path.write_text(_make_report(selection, manifest), encoding="utf-8")
    print(f"Wrote {selection_path} ({len(selection['groups'])} groups)")
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"selection build failed: {exc}", file=sys.stderr)
        raise
