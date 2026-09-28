# Active Work

## KB interface refinement, measured on small agents
**Status:** Stage 4 implementation complete; retrieval gate strict FAIL.
**Current state:** The tools are search, read, list_books, find_books, and grep_books. Default tool schema is 1,077 cl100k_base tokens versus 1,237 at HEAD; the HyDE schema is 1,079 versus 1,225. Chapter, chunk, error, import-time, warm-up, and benchmark parser checks passed. The s4-check NDCG@10 is 0.7699 against 0.7700 required. See [Stage 4 interface report](../data/bench/stage4-report.md).
The C3 v8 candidate merge utility is complete; its scratch-only verification and environment caveat are recorded in [C3-report.md](v8/C3-report.md).
**Next step:** Review the 0.0001 retrieval gate shortfall before choosing further work. Do not run agent_bench.py against a model in this stage.

Details in [Agent Benchmark](agent-benchmark.md).
