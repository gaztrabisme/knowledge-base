"""Mechanical checks on a phase B test-set file against data/philosophy/phase-b/sanity-b-rules.md.

Covers the rules a script can check (counts, targets, language, copying). The judgment rules
(7, 8, 10) are the blind reviewer's. Usage: check_sanity_set.py <file> [--reviewed]
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PHASE_A = {"original-library", "tao-te-ching-jonathan-star", "tao-te-ching-stephen-mitchell",
           "tao-te-ching-tse-lao", "zhuan-falun"}
LANGS = ("en", "vi", "zh-Hans", "zh-Hant")
CJK = re.compile(r"[㐀-鿿]")


def main() -> int:
    path = Path(sys.argv[1])
    reviewed = "--reviewed" in sys.argv
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    bad: list[str] = []
    registry = json.loads((ROOT / "data/philosophy/works.json").read_text(encoding="utf-8"))
    records = {(w["work_id"], lang): rec for w in registry["works"] for lang, rec in w["languages"].items()}
    chunk_cache: dict[tuple[str, str], dict[str, dict]] = {}
    per_lang: Counter[str] = Counter()
    per_work: dict[str, Counter[str]] = defaultdict(Counter)
    underived_hant = 0
    for number, row in enumerate(rows, 1):
        if reviewed and row.get("verdict") == "drop":
            continue
        lang, work_id, target = row.get("language"), row.get("work_id"), row.get("target_chunk_id")
        label = f"row {number} ({target})"
        if lang not in LANGS or row.get("group") != lang or row.get("language_filter") != lang:
            bad.append(f"{label}: group/language/language_filter must be the same language code")
            continue
        if row.get("work_filter") is not None:
            bad.append(f"{label}: work_filter must be null")
        if work_id in PHASE_A or (work_id, lang) not in records:
            bad.append(f"{label}: not a phase B work-language")
            continue
        record = records[(work_id, lang)]
        key = (work_id, lang)
        if key not in chunk_cache:
            data = json.loads((ROOT / record["chunks_file"]).read_text(encoding="utf-8"))
            chunk_cache[key] = {child["child_id"]: child for child in data["children"]}
        child = chunk_cache[key].get(target)
        if child is None:
            bad.append(f"{label}: target chunk not found in {record['chunks_file']}")
            continue
        if child["metadata"].get("section_key") != row.get("section_key"):
            bad.append(f"{label}: section_key does not match the target chunk")
        text, query = child["text"], row.get("query", "")
        minimum = 80 if lang.startswith("zh") else 150
        if len(text.strip()) < minimum:
            bad.append(f"{label}: target shorter than {minimum} characters")
        is_cjk_query = len(CJK.findall(query)) >= max(2, len(query) // 3)
        if lang.startswith("zh") != is_cjk_query:
            bad.append(f"{label}: query language does not match the target language")
        if lang.startswith("zh"):
            q = re.sub(r"\s+", "", query)
            t = re.sub(r"\s+", "", text)
            if any(q[i:i + 9] in t for i in range(max(0, len(q) - 8))):
                bad.append(f"{label}: query copies more than 8 consecutive characters from the target")
        else:
            words = re.findall(r"\w+", query.casefold())
            target_text = " ".join(re.findall(r"\w+", text.casefold()))
            if any(" ".join(words[i:i + 5]) in target_text for i in range(max(0, len(words) - 4))):
                bad.append(f"{label}: query copies more than 4 consecutive words from the target")
        per_lang[lang] += 1
        per_work[lang][work_id] += 1
        if lang == "zh-Hant" and not record.get("derived"):
            underived_hant += 1
    for lang in LANGS:
        if not reviewed and per_lang[lang] != 20:
            bad.append(f"{lang}: {per_lang[lang]} rows, expected 20")
        for work_id, count in per_work[lang].items():
            if count > 1:
                bad.append(f"{lang}: {count} rows from {work_id}; at most one per work per language")
    available = sum(1 for (work, lang), rec in records.items()
                    if lang == "zh-Hant" and work not in PHASE_A and rec.get("status") == "included"
                    and not rec.get("derived"))
    if not reviewed and underived_hant < min(10, available):
        bad.append(f"zh-Hant: {underived_hant} targets from files that are not derived; need {min(10, available)}")
    print(f"rows per language {dict(per_lang)}; zh-Hant not derived {underived_hant}")
    print("\n".join(bad) if bad else "OK")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
