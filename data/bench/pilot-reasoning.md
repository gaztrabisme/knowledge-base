# Reasoning-on pilot

Reader: whoever sizes or interprets the reasoning-on agent benchmark runs.

Every earlier arm ran with the harness forcing `enable_thinking=false` and `max_tokens=2048`.
From commit c14b379 the harness sends no generation parameters, so oMLX's per-model settings
apply (thinking on, `max_tokens` 32768), and from 1a08107 the tool-call cap is 25.

The pilot reran, with reasoning on, questions that the reasoning-off runs had failed, scored on
`questions_v2.jsonl`: per model, 5 that A1 did not cite and 5 that A1 cited but A2b did not.
Every transcript carries `reasoning_content`.

| Model | Block | Cited now | Calls per run (off → on) | Completion tokens (off → on) | Wall time, s (off → on) |
|---|---|---:|---|---|---|
| Gemma-4-12B | A1 failures | 5/5 | 0.8 → 1.8 | 551 → 623 | 257 → 229 |
| Gemma-4-12B | A2b losses | 2/5 | 1.4 → 1.6 | 435 → 467 | 177 → 146 |
| Qwen3.6-35B-A3B | A1 failures | 5/5 | 3.2 → 3.4 | 608 → 1,517 | 217 → 168 |
| Qwen3.6-35B-A3B | A2b losses | 4/5 | 4.2 → 7.8 | 1,308 → 1,798 | 261 → 368 |

No run hit the 25-call cap. The questions were selected for having failed once and the
runs sample without a seed, so part of the recovery is regression to the mean; the pilot sizes
the full runs (about the same wall time as reasoning-off) and shows reasoning is live. The
effect of reasoning is measured by the full paired runs.

Rows: `data/bench/runs/A1p-*.jsonl`, `A2bp-*.jsonl`.
