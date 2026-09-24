# Agent Tool Benchmark

The benchmark measures complete model/tool cycles over the FastMCP interface without changing tool behavior. Its implementation and acceptance output are in [the benchmark report](../data/bench/report.md).

## Artifacts

- `data/bench/questions.jsonl` — 120 seed-42 questions sampled from the hard golden set.
- `data/bench/runs/<arm>-<model>.jsonl` — one result per qid; resume skips qids already present.
- `data/bench/transcripts/` — full model and tool message sequences; ignored by Git.
- `data/bench/calls/` — per-tool JSONL measurements; ignored by Git.

The golden sample includes all 7 distributed questions, 12 of 17 database questions, and 101 others allocated in proportion to ML/Rust/security counts (51/33/17). Sampling within each domain is proportional by archetype.

## Reproduction

```sh
PYTHONPATH=. .venv/bin/python scripts/bench_questions.py
PYTHONPATH=. .venv/bin/python scripts/agent_bench.py --arm baseline --model MODEL_ID --questions data/bench/questions.jsonl
PYTHONPATH=. .venv/bin/python scripts/bench_compare.py data/bench/runs/ARM-A.jsonl data/bench/runs/ARM-B.jsonl
```

The agent runner reads the oMLX key from `~/.omlx/settings.json`, sends explicit thinking control, counts JSON tool results with `cl100k_base`, and serializes in-process tool calls behind one lock. `cited_ids` stores chunk IDs; the `cited` metric maps them to parents before comparison with positive gold parents.

## Initial smoke

The Qwen and Gemma 3-qid smoke files each contain three complete rows. Gemma returned four parsed `tool_calls` and no native tool-call markers in message content. `data/bench/report.md` includes each row and the paired tables. At n=3 the statistics are a harness check only.
