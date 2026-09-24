# Active Work

## KB interface refinement, measured on small agents
**Status:** Stage 3 implementation complete; retrieval gate `s3-check` completed with a strict metric mismatch.
**Current state:** Search and search_book wrap hits with related headings. Tool descriptions support the default and `KB_TOOL_DOCS=hyde` arms. Harness and call-log counts handle the results wrapper. Live search and helper checks pass. Gate NDCG@10 was 0.7699 versus required 0.7700; see [Stage 3 interface report](../data/bench/stage3-report.md).
**Next step:** User runs the agent smoke test and reviews the −0.0001 gate difference. Do not run `agent_bench.py` against a model in this stage.

Details in [Agent Benchmark](agent-benchmark.md).
