#!/usr/bin/env python3
"""Print the positive-parent text for selected qids, to diagnose vocabulary gaps."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.normpath(os.path.join(HERE, "..", "..", "..", "data", "bench"))
CHUNKS = os.path.normpath(os.path.join(HERE, "..", "..", "chunks"))
QS = os.path.join(BENCH, "questions.jsonl")

WANT = {
    "h0027": ["machinelearningengineeringwithpython_secondedition-p145"],
    "h0116": ["deepreinforcementlearninghands-on_thirdedition-p187"],
    "h0167": ["boneh-shoup-applied-cryptography-p915"],
    "h0180": ["machinelearningwithpytorchandscikit-learn-p343"],
    "h0246": ["joy-of-cryptography-p113"],
    "n005": ["building-reliable-ai-systems-p70"],
    "n014": ["human-in-the-loop-ml-p172"],
    "h0152": ["designing-distributed-systems-p8"],
}

index = {}
for fn in os.listdir(CHUNKS):
    if not fn.endswith(".json"):
        continue
    with open(os.path.join(CHUNKS, fn)) as fh:
        data = json.load(fh)
    parents = data["parents"] if isinstance(data, dict) else data
    for c in parents:
        index[c.get("parent_id") or c.get("chunk_id", "").rsplit("-c", 1)[0]] = c

qs = {}
with open(QS) as fh:
    for line in fh:
        q = json.loads(line)
        qs[q["qid"]] = q

for qid, parents in WANT.items():
    print("=" * 20, qid, qs[qid]["query"][:110])
    for p in parents:
        c = index.get(p)
        if not c:
            print("  !! parent not found:", p)
            continue
        hp = c.get("heading_path", "")
        txt = (c.get("text") or c.get("child_text") or "")[:700]
        print(f"  [{p}] {hp}\n  {txt}\n")
