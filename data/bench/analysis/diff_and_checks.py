#!/usr/bin/env python3
"""Diff partition, archetype breakdowns, malformed-citation counts. Read-only."""
import json, os, re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.normpath(os.path.join(HERE, "..", "..", "..", "data", "bench"))
MODEL = "Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B"


def load(arm):
    with open(os.path.join(BENCH, "runs", f"{arm}-{MODEL}.jsonl")) as fh:
        return {json.loads(l)["qid"]: json.loads(l) for l in fh}


def questions():
    with open(os.path.join(BENCH, "questions.jsonl")) as fh:
        return {json.loads(l)["qid"]: json.loads(l) for l in fh}


a0, a1 = load("A0"), load("A1")
qs = questions()

both = sorted(q for q in a1 if not a0[q]["cited"] and not a1[q]["cited"])
o0 = sorted(q for q in a1 if a0[q]["cited"] and not a1[q]["cited"])
o1 = sorted(q for q in a1 if not a0[q]["cited"] and a1[q]["cited"])
print("both fail", len(both), both)
print("A0-only success", len(o0), o0)
print("A1-only success", len(o1), o1)
print()

for arm, rows in (("A0", a0), ("A1", a1)):
    c = [(q, rows[q]["archetype"], qs[q]["domain"]) for q in sorted(rows)
         if not rows[q]["cited"] and rows[q]["n_calls"] == 0]
    print(arm, "no-tool-use failures:", len(c), c)
print()

for arm, rows in (("A0", a0), ("A1", a1)):
    tab = Counter((r["n_calls"] == 0, r["cited"]) for r in rows.values())
    print(arm, "(no_calls, cited):", dict(tab))
    print(arm, "invalid_calls total:", sum(r["invalid_calls"] for r in rows.values()),
          "| runs with empty_results:", sum(1 for r in rows.values() if r["empty_results"]),
          "| gave_up:", sum(1 for r in rows.values() if r["gave_up"]))

# malformed (bold/backtick) CITED occurrences
BAD = re.compile(r"\*\*\s*CITED|CITED\s*:\*\*|`\s*CITED", re.I)
for arm, rows in (("A0", a0), ("A1", a1)):
    ok = sorted(q for q, r in rows.items() if r["cited"] and BAD.search(r["final_answer"]))
    bad = sorted(q for q, r in rows.items() if not r["cited"] and BAD.search(r["final_answer"]))
    print(arm, "bold-CITED cited=true:", len(ok), "| cited=false:", len(bad), bad)
