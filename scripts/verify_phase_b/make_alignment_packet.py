"""Build the blind section-alignment packet (U5): 40 random aligned section pairs plus
20 random chunks for a reading-order check. key.json (outside the reviewer's folder) maps rows back."""
from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PHASE_A = {"original-library", "tao-te-ching-jonathan-star", "tao-te-ching-stephen-mitchell",
           "tao-te-ching-tse-lao", "zhuan-falun"}


def main(out_dir: str) -> None:
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(20261001)
    registry = json.loads((ROOT / "data/philosophy/works.json").read_text(encoding="utf-8"))
    sections: dict[tuple[str, str], dict[str, dict]] = {}
    all_children = []
    for work in registry["works"]:
        if work["work_id"] in PHASE_A:
            continue
        for lang, rec in work["languages"].items():
            if rec.get("status") != "included":
                continue
            data = json.loads((ROOT / rec["chunks_file"]).read_text(encoding="utf-8"))
            by_key: dict[str, dict] = defaultdict(lambda: {"title": "", "text": ""})
            for child in data["children"]:
                key = child["metadata"]["section_key"]
                by_key[key]["title"] = child["metadata"].get("section_title", "")
                text = child["text"]
                # Only a leading "# key — title" line is a heading; everything else is body.
                if text.startswith("# ") and "\n\n" in text:
                    text = text.split("\n\n", 1)[1]
                by_key[key]["text"] += text + "\n"
                all_children.append((work["work_id"], lang, child["child_id"], child["text"]))
            if rec.get("aligned"):
                sections[(work["work_id"], lang)] = by_key
    candidates = []
    works = defaultdict(list)
    for (work_id, lang) in sections:
        works[work_id].append(lang)
    for work_id, langs in works.items():
        langs = sorted(langs)
        for i, a in enumerate(langs):
            for b in langs[i + 1:]:
                for key in sections[(work_id, a)]:
                    if key in sections[(work_id, b)]:
                        candidates.append((work_id, key, a, b))
    rng.shuffle(candidates)
    # at most two pairs per work, so the sample spreads over works
    picked, per_work = [], defaultdict(int)
    for cand in candidates:
        if per_work[cand[0]] < 2:
            picked.append(cand); per_work[cand[0]] += 1
        if len(picked) == 40:
            break
    rows, key_rows = [], []
    for number, (work_id, key, a, b) in enumerate(picked, 1):
        sa, sb = sections[(work_id, a)][key], sections[(work_id, b)][key]
        side = lambda lang, s: {"language": lang, "section_title": s["title"],
                                "opening": " ".join(s["text"].split())[:600],
                                "ending": " ".join(s["text"].split())[-300:],
                                "length_chars": len(s["text"])}
        rows.append({"pair": number, "left": side(a, sa), "right": side(b, sb)})
        key_rows.append({"pair": number, "work_id": work_id, "section_key": key, "left": a, "right": b})
    (out / "pairs.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    sample = rng.sample(all_children, 20)
    (out / "chunks.jsonl").write_text("".join(json.dumps({"item": i + 1, "language": s[1], "text": s[3]}, ensure_ascii=False) + "\n"
                                               for i, s in enumerate(sample)), encoding="utf-8")
    (ROOT / "data/philosophy/phase-b/alignment-key.json").write_text(json.dumps(
        {"pairs": key_rows, "chunks": [{"item": i + 1, "child_id": s[2]} for i, s in enumerate(sample)]}, indent=1), encoding="utf-8")
    print(f"candidates {len(candidates)}, pairs {len(rows)} over {len(per_work)} works, chunks {len(sample)}")


if __name__ == "__main__":
    main(sys.argv[1])
