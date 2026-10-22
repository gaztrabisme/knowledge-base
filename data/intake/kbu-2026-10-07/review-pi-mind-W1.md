# Review: pi-mind W1 memory writer, first slice

Reader: Gary, deciding whether pi-mind's first build wave (run W1) may build the memory unit (U5) as proposed.

Under review: `~/Documents/Work/tools/pi-mind/research/W1/memory-section.md` (the "slice"). It is checked against the organized-mind design, `data/intake/kbu-2026-10-07/design-spec.md` (the "design"), and the memory survey behind it, `reports/R4-REPORT.md` ("R4"). Reviewed 2026-10-11. This is a document review. Nothing was built or run.

## Terms used below

- **Memory writer**: the one service that accepts agents' contributions (lessons, flags, feedback) and stores them. The design allows only this service to write memory.
- **Journal**: the writer's storage. Records are added and never edited in place.
- **Contribution / record**: one item an agent submits, such as a lesson. It has a **stable ID**, an identifier that never changes, and one or more **revisions**, numbered versions that are never edited once saved.
- **Request key (idempotency key)**: a value sent with each write. If the same write is sent twice, for example after a dropped connection, the writer recognises the key and returns the first result instead of saving a duplicate.
- **Receipt**: the writer's reply to a write: ID, revision, whether the record is saved and whether it is searchable yet.
- **Projection**: a Markdown note generated from the journal so a person can read it. The journal is the authority; the note is a copy.
- **MCP**: Model Context Protocol, the standard through which coding agents (Claude Code, Codex, pi) call tools on a server. **stdio** means each agent starts its own copy of the server as a child process and talks to it over standard input and output.
- **SQLite**: a database kept in one file. **WAL** (write-ahead log) is a SQLite mode that lets readers and one writer work at the same time; it keeps two side files next to the main file.
- **Selector**: the data that pins a comment to an exact place in a source text: source ID, source revision, the exact quoted words, the words just before and after them, and character offsets.

## Verdicts

| # | Question (short) | Verdict |
|---|---|---|
| 1 | Is lesson + stale flag + feedback a sound first cut, without a later schema migration? | change |
| 2 | Does the revision table leave room for passage selectors? | change |
| 3 | Is a local SQLite file on this Mac acceptable while the writer host is undecided? | keep |
| 4 | Is writer identity from client configuration, with no authentication, enough for W1? | change |
| 5 | Do the `rule` / `anti-pattern` polarity and the evidence gate conflict with the design? | change |
| 6 | Should W1 store a reviewer field? | keep |

Totals: 2 keep, 4 change, 0 block. Every "change" is a specification the coordinator can fold into the U1 (contracts) and U5 (memory) briefs; none needs a decision from you before U5 starts. The section "What the slice contradicts" below lists further problems the questions did not ask about. One of those (projection overwrite) also belongs in the U5 brief, and one (starting this phase before its entry checks) is yours to accept.

### 1. Lesson + stale flag + feedback as the first cut — change

**Verdict.** The choice of three kinds is sound. The storage shape must be fixed now so that comments, tags and links can be added later without changing tables.

**Reason.** The design gives every contribution kind the same envelope (stable ID, revision, kind, owner/project scope, origin, writer, claimed harness/model, session and run IDs, server time, assertion type, evidence IDs, review history) and a kind-specific payload. R4's proposed record has the same split: a shared envelope with `schema_version`, and the per-kind fields beside it. If W1 stores the envelope as columns and the kind payload as validated JSON tagged with a schema version, a new kind is a new JSON schema and a new tool, not a table change. If W1 gives lessons their own columns (claim, trigger, action and so on), adding comments or links later forces a migration.

Three things in the slice would still force a migration if left as they are:

1. **Targets.** A stale flag and a feedback event point at something. In W1 that can only be a memory record revision, because sources have no IDs yet (the catalog backfill has not run). Store the target as a typed reference, `{target_type, target_id, target_revision}`, with `target_type` allowing `memory_record` now and `source` later. A target column that assumes "lesson revision" has to change when flags on sources arrive.
2. **Missing envelope fields.** The slice does not mention assertion type (observation, inference or user statement), `expires_at`, `review_due_at`, `last_reviewed_at`, `last_supported_at`, or the `supersedes` / `contradicts` / `related` lists. The design requires all of them on every contribution and keeps the four dates separate. Add them now, empty where W1 has nothing to put in them; adding them later is a migration.
3. **Review history.** The design requires review history on every contribution. Keep it in the same append-only audit-event table the slice already commits with each write, with an event type field. Review events then become a new event type later, not a new table.

