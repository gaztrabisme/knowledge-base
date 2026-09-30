#!/usr/bin/env python3
"""Compose the U6 sampling report from the hand-written JSONL and source chunks."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
REPORT = ROOT / "data/philosophy/phase-b/u6-report.md"
ROWS_PATH = ROOT / "data/philosophy/phase-b/sanity-b.jsonl"
works = json.loads((ROOT / "data/philosophy/works.json").read_text(encoding="utf-8"))["works"]
work_by_id = {work["work_id"]: work for work in works}
rows = [json.loads(line) for line in ROWS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
langs = ("en", "vi", "zh-Hans", "zh-Hant")

lines = [
    "# U6 phase B test set report",
    "",
    "## Sampling",
    "",
    "Seed: `20261001`.",
    "",
    "The picker in `u6-work/pick_candidates.py` excluded the Original Library, Zhuan Falun, and all three Tao Te Ching works. For each language it sampled 16 included book works and 10 included writing works without replacement, then selected one child chunk uniformly at random from each sampled work. It shuffled the 26 candidates per language after selection. The picker did not filter by text length and did not write queries. I read every candidate with its adjacent chunks before choosing targets.",
    "",
    "Of 104 sampled candidates, 24 were not retained:",
    "",
    "- 5 failed sampling rule 4: one English chunk consisted of translation notes rather than passage text; one Simplified Chinese chunk had only 75 characters; and three Traditional Chinese candidates had under 80 body characters after headings, dates, and audience notation were excluded.",
    "- 1 Simplified Chinese poem extraction was corrupted and unreadable, so no honest query could be written.",
    "- 18 candidates passed rule 4 but were left out after selecting the final 20 per language with stronger passage-specific questions and balanced work-kind coverage.",
    "",
    "The five rule 4 candidates were `stay-rational.en-p0-c3`, `a-congratulatory-letter-to-the-fa-conference-of-taiwan.zh-Hans-p0-c1`, `teachings-at-the-2004-international-conference-in-new-york.zh-Hant-p35-c6`, `hong-yin-ii.zh-Hant-p68-c0`, and `hong-yin-iv.zh-Hant-p98-c0`. The unreadable extraction was `hong-yin-iii.zh-Hans-p26-c1`.",
    "",
    "## Row counts",
    "",
    "| Language | Total | Book | Writing |",
    "|---|---:|---:|---:|",
]
for lang in langs:
    subset = [row for row in rows if row["language"] == lang]
    kinds = Counter(work_by_id[row["work_id"]].get("kind", "writing") for row in subset)
    lines.append(f"| `{lang}` | {len(subset)} | {kinds['book']} | {kinds['writing']} |")
hant = [row for row in rows if row["language"] == "zh-Hant"]
derived_counts = Counter(bool(work_by_id[row["work_id"]]["languages"]["zh-Hant"].get("derived", False)) for row in hant)
lines.extend([
    "",
    f"For `zh-Hant`, {derived_counts[True]} targets are from files flagged `derived`; {derived_counts[False]} are not derived.",
    "",
    "## Eight example rows with target text",
    "",
    "Each excerpt below is exactly the first 300 characters of the target chunk.",
    "",
])
for lang in langs:
    subset = [row for row in rows if row["language"] == lang][:2]
    for n, row in enumerate(subset, 1):
        work = work_by_id[row["work_id"]]
        chunk_path = ROOT / work["languages"][lang]["chunks_file"]
        children = json.loads(chunk_path.read_text(encoding="utf-8")).get("children", [])
        chunk = next(child for child in children if child["child_id"] == row["target_chunk_id"])
        lines.extend([
            f"### `{lang}` example {n}",
            "",
            "Row:",
            "",
            "```json",
            json.dumps(row, ensure_ascii=False),
            "```",
            "",
            "Target chunk (first 300 characters):",
            "",
            "```text",
            chunk.get("text", "")[:300],
            "```",
            "",
        ])
REPORT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
print(f"wrote {REPORT.relative_to(ROOT)}")
