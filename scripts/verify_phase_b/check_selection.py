"""Phase B U2 acceptance: data/philosophy/phase-b/selection.json covers the archive manifest.

Written by the coordinator before dispatch. Exits 0 when every rule holds; prints each violation.
"""
from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
ARCHIVE = Path("/Users/GaryT/Documents/books/falun-dafa-pdf-archive")
SELECTION = ROOT / "data" / "philosophy" / "phase-b" / "selection.json"
LANG = {"en": "en", "vi": "vi", "gb": "zh-Hans", "big5": "zh-Hant"}
PHASE_A_IDS = {"original-library", "tao-te-ching-jonathan-star", "tao-te-ching-stephen-mitchell",
               "tao-te-ching-tse-lao"}
STATUSES = {"included", "derive", "skipped", "phase-a"}


def main() -> int:
    bad: list[str] = []
    manifest = json.loads((ARCHIVE / "manifest.json").read_text(encoding="utf-8"))
    outputs = {o["output_id"]: o for o in manifest["outputs"] if o["kind"] != "writing_variant"}
    wanted = {(LANG[o["language"]], o["title"]) for o in outputs.values()}
    selection = json.loads(SELECTION.read_text(encoding="utf-8"))
    groups = selection["groups"]

    seen_ids: set[str] = set()
    covered: dict[tuple[str, str], str] = {}
    chinese_included: list[tuple[str, dict]] = []
    for group in groups:
        work_id = group.get("work_id", "")
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", work_id):
            bad.append(f"bad work_id {work_id!r}")
        if work_id in seen_ids or work_id in PHASE_A_IDS:
            bad.append(f"duplicate or reserved work_id {work_id}")
        seen_ids.add(work_id)
        if group.get("kind") not in {"book", "writing"}:
            bad.append(f"{work_id}: kind must be book or writing")
        languages = group.get("languages", {})
        if not languages:
            bad.append(f"{work_id}: no languages")
        for lang, record in languages.items():
            if lang not in LANG.values():
                bad.append(f"{work_id}: bad language code {lang}")
                continue
            title = group.get("titles", {}).get(lang)
            if not title:
                bad.append(f"{work_id}/{lang}: no title")
            key = (lang, title)
            if key in covered:
                bad.append(f"{key} appears in both {covered[key]} and {work_id}")
            covered[key] = work_id
            # Other manifest titles in this language that are the same work (not selected).
            for other in record.get("other_titles", []):
                other_key = (lang, other.get("title"))
                if other_key in covered:
                    bad.append(f"{other_key} appears in both {covered[other_key]} and {work_id}")
                if not other.get("reason"):
                    bad.append(f"{work_id}/{lang}: other_titles entry without a reason")
                covered[other_key] = work_id
            status = record.get("status")
            if status not in STATUSES:
                bad.append(f"{work_id}/{lang}: bad status {status!r}")
                continue
            if status == "phase-a" and work_id != "zhuan-falun":
                bad.append(f"{work_id}/{lang}: only zhuan-falun may be phase-a")
            if status in {"included", "derive", "phase-a"} and work_id == "zhuan-falun" and status != "phase-a":
                bad.append(f"zhuan-falun/{lang}: must stay phase-a")
            if status == "skipped" and not record.get("reason"):
                bad.append(f"{work_id}/{lang}: skipped without a reason")
            if status == "included":
                output_id = record.get("output_id")
                if output_id is not None:
                    out = outputs.get(output_id)
                    if out is None:
                        bad.append(f"{work_id}/{lang}: output_id {output_id} is not a non-variant manifest output")
                        continue
                    if LANG[out["language"]] != lang or out["title"] != title:
                        bad.append(f"{work_id}/{lang}: output {output_id} is {out['language']}/{out['title']}")
                    path = ARCHIVE / out["pdf_path"]
                else:
                    path = Path(record.get("file", ""))
                    if not record.get("source_note"):
                        bad.append(f"{work_id}/{lang}: a file outside the manifest needs source_note")
                if not path.is_file():
                    bad.append(f"{work_id}/{lang}: file missing {path}")
                    continue
                if not record.get("edition_reason"):
                    bad.append(f"{work_id}/{lang}: no edition_reason")
                if lang.startswith("zh"):
                    check = record.get("text_check") or {}
                    if check.get("passed") is not True:
                        bad.append(f"{work_id}/{lang}: included Chinese file without a passed text_check")
                    chinese_included.append((f"{work_id}/{lang}", {"path": path, "lang": lang, "check": check}))
            if status == "derive":
                if lang != "zh-Hant":
                    bad.append(f"{work_id}/{lang}: only zh-Hant may be derived")
                source = languages.get("zh-Hans", {})
                if source.get("status") != "included" or record.get("derive_from_output_id") != source.get("output_id"):
                    bad.append(f"{work_id}/{lang}: derive needs an included zh-Hans edition in the same group")
                if not record.get("reason"):
                    bad.append(f"{work_id}/{lang}: derive without the reason the Traditional file was rejected")

    for key in sorted(wanted - set(covered)):
        bad.append(f"manifest title not placed in any group: {key}")
    for key in sorted(set(covered) - wanted):
        work = covered[key]
        record = next(g for g in groups if g["work_id"] == work)["languages"][key[0]]
        if key[1] != next(g for g in groups if g["work_id"] == work)["titles"].get(key[0]):
            bad.append(f"other_titles entry not in the manifest: {key} ({work})")
            continue
        if record.get("status") == "included" and record.get("output_id") is None:
            continue  # a file from outside the manifest (the Hồng Ngâm retry)
        if record.get("status") == "derive":
            continue
        bad.append(f"group title not in the manifest: {key} ({work})")

    # Recompute the Chinese text check on a sample, independently of the builder's numbers.
    from knowledge_base.philosophy.textcheck import check_pdf
    rng = random.Random(20260930)
    for label, item in rng.sample(chinese_included, min(15, len(chinese_included))):
        mine = check_pdf(item["path"], item["lang"])
        if not mine.passed:
            bad.append(f"{label}: recomputed text check fails ({mine.outside_share:.3f})")
        recorded = item["check"].get("outside_share")
        if recorded is None or abs(recorded - mine.outside_share) > 0.01:
            bad.append(f"{label}: recorded outside_share {recorded} vs recomputed {mine.outside_share:.4f}")

    by_status: dict[str, int] = {}
    for group in groups:
        for record in group["languages"].values():
            by_status[record.get("status")] = by_status.get(record.get("status"), 0) + 1
    multi = sum(1 for g in groups if len(g["languages"]) > 1)
    print(f"groups {len(groups)} (multi-language {multi}); language records by status {by_status}")
    print("\n".join(bad[:80]) if bad else "OK")
    if len(bad) > 80:
        print(f"... and {len(bad) - 80} more")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