**Rests on.** "Memory and annotations", paragraph 2 (envelope fields, separate dates) and the contribution table; R4, "proposed logical model" (envelope with `schema_version`, per-kind table).

### 2. Room for source-anchor selectors — change

**Verdict.** The slice does not describe the revision table's columns, so the question cannot be answered from the document. Write the table into the U1 contract with the layout below; with it, selectors fit without a migration.

**Reason.** The design says detailed selectors live in structured JSON, following the W3C Web Annotation model: exact quote, prefix, suffix, offsets, and source ID and revision. R4's comment record puts them under `target.selector`. The payload JSON from question 1 holds that. Two parts must be in place from W1:

- **The typed target reference from question 1, as indexed columns.** The review queue and the reattachment step need "all comments on source X, revision Y" as a query. That should not require reading every JSON payload.
- **Reattachment is a new revision plus an event.** When a source changes, the design creates a recorded reattachment event: a unique exact match proposes a move, and an ambiguous or missing match leaves the comment detached. The revision table must therefore never update a selector in place. If W1 enforces "revisions are insert-only" at the database level (no UPDATE path on revision rows), this holds automatically.

Character offsets are never a comment's only identity (R4). The schema should not make offsets a key.

**Rests on.** "Memory and annotations", paragraphs 3 and 4 (selectors in JSON; anchors combine exact text, surrounding text and source version; reattachment creates an event); contribution table, row "Passage comment"; R4, comment record shape.

### 3. Local SQLite file on this Mac while open choice #2 is open — keep

**Verdict.** Acceptable for W1. Open choice #2 (which machine hosts the writer) lists "the Mac" as one of its two options. A file outside the repo also meets the design's rule that mutable memory history lives outside replaceable release directories.

**Conditions to put in the U5 brief.** These are build requirements, not reasons to change the plan:

- **Several processes, one file.** With stdio, each client starts its own server process, so three processes write one file. The design wants one writer validating every write. That holds only if each write's validation (key lookup, expected-revision check, scope check) runs inside the same write transaction as the insert (SQLite `BEGIN IMMEDIATE`), and the request key has a UNIQUE constraint. Otherwise two processes can both see "key not used" and both save. Turn on WAL mode and a busy timeout. Add a proving case: two processes send the same key at the same moment, and exactly one record results.
- **"Moving is a file move" needs a procedure.** In WAL mode the data sits in up to three files (`mind.sqlite`, `-wal`, `-shm`). Copying only the main file while clients run can lose recent writes. The move procedure is: stop the clients, checkpoint, copy, check record counts and receipts on the new host. Add that procedure to the slice.
- **Codex's sandbox (inference).** The design says to separately verify Codex's sandbox, network and tool permissions. Whether a Codex-launched MCP server can write `~/.pi-mind/` is not confirmed here. The three-client receipt test will show it; if it fails, that is the cause to check first.

**Rests on.** "Open choices for Huy" #2; "Repo layout and distribution" (mutable memory history outside release directories); "Memory and annotations", paragraph 6 (revision, audit event, fingerprint and receipt commit together).

### 4. Writer identity from client configuration, no authentication — change

**Verdict.** Enough for W1, on one condition: W1 records must say that the writer was configured, not authenticated, so they can never later be mistaken for authenticated ones.

**Reason.** The design's envelope field is "authenticated writer", and it says the server enforces owner/project identity and that "claimed identity in model text is not authorization". The slice meets the second rule: identity comes from the server's launch configuration, not from anything the model types. It does not meet the first: any process on the Mac can start the server, or run `mindctl`, with any configured name. On a single-owner machine where W1 has no review tools and nothing can change a record's authority, the harm is limited to a mislabelled candidate. A label limits that harm; authentication is not needed yet. Change:

- Store `writer_assurance: "configured"` (or an equivalent name) on every W1 record and receipt, and show it in `memory_read` and in the projection. A later authenticated writer records `"authenticated"`.
- `mindctl` takes identity from its configuration file, never from a command-line flag an agent can type.
- Before any review tool exists, authentication is required. The design says review tools are unavailable to ordinary agent write credentials, which presupposes credentials that tell an agent from the owner. State this in the slice as the condition for building `review_decide`.

