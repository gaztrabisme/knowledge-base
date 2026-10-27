# Active Work

## Project wiki corpus (2026-10-27)
**Status:** Implemented on `wiki-corpus`, uncommitted. Offline wiki and edition checks pass (31 cases). Full-suite acceptance is blocked here by an uncached tokenizer, a pinned-validator version mismatch, and absent philosophy data.

**Next:** Coordinator runs the full suite and the live Qdrant index, confirms a second pass reports zero re-embedded files, then checks three real queries. Configuration, commands, review limitations and test names are in the [wiki corpus report](runs/2026-10-27-wiki-corpus.md).

## Organized mind: research and design (run kbu-2026-10-07)
**Status:** Approved by Huy 2026-10-14 (decisions.md). The build is run by the pi-mind conductor session (phases 1-7); this run owns the embedding switch and the LFM2.5 graph test. Goal file: [2026-10-07-organized-mind](goals/2026-10-07-organized-mind.md); deliverables in `data/intake/kbu-2026-10-07/`.

**Embedding switch: DONE 2026-10-16.** Live `developer_knowledge` → `developer_knowledge_v11` (embeddinggemma-2, 768 dims); main at 6ebedf1, not pushed. Gate and latency in `data/bench/gate-v11.md`; decision and rollback in decisions.md. v10 kept for rollback. Running KB MCP servers needed a restart (the Mac restart on 2026-10-16) to load the new code.

**LFM2.5 graph test (M4), this run's part DONE 2026-10-15:** fits on the 5080 and is ~9x faster than Qwen, but 3/48 strict-valid vs 35/48 with the GGUF's embedded chat template, which Huy says is broken. P6 (pi-mind) reruns with the upstream template ([report](../data/intake/kbu-2026-10-07/reports/M4-REPORT.md)).

**Open:** Huy's choice 10 (evidence in gate-v11.md); push of KB main (not requested); LFM2.5 rerun with the fixed template (pi-mind P6).

## Philosophy phase B: rest of the Falun Dafa archive
**Status:** Built and gated 2026-10-01. **Not promoted:** the gate failed conditions (b), (c) and (f) ([gate report](../data/bench/gate-philosophy-b.md)). The decision is Gary's. Goal file: [2026-09-30-philosophy-phase-b](goals/2026-09-30-philosophy-phase-b.md).

**State:**
- Live `philosophy`: unchanged, 8,432 points. Candidate `philosophy_b`: 52,122 points on the Mac's Qdrant (phase A + 43,690 phase B chunks from 117 works).
- Registry `data/philosophy/works.json` lists the phase B works (319 included, 30 derived, 57 skipped language records); chunks and markdown under `data/{chunks,markdown}/philosophy/`; vector cache `data/philosophy-vectors/` (not tracked).
- No `data-v9.1` release; the installer still defaults to `data-v9`.

**Rows:** done: 1 (Hồng Ngâm), 2 (registry), 3 (match review), 4 (phase A untouched), 5 (ingest), 6 (alignment sample), 7 (reviewed test set), 8 (candidate), 9 (gate report), 10 (fail branch: live unchanged, failure reported), 11 (fail branch: no release), 12 (technical untouched), 13 (tests), 14 (docs, wiki, push).

**Open:**
- Gary's call on `philosophy_b`: promote anyway, keep separate or behind a default filter, or improve retrieval first.
- Missing editions: Hồng Ngâm (Hong Yin) I, II, IV, V in Simplified Chinese and I in Traditional (failed the text check); `hong-yin-iii.zh-Hans` garbled; 52 Vietnamese writings are web shells in the archive; 13 Vietnamese lectures are chapters of collected volumes and are not aligned to them.
- `knowledge_base/chunk.py` drops a section's short final paragraph group (technical and phase A).
- bppc's `~/kb-work/phase-b/` can be deleted once the candidate is decided.

## v9 review fixes
**Status:** Done 2026-09-30. All 15 goal rows pass; Gary then promoted v9 (below). Goal file: [2026-09-30-v9-review-fixes](goals/2026-09-30-v9-review-fixes.md).

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
- A6 promotion: Gary promoted v9 after the goal closed (see [decisions](decisions.md)).
- A3: regression 15/15 byte-identical.
- A5: the `u6c.sh` failure was not reproduced in 13 runs (10 sequential, 3 concurrent), all exit 0 ([report](../data/intake/v9-u6c-flake.md)). Two possible causes remain:
  - the script's first Python block can exit 1 after printing only counts;
  - concurrent runs overwrite each other's shared `/tmp` diagnostic files.

  Neither script is fixed.
- Open, not in this goal:
  - the chunk heading paths repeat `(part 1) (part 1)`, from `knowledge_base/chunk.py`;
  - the four live books with no headings.

**Promoted 2026-09-30 on Gary's call.**
- `developer_knowledge` points to `developer_knowledge_v9`, and v8 is kept for rollback.
- Release [data-v9](https://github.com/gaztrabisme/knowledge-base/releases/tag/data-v9) is published; its four parts match the manifest's SHA-256.
- The installer defaults to data-v9, and main is pushed at `8f058d9`.

**Fixed after promotion (2026-09-30):**
- The installer deleted its extracted snapshot but not Qdrant's own copy of the upload (4.3 GB for full). Fixed 2026-09-30: it now deletes that copy after the point count checks out.

**Open:**
- The five sanity misses (Agentic Mesh, Head First PMP, Python for DevOps, Selling to Big Companies, Fieldbook Companion).
- The `(part 1) (part 1)` heading-path defect in `knowledge_base/chunk.py`.
- The four live books with no headings.
- bppc keeps the `developer_knowledge_v9` collection as the baseline for the next gate. Its build folder `~/kb-work/v9` was moved to bppc's trash on 2026-09-30. Still on bppc and not needed: the old 132,623-point `developer_knowledge` (v7.1), `developer_knowledge_v8`, and `~/kb-work/v8new` (2.6 GB).

## KB v9: 29 new books with heading repair
**Status:** Built and gated 2026-09-30. The gate failed one of its three pre-set conditions; Gary promoted it anyway the same day (see "v9 review fixes" above).

**State at the gate** (before promotion):
- `developer_knowledge_v9`: 286,723 points, which is v8's 266,647 plus 20,076 from 29 new books.
- Gate results ([gate-v9](../data/bench/gate-v9.md)):
  - hard NDCG@10 drop 0.0020 (limit 0.010, pass);
  - hard recall@10 drop 0 (limit 0.005, pass);
  - sanity recall@10 23/29 = 0.793 (threshold 0.80, **fail by one query**).
- Two new domains: `sales` (10 books) and `research-methods` (6). v9 also adds 3 books to `management` and 10 technical titles to existing domains.
- Heading repair is in the pipeline:
  - `knowledge_base/headings.py` checks heading quality and recovers headings. It runs only for books whose headings fail the check.
  - Heading maps for five books are in `data/intake/heading-maps/`.
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
**Status:** Done 2026-09-28. The scratch Qdrant below was gone by 2026-09-30: nothing listens on 6363, and the only Qdrant process is the live one.

- The lane A fix commit added edition-aware restore/update checks, resumable verified downloads, Qdrant version and process tracking, token scrubbing, proxy handling, and disk-space guards.
- `uvx pyflakes` passed; the full suite passed 58 tests; a local core release install restored 266,647 points and completed its smoke query.
- The scratch Qdrant on port 6363 was left running at the time, because the runner could not send process signals.
