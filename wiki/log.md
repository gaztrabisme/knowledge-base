# Wiki Log

## [2026-09-28] session | v8 technical shelf C2 ingest and audit
- Ingested and chunked all 166 manifest rows with `.venv/bin/python`; no embeddings, reranking, or indexing were run.
- Added Markdown/front-back matter and chunk-cap audits, hard chunk splitting, and targeted heading/TOC/PDF extraction repairs. Strict audit passes with 16 source-density exceptions and no other flags.
- Regression guard passed 15/15 byte-identical comparisons. Wrote a 60-row sanity set from 60 different new books across all 15 domains; all positive child IDs resolve.
- Full per-book metrics, calibration, changes, and exception details: [C2 report](../data/intake/C2-report.md).

## [2026-09-28] session | C3 candidate collection merge
- Added `scripts/merge_collection.py` to copy source vector, index, HNSW, optimizer, WAL, quantization, and payload-index settings; merge embedded points; verify samples; repair mismatched IDs on resume; and switch aliases atomically.
- Scratch verification passed via `.venv/bin/python` with pytest isolated under `/private/tmp` (`1 passed`); pytest has since been installed into `.venv`, and the direct command passes.
- The test exercised a corrupted source point and corrupted addition being repaired on resume, plus undeclared collision refusal and declared overwrite verification.
- Final Qdrant state: only `developer_knowledge`, 132,623 points, no aliases. Production collection and `.mcp.json` were not changed.
- Full command and promotion configuration: [C3-report.md](v8/C3-report.md).

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

## [2026-09-24] session | Stage 4 fewer tools
- Removed search_book, merged chunk and chapter reading into read, added numeric-title-first chapter resolution, and added the main() daemon warm-up.
- Tool set is exactly search, read, list_books, find_books, grep_books; JSON tool tokens fell from 1,237 to 1,077 (default) and 1,225 to 1,079 (hyde). Chunk-output parity with HEAD and agent_bench.parent_ids passed.
- Chapter checks passed; PostgreSQL 14's listed chapters are unnumbered, so chapter 4 fell back to Part V Types of Indexes.
- The s4-check retrieval run completed with NDCG@10=0.7699 against 0.7700 required (strict FAIL by 0.0001). Full output: [stage4-report.md](../data/bench/stage4-report.md).

## [2026-09-28] session | v8 technical shelf intake
- Curated 185 source files into the manifest: 166 ingest, 2 verified duplicate copies, 11 indexed works, and 6 philosophy files.
- Added seven domains, 166 `BOOKS` entries in config and remote index, and 166 catalog entries; catalog validation passed with 292 entries and `knowledge_base.books` imported cleanly.
- `check_intake.py` confirms inventory/config/catalog consistency but fails on 166 absent hard links. `os.link` returned EPERM from the read-only source tree to both workspace and temp targets; no alternate file type was used.
- Full skips, domain counts, and remaining work: [C1 report](../data/intake/C1-report.md).
## [2026-09-28] session | Philosophy C4b
- Derived Zhuan Falun zh-Hant from the accepted zh-Hans markdown with OpenCC `s2t`, kept all ten alignment keys, and retained the failed Traditional PDF check in the registry.
- Added `derived` markers to generated chunk metadata, remote payloads, and philosophy search results; normalized custom sparse CJK tokens with OpenCC `t2s` in both tokenizer copies.
- Acceptance: `.venv/bin/python -m pytest tests/test_philosophy.py -q` → 8 passed in 4.44s. No model load or embedding run.
- Full change and check results: [C4 report](../data/philosophy/C4-report.md).

## 2026-09-28: v8 live check over MCP
A fresh `knowledge_base.server` was started over stdio and called through a FastMCP client. It lists 8 tools, including `search_philosophy` and `list_philosophy`.
- `search_philosophy("the usefulness of emptiness")` returned Tao Te Ching ch. 11 (Mitchell). Its parallels were the Jonathan Star (en) and Tse Lao (es) passages, then Zhuan Falun hits with 2 passages each in vi, zh-Hans and zh-Hant.
- `search("CSS cascade layers")` returned css-definitive-guide and css-in-depth-2e.

## [2026-09-28] session | Portable release packaging lane A
- Added `KB_EDITION` registration, detached local Qdrant startup, split release bundles with SHA-256 manifests, and a stdlib-download installer with streamed snapshot restores.
- `uv run pytest tests -q` → 35 passed. Core registered six tools; full registered eight. Release dry-run read both live collections without creating snapshots and reported 266,647 technical points and 8,432 philosophy points.
- HEAD requests for all five Qdrant v1.18.2 platform assets returned HTTP 200. No release snapshot or restore was run against the local Qdrant server.
