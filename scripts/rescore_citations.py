"""Recompute cited_ids and cited in benchmark run files with the current parser.

Each arm runs from a worktree pinned at its own commit, so its rows were scored
with that commit's cited_ids(). The first parser missed markdown-formatted lines
("**CITED:** ..."), which undercounted cited in every arm. Rows keep final_answer,
so this rescoring needs no model calls; it rewrites the files in place.

Usage:
  python3 scripts/rescore_citations.py data/bench/runs/*.jsonl
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agent_bench import cited_ids, parent_ids  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--questions", default=str(ROOT / "data/bench/questions.jsonl"))
    args = ap.parse_args()

    positives = {}
    for line in open(args.questions):
        q = json.loads(line)
        positives[q["qid"]] = set(q["positive_parents"])

    for path in args.runs:
        rows = [json.loads(line) for line in open(path) if line.strip()]
        changed = 0
        for row in rows:
            ids = cited_ids(row.get("final_answer") or "")
            cited = bool(positives[row["qid"]] & parent_ids([{"chunk_id": i} for i in ids]))
            if ids != row.get("cited_ids") or cited != row.get("cited"):
                changed += 1
            row["cited_ids"], row["cited"] = ids, cited
        with open(path, "w") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")
        rate = sum(r["cited"] for r in rows) / len(rows) if rows else 0
        print(f"{path}: {changed} rows changed, cited {rate:.3f} (n={len(rows)})")


if __name__ == "__main__":
    main()
