# Wiki Log

## [2026-09-28] session | Portable installer hardening, lane A round 2
- Fixed the install blockers and hardened update, download, proxy, process, and disk-space handling; regression coverage is in `tests/test_install.py`.
- Full test suite: 58 passed. Local release core install completed and `/collections/developer_knowledge` reported 266,647 points.
- Scratch Qdrant cleanup remains pending: process signaling was denied by the runner and Activity Monitor/Terminal access was refused. The process is only on test port 6363; see [active-work.md](active-work.md).

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

## [2026-09-28] session | Laya model fit check
- Inspected the Laya model card and SDK batch API against the live technical and philosophy search paths.
- Identified one viable experiment: batched two-option relevance scoring of the same 50 fused candidates, compared with Ettin on parent-level quality and warmed latency. No model was downloaded or installed and no search code was changed.
- Recorded the fit check, alternatives, and trial gate in [decisions.md](decisions.md).

## [2026-09-29–30] conductor run | KB v9 intake with heading repair
Plan: `~/.claude/plans/1-their-own-domain-elegant-patterson.md`. Goal file: [goals/2026-09-29-v9-intake.md](goals/2026-09-29-v9-intake.md).

**Outcome.** 29 books were built into `developer_knowledge_v9` (286,723 points = v8's 266,647 + 20,076). The gate failed one pre-set condition, sanity recall@10, at 23/29 = 0.793 against 0.80. v9 is not promoted, and the live alias stays on v8. Details: [gate-v9](../data/bench/gate-v9.md).

**Lane check** (2026-09-29, `subagent doctor --prompt --json` with keys loaded): codex, glm, gemini, bppc and omlx were open. deepseek was closed ("402 Insufficient Balance"); its two units (the heading check and the gate) went to Codex.

**Units, lane, verdict** (each verdict comes from the coordinator's own run of the acceptance script in `.claude/plan-goal/verify/`):
- U0 commit the previous session's wiki edits — GLM — PASS (`a365c34`).
- U1 heading check `knowledge_base/headings.py` — Codex — PASS on the third run.
  - The first two runs were killed by the subagent MCP loop detector: 8 edits to one file look identical to it (see below). The third ran as direct `codex exec`.
  - The 291 live books pass. Four are listed exceptions with zero headings.
  - All 29 dry-run fixtures separate correctly (8 broken, 4 OCR, 17 clean).
- U2 mobi → EPUB — GLM — PASS on the second run.
  - The first run began OCR'ing The Pyramid Principle, which turned out to be 236 page images. It was cancelled, and the book is skipped under the no-OCR rule.
- U3, U3b–U3e heading recovery — Codex — PASS; 15/15 regression books stay byte-identical throughout. Three rework rounds came from reading the actual headings; the checks had passed each time:
  - four PDFs passed the check while still carrying footnotes, steps and OCR fragments as headings, so they got heading maps;
  - one fix dropped Research Ethics from 19 chapters to 9, caught by the new `u3_epub.sh`;
  - front-matter stripping had cut How to Read a Paper's Chapter 1 (71k characters), so a map now defines where content starts.
- U3r adversarial review — Gemini — 14 findings. Six were confirmed and fixed in U3c; the worst was PDF heading placement overwriting body text.
- U4 heading maps — GLM ×3, Codex ×1 — PASS, every entry placed:
  - Software Engineering at Google 517;
  - Practical Cloud Security 160;
  - How to Read a Paper 176;
  - Bargaining for Advantage 90;
  - PMBOK 200.
- U5 intake registration — Codex in a worktree — PASS.
  - The Codex sandbox refused the hard links (`EPERM`), so GLM created them.
- U5c PMBOK Guide 7e and Head First PMP added at Gary's request — GLM — PASS.
- U6, U6b, U6c ingest, chunk, audit — Codex — PASS.
  - 29 books, 4,799 parents, 20,076 children; the strict audit passes; the 582 pre-existing files are unchanged.
  - Three rework rounds: tiktoken needed network access; recovered EPUBs had kept their front matter; mapped books kept their back-of-book index as body text.
- U7 embedding on the bppc GPU and the v9 build on both servers — Codex — PASS; verify is identical, with 0 overwrites.
- U8 gate — Codex — FAIL on the sanity condition. The hard set is unchanged apart from NDCG −0.0020 (10 regressed, 3 improved).
- U9 promotion, release and docs — not run, because the gate failed. The brief is kept as [v9-promotion-brief.md](../data/intake/v9-promotion-brief.md).

**Decisions made during the run without asking** (each reversible):
- Research, privacy and journalism books went into a separate `research-methods` domain.
- The Pyramid Principle was skipped as image-only, so the batch has 29 books, not the 28 in the goal file's row 6.
- Codex units ran as direct `codex exec` after the MCP loop-detector false positive.
- U5 ran after U3 rather than in parallel.
- Two map children shared the repo workspace; they wrote disjoint files.
- The U5c child was cancelled after its acceptance passed, before it finished its report.
- Codex's wiki edits from U5 were stashed in the u5 worktree (`stash@{0}`). Its U6b wiki edits were corrected here.

**Lane lessons**, written into `conductor/references/lane-plan.md`:
- the lane check must load `~/.config/agent-capabilities/subagent.env`, or keyed lanes falsely show as closed;
- the MCP `verification` command must be a single command;
- direct `codex exec` needs `-s workspace-write`;
- the subagent-mcp Codex adapter reports every edit to one file with the same signature, so the loop detector kills multi-edit work (`src/subagent/providers/codex.py` `_tool_use`). This one is not fixed.

**Unexplained:** one `u6c.sh` run exited 1 with no FAIL line; three reruns exited 0.

## [2026-09-30] conductor run | v9 review fixes
Goal file: [goals/2026-09-30-v9-review-fixes.md](goals/2026-09-30-v9-review-fixes.md). The run fixes what the v9 run review found, in three repos.

**Lane check** (2026-09-30, key file loaded): codex, glm and gemini were open. Three were closed:
- deepseek: 402, out of balance;
- bppc: health check failed;
- omlx: `copilot_model_unavailable`.

**Units, lane, verdict** (each verdict is the coordinator's own run of the row's UAT):
- A1 sanity review, Gemini — PASS: 25 keep, 1 fix-query (PMBOK), 2 fix-label, 1 drop. The reviewer was blind to results.
- A2 PMBOK diagnosis, direct Codex — PASS, branch query-or-label:
  - 523/523 PMBOK points match their chunks;
  - the labelled chunk ranks 2,387 on dense search and 1,204 on BM25 for the original query, and rank 1 for a query that uses the passage's own terms.
  - Found in passing: heading paths repeat `(part 1) (part 1)` (`knowledge_base/chunk.py`). Not fixed.
- A4 rescore, direct Codex — PASS. The Mac reproduces 23/29, and the reviewed set scores 0.821 (23/28). The coordinator filled in the reviewer's lane name, which the unit had written as unknown.
- B1 loop fix, direct Codex — the code passed. The Codex sandbox blocked socket tests and `.git` writes. The coordinator ran the suite outside the sandbox (868 passed). The commit went to a Claude Agent (`6ae599a`), because the `subagent` server refuses its own repo as a workspace.
- C1 and C2, GLM — PASS on the coordinator's runs. C1's verify script sat outside the workspace and was blocked, so it was moved inside for C2.
- C3, direct Codex — PASS on the coordinator's run. The sandbox could not see the scratchpad script.
- C4 (coordinator) — Evolution 4 marked KEEP after two runs, and Evolution 5 added.
- D1 (coordinator) — Character line installed.
- A7 (coordinator) — the destructive-command hook blocked a recursive delete, so `data/qdrant-v9-add` went to the Trash.
- A5 `u6c.sh` flake hunt — PASS, not reproduced (13 runs, all exit 0).
  - Paused at 5/10 runs: another session's 27B training on the Mac GPU had died twice, at 09:12 and 09:58, when A2's and A4's evals loaded models on MPS. That session asked for no GPU work.
  - The ingest checks load no torch, and magika pins `onnxruntime` to the CPU, so they resumed CPU-only and the other session was told.
  - The resumed GLM run showed no transcript activity for 33 minutes and was cancelled. Its cancel result then reported 50 steps, so the empty transcript was misleading.
  - The unit was rerouted to direct Codex. Codex left a `.scratch-u6c/` folder in the repo against its brief; it went to the Trash.
  - `r_a5.sh`'s wiki check failed on the coordinator's own baseline, taken before the coordinator committed the goal file. The wiki was unchanged since `c07d734`, so the check was re-baselined.
- A3 regression (coordinator, CPU-only) — PASS, 15/15 byte-identical.

**Decided forward:**
- The reviewer's lane name was added to gate-v9.md by the coordinator.
- The remaining store was trashed rather than deleted.
- GPU work was paused for the other session.

**Found in this run:** the C4 goal row's UAT (`grep -A12`) prints too few lines to reach the Evolution 4 verdict. The criterion was checked with the full section.

## [2026-09-30] decision | v9 promoted on Gary's call
Gary said "Promote" after seeing both numbers: the pre-set gate FAIL at 0.793 (23/29), and the blind-reviewed set at 0.821 (23/28), with five fair queries still missing. As with v8, the promotion overrides a failed pre-set condition, by the owner's decision and with the failure on record in `data/bench/gate-v9.md`. Promotion runs from `data/intake/v9-promotion-brief.md`, updated with these facts. Another session's GPU training was running on the Mac, so every model-loading step ran CPU-only.
- Promotion unit, GLM: alias switched, tooling and docs changed, release built, 103 tests passed (CPU-only). The first session hit the 80-turn cap; a second finished the doc fixes (`078cc42`, `8f058d9`).
  - The subagent guard refused `gh release create` and `git push`, and the child did not route around it. The coordinator ran both, under Gary's "Promote".
  - Before publishing, the coordinator corrected one wrong sentence in the release notes: the review changes are 1 query rewritten, 2 labels fixed and 1 dropped.
  - `r_u9.sh` PASS. Release `data-v9` is published with 4 assets whose SHA-256 match `manifest.json`, and main is pushed.
  - `.mcp.json` sets no `KB_COLLECTION`, so the live server follows the alias. The new "320 books" instruction text appears when each MCP server restarts.
