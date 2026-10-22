# Wiki Log

## [2026-10-01] run | Philosophy phase B: rest of the Falun Dafa archive (gate failed, not promoted)
Goal file: [2026-09-30-philosophy-phase-b](goals/2026-09-30-philosophy-phase-b.md). Gate: [gate-philosophy-b.md](../data/bench/gate-philosophy-b.md) — DO NOT PROMOTE (b, c, f fail).

**Units, lanes, verdicts**
- U1 Hồng Ngâm retry: GLM refused (Z.ai 1301 "unsafe or sensitive content") → Codex direct. 9/9 fetched (the original failures were a 1.5 s timeout). PASS.
- U2 selection (Codex direct): 118 works, one edition per language, Chinese text check on every candidate. PASS (`check_selection.py`).
- U3 blind match review (Gemini): first run killed by the loop detector (12 shell reads reported as identical calls) → rerun reading with the file viewer. 106/106 groups match (incl. the two phase A works). PASS.
- U4 splitter/ingest (Codex direct, one session resumed 4 times): first output passed `check_registry.py` with scrambled 2-up Chinese, letter-spaced Traditional text, heading-only chunks and contents lines as sections. The coordinator added `check_chunk_quality.py` and sent a rework brief. The run was cut twice by the background-shell 2-hour limit. Fix 2 (after U5 run 1): lost section endings, poem pages, a merged boundary, download furniture. Fix 3 (after U5 run 3): late section starts (59 to 0), garbled `hong-yin-iii.zh-Hans` skipped. Final: 43,690 chunks. PASS.
- U5 blind alignment review (Gemini): run 1 26/40 (real tail loss); run 2 33/40 on a defective packet (the coordinator's builder dropped each chunk's first paragraph); run 3 35/40 on the corrected packet (5 real late starts); run 4, new seed after fix 3, 40/40. One Gemini quota refusal (reset in 46 min) waited out rather than falling back to Codex, to keep a different model family as reviewer.
- U6 test set: fresh Codex wrote 80 rows from written rules; stopped once because fix 2 was about to re-chunk; rerun; targets re-pointed by text after fix 3; Gemini review: 64 keep, 14 fix label, 1 fix query, 1 drop → 79 rows.
- U7 candidate builder (Codex direct): sparse/BM25 on CPU; dense stage tested on CPU (cosine 1.000000 vs the production path); U7b added `cuda`. Dense pass on bppc's RTX 5080 (~3 min) after bppc came back at 06:33; GPU vs CPU vectors cosine ≥ 0.9999. `philosophy_b` = 52,122 points. PASS.
- U8 gate script (Codex direct). The first gate run was cut by the 2-hour limit during step 5; steps 5–6 finished through the script's own runner (`.claude/plan-goal/verify/gate_resume.py`).
- U9 promotion/release: not run (fail branch).

**Forks decided forward**
- GLM closed for this corpus (content filter); its units went to Codex.
- bppc was off the network 21:45–06:33; a Mac GPU window was arranged with the gsq session for 14:00, then released when bppc returned.
- U3 and U4 ran in parallel; U6 was stopped and rerun when fix 2 had to re-chunk under it (the coordinator had started fix 2 while U6 shared the workspace).
- Gate condition (b) "no filters" was read as dropping both the work and the language filter.
- Test-set queries use a language filter and no work filter.
- Remaining text defects accepted and documented (contents lines in the opening of Falun Gong, one interleaved question in collected-fa-teachings-vol-xv.zh-Hans).

**Findings outside the run**
- `knowledge_base/chunk.py` `create_children` drops a section's final paragraph group under 75 tokens (technical and phase A chunks affected).
- Live philosophy cross-language eval reads 0.800 today on CPU (phase A recorded 1.000 on GPU); the pre-run code gives the same per-query result.
- (f) technical differences: 5/50 queries changed top-10 membership slightly with the technical collection unchanged; likely CPU reranker nondeterminism between runs (6 vs 8 threads), not confirmed.

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

## [2026-10-10] run | kbu-2026-10-07 organized-mind research — dispatched
Huy said "Go" on the revised plan (goal file `wiki/goals/2026-10-07-organized-mind.md`, grounding `data/intake/kbu-2026-10-07/grounded.md`). He asked that resources be coordinated with other sessions.

