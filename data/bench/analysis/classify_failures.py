#!/usr/bin/env python3
"""Classifier for cited=false runs, A0 vs A1. Read-only; prints tables.

Classes (first match wins):
  c  no_tool_use      n_calls == 0
  f  stopped_early    gave_up or stop_reason == 'max_calls'
  e  tool_error_empty any call error, or empty result set
  d  bad_citation     a positive-parent chunk id appears in the answer text
                       but the harness-extracted cited ids contain none
  a  never_retrieved  found == False (no correct passage in any tool output)
  b  retrieved_not_c  found == True but answer never names a positive id
  g  other
"""
import json, os, re, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.normpath(os.path.join(HERE, "..", "..", "..", "data", "bench"))
MODEL = "Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B"
CHUNK_ID_RE = re.compile(r"[A-Za-z0-9_.-]+-p\d+-c\d+")


def load(arm):
    rows = {}
    with open(os.path.join(BENCH, "runs", f"{arm}-{MODEL}.jsonl")) as fh:
        for line in fh:
            r = json.loads(line)
            rows[r["qid"]] = r
    return rows


def questions():
    qs = {}
    with open(os.path.join(BENCH, "questions.jsonl")) as fh:
        for line in fh:
            q = json.loads(line)
            qs[q["qid"]] = q
    return qs


def calls(arm):
    out = {}
    with open(os.path.join(BENCH, "calls", f"{arm}-{MODEL}.jsonl")) as fh:
        for line in fh:
            c = json.loads(line)
            out.setdefault(c["run_id"].split("|")[2], []).append(c)
    return out


def harness_cited_line(answer):
    line = None
    for ln in answer.splitlines():
        if ln.strip().lower().startswith("cited:"):
            line = ln.strip().lower()
    return line


def classify(row, q, cs):
    pos = set(q["positive_parents"])
    ans = row.get("final_answer") or ""
    ans_ids = CHUNK_ID_RE.findall(ans)
    ans_pos = any(any(i == p or i.startswith(p + "-") for p in pos) for i in ans_ids)

    line = harness_cited_line(ans)
    if row["n_calls"] == 0:
        return "c", "no_tool_use", ans_pos, line
    if row.get("gave_up") or row.get("stop_reason") == "max_calls":
        return "f", "stopped_early", ans_pos, line
    errs = [c for c in cs if c.get("error")]
    empt = [c for c in cs if c.get("n_results") == 0]
    if errs or empt:
        return "e", "tool_error_empty", ans_pos, line
    if ans_pos and not row["cited"]:
        return "d", "bad_citation", ans_pos, line
    if not row["found"]:
        return "a", "never_retrieved", ans_pos, line
    if row["found"] and not ans_pos:
        return "b", "retrieved_not_cited", ans_pos, line
    return "g", "other", ans_pos, line


def main():
    qs = questions()
    for arm in ["A0", "A1"]:
        rows = load(arm)
        cs = calls(arm)
        false_ids = sorted(q for q, r in rows.items() if not r["cited"])
        print(f"\n===== {arm} cited=false n={len(false_ids)}")
        counts = Counter()
        for qid in false_ids:
            r = rows[qid]
            cls, name, ans_pos, line = classify(r, qs[qid], cs.get(qid, []))
            counts[name] += 1
            errs = [c for c in cs.get(qid, []) if c.get("error") or c.get("n_results") == 0]
            extra = ""
            if errs:
                extra += " ERR=" + "; ".join(
                    f"{c['tool']}:{(c.get('error') or 'EMPTY')}({c.get('n_results')})" for c in errs)
            print(f"{qid:6} {name:18} found={int(r['found'])} n={r['n_calls']:2} "
                  f"stop={r.get('stop_reason'):9} ans_pos={int(ans_pos)} "
                  f"cited_ids={len(r.get('cited_ids') or [])}{extra}")
            if line is None:
                tail = (r.get('final_answer') or '').strip().splitlines()
                tail = [t for t in tail if 'cited' in t.lower()]
                print(f"        ANSWER-CITED-TAIL: {tail[:2]}")
        print(f"-- counts: {dict(counts)}  sum={sum(counts.values())}")


if __name__ == "__main__":
    main()
