# Wiki Log

## [2026-09-24] session | Agent tool benchmark harness
- Added opt-in per-call JSONL logging while preserving the six FastMCP schemas byte-for-byte.
- Generated the deterministic 120-question set and added resumable oMLX agent, transcript, call, and paired-comparison outputs.
- Acceptance: 120 questions; schema parity true; call-log row complete; both requested 3-question smoke runs completed; comparator emitted per-pair and pooled tables.
- Commit attempt was blocked because the workspace exposes `.git` read-only (`git add` could not create `.git/index.lock`); no files were staged.
- Full commands, output rows, comparison tables, and the smoke token-normalization note: [data/bench/report.md](../data/bench/report.md).

## [2026-09-24] session | Stage 3 search interface
- Added ranked overflow heading hints, wrapped search/search_book responses, compact default tool descriptions, and the `KB_TOOL_DOCS=hyde` description arm.
- Updated agent-benchmark and call-log counts for the result wrapper; updated the Stage 2 contract assertion.
- Live examples each returned eight distinct related headings with no normalized duplicate of a returned heading; the default tool list shrank from 1,674 to 1,237 `cl100k_base` tokens.
- Retrieval gate `s3-check` completed: NDCG@10=0.7699 vs required 0.7700 (strict FAIL by 0.0001); no ranking or cutoff change was made.
- Full acceptance outputs: [stage-3-interface-report.md](../data/bench/stage3-report.md).
