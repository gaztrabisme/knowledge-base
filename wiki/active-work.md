# Active Work

## v9 review fixes
**Status:** In progress 2026-09-30. Two rows are paused: another session's GPU training on this Mac asked for no GPU work for about 4 hours. Goal file: [2026-09-30-v9-review-fixes](goals/2026-09-30-v9-review-fixes.md).

**Rows:**
- Done:
  - A1: blind review of the sanity queries;
  - A2: PMBOK diagnosis (the query's wording, not indexing);
  - A4: the rescore, 0.821 (23/28) beside the pre-set 0.793;
  - A7: the u5 worktree, its stash and `data/qdrant-v9-add` removed (the store is in the Trash);
  - B1: subagent-mcp loop fix `6ae599a`;
  - C1–C3: skill rules;
  - C4: skill ledger (`3e2d6db`, `635a4c7`);
  - D1: the Character line.
- A6 promotion: no call yet, and the alias stays on v8 (see [decisions](decisions.md)).
- Paused:
  - A3: the regression check;
  - A5: the `u6c.sh` flake hunt, 5 of 10 runs done, all exit 0.

  Both resume when the other session reports its training has ended.

**Next step (Gary):** promote v9 or keep v8. The pre-set gate failed at 0.793 (23/29). The blind-reviewed set scores 0.821 (23/28). Five fair queries still miss.

## KB v9: 29 new books with heading repair
**Status:** Built and gated 2026-09-30. **Not promoted:** the gate failed one of its three pre-set conditions, so Gary decides next.

**Current state:**
- `developer_knowledge_v9` exists on the Mac's Qdrant and on bppc's: 286,723 points, which is v8's 266,647 plus 20,076 from 29 new books. The live alias `developer_knowledge` still points to `developer_knowledge_v8`.
- Gate results ([gate-v9](../data/bench/gate-v9.md)):
  - hard NDCG@10 drop 0.0020 (limit 0.010, pass);
  - hard recall@10 drop 0 (limit 0.005, pass);
  - sanity recall@10 23/29 = 0.793 (threshold 0.80, **fail by one query**).
- The six sanity misses are PMBOK Guide, Agentic Mesh, Head First PMP, Python for DevOps, Selling to Big Companies and the Flawless Consulting Fieldbook Companion.
- Two new domains: `sales` (10 books) and `research-methods` (6). v9 also adds 3 books to `management` and 10 technical titles to existing domains.
- Heading repair is in the pipeline:
  - `knowledge_base/headings.py` checks heading quality and recovers headings. It runs only for books whose headings fail the check.
  - Heading maps for five books are in `data/intake/heading-maps/`.
- No `data-v9` release exists; the installer still pins `data-v8`.

**Next step (Gary):**
- Choose one:
  - promote v9 anyway, as was done for v8;
  - look at the six missed sanity queries first. The query-writing pass was single and unreviewed, so some may be badly posed;
  - keep v8 live.
- If promoting, [v9-promotion-brief.md](../data/intake/v9-promotion-brief.md) is the ready brief. It covers the alias switch, the data-v9 release, the installer default, the docs and the push.
- Four live books have no headings at all and are listed in `data/intake/heading-exceptions.json` as repair candidates: ai-modern-approach, microservices-design-to-deploy, refactoring, tdd-by-example.

## KB v8: technical shelf and philosophy collection
**Status:** Done 2026-09-28. The Character section is installed in the global CLAUDE.md.

**Current state:**
- `developer_knowledge` is an alias for `developer_knowledge_v8`: 291 books, 266,647 vectors. It was promoted on Gary's decision after failing the dilution rule, 22 of 40 against a limit of 20 ([gate report](../data/bench/gate-v8.md)).
- The `philosophy` collection is live with 8,432 vectors, covering the Original Library, the Tao Te Ching and Zhuan Falun, and is served through `search_philosophy` and `list_philosophy`.

**Next step:**
- Gary reviews the draft Character section: [character-draft.md](character-draft.md).
- Then either the Falun Dafa archive phase B, which ingests the other works into `philosophy`, or the reranker dilution recorded in the gate report.

## KB interface refinement, measured on small agents
**Status:** Done. Main serves the A1 interface (commit 33ff7ba); the LFM2.5 and `claude -p` checks are recorded in [interface-bench.md](interface-bench.md).

Details in [Agent Benchmark](agent-benchmark.md).

## Portable installer hardening — lane A round 2
**Status:** Implementation and verification done 2026-09-28; scratch-process cleanup remains pending.

- The lane A fix commit added edition-aware restore/update checks, resumable verified downloads, Qdrant version and process tracking, token scrubbing, proxy handling, and disk-space guards.
- `uvx pyflakes` passed; the full suite passed 58 tests; a local core release install restored 266,647 points and completed its smoke query.
- The scratch Qdrant remains ready on port 6363 because this runner denied process signals and refused Terminal/Activity Monitor control. Stop only the PID recorded under the scratch install's `qdrant-storage/.kb-qdrant-process.json` when process control is available.
