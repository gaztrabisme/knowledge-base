#!/usr/bin/env python3
"""Seeded candidate picker for U6. Chooses chunks only; it never writes queries."""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
WORKS = ROOT / "data/philosophy/works.json"
OUT = Path(__file__).resolve().parent / "candidates.jsonl"
SEED = 20261001
LANGUAGES = ("en", "vi", "zh-Hans", "zh-Hant")
EXCLUDED = {
    "original-library", "zhuan-falun", "tao-te-ching-jonathan-star",
    "tao-te-ching-stephen-mitchell", "tao-te-ching-tse-lao",
}
COUNTS = {"book": 16, "writing": 10}

rng = random.Random(SEED)
works_data = json.loads(WORKS.read_text(encoding="utf-8"))
rows = []
for language in LANGUAGES:
    pools = {kind: [] for kind in COUNTS}
    for work in works_data["works"]:
        work_id = work["work_id"]
        if work_id in EXCLUDED:
            continue
        kind = work.get("kind", "writing")
        if kind not in pools:
            continue
        language_meta = work.get("languages", {}).get(language, {})
        if language_meta.get("status") != "included" or not language_meta.get("chunks_file"):
            continue
        chunk_path = ROOT / language_meta["chunks_file"]
        if not chunk_path.is_file():
            continue
        payload = json.loads(chunk_path.read_text(encoding="utf-8"))
        children = payload.get("children", [])
        if not children:
            continue
        pools[kind].append((work, language_meta, chunk_path, children))
    for kind, wanted in COUNTS.items():
        if len(pools[kind]) < wanted:
            raise SystemExit(f"Need {wanted} {kind} candidates for {language}; found {len(pools[kind])}")
        chosen = rng.sample(pools[kind], wanted)
        for work, language_meta, chunk_path, children in chosen:
            index = rng.randrange(len(children))
            child = children[index]
            rows.append({
                "language": language,
                "kind": kind,
                "work_id": work["work_id"],
                "derived": bool(language_meta.get("derived", False)),
                "chunk_file": str(chunk_path.relative_to(ROOT)),
                "child_index": index,
                "target_chunk_id": child["child_id"],
                "section_key": child.get("metadata", {}).get("section_key", ""),
                "target_text": child.get("text", ""),
                "previous_text": children[index - 1].get("text", "") if index else "",
                "next_text": children[index + 1].get("text", "") if index + 1 < len(children) else "",
            })
rng.shuffle(rows)
OUT.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
print(f"seed={SEED} candidates={len(rows)} file={OUT.relative_to(ROOT)}")
for language in LANGUAGES:
    subset = [row for row in rows if row["language"] == language]
    books = sum(row["kind"] == "book" for row in subset)
    writings = sum(row["kind"] == "writing" for row in subset)
    nonderived = sum(not row["derived"] for row in subset)
    print(f"{language}: {len(subset)} candidates ({books} books, {writings} writings, {nonderived} not-derived)")
