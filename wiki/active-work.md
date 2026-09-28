# Active Work

## v8 technical shelf intake
**Status:** C2 complete: all 166 ingest rows have Markdown and nonempty chunks; strict audit passes with 16 documented density exceptions.
**Current state:** All heading, chapter-structure, garble, front/back matter, and chunk-size checks pass. The 15-book regression set is byte-identical, and the 60-row sanity set references 60 distinct new books across all domains. No embeddings or index writes were made.
**Next step:** The outputs are ready for the later embedding/index stage on the other machine. See [C1 intake report](../data/intake/C1-report.md) and [C2 ingest report](../data/intake/C2-report.md).

## KB interface refinement, measured on small agents
**Status:** Stage 4 implementation complete; retrieval gate strict FAIL.
**Current state:** The tools are search, read, list_books, find_books, and grep_books. Default tool schema is 1,077 cl100k_base tokens versus 1,237 at HEAD; the HyDE schema is 1,079 versus 1,225. Chapter, chunk, error, import-time, warm-up, and benchmark parser checks passed. The s4-check NDCG@10 is 0.7699 against 0.7700 required. See [Stage 4 interface report](../data/bench/stage4-report.md).
The C3 v8 candidate merge utility is complete; its scratch-only verification and environment caveat are recorded in [C3-report.md](v8/C3-report.md).
**Next step:** Review the 0.0001 retrieval gate shortfall before choosing further work. Do not run agent_bench.py against a model in this stage.

Details in [Agent Benchmark](agent-benchmark.md).
