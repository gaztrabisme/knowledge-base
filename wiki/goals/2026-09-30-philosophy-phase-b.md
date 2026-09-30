# Goal — 2026-09-30 — philosophy phase B

**Set by:** Gary ("Go", 2026-09-30, on the Plan Block of the same day). **Audited by:** the coordinator at close, against this file only.

**What this run does.** It ingests the rest of the Falun Dafa archive (`~/Documents/books/falun-dafa-pdf-archive/`) into the `philosophy` collection: one edition per work per language, in English, Vietnamese, Simplified Chinese and Traditional Chinese. Phase A put in Zhuan Falun only. The technical collection is not touched.

**Rules for these rows.** No row states a count the run can change; counts come from the file that holds them. A row that depends on a decision passes on each branch. Scope changes from Gary are appended under "Amendments" in his words.

**Baselines recorded before dispatch** (`data/philosophy/phase-b/`): `phase-a-baseline.sha256` (the 20 phase A chunk and markdown files), `baseline.json` (live point counts and alias), `works-phase-a.json` (the registry as it was), `wiki-baseline.txt`.

## Deliverable: the `philosophy` collection with the archive's remaining works

| # | Success criterion | UAT (how to verify) |
|---|---|---|
| 1 | **Hồng Ngâm retried.** Each of the failed Vietnamese Hồng Ngâm URLs in the archive manifest's `source_failures` was retried once with a long timeout. Each is either fetched (file on disk, SHA-256 recorded) or recorded as still failing with the error. | `data/philosophy/phase-b/hong-ngam-retry.json` has one entry per URL in `source_failures`, each with `status` fetched or failed; every fetched entry's file exists and matches its SHA-256 |
| 2 | **Registry complete.** `data/philosophy/works.json` accounts for every book and writing title in the archive manifest (print-layout variants excluded): each is either included with one edition per language, or skipped with a reason. Every included Chinese file has a text-check result that passed, or is flagged `derived` with its source named. The phase A work records are unchanged. | `.venv/bin/python scripts/verify_phase_b/check_registry.py` exits 0 |
| 3 | **Work matching reviewed blind.** Every cross-language work group in the registry has a verdict (match / mismatch / unsure) from a reviewer on a different lane from the one that built the table, who saw titles and opening text but not the builder's reasoning. Every mismatch or unsure is either fixed in the registry or kept with a written reason. | `data/philosophy/phase-b/work-match-review.jsonl` has one row per multi-language group in `works.json`, each with `verdict`; `work-match-resolution.md` lists each non-match and what was done |
| 4 | **Phase A outputs untouched.** | `shasum -a 256 -c data/philosophy/phase-b/phase-a-baseline.sha256` reports every file OK |
| 5 | **Everything included is ingested.** Every included language file in the registry has a markdown file and a chunk file, and every chunk carries `work_id`, `language` and `section_key`. | `check_registry.py --chunks` exits 0 |
| 6 | **Section alignment sampled blind.** 40 aligned section pairs, drawn at random from phase B works, were judged by a reviewer on a different lane from the splitter's author. | `data/philosophy/phase-b/alignment-sample.jsonl` has 40 rows, each with `verdict`; the count of `match` is reported in the gate file |
| 7 | **Test set reviewed before the gate.** A known-item test set from phase B works, 20 queries in each of the four languages, was written from sampled passages and then reviewed by a different lane that was not shown any retrieval result. The review finished before the gate ran. | `data/philosophy/phase-b/sanity-b-reviewed.jsonl` exists with a `verdict` and `reason` per row of `sanity-b.jsonl`; the gate file states it used the reviewed file, and the review report's timestamp precedes the gate report's |
| 8 | **Candidate built.** `philosophy_b` exists on the Mac's Qdrant. Its point count equals the baseline `philosophy` count plus the number of child chunks in the phase B chunk files. | `.venv/bin/python scripts/verify_phase_b/check_candidate.py` exits 0 |
| 9 | **Gate reported.** `data/bench/gate-philosophy-b.md` reports each of the six conditions set in the Plan Block, with its number and pass or fail: (a) the 60-query eval with filters, no group down more than 1 query; (b) the same 60 unfiltered, no group down more than 2; (c) reviewed test set recall@10 at least 0.80 overall and 0.70 per language; (d) at least 36 of 40 alignment pairs match; (e) every included Chinese file passed the text check or is flagged derived; (f) 50 technical hard-set queries give identical results before and after. | The file exists and has a line per condition (a)–(f) with a number and PASS or FAIL; the coordinator re-reads each number from the run's raw output |
| 10 | **Promotion follows the gate.** **If** all six pass: a snapshot of the pre-run collection is in `data/snapshots/`, and `philosophy` holds the candidate's point count. **If** any fails: `philosophy` still has its baseline count and the failure is reported to Gary with the numbers. | `curl` point count of `philosophy`, read against row 9's verdict and `baseline.json`; on the pass branch `ls data/snapshots/philosophy-phase-a.snapshot` |
| 11 | **Release published (pass branch only).** Release `data-v9.1` carries the kb-core parts, the new kb-philosophy parts and a manifest whose SHA-256 values match the uploaded files. `scripts/install.py` defaults to it. README states the new download and installed sizes. **On the fail branch** no release exists and the installer default is unchanged. | `gh release view data-v9.1` lists the manifest and parts, and the downloaded manifest's hashes match `shasum` of `dist/release/*`; `grep -n '"--release-tag"' scripts/install.py`; on the fail branch `gh release view data-v9.1` errors |
| 12 | **Technical collection untouched.** The `developer_knowledge` alias and the point count of `developer_knowledge_v9` equal `baseline.json`. | `curl -s localhost:6333/aliases` and the v9 count, compared with `baseline.json` |
| 13 | **Tests pass.** | `uv run pytest tests -q` with the GPU hidden (`.claude/plan-goal/verify/cpu.py -m pytest tests -q`) exits 0 |
| 14 | **Docs and wiki closed, pushed.** CLAUDE.md describes the philosophy collection as it now is. `wiki/log.md` has the run ledger (each unit, lane, verdict, reroute, fork decided forward). `wiki/decisions.md` records the decisions of the Plan Block and the gate outcome. `wiki/active-work.md` reconciles every row. `main` equals `origin/main`. | `grep -n "phase B"` matches in the three wiki files; `git fetch origin` then `git rev-parse main` equals `git rev-parse origin/main` |

