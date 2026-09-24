# Wiki Log

## [2026-09-24] session | Agent tool benchmark harness
- Added opt-in per-call JSONL logging while preserving the six FastMCP schemas byte-for-byte.
- Generated the deterministic 120-question set and added resumable oMLX agent, transcript, call, and paired-comparison outputs.
- Acceptance: 120 questions; schema parity true; call-log row complete; both requested 3-question smoke runs completed; comparator emitted per-pair and pooled tables.
- Commit attempt was blocked because the workspace exposes `.git` read-only (`git add` could not create `.git/index.lock`); no files were staged.
- Full commands, output rows, comparison tables, and the smoke token-normalization note: [data/bench/report.md](../data/bench/report.md).
