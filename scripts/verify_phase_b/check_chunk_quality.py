"""Phase B chunk-quality rules, added by the coordinator after reading the first U4 output.

The first ingest passed check_registry.py while its text had heading-only chunks, letter-spaced
Chinese, single-character section titles and contents lines used as sections. These rules make
those defects fail. Exits 0 when every rule holds.
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHUNKS = ROOT / "data" / "chunks" / "philosophy"
PHASE_A = {line.split()[1].split("/")[-1]
           for line in (ROOT / "data/philosophy/phase-b/phase-a-baseline.sha256").read_text().splitlines()}
CJK = re.compile(r"[㐀-鿿]")
SPACED = re.compile(r"[㐀-鿿] (?=[㐀-鿿])")
BAD_TITLES = {"contents", "table of contents", "mục lục", "目录", "目錄", "目 录", "目 錄"}


def main() -> int:
    bad: list[str] = []
    per_lang = defaultdict(lambda: {"sections": 0, "short": 0, "chunks": 0})
    sections_by_work: dict[str, dict[str, dict[str, int]]] = defaultdict(dict)
    aligned: dict[tuple[str, str], bool] = {}
    registry = json.loads((ROOT / "data/philosophy/works.json").read_text(encoding="utf-8"))
    for work in registry["works"]:
        for lang, record in work.get("languages", {}).items():
            aligned[(work["work_id"], lang)] = bool(record.get("aligned"))
    for path in sorted(CHUNKS.glob("*.json")):
        if path.name in PHASE_A:
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        lang, work_id, children = data["lang"], data["work_id"], data["children"]
        titles: dict[str, str] = {}
        lengths: dict[str, int] = defaultdict(int)
        for child in children:
            text = child["text"].strip()
            meta = child["metadata"]
            titles[meta["section_key"]] = meta.get("section_title", "")
            lengths[meta["section_key"]] += len(text)
            lines = [line for line in text.splitlines() if line.strip()]
            if text.startswith("# ") and len(lines) == 1:
                bad.append(f"{child['child_id']}: heading-only chunk")
            body = re.sub(r"\s+", "", text)
            title = re.sub(r"\s+", "", meta.get("section_title", ""))
            if title and body.replace(title, "") == "":
                bad.append(f"{child['child_id']}: chunk is only its section title")
        per_lang[lang]["chunks"] += len(children)
        per_lang[lang]["sections"] += len(titles)
        for key, title in titles.items():
            clean = title.strip()
            if len(clean) <= 2:
                per_lang[lang]["short"] += 1
            if clean.casefold() in BAD_TITLES or clean.startswith(("▪", "•", "●")):
                bad.append(f"{path.name}: section {key} has a contents or list line as its title: {clean!r}")
        if lang.startswith("zh"):
            text = "".join(child["text"] for child in children)
            count = len(CJK.findall(text))
            if count and len(SPACED.findall(text)) / count > 0.05:
                bad.append(f"{path.name}: Chinese characters separated by spaces "
                           f"({len(SPACED.findall(text)) / count:.0%})")
        sections_by_work[work_id][lang] = dict(lengths)

    for lang, numbers in sorted(per_lang.items()):
        share = numbers["short"] / max(1, numbers["sections"])
        print(f"{lang}: {numbers['chunks']} chunks, {numbers['sections']} sections, "
              f"{numbers['short']} with a title of 1-2 characters ({share:.0%})")
        if share > 0.05:
            bad.append(f"{lang}: {share:.0%} of section titles are 1-2 characters")

    # Aligned languages: each shared section's length should follow the work's overall ratio.
    for work_id, langs in sections_by_work.items():
        shared = [lang for lang in langs if aligned.get((work_id, lang))]
        for other in shared[1:]:
            first = shared[0]
            keys = [k for k in langs[first] if k in langs[other]]
            if len(keys) < 3:
                continue
            total_ratio = sum(langs[other][k] for k in keys) / max(1, sum(langs[first][k] for k in keys))
            off = 0
            for key in keys:
                ratio = langs[other][key] / max(1, langs[first][key])
                if not (total_ratio / 3 <= ratio <= total_ratio * 3):
                    off += 1
            if off / len(keys) > 0.10:
                bad.append(f"{work_id}: {first}/{other} aligned, but {off} of {len(keys)} sections "
                           f"differ in length by more than 3x the work's ratio")

    print("\n".join(bad[:60]) if bad else "OK")
    if len(bad) > 60:
        print(f"... and {len(bad) - 60} more")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
