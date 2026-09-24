#!/usr/bin/env python3
"""Tool-usage stats for A0/A1 + detail for 'retrieved, not cited' rows. Read-only."""
import json, os, re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.normpath(os.path.join(HERE, "..", "..", "..", "data", "bench"))
MODEL = "Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B"
CHUNK_ID_RE = re.compile(r"[A-Za-z0-9_.-]+-p\d+-c\d+")
STOP = set("a an the of for in on to with and or is are be how what why when do i my you your it its".split())


def load_calls(arm):
    out = {}
    with open(os.path.join(BENCH, "calls", f"{arm}-{MODEL}.jsonl")) as fh:
        for line in fh:
            c = json.loads(line)
            out.setdefault(c["run_id"].split("|")[2], []).append(c)
    return out


def load_questions():
    qs = {}
    with open(os.path.join(BENCH, "questions.jsonl")) as fh:
        for line in fh:
            qs[json.loads(line)["qid"]] = json.loads(line)
    return qs


def norm_tokens(q):
    return frozenset(t for t in re.findall(r"\w+", q.lower()) if t not in STOP)


def repeats(call_list):
    """count runs with >=1 near-identical query pair (token-set Jaccard >= 0.75)."""
    qs = [(c["args"] or {}).get("query", "") for c in call_list if c["tool"] == "search"]
    pairs = []
    for i in range(len(qs)):
        for j in range(i + 1, len(qs)):
            a, b = norm_tokens(qs[i]), norm_tokens(qs[j])
            if a and b:
                jac = len(a & b) / len(a | b)
                if jac >= 0.75:
                    pairs.append((qs[i], qs[j], round(jac, 2)))
    return pairs


arm_calls = {a: load_calls(a) for a in ("A0", "A1")}
qs = load_questions()

for arm, cs in arm_calls.items():
    runs = sorted({qid for qid in cs} | {json.loads(l)["qid"] for l in open(os.path.join(BENCH, "runs", f"{arm}-{MODEL}.jsonl"))})
    first = Counter()
    n_runs_with_search = n_with_read_after_search = n_book_kw = 0
    n_read = 0
    rep_runs = []
    for qid in runs:
        cl = cs.get(qid, [])
        if not cl:
            first["(none)"] += 1
            continue
        first[cl[0]["tool"]] += 1
        tools = [c["tool"] for c in cl]
        if "search" in tools:
            n_runs_with_search += 1
        if "read_chunk" in tools and "search" in tools and tools.index("read_chunk") > tools.index("search"):
            n_with_read_after_search += 1
        n_read += sum(1 for t in tools if t == "read_chunk")
        if any((c["args"] or {}).get("book") for c in cl if c["tool"] == "search"):
            n_book_kw += 1
        if repeats(cl):
            rep_runs.append(qid)
    total = len(runs)
    print(f"\n### {arm} ({total} runs, {sum(len(v) for v in cs.values())} calls)")
    print(f"first call: {dict(first)}")
    print(f"runs with >=1 search: {n_runs_with_search}; runs where read_chunk used after a search: {n_with_read_after_search}")
    print(f"read_chunk calls total: {n_read}")
    print(f"runs using book= on search: {n_book_kw}")
    print(f"runs with near-identical query repeat (Jaccard>=0.75): {len(rep_runs)} -> {rep_runs}")
    for qid in rep_runs:
        for a, b, j in repeats(cs[qid]):
            print(f"    {qid} [{j}] {a!r} vs {b!r}")

# which tools exist per arm
for arm, cs in arm_calls.items():
    print(f"\n{arm} tool histogram: {Counter(c['tool'] for cl in cs.values() for c in cl)}")

# (b) retrieved-not-cited detail for A1
rows = {json.loads(l)["qid"]: json.loads(l) for l in open(os.path.join(BENCH, "runs", f"A1-{MODEL}.jsonl"))}
print("\n### A1 retrieved-not-cited detail: positive parents that appeared in tool output, and what was cited")
for qid, r in sorted(rows.items()):
    if r["cited"] or not r["found"]:
        continue
    pos = set(qs[qid]["positive_parents"])
    hits = []
    for c in arm_calls["A1"].get(qid, []):
        for p in (c.get("parent_ids") or []):
            if p in pos:
                hits.append((c["tool"], p))
    cited = r.get("cited_ids")
    print(f"{qid:6} hits={hits[:6]} cited={cited}")
