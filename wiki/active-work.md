# Active Work

## KB v8: technical shelf and philosophy collection
**Status:** Done 2026-09-28, except the Character section, which waits for Gary's approval.

**Current state:**
- `developer_knowledge` is an alias for `developer_knowledge_v8`: 291 books, 266,647 vectors. It was promoted on Gary's decision after failing the dilution rule, 22 of 40 against a limit of 20 ([gate report](../data/bench/gate-v8.md)).
- The `philosophy` collection is live with 8,432 vectors, covering the Original Library, the Tao Te Ching and Zhuan Falun, and is served through `search_philosophy` and `list_philosophy`.

**Next step:**
- Gary reviews the draft Character section: [character-draft.md](character-draft.md).
- Then either the Falun Dafa archive phase B, which ingests the other works into `philosophy`, or the reranker dilution recorded in the gate report.

## KB interface refinement, measured on small agents
**Status:** Done. Main serves the A1 interface (commit 33ff7ba); the LFM2.5 and `claude -p` checks are recorded in [interface-bench.md](interface-bench.md).

Details in [Agent Benchmark](agent-benchmark.md).
