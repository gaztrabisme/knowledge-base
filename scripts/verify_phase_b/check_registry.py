"""Phase B acceptance for goal rows 2 and 5: works.json against selection.json and the chunk files.

Written by the coordinator before the ingest unit was dispatched. Exits 0 when every rule holds.
  check_registry.py            registry rules (row 2)
  check_registry.py --chunks   plus chunk-file rules (row 5) and the Chinese text check on chunk text
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
PHASE_B = ROOT / "data" / "philosophy" / "phase-b"


def main() -> int:
    with_chunks = "--chunks" in sys.argv
    bad: list[str] = []
    registry = json.loads((ROOT / "data" / "philosophy" / "works.json").read_text(encoding="utf-8"))
    before = json.loads((PHASE_B / "works-phase-a.json").read_text(encoding="utf-8"))
    selection = json.loads((PHASE_B / "selection.json").read_text(encoding="utf-8"))
    works = {work["work_id"]: work for work in registry["works"]}
    if len(works) != len(registry["works"]):
        bad.append("duplicate work_id in works.json")

    for old in before["works"]:
        if works.get(old["work_id"]) != old:
            bad.append(f"phase A record changed: {old['work_id']}")

    from knowledge_base.philosophy.textcheck import check_text
    seen_children: set[str] = set()
    totals = {"included": 0, "derived": 0, "skipped": 0, "chunks": 0, "aligned_records": 0}
    for group in selection["groups"]:
        work_id = group["work_id"]
        if work_id == "zhuan-falun":
            continue
        work = works.get(work_id)
        if work is None:
            bad.append(f"{work_id}: in selection.json but not in works.json")
            continue
        keys_by_lang: dict[str, set[str]] = {}
        aligned_langs: list[str] = []
        for lang, chosen in group["languages"].items():
            record = work.get("languages", {}).get(lang)
            if record is None:
                bad.append(f"{work_id}/{lang}: no registry record")
                continue
            if chosen["status"] == "skipped":
                if record.get("status") != "skipped" or not record.get("reason"):
                    bad.append(f"{work_id}/{lang}: must be skipped with a reason")
                totals["skipped"] += 1
                continue
            if record.get("status") != "included":
                # A selected file the ingest could not use must say why.
                if record.get("status") != "skipped" or not record.get("reason"):
                    bad.append(f"{work_id}/{lang}: selected but neither included nor skipped with a reason")
                totals["skipped"] += 1
                continue
            if chosen["status"] == "derive":
                if record.get("derived") is not True:
                    bad.append(f"{work_id}/{lang}: derived edition not flagged derived")
                totals["derived"] += 1
            else:
                totals["included"] += 1
            if lang.startswith("zh") and (record.get("text_check") or {}).get("passed") is not True:
                bad.append(f"{work_id}/{lang}: Chinese record without a passed text_check")
            if "aligned" not in record:
                bad.append(f"{work_id}/{lang}: no aligned flag")
            markdown = ROOT / (record.get("markdown_file") or "missing")
            chunks = ROOT / (record.get("chunks_file") or "missing")
            if not markdown.is_file() or not chunks.is_file():
                bad.append(f"{work_id}/{lang}: markdown or chunk file missing")
                continue
            if not with_chunks:
                continue
            data = json.loads(chunks.read_text(encoding="utf-8"))
            children = data.get("children", [])
            if not children or len(children) != record.get("chunk_count"):
                bad.append(f"{work_id}/{lang}: {len(children)} children vs chunk_count {record.get('chunk_count')}")
            totals["chunks"] += len(children)
            parents = {p["parent_id"] for p in data.get("parents", [])}
            keys: set[str] = set()
            for child in children:
                meta = child.get("metadata", {})
                if child["child_id"] in seen_children:
                    bad.append(f"duplicate child_id {child['child_id']}")
                seen_children.add(child["child_id"])
                if meta.get("work_id") != work_id or meta.get("lang") != lang or not meta.get("section_key"):
                    bad.append(f"{child['child_id']}: bad work_id/lang/section_key metadata")
                    break
                if child.get("parent_id") not in parents or not child.get("text", "").strip():
                    bad.append(f"{child['child_id']}: orphan or empty child")
                    break
                keys.add(meta["section_key"])
            keys_by_lang[lang] = keys
            if record.get("aligned"):
                aligned_langs.append(lang)
                totals["aligned_records"] += 1
            if lang.startswith("zh"):
                check = check_text("\n".join(child["text"] for child in children), lang)
                if not check.passed:
                    bad.append(f"{work_id}/{lang}: chunk text fails the Chinese check ({check.outside_share:.3f})")
        if with_chunks:
            if len(aligned_langs) == 1:
                bad.append(f"{work_id}: only {aligned_langs[0]} is flagged aligned")
            for lang in aligned_langs[1:]:
                if keys_by_lang[lang] != keys_by_lang[aligned_langs[0]]:
                    bad.append(f"{work_id}: aligned languages {aligned_langs[0]} and {lang} have different section keys")
            for lang, keys in keys_by_lang.items():
                if lang in aligned_langs:
                    continue
                for other, other_keys in keys_by_lang.items():
                    if other != lang and keys & other_keys:
                        bad.append(f"{work_id}: unaligned {lang} shares section keys with {other}")

    extra = set(works) - {g["work_id"] for g in selection["groups"]} - {w["work_id"] for w in before["works"]}
    for work_id in sorted(extra):
        bad.append(f"{work_id}: in works.json but not in selection.json")
    print(f"works {len(works)}; phase B records {totals}")
    print("\n".join(bad[:80]) if bad else "OK")
    if len(bad) > 80:
        print(f"... and {len(bad) - 80} more")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