**Rests on.** "Memory and annotations", paragraph 2 ("authenticated writer"); "Agent tools for every harness", paragraph 1 (server-side identity) and the paragraph after the tools table (review tools unavailable to agent credentials); R4 ("a model-supplied agent name is only claimed identity").

### 5. `rule` / `anti-pattern` polarity and the evidence gate — change

**Verdict.** Neither addition conflicts with the contribution model in principle. Each needs one rule written down so that it cannot drift into one.

**Polarity.** A lesson recording what to avoid fits the design's lesson payload: the claim is "X causes Y", and the recommended action is "do not do X; do Z". Keep polarity as a field the writer sets at creation. Add to the slice:

- Polarity is part of the claim. It is never changed by feedback, decay or any automatic process. Harmful feedback on a `rule` is a feedback event against that revision; it does not turn the rule into an `anti-pattern`. The design requires feedback to keep conflicting evidence beside the claim, and forbids silently choosing the newest claim. Flipping a lesson's meaning automatically would be both. (R4 describes cass's polarity checks only as conflict warnings. Whether cass also inverts harmful rules automatically is not stated in R4, so this is a guard, not a finding about cass.)
- `recommended_action` stays required for anti-patterns, so a lesson cannot be only "don't".

**Evidence gate.** The slice says a lesson "must cite at least one evidence reference", then says that without one its support is recorded as `not found` and stays unresolved. These two sentences disagree on whether a lesson with no evidence is refused or saved. The design says saved: missing evidence fields say `not found` and leave support unresolved, and R4 says missing evidence leaves the lesson a candidate. Change the slice to: "a lesson without evidence is saved as a candidate with support `not found`; it is not refused." Calling it a gate suggests refusal.

Two further changes:

- **What an evidence reference is in W1.** The design's evidence IDs are versioned, but W1 has no source IDs. Define a typed reference (`memory_record`, `file` with content hash, `commit`, `url`, `session`) and record every W1 reference as cited, not checked. A lesson citing a file path is still unverified; nothing in W1 marks support resolved.
- **Assertion type.** Add the design's required assertion type (observation, inference or user statement) to the lesson payload. It is the field that stops an agent's guess being stored like an observation.

**Rests on.** "Memory and annotations", paragraphs 2 and 5 (missing evidence is `not found`, never silently choose the newest claim) and contribution table rows "Lesson" and "Feedback/review" (retain conflicting evidence); R4 (cass curator polarity warnings; "missing evidence leaves it candidate"; harmful feedback must name failure and scope).

### 6. Reviewer field before review tools exist — keep

**Verdict.** Leave out any "designated reviewer" setting until review tools are built, as the slice proposes. One related field is required now.

**Reason.** The design's Feedback/review row requires "reviewer/check identity" on every feedback event. In W1 that is the writer identity of the agent giving feedback (with its `writer_assurance` label from question 4), plus a check name when the feedback comes from a named check. Store that. Do not store a person's name as "the reviewer"; that belongs to open choices #6 (who reviews lessons) and #7 (who may close stale flags), both still open, and to the authentication in question 4.

**Naming.** The design names Huy as reviewer and pi-mind's records name Gary. It is an inference, not confirmed by any document read here, that both names refer to you. The verdict does not depend on it: with no reviewer field in W1, nothing is stored under either name. When review tools are designed, store the reviewer as a principal ID resolved from configuration (for example `owner`), not as a written name, so the naming question does not end up in the data.

**Rests on.** Contribution table, row "Feedback/review"; "Open choices for Huy" #6 and #7.

## What the slice contradicts that the questions did not ask

1. **Projection rebuilds can silently erase hand edits.** The slice rebuilds notes from the journal and leaves out "reading back hand edits". The design says direct edits to projections cannot "disappear silently": unexpected changes are surfaced as proposed drafts. If W1 rebuilds by overwriting, an edit you make in Obsidian vanishes. Minimal fix for W1: write projections read-only; before rewriting a note, compare it with the hash recorded at its last write; if it differs, move the edited copy aside and report it in `mind_status`, without parsing it. Also check projection paths after resolving symbolic links, so a note cannot be written outside the configured folder. (Design: "Memory and annotations", paragraphs 3 and 6.) Add to the U5 brief.