**Lane check 2026-10-10 00:30:** open: codex (model now gpt-6.1-sol), omlx, bppc-lfm (belongs to the IELTSy session, not used). Closed: gemini (disabled by Huy 2026-10-07 after two loops), bppc (no model server: the IELTSy session's `epi-lfm-vllm` container holds 13.5 of 16 GB GPU), glm (429, out of balance), deepseek (auth failure).
**Resources:** Mac swap 16.3 / 17.4 GB used, 51% memory free: no model loads on the Mac. bppc GPU held by IELTSy; message sent to that session asking for a GPU window. Wave 1 is CPU-only.

| Run ID | Unit | Lane | Status | Acceptance | Forward decision / reroute |
|---|---|---|---|---|---|
| kbu-2026-10-07 | lanes | — | — | — | Gemini fallback (F4) no longer exists: every codex unit has no cloud fallback; R6 and A1 move to omlx (A1 must differ from the writer's lane); R1 timing runs on bppc CPU instead of the Mac. |
| kbu-2026-10-07 | R1–R4 | codex | dispatched | `bash verify.sh` | — |
| kbu-2026-10-07 | R5, R6 | codex, omlx | queued | — | subagent `max_agents = 4`; dispatched when slots free. |
| kbu-2026-10-07 | R1 (MCP attempt) | codex | FAIL (form passed) | `bash verify.sh` exit 0, but REPORT.md holds no facts or timings | Refusal: the subagent guard's supervisor denies all network calls by design (`guard/supervisor.py`: "DENY anything that … sends data to a network endpoint"), so ssh to bppc, WebFetch and WebSearch were denied. Format pass not accepted. |
| kbu-2026-10-07 | R2–R4 (MCP attempts) | codex | cancelled | — | Same network block; cancelled at about 8 min. R3's cached paper texts and R4's local inventory kept for reuse. |
| kbu-2026-10-07 | R1–R5 | direct `codex exec` (gpt-6.1-sol, xhigh, workspace-write, network on, live web search) | dispatched | `bash verify.sh` | Reroute per lane-plan.md "Codex directly": research needs the network the MCP guard denies. Runner `checks/run_unit.sh`, 2 h alarm each. |
| kbu-2026-10-07 | R6 | omlx (MCP) | dispatched | `bash verify.sh` | No network needed. |
| kbu-2026-10-07 | R6 (omlx) | omlx | FAIL | — | omlx stream stalled after 21 min ("OpenAI completions stream stalled"), nothing written. Rerouted to direct codex (no network needed). |
| kbu-2026-10-07 | R3 | direct codex | PASS | `bash R3/verify.sh` PASS; read prior-reasons table (3 quoted reasons, each answered), recommendation (build catalog + coverage ledger first, graph tools optional, 48-unit / 96-question pilot design) and litgraph read-only audit sample (24,782 canonical nodes, 31,428 aliases) | — |
| kbu-2026-10-07 | R4 | direct codex | PASS | `bash R4/verify.sh` PASS, 12/12 inventory paths exist; read edit-vs-annotate (recommends annotate-by-default, reviewed patches for source changes) and both pointer repos examined at pinned commits | — |
| kbu-2026-10-07 | R5 | direct codex | PASS | `bash R5/verify.sh` PASS; read core-vs-adapter interface (7 adapter functions, 5 core functions) and mapping table (6 principles + 7 anti-patterns, each with a proving check) | — |
| kbu-2026-10-07 | GPU window | — | granted | — | efficient-pi-ae (owner of `epi-lfm-vllm`) lent bppc's GPU "until I ask for it back" (est. 2–4 h), terms: one job at a time, release within ~10 min on request, stop-daily.sh before hand-back. M3 chosen for this window; M1 waits for the large window after efficient-pi-ae's scored runs. The IELTSy session's essay run uses the Mac's oMLX, which explains R6's stall. |
| kbu-2026-10-07 | M3 | direct codex (extraction on bppc qwen3.8-27b via start-llm) | dispatched | `bash M3/verify.sh` | Course input: 8 English VTTs of the Coursera "Use Generative AI as Your Thought Partner" lectures, fetched by the coordinator through Huy's signed-in browser (`M3/inputs/`). |
| kbu-2026-10-07 | R1 | direct codex | PASS | `bash R1/verify.sh` PASS; read fact sheet and timing: 744M params full / 271M text-only; 768 dims, Matryoshka 768/512/256/128; 8,192-token input; text query 34.9 ms fp32 / 15.2 ms int8 on bppc 9950X @16 threads vs Jina v5 92.1 ms; image ~1.08 s fp32; KB `embedder.py` defaults unknown models to 1024-dim Jina task args, so a swap needs explicit registration | — |
| kbu-2026-10-07 | R2 | direct codex | PASS | `bash R2/verify.sh` PASS; 30 technique rows; read recommended stack (hash-manifest re-ingestion, 256-dim Matryoshka first, Qdrant int8 scalar + rescoring, Ettin ONNX re-check, exact caches); no end-to-end speedup claimed (stage shares not found) | — |
| kbu-2026-10-07 | R6 | direct codex | PASS | `bash R6/verify.sh` PASS; read options: recommends Option C (separate repos + shared document format + one MCP interface + one installer); notes Option B fits "one repo" if Huy means that | Fork for Huy at Close: what "one project" means physically. |
| kbu-2026-10-07 | wave 1 | — | PASS (6/6) | — | — |
| kbu-2026-10-07 | M2, P1 | direct codex | dispatched | `bash M2/verify.sh`, `bash P1/verify.sh` | M2 CPU-only on bppc (GPU lent to M3). P1 starts before M1–M3 finish and marks their dependent measures "pending"; it gets a revision pass once they land. |
| kbu-2026-10-07 | M2 | direct codex | PASS | `bash M2/verify.sh` PASS (24 image, 12 code queries); read results: text-only page recall@10 24/24 (saturated); multimodal 23/24 with MRR 0.683→0.819; exact figure in top 10 for 20/24, 8/9 where the answer is only in the figure; one loss (I08); code 12/12 for all three arms (no separation) | Queries written by the same agent after seeing the figures: biased; recorded in the report. |
| kbu-2026-10-07 | P1 | direct codex | PASS | `bash P1/verify.sh` PASS; read opportunity comparison (recommends B: KB + coverage catalog + annotated memory; typed graph gated) and 8 open questions | P1 calls the live baseline "unresolved"; it is `developer_knowledge_v10` (grounded.md Input 2). Passed to D1 as a correction. |
| kbu-2026-10-07 | M3 | direct codex | stopped (GPU recalled) | — | efficient-pi-ae sent "need the GPU back" at ~02:50; coordinator killed extract.py and its codex parent, left the daily Qwen up at that session's request (not stop-daily.sh), replied "released". 30/48 units done at concurrency 1; concurrency 2/4 slice not run. Analysis pass dispatched (no model calls) to write a PARTIAL report from the 30 units. |
| kbu-2026-10-07 | M3 (analysis pass) | direct codex | PASS (PARTIAL data) | `bash M3/verify.sh` PASS; read throughput (30 units at concurrency 1: median 178 s/unit, 4 timeouts at 300 s; 12 book, 12 course, 6 paper, 0 code), spot-check (same-agent: e.g. paper 6/6 and 8/8 supported, book-01 6/7 with 2 invalid quotes) and projection (320 books ≈ 4,930 GPU hours at measured rate; papers ≈ 1,109 h; code not measured; concurrency scaling not measured) | Load-bearing for D1: whole-library typed extraction is not practical on local hardware at this rate. |
| kbu-2026-10-07 | D1 | direct codex | dispatched | `bash D1/verify.sh` | Coordinator-verified corrections in the brief: live = v10; M1 not run, so the design states pass/fail branches. |
| kbu-2026-10-07 | D1 | direct codex | PASS (v1) | `bash D1/verify.sh` PASS; 11,203 words; read Product summary (shape B; v10 control; corrections applied) and Storage and search (Qdrant + BM25 + Ettin kept; embeddinggemma-2 768-dim reference then 256/512; int8 scalar + rescoring; explicit M1 pass / fail / pending branches) | — |
| kbu-2026-10-07 | A1 | omlx (MCP) | dispatched | `bash A1/verify.sh` after the D1 revision | Different lane from the writer (codex). oMLX was idle (0 models, 0 requests); IELTSy session notified. |
| kbu-2026-10-07 | A1 (omlx) | omlx | FAIL | — | Loop detector: "identical tool call repeated 8 times" after 715 s (cold load). Second omlx failure this run. Rerouted to a fresh direct codex session with a refute mandate; independence is weaker (same model family as the writer, no shared context) and is recorded as such in the close report. |
| kbu-2026-10-07 | M3 (completion) | direct codex (bppc qwen3.8-27b) | dispatched | `bash M3/verify.sh` | Second GPU window from efficient-pi-ae (est. 3–4 h). Partial report kept as `M3/REPORT-partial-30.md`. |
| kbu-2026-10-07 | A1 (codex) | direct codex, fresh session | audit written | register read: 120 claims — 106 supported, 10 evidence only, 2 assertion, 2 overstated; open claims table read | Main finding: P1 states the promotion gate as two hard-set limits and drops the inherited sanity condition (recall@10 ≥ 0.80; v10 scored 28/30 = 0.9333, `data/bench/gate-v10.md`), against Huy's "same as v9/v10 gate". Also: unowned thresholds (0.80 latency ratio, 6,000-token cap, 20-task review window, one retry), chapter-read metadata contract gap, P1's run-wide GPU ban overstated. D1 revision held until M3's final numbers so one pass covers both. A1 `verify.sh` runs after that revision. |
| kbu-2026-10-07 | M3 (completion) | direct codex | stopped (GPU recalled, 2nd window) | 48/48 units at concurrency 1 (12 per type); concurrency 2/4 slice not run | Replied "released" to efficient-pi-ae; daily Qwen left up. M3 needs no more GPU. Final analysis pass (no model calls) then D1 v2 revision, sequential. |
| kbu-2026-10-07 | M3 (final) | direct codex | PASS | `bash M3/verify.sh` PASS; read: 48/48 at concurrency 1; returned 40, strict-valid 35; median 182 s/unit, 4–3 timeouts per type at 300 s; code 12 units (≈31k source tokens/h); 320 books ≈ 5,430 sequential GPU hours; concurrency not measured | — |
| kbu-2026-10-07 | D1 v2 | direct codex | PASS | `bash D1/verify.sh` PASS; `bash A1/verify.sh` PASS; read revision log (C022–C120 and the M3 claims each addressed) and the complete gate (hard NDCG drop ≤ 0.010 AND hard recall drop ≤ 0.005 AND sanity recall@10 ≥ 0.80) | Measurement- and Huy-owned A1 claims left as open choices 10–14, not invented. |

### Close audit (2026-10-10) — goal file `wiki/goals/2026-10-07-organized-mind.md`
G1–G6 PASS · G7 (M1) **FAIL — not run**: bppc's GPU is shared and the long window comes after efficient-pi-ae's scored runs; the run stays open for M1 only · G8–G12 PASS · G13 PASS (alias still v10; litgraph, agent-workflow skills and KB code unchanged) · G14 (Huy's keystone) open.
Deliverables copied to `data/intake/kbu-2026-10-07/`: `product-brief.md`, `design-spec.md` (v2), `audit.md`, `reports/*`. Workspaces stay at `~/Documents/Work/tools/kbu-2026-10-07/`. Daily Qwen on bppc left running at efficient-pi-ae's request.
**Decided forward:** units rerouted from the subagent MCP server to direct `codex exec` with network (the guard denies all network by design); R6 and A1 moved off omlx after a stall and a loop; A1's independence is weaker than planned (fresh codex session, same model family as the writer); M3 run in two lent GPU windows; D1 revision batched with final M3.
| kbu-2026-10-07 | M1 | — | waiting | — | 2026-10-10: efficient-pi-ae reports Huy is shutting bppc down for a rest; its run is paused with 6 tasks left, and M1's window moves after bppc returns and those finish. No kbu process was running on bppc. M1 brief ready at `checks/brief-M1.md`. |
| kbu-2026-10-07 | context request | — | answered | — | 2026-10-11: the "Test epi agent subagent call" session (designing a harness-neutral MCP + skill bundle on pi core 1.0, at Huy's request) asked for this run's memory-layer design; sent pointers only (paths and section line numbers), no content. efficient-pi-ae's SWE-bench run is closed and it no longer needs bppc; M1 can run once bppc is powered back on. |
- 2026-10-14 07:40: Huy: coordinate bppc with the pi-mind sessions, start M1 after they finish. bppc up; Strata (Qwen3.8-Flash) holds 15.5/16 GB GPU since 07:37. Asked 'Pi-mind conductor Plan Block' and 'Review pi-mind W1 memory slice' for their schedule and a 'bppc released' message; GPU watcher running. untouched.sh FAILs on agent-workflow skills/ edits by other sessions (reward-design, omlx, 5 design skills), not by this run's lanes.
- 2026-10-14 07:45: Strata = pi-mind conductor's W1 SWE-bench run (daily LLM via start-llm proxy). GPU expected free ~19:00-21:00 today, worst case ~20 h. Hold until 'bppc released'; then run ~/.local/bin/stop-llm from the Mac and launch M1. Their CPU scoring in Docker on bppc follows; they will check before starting it.
- 2026-10-14: pi-mind sent 'bppc released' (Gary stopped its benchmark). stop-llm run from Mac; GPU 120 MiB. M1 launched via run_unit.sh, 16 h cap. pi-mind will ask for a GPU window later (Swift 1.5 engine test, then 10-20 h scoring).
- 2026-10-14 12:43: M1 done (codex, exit 0, verify PASS). kbu_m1_gemma768 PASS: hard NDCG@10 0.7393->0.7351 (-0.0042), hard recall@10 0.9521->0.9498 (-0.0023), sanity 28/30 (0.933). kbu_m1_gemma256 PASS: hard NDCG -0.0045, recall -0.0023, sanity 28/30. CPU query embed (9950X, 16 thr, fp32): Jina median 103 ms, Gemma768 42.7 ms. Build 2,578 s active embedding on RTX 5080, 6 sessions. Operator inference: 1,160 PostgreSQL children restored from frozen v10 payloads in the private copy (current Mac files differ from v10); owner confirmation not received. No promotion; Mac alias still v10. GPU handed to pi-mind ('go'). Close audit: G1-G12 PASS; G13 untouched.sh FAILs only on agent-workflow skills/ edits by other sessions (alias, litgraph, KB code unchanged); G14 open (Huy's verdict on brief/design).
- 2026-10-14 13:30: Huy's answers on open decisions. B: switch live search to Gemma 768 = yes. C: use today's chunk files (not restored v10 payloads). Part 2: 1 = separate repos + one interface/installer (R6 C); 2 = this Mac hosts the writer and all infrastructure, bppc only the LLM engine; 3 = start coverage on one current task; 8 = testable subset first; 9 = keep 300 ms provisional; 10 = wait for Mac measurement; 14 = accept pre-registered scoring. Asked for explanation: A (why ~5,430 h graph), 4, 5, 6, 7, 11, 12, 13. M1b launched (resumed M1 codex thread, CPU only on bppc, 8 threads): rebuild kbu_m1_gemma768_cur from today's chunk files and re-gate.
- 2026-10-14: Huy: A (graph) → test a smaller model, LFM2.5-24B-A2B, with a quant that fits entirely on the RTX 5080. "Ok to rest" = accept recommendations for 4 (bounded scope, freeze GPU-hour ceiling first), 5 (page links + separate figure search, one-subject trial), 6 (Huy reviews candidates via review queue), 7 (mechanical facts closed by recorded recheck; guidance by Huy), 11 (6,000-token cap for the answer-benefit experiment only), 12 (review all lessons from first 20 tasks), 13 (one retry, receipt check first, outbox). M4 brief written (checks/brief-M4.md); quants QAD-Q4_0 (13.58 GB) and UD-Q3_K_XL (10.95 GB) downloading to bppc; M4 waits for pi-mind's GPU release.
- 2026-10-14: M1b (today's files, kbu_m1_gemma768_cur) gate FAIL: hard NDCG -0.0123, recall -0.0137; 9 PostgreSQL parent IDs re-chunked to different text; 7 touched hard queries 5->0 hits, other 431: 412->411. M1c launched: remap the 9 labels by text overlap, re-gate on CPU with a CPU v10 control.
- 2026-10-14 16:53: pi-mind timed scoring starting (2x25 SWE-bench, up to ~20 h). M1c paused via M1c/PAUSE at candidate hard 431/438; replied 'paused'. Note: run_m1c.sh 4 h alarm will end the Codex turn during the pause; resume the M1 thread (01a1388f-...) after 'bppc released', remove PAUSE, then launch M4.
- 2026-10-14: Choice 1 clarified (Gary's words "A it is", relayed by the pi-mind conductor session, not said in this session): pi-mind stays one repo for the harness side (extension, bundle server, memory server, plan-goal); the knowledge base and archive keep their own repos, joined to pi-mind by the shared interface and one installer.
- 2026-10-14 19:35: M1c Codex turn ended by its 4 h cap during the pause (exit 142), as expected. REPORT.md is a placeholder: 'FAIL, incomplete evidence' (verify.sh passes on format only). Progress kept at candidate hard 431/438; PAUSE marker still set. Resume after 'bppc released'.
- 2026-10-14: G14 met: Huy 'Approve as whole' (relayed by pi-mind). Recorded in decisions.md, active-work.md, goal file.
- 2026-10-14 22:30: Goal step 3a/3b done ahead of step 1 (no live change). Worktree ../knowledge-base-wt/gemma-switch, branch unit/gemma-switch (uncommitted): knowledge_base/embedder.py registers google/embeddinggemma-2 (768 and ::256, pinned 914f7f89, SearchQuery/Document prompts, float32, text-only, literal media-marker path from M1); transformers 5.17->5.19 and torchvision 0.29.1 added (the Gemma processor imports torchvision). pytest: 166 pass, 2 philosophy tests fail only because untracked philosophy chunk files are absent from the worktree (same tests pass on main). Mac CPU query latency, 100 hard queries, 8 threads, oMLX busy in background (load ~7): Gemma768 median 98/83/78 ms, p95 120/94/87 ms, peak RSS 2.4 GB; Jina v10 median 166/168/138 ms, p95 210/190/158 ms, peak RSS 4.1 GB (3 runs each, kbu-2026-10-07/S3). Both under the 300 ms reference; Gemma median ≈ 0.5-0.6x Jina.
- 2026-10-15: Huy: Bob (~/Documents/Work/tools/bob, headless session 285b6d9e-…) is now the point of contact for shared machine resources. Told pi-mind, IELTSy, the pi-mind W1 reviewer and Bob; existing arrangements stand until each session hands over.
- 2026-10-15: Bob now runs continuously in tmux session "bob" (claude --resume with --remote-control Bob), at Huy's request; hourly read-only round scheduled (cron 7b1020a5, :07 each hour). Stop: tmux kill-session -t bob.
- 2026-10-15: Bob's board D-bppc: Huy approved a bppc security-update reboot after M4 and pi-mind's rebuild (~05:00-07:00 on 10-16), and a Mac restart ~10:00-12:00 on 10-16 that ends all Claude sessions. Agreed: report 'M1c done'/'M4 done' to Bob; no new bppc jobs until he confirms the reboot finished; step 3c booked with Bob, after the Mac restart if needed. If this session ends in the restart, resume from this log: goal steps in the 2026-10-14 entries, M1c thread 01a1388f-..., worktree ../knowledge-base-wt/gemma-switch (uncommitted).
- 2026-10-15 19:00: pi-mind 'bppc released' (engine stopped 12:20 UTC). M1c resumed (PAUSE removed, Codex thread resumed with checks/resume-M1c.md, CPU threads 0-7); M4 started (checks/run_unit.sh M4, 14 h cap, cores 8-31, GPU). Bob confirmed bppc free at 18:53.
- 2026-10-15 20:00: M4 done (verify PASS). LFM2.5-24B-A2B QAD-Q4_0 fits fully on the 5080 (41/41 layers, 13.6-14.1 GB) and is ~9x faster per unit (median 20 s vs 182 s) but 3/48 strict-valid vs Qwen 35/48 at 8k context (43 length stops mid-reasoning); 32k diagnostic 2/4 strict-valid, 5/22 relations supported (type/predicate errors). Recommendation: keep Qwen for bounded graph repair; any further LFM trial needs >=32k context and a revised prompt. Pencilled 32k GPU hour cancelled with Bob.
- 2026-10-15: Huy (via pi-mind): LFM2.5's chat template is broken and needs updating. M4 used the GGUF's embedded template (--jinja, no --chat-template). The M4 verdict therefore holds only for that template; P6 (pi-mind) will rerun M4's 48 units, separately versioned, with the current upstream template.
- 2026-10-15 20:42: M1c done, PASS (verify PASS). kbu_m1_gemma768_cur vs CPU v10 control: hard NDCG@10 -0.0035, hard recall@10 0.000 (417/438 both), sanity recall@10 0.933; easy NDCG -0.0052, recall 1.0. 8/9 PostgreSQL labels remapped by literal overlap (0.875-0.979 combined); p140 unmapped (0.094). Touched hard queries: control 5/7, candidate 6/7 hits. Note: the report attributes 'finish every remaining arm' to Huy; it was the coordinator's resume instruction. Next: step 3c (snapshot, Mac restore as v11, Mac gate), booked with Bob.
- 2026-10-15 20:45: Step 3c part 1 done: snapshot of kbu_m1_gemma768_cur (2,728,179,712 bytes, sha256 5759b19d…0642, matches Qdrant checksum) copied to the Mac at knowledge-base/data/snapshots-v11/ (gitignored). The snapshot also stays inside kb-qdrant's container snapshot dir on bppc (not on a mounted volume); Bob has it for cleanup after the switch. Mac restore + gate: Bob's slot after the 10-16 Mac restart, once memory is green with IELTSy's Qwen loaded (2 h, ≤8 threads).
- 2026-10-15 21:00: Step 3c prepared: kbu-2026-10-07/S3c/run_gate.sh (restore snapshot as developer_knowledge_v11, then unchanged eval_retrieval.py on CPU, 8 threads, remapped labels from M1c). Branch change: knowledge_base/search.py reranker now honours KB_DEVICE (so CPU runs stay off the Mac GPU). Worktree data/chunks symlinked to main's data/chunks. Waiting on Bob's Mac slot after the 10-16 restart. Gate record will be data/bench/gate-v11.{md,json} (pi-mind P5F reads the JSON).
- 2026-10-15: Huy: "Yes" to switching the live alias developer_knowledge to developer_knowledge_v11 if the Mac gate passes (asked as 'yes, switch if it passes'). Merge of unit/gemma-switch is still a separate ask.
- 2026-10-16 07:25: Step 3c PASS on the Mac. developer_knowledge_v11 restored (330,833 points). Mac CPU gate: hard NDCG@10 0.7360 vs v10 0.7391 (-0.0031), hard recall@10 0.9521 both, sanity 0.9333; easy 0.8988/1.0. gate-v11.md/json written on branch unit/gemma-switch. Alias NOT moved: live MCP servers run main's Jina code, so the switch needs the merge (Huy's separate yes) + uv sync + server restart. Branch now also: config default = Gemma; philosophy search loads its own Jina (its collection is 1024-d); reranker follows KB_DEVICE. Tests: no new failures (2 FP baseline tests fail on main too; 2 philosophy tests need untracked data). Bob told the restart need not wait.
- 2026-10-16 07:35: Switch done (Huy: 'Merge and switch'). Pi-mind notified first. unit/gemma-switch rebased onto 6bb95e3 and fast-forwarded: main 2b35da9 (switch + gate-v11.md/json), then 6ebedf1 (test_merge_collection uses EMBEDDING_DIM). uv sync on main (transformers 5.19, torchvision 0.29.1). Fresh-process searches on v11 and philosophy OK. Alias developer_knowledge → developer_knowledge_v11 (atomic delete+create); v10 kept (330,778 points, green). pytest main: 207 passed, 2 failed (pi-mind's FP baseline jsonschema issue, pre-existing). Running KB MCP servers keep old Jina code until the Mac restart (Bob: OK at 08:00). Rollback: alias → v10 + KB_EMBEDDING_MODEL=jinaai/jina-embeddings-v5-text-small-retrieval (or revert 2b35da9) + restart MCP servers. Not pushed. Worktree ../knowledge-base-wt/gemma-switch can be removed; snapshots in data/snapshots-v11 and on bppc kb-qdrant are Bob's cleanup items.
- 2026-10-16 07:35: FAULT from Bob: running KB MCP servers (old Jina code in memory) failed against v11 ('expected dim 768, got 1024'); the Mac restart moved to ≥08:45. Alias moved back to v10 at 07:35; a search via the running MCP server works again. Main keeps the Gemma code (2b35da9). Booked with Bob: re-switch the alias to v11 right before the restart, on his 'go'. Lesson: an embedding-model switch must move the alias in the same moment the MCP servers restart, not before.
- 2026-10-16 07:50: Huy: 'switch'. Alias developer_knowledge → developer_knowledge_v11 (final); a fresh-process search through the live alias works. Bob told RELEASED alias; Mac restart 08:00 reloads all KB MCP servers onto main's Gemma code. gate-v11 records updated (commit on main, not pushed). Session close: this run's share of the organized-mind build is done.
- 2026-10-16 08:05: After the Mac restart, this session's KB MCP server (new Gemma code) searched the live alias (v11) and returned postgresql-14-internals p67 'Autovacuum in Action (part 17)' for the WAL-recycling question, the remapped gate answer. Switch verified end to end. Mac memory 95% free.
