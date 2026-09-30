# Goal — 2026-09-30 — v9 review fixes

**Set by:** Gary, via `/goal`. **Audited by:** the coordinator at close, against this file only.

**Source:** the v9 run review of 2026-09-30. It found problems in three places: the knowledge-base repo, the conductor and applied-ml-problem-solver skills, and the subagent MCP server (`~/Documents/Work/tools/mcp/subagent-mcp`).

**Rules for these rows** (learned from the v9 goal file, where two rows could never pass):
- No row states a count that the run can change. Counts come from the file that holds them.
- A row that depends on a decision passes on each branch of that decision, and says so.
- If Gary changes the scope mid-run, the change is appended under "Amendments" with the date and his words. Existing rows are not re-worded.

## Deliverable A: knowledge-base repo

| # | Success criterion | UAT (how to verify) |
|---|---|---|
| A1 | **Sanity set reviewed.** Every query in `data/bench/gate-v9/sanity.jsonl` has a verdict (keep / fix query / fix label / drop) and a reason. The reviewer is a different lane from the one that wrote the queries, and is not told which queries missed. Every positive chunk ID in the reviewed file exists in `data/chunks/`. | `.venv/bin/python -c` check: the row count of `sanity-v9-reviewed.jsonl` equals the row count of `sanity.jsonl`; every row has `verdict` and `reason`; every positive resolves. The brief records that the miss list was withheld. |
| A2 | **PMBOK miss explained.** `data/bench/gate-v9/pmbok-diagnosis.md` names the cause, with evidence. **If** the cause is in ingest or chunking: the fix is in, PMBOK is re-embedded, its points in `developer_knowledge_v9` are replaced, and a pmbok-guide-7e passage reaches the top 50 candidates for its query. **If** the cause is the query or label: the diagnosis says so, and A1 carries the fix. | The diagnosis file exists and states which branch applies. For the ingest branch: the candidate check prints a pmbok-guide-7e hit in the top 50, and `merge_collection.py verify` passes. |
| A3 | **Existing books untouched.** | `.venv/bin/python scripts/regression_ingest.py` reports all regression books byte-identical |
| A4 | **Rescore reported without overwriting the gate.** `data/bench/gate-v9.md` still reports sanity recall@10 = 0.793 (23/29) as the result under the conditions set before the run. A new section adds the score on the reviewed set, the queries that changed and why, and the v9 collection state it ran on. | `grep -n "0.793103 (23/29; 24 hits required)" data/bench/gate-v9.md` matches, and `grep -n "Reviewed sanity set" data/bench/gate-v9.md` matches |
| A5 | **The `u6c.sh` exit is explained or bounded.** | `data/intake/v9-u6c-flake.md` exists, records at least 10 runs with their exit codes, and names a cause or states "not reproduced" |
| A6 | **Promotion follows Gary's call.** **If** Gary said promote after seeing A4: the alias points to `developer_knowledge_v9` and `v9-promotion-brief.md` ran to its own acceptance. **Otherwise**: the alias still points to `developer_knowledge_v8`. | `curl -s http://127.0.0.1:6333/aliases`, read against the decision recorded in `wiki/log.md` |
| A7 | **Loose ends removed.** The `knowledge-base-u5` worktree, its stash (`u5 wiki edits`) and `data/qdrant-v9-add/` are gone. | `git worktree list` has no `knowledge-base-u5`; `git stash list` has no "u5 wiki edits"; `test ! -e data/qdrant-v9-add` |
| A8 | **Pushed.** | `git fetch origin` then `git rev-parse main` equals `git rev-parse origin/main`, and `git status --short -- . ':!wiki'` is empty |

## Deliverable B: subagent MCP server

| # | Success criterion | UAT (how to verify) |
|---|---|---|
| B1 | **The Codex loop false positive is fixed.** A Codex run that edits one file 10 times, with commands in between, is not killed. 8 identical commands are still killed. | In `~/Documents/Work/tools/mcp/subagent-mcp`: `uv run pytest -q` passes and includes the two new tests (named in the report). The fix is committed locally, and `git status --short -- src tests` is empty. |

