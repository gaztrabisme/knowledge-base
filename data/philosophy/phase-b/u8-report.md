# U8 — Philosophy B gate script

Reader: Gary.

## What the script runs

`scripts/gate_philosophy_b.py` writes each run into a timestamped directory under `data/bench/gate-philosophy-b/`, saves the per-query JSON for every philosophy eval, snapshots the gate inputs it needs, and writes the summary to `data/bench/gate-philosophy-b.md`. It runs each evaluator through `.venv/bin/python .claude/plan-goal/verify/cpu.py`; it does not write to Qdrant.

The measurements run in this order:

1. Snapshot the reviewed sanity rows after excluding `verdict: drop`, the 40-pair alignment sample, all alignment review history files, the 50-query technical baseline, and the included Chinese registry records. This should take under one second.
2. Run (a), the filtered 60-query eval, against `philosophy` and then `philosophy_b`, saving one JSON file per collection. Allow about 1–5 minutes per run on CPU, or 2–10 minutes total.
3. Run (b), the same 60 queries with `--no-filters`, against live and candidate. Allow about 2–6 minutes per run because unfiltered search can do more work, or 4–12 minutes total.
4. Run (c), the reviewed sanity set against `philosophy_b`. Allow about 2–7 minutes for up to 79 retained queries.
5. Calculate (d) from the copied 40-pair review sample and list the match counts from the copied alignment review history. Check (e) against the copied included-Chinese registry records. These local checks should take under one second.
6. Run (f) with `scripts/eval_retrieval.py --label phaseb-tech-after --golden data/golden/golden_queries_hard.jsonl --limit 50 --per-query <path>`, writing both the per-query file and summary JSON in the run directory. Each query runs the full technical search and its retrieval-ceiling search; allow about 2–8 minutes on CPU.
7. Build the report from the saved run outputs. This should take under one second.

Plan for roughly 10–40 minutes total, plus possible first-run model loading time. These are CPU planning estimates; this sandbox could not access the Qdrant server, so evaluator timings and the live promotion verdict have not been measured here. The coordinator should run the script after the server is available.

## Dry-run output

Captured with `.venv/bin/python .claude/plan-goal/verify/cpu.py scripts/gate_philosophy_b.py --dry-run`:

```text
1. KB_PHILOSOPHY_COLLECTION=philosophy .venv/bin/python .claude/plan-goal/verify/cpu.py scripts/eval_philosophy.py --eval-file data/philosophy/eval.jsonl --json-out data/bench/gate-philosophy-b/run-20260930T231555Z/a-live.json
2. KB_PHILOSOPHY_COLLECTION=philosophy_b .venv/bin/python .claude/plan-goal/verify/cpu.py scripts/eval_philosophy.py --eval-file data/philosophy/eval.jsonl --json-out data/bench/gate-philosophy-b/run-20260930T231555Z/a-candidate.json
3. KB_PHILOSOPHY_COLLECTION=philosophy .venv/bin/python .claude/plan-goal/verify/cpu.py scripts/eval_philosophy.py --eval-file data/philosophy/eval.jsonl --json-out data/bench/gate-philosophy-b/run-20260930T231555Z/b-live.json --no-filters
4. KB_PHILOSOPHY_COLLECTION=philosophy_b .venv/bin/python .claude/plan-goal/verify/cpu.py scripts/eval_philosophy.py --eval-file data/philosophy/eval.jsonl --json-out data/bench/gate-philosophy-b/run-20260930T231555Z/b-candidate.json --no-filters
5. KB_PHILOSOPHY_COLLECTION=philosophy_b .venv/bin/python .claude/plan-goal/verify/cpu.py scripts/eval_philosophy.py --eval-file data/bench/gate-philosophy-b/run-20260930T231555Z/sanity-b-filtered.jsonl --json-out data/bench/gate-philosophy-b/run-20260930T231555Z/sanity-candidate.json
6. .venv/bin/python .claude/plan-goal/verify/cpu.py scripts/eval_retrieval.py --label phaseb-tech-after --golden data/golden/golden_queries_hard.jsonl --limit 50 --per-query data/bench/gate-philosophy-b/run-20260930T231555Z/tech-after.jsonl --report-out data/bench/gate-philosophy-b/run-20260930T231555Z/tech-after-summary.json
```

## Verification

The local-path Qdrant arithmetic tests use tiny eval rows and cover the exact (a) one-query and (b) two-query loss boundaries, (c) 0.80 overall and 0.70 per language, and (d) 36 of 40 matches. They also check the Chinese text rule, exact technical top-10 equality, report misses/history, and command construction.

`.venv/bin/python .claude/plan-goal/verify/cpu.py -m pytest tests -q` passed: **158 passed, 1 skipped**. The server-backed measurements were not run in this sandbox.