2. **The slice has an update path but no update tool.** Its "Conflicts" row says an update carries the expected prior revision, and the proving case `conflicting_revision_preserves_both_claims` needs one. None of the six tools updates a record. Say which operation creates revision 2 of a lesson (for example an `expected_revision` argument on `memory_create_lesson`, or a separate `memory_revise_lesson`), and whether an agent may revise another writer's lesson. The design allows agents to create candidates. It does not say they may revise others' records. Until you decide, the safe default is that a writer may revise only its own lessons.

3. **How a record becomes "retired" is not stated.** One W1 proving case is that retired records are left out of search. Retiring is a status change. The slice says nothing in W1 can change a record's authority, and the design keeps status and authority separate, so the slice does not say who may retire a record. If `mindctl` can retire records, any agent with a shell can take a lesson out of everyone's search, which the design leaves to review. Either the test uses a fixture written directly, or retirement is an owner-only `mindctl` command, recorded as an audit event and not exposed through MCP. A retraction by the record's own writer (design: "a retraction appends a revision") is a different, allowed operation; keep the two apart.

4. **There is no way to recover a lost receipt.** The design's recovery rule is: on an unknown outcome, ask the writer for the receipt by request key, then replay with the same key; never assign a new key because a response was lost. W1 has no client retry, which is acceptable while open choice #13 is open. But in Claude Code and Codex the model writes the tool arguments, so the request key is likely chosen by the model (inference). A model that sees a timeout may call again with a new key, and that creates a duplicate the writer cannot detect. Add a receipt lookup by request key (in `memory_read` or `mind_status`), and tell agents in the tool description to look up the key before resending.

5. **Receipt and response fields are not specified.** The design requires every write to return ID, revision, provenance, save/index state and request key. Every new structured response also carries schema version, backend availability, privacy scope, structured errors and pagination or omitted counts. The receipt keeps "saved" separate from "indexed", even if W1's full-text index updates in the same transaction and both are always true. Put these fields in the U1 contract now; adding them after three clients depend on the shape is a breaking change.

6. **This phase's entry checks are not met.** The design's migration row "Shared memory and gateway" starts only when source identities are stable, the writer host and credentials are chosen, and Huy has decided context counting, retry policy and review capacity. None holds today. The slice's scope is consistent with that: it leaves out comments, review and outboxes, which are the parts that depend on those checks. It is still an early start of a gated phase, and the decision is yours. If you accept it, record W1 as a prototype ahead of the gate. The design's rollback for this phase then applies: disable faulty writes, keep the journal, append corrective revisions, never erase history.

7. **If you choose the memory-on scored run.** Lessons written on one SWE-bench task and read on a later one are unreviewed candidates. The design permits that only if they are labelled as candidates in search (#6), it does not count several agents summarising one event as independent support, and its proposed review of the first 20 tasks' contributions is still awaiting your choice (#12). The slice already says no score difference is attributed to memory from one run. Add that each memory-on task records whether memory was consulted, including an explicit "no contribution" record (design, "Agent tools for every harness", harness-acceptance paragraph).

8. **Decay must never change status.** The slice defers "confidence decay" to a later ranking signal. When it arrives, the design's rules apply: age alone does not establish falsity, and harmful feedback does not refresh support. Decay may reorder search results but never sets `contested`, `retired` or a stale flag. (R4 records that in cass a harmful mark makes a rule look recently reviewed; the design separated the dates for this reason.)

9. **Where the contract lives.** The design placed the shared integration schema in `agent-workflow/contracts/`, with copy-equality checks wherever another repository holds a copy. pi-mind's `packages/contracts` now holds the memory schema. You decided the repo on 2026-10-11; that decision is not reopened here. The point is only that one place must own the schema. Name pi-mind's contracts package as the owner, or add the copy check, so that the knowledge-base gateway and pi-mind cannot drift apart.

10. **Stale flags cannot be closed in W1.** That is consistent with open choice #7 being open. State it in the slice: W1 flags stay open, and closing one later needs a recorded outcome, as the design requires.

## What this review did not check

- No pi-mind code exists, so no claim here is tested.
- The slice gives no table definitions, so questions 1 and 2 are answered for the layout this review recommends, not for a schema seen.
- Whether Codex-launched MCP servers can write outside the workspace, and whether "Huy" and "Gary" are one person, are unconfirmed.