## Deliverable C: skills (conductor, applied-ml-problem-solver)

| # | Success criterion | UAT (how to verify) |
|---|---|---|
| C1 | **Goal-file rules.** `conductor/references/goal-file.md` states the three rules at the top of this file: no changeable literal counts, a pass on each branch of a decision-dependent row, and owner scope changes appended as dated amendments. | `grep -n` finds each of the three rules in `goal-file.md` |
| C2 | **Acceptance looks at output.** `conductor/references/lane-plan.md` requires three things in each brief: acceptance includes a sample of the real output that the coordinator reads; a brief that forbids wiki edits has a wiki-untouched check; and environment facts in a brief are checked on the machine before dispatch. | `grep -n` finds each of the three rules in `lane-plan.md` |
| C3 | **Test sets are reviewed before the gate.** An `applied-ml-problem-solver` reference requires that a test or sanity set written for a gate is reviewed against written rules, by a different lane from its author, before the gate runs. | `grep -rn` finds the rule under `applied-ml-problem-solver/` |
| C4 | **Skill ledger settled.** In `conductor/EVOLUTION.md`, Evolution 4 has a verdict other than PENDING, and an entry records C1–C3. **If** B1 passed: `lane-plan.md` no longer tells Codex multi-edit units to go through direct `codex exec`. **Otherwise**: the workaround stays. Both skill repos are committed. | `grep -n "Evolution 4" -A12 EVOLUTION.md` shows the verdict; `grep -c "Until the adapter puts the diff" lane-plan.md` is 0 if B1 passed and 1 if not; `git status --short` is empty in `conductor/` and `applied-ml-problem-solver/` |

## Deliverable D: global instructions and wiki

| # | Success criterion | UAT (how to verify) |
|---|---|---|
| D1 | **Character line installed.** The Truthfulness bullet in `~/.claude/CLAUDE.md` says that a passing check is not the output. The Character section stays under 15 lines. | `grep -n "a passing check is not the output" ~/.claude/CLAUDE.md` matches; the line count between `## Character` and the next `##` is under 15 |
| D2 | **Wiki closed.** `wiki/log.md` has this run's ledger: each unit, lane, verdict and reroute, and every fork decided forward. `wiki/decisions.md` records the rescoring rule (A4) and the promotion call. `wiki/active-work.md` reconciles every row here as done, deferred or blocked. | `grep -n "v9 review fixes"` matches in `wiki/log.md`, `wiki/decisions.md` and `wiki/active-work.md` |

## Working pattern (binds this run)

- **Lanes open** (checked 2026-09-30 with `subagent doctor --prompt --json`, key file loaded): codex, glm, gemini.
- **Lanes closed:**
  - deepseek: 402, out of balance;
  - bppc: `:8080/v1/health` does not answer;
  - omlx: `copilot_model_unavailable`.
- **Units and lanes:**
  - A1: gemini, in a scratch folder, single-file output → fallback codex, in a fresh session.
  - A2: codex → glm. If re-embedding is needed, it runs on the Mac, because bppc is down.
  - A4: codex.
  - A5: glm → codex.
  - B1: direct `codex exec -s workspace-write`, because the MCP path hits the bug it fixes → glm.
  - C1 and C2: glm → codex.
  - C3: codex → glm.
  - C4, D1, D2, A7: coordinator paperwork.
  - A8: coordinator, after A1–A7.
- At most 2 units run at once. Each Codex unit that edits one file repeatedly runs as direct `codex exec` until the MCP server restarts with B1.
- **Not in scope:**
  - OCR for The Pyramid Principle;
  - repairing the 4 live books with no headings (a separate run, because their chunk IDs may sit under test labels);
  - the Claude Code `/goal` stop-hook loop itself;
  - reranker dilution.

## Amendments

(none)
