# Active Work

## KB interface refinement, measured on small agents
**Status:** Stage 0 (measurement harness) done. Stages 1–5 pending.
**Current state:** `scripts/agent_bench.py` runs an agent loop against oMLX models over the in-process tools; `knowledge_base/calllog.py` logs every tool call when `KB_CALL_LOG` is set; `scripts/bench_compare.py` compares two arms paired per question.
**Next step:** Extend the question set with 30 v7.1-book questions, then run the A0 baseline on three models.

Details in [Agent Benchmark](agent-benchmark.md).