## Working pattern (binds this run)

- **Lanes open** (checked 2026-09-30 with `subagent doctor --prompt --json`, key file loaded): codex, glm, gemini.
- **Lanes closed:** deepseek (no balance); bppc agent lane (its model server is off, and stays off because embedding needs the GPU); omlx (model unavailable).
- **Codex route.** This session's `subagent` server started before fix `6ae599a`, so Codex units that edit one file many times go through direct `codex exec -s workspace-write`. Their commits and any network or socket step are run by the coordinator or another lane.
- **Units and lanes** (primary → fallback):
  - U1 Hồng Ngâm retry: glm → codex.
  - U2 registry, work matching, edition choice, Chinese text check: codex → glm.
  - U3 blind review of work matching: gemini (scratch folder) → fresh codex.
  - U4 general splitter, section alignment, ingest and chunk: codex → glm.
  - U5 blind alignment sample: gemini (scratch folder) → fresh codex.
  - U6 test set: fresh codex writes; gemini reviews blind.
  - U7 embed on bppc, build `philosophy_b`: codex → glm; remote steps run by the coordinator if the sandbox blocks them.
  - U8 gate: fresh codex → glm; runs on bppc.
  - U9 promote, release, docs, push: glm → codex; the coordinator runs the publish and push if the guard refuses.
- **Hardware.** The Mac's GPU belongs to another session. All embedding and evaluation run on bppc; Mac work is CPU-only.
- **Standing rule from the peer session.** If anything in this run would change technical chunk ids, message the session `release-one-gap-study` first. Nothing planned here does.

## Amendments

(none)
