#!/usr/bin/env python3
"""Read-only helper for failures-qwen36-A0-A1.md.

Classifies cited=false runs for the A0 vs A1 interface comparison and
summarises A1 tool-usage patterns. Writes nothing except stdout text.
"""
import json, os, re, sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BENCH = os.path.join(ROOT, "data", "bench")
MODEL = "Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B"
ARMS = ["A0", "A1"]

CITE_RE = re.compile(r"^\s*CITED\s*:", re.I | re.M)


def load_run(arm):
    path = os.path.join(BENCH, "runs", f"{arm}-{MODEL}.jsonl")
    rows = {}
    for line in open(path):
        r = json.loads(line)
        rows[r["qid"]] = r
    return rows


def load_questions():
    qs = {}
    for line in open(os.path.join(BENCH, "questions.jsonl")):
        q = json.loads(line)
        qs[q["qid"]] = q
    return qs


def load_calls(arm):
    """qid -> list of call dicts (from calls/<arm>-<model>.jsonl)."""
    path = os.path.join(BENCH, "calls", f"{arm}-{MODEL}.jsonl")
    out = defaultdict(list)
    for line in open(path):
        c = json.loads(line)
        qid = c["run_id"].split("|")[2]
        out[qid].append(c)
    return out


def load_transcript(arm, qid):
    path = os.path.join(BENCH, "transcripts", f"{arm}-{MODEL}", f"{qid}.json")
    if not os.path.exists(path):
        return None
    return json.load(open(path))


def final_cited_line(run):
    fa = run.get("final_answer") or ""
    m = re.search(r"CITED\s*:\s*(.*)", fa, re.I)
    if not m:
        return None
    return m.group(1).strip()


def ids_in_tool_outputs(run):
    """chunk ids that appeared in any tool output of this run (from calls log)."""
    return set()


def run_row_ids(row):
    return set(row.get("cited_ids") or [])


def cited_ids_valid(row, questions):
    fa = row.get("final_answer") or ""
    m = re.search(r"CITED\s*:\s*(.+)", fa, re.I | re.S)
    if not m:
        return None, "missing"
    line = m.group(1)
    # take only the tail line (avoid swallowing prose if CITED appears mid-text)
    line = line.strip().splitlines()[0]
    ids = [t.strip().strip(",") for t in line.split(",") if t.strip()]
    if not ids:
        return None, "empty"
    pos = set(questions[row["qid"]]["positive_parents"])
    # parent ids may be cited as chunk ids; allow prefix match
    ok = [i for i in ids if any(i == p or i.startswith(p + "-") for p in pos)]
    return ok, ("ok" if ok else "no-valid-id")


def analyse_arm(arm, rows, questions, calls):
    false_ids = [q for q, r in rows.items() if not r["cited"]]
    print(f"== {arm}: {len(rows)} rows, {len(false_ids)} cited=false")
    for qid in sorted(false_ids):
        r = rows[qid]
        q = questions[qid]
        pos = q["positive_parents"]
        cl = calls.get(arm if False else qid) or []
        print(f"--- {qid} [{r['stratum']}/{q['domain']}/{q.get('archetype')}] "
              f"n_calls={r['n_calls']} invalid={r.get('invalid_calls')} "
              f"empty={r.get('empty_results')} gave_up={r.get('gave_up')} "
              f"stop={r.get('stop_reason')} turns={r.get('turns')}")
        print(f"    Q: {q['query'][:160]}")
        print(f"    positives: {pos[:4]}{' ...' if len(pos) > 4 else ''}")
        line = final_cited_line(r)
        print(f"    cited_line: {str(line)[:200]!r}")
        for c in cl:
            args = c.get("args") or {}
            if c["tool"] == "search":
                a = f"query={args.get('query')!r}"
                if args.get("book"):
                    a += f" book={args.get('book')!r}"
                if args.get("bm25_keywords"):
                    a += f" kw={str(args.get('bm25_keywords'))[:60]!r}"
            elif c["tool"] == "read_chunk":
                a = f"chunk_id={args.get('chunk_id')!r} window={args.get('window')}"
            elif c["tool"] == "get_chapter":
                a = f"book={args.get('book')!r} chapter={args.get('chapter')!r}"
            else:
                a = json.dumps(args)[:160]
            err = f" ERROR={c.get('error')!r}" if c.get("error") else ""
            print(f"      call {c['tool']:<12} n={c.get('n_results')}{err} {a[:230]}")
    return false_ids


if __name__ == "__main__":
    arm = sys.argv[1] if len(sys.argv) > 1 else "A1"
    rows = load_run(arm)
    questions = load_questions()
    calls = load_calls(arm)
    analyse_arm(arm, rows, questions, calls)
