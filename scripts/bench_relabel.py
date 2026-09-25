import json, sys
from collections import defaultdict
from scipy.stats import binomtest
T = "/Users/GaryT/Documents/Work/tools"
qs = {json.loads(l)["qid"]: json.loads(l) for l in open("data/bench/questions.jsonl")}
aud = {r["qid"]: r for r in map(json.loads, open("data/bench/analysis/golden-audit.jsonl"))}
def labels(qid, mode):
    pos = set(qs[qid]["positive_parents"])
    if mode == "orig": return pos
    a = aud[qid]
    fixed = (pos - set(a["wrong_positive_parents"])) | set(a["extra_positive_parents"])
    return fixed
def parent(cid): return cid.rsplit("-c", 1)[0] if "-c" in cid.rsplit("-p",1)[-1] else cid
MODELS = ["gemma-4-12B-it-qat-OptiQ-4bit", "Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B"]
res = {}
for arm in ["A0", "A1"]:
    for m in MODELS:
        seen = defaultdict(set)
        for c in map(json.loads, open(f"{T}/kb-bench-{arm}/data/bench/calls/{arm}-{m}.jsonl")):
            seen[c["run_id"].split("|")[-1]] |= set(c.get("parent_ids") or [])
        rows = {r["qid"]: r for r in map(json.loads, open(f"data/bench/runs/{arm}-{m}.jsonl"))}
        for mode in ["orig", "fixed", "fixed_dropbad"]:
            f = c_ = 0; out = {}
            for qid, r in rows.items():
                if mode == "fixed_dropbad" and aud[qid]["verdict"] in ("ambiguous", "unanswerable", "leaky"):
                    continue
                L = labels(qid, "orig" if mode == "orig" else "fixed")
                fd = bool(seen[qid] & L) or (mode == "orig" and r["found"])
                ct = bool({parent(i) for i in r["cited_ids"]} & L)
                out[qid] = (fd, ct)
            res[(arm, m, mode)] = out
for mode in ["orig", "fixed", "fixed_dropbad"]:
    print(f"== {mode}")
    for m in MODELS:
        for arm in ["A0", "A1"]:
            o = res[(arm, m, mode)]; n = len(o)
            print(f"  {arm} {m[:12]:12} n={n} found {sum(v[0] for v in o.values())/n:.3f} cited {sum(v[1] for v in o.values())/n:.3f}")
    for k, name in [(0, "found"), (1, "cited")]:
        b = c = 0
        for m in MODELS:
            a0, a1 = res[("A0", m, mode)], res[("A1", m, mode)]
            for q in a0:
                if a0[q][k] and not a1[q][k]: b += 1
                if a1[q][k] and not a0[q][k]: c += 1
        p = binomtest(min(b, c), b + c, 0.5).pvalue if b + c else 1
        print(f"  pooled A1 vs A0 {name}: A0-only {b}, A1-only {c}, p={p:.3f}")
