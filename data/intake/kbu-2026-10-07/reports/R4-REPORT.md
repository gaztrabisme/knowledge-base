# R4 — Shared agent lessons and annotations

Owner: Huy. Run: `kbu-2026-10-07`. Research date: 2026-10-10, Asia/Ho_Chi_Minh.

**Recommendation:** preserve source material and let agents append clearly marked lessons, comments, stale flags, and links in a separate shared memory store. Let Huy approve promotion into source material or standing instructions. Use one writer and the same record identifiers from every harness. Obsidian-compatible Markdown should be the readable representation; a search index should be rebuildable from those records.

Here, **provenance** means the recorded origin of a claim: who wrote it, in which session, on what date, from which evidence and source version. **Stale** means that a record needs renewed checking; it does not mean false. A **harness** is the application that runs a coding agent and its tools. **Consolidation** means combining observations into reusable memory. **MCP** means Model Context Protocol, a client/server interface for exposing tools and resources; it does not define memory quality or storage policy. [MCP architecture][mcp]

An **API** is a programming interface; an **SDK** is a library developers use to call it. A **CLI** is a command-line interface. **Markdown** is plain text with headings and links; **JSON** and **YAML** are formats for structured data. A **token** is a piece of text processed by a language model. An **embedding** represents content as numbers for similarity search; a vector store indexes those representations. A **graph** connects entities, called nodes, through relationships, called edges. These explain the survey's storage terms; none of these mechanisms alone establishes whether a claim is true.

This is research and a proposed design, not an installed memory service. The two pointer repositories were downloaded as source archives into `R4/research`, without a Git checkout or running their code. I inspected their READMEs, implementation plans, schemas, memory paths, consolidation/curation code and access surfaces. The pi plan references a separate design document that was **not found** in its downloaded tree. No models, embeddings, package installation, remote computation, GPU access, containers, or existing services were used. No source repository was changed. Existing local inventory artifacts were reused rather than repeating transcript reads.

## Survey

The survey covers 2025–2026 research and the current primary documentation inspected on 2026-10-10. Earlier MemGPT and annotation standards are included as background. Publication dates and observation dates are distinguished in Sources. “Not found” below means not established by the inspected material, rather than a claim that a feature cannot exist. Vendor benchmark results were not reproduced and are not used to rank systems for Huy.

### pi-observational-memory — detailed examination

The snapshot is commit `78a1efcfdd46332253fb289724f05b26dfc7769e`, dated 2026-08-24. It is a pi extension, disabled by default per session. It stores three forms of derived memory: atomic observations, topic files, and a descriptive `JOURNEY.md`. Observer subprocesses distill conversation chunks; the master keeps a ledger, meaning a sequence of recorded events. Compaction renders the observation buffer without another model rewrite. A consolidator moves older observations into topic files and the master regenerates `INDEX.md`. Access is through pi events and commands plus ordinary file reads; a standalone shared-memory MCP server was **not found**. [README][pi-readme]

The implemented observation is `{timestamp, content, tokenCount}`. Its timestamp also serves as its identifier. Recorded batches carry `coversUpToId`, the last covered conversation-entry identifier. The schema explicitly omits individual `sourceEntryIds`. **Provenance limitation:** a batch boundary can establish which conversation portion was processed, but the stored observation cannot identify the exact messages that support it. This is a code-based inference, not a measured recall failure. The plan explicitly postpones exact observation-level attribution. [Ledger schema][pi-schema], [implementation plan][pi-plan]

The decisive storage behavior is in `sessionMemoryRoot` and `ensureSessionMemory`: durable memory is under `<project>/.memory/<sessionId>/`; a fork copies its parent's memory once. Two independent sessions do not share consolidator output. Short-term ledger state follows the pi conversation branch, but topic files persist when the user moves backward through `/tree`. **Inference:** returning to an earlier branch can expose durable notes written after that branch position. This matters for provenance and rollback. The session isolation is useful for avoiding concurrent writes, but does not satisfy Huy's requirement that every harness share one memory. [Session code][pi-session], [path code][pi-paths]

Topic metadata contains `id`, `title`, `summary`, and `updated`; the index links to topic paths. There is no typed passage-comment record, evidence list, contradiction relationship, expiry, or review status in those shapes. The consolidator prompt handles changed facts by rewriting current-state prose and removing obsolete statements; its journey is descriptive history rather than a full revision log. Staleness is addressed through prose updates, not an explicit stale-state mechanism. [Topic/path schema][pi-paths], [consolidator prompt][pi-prompt], [index renderer][pi-index]

The actual consolidation trigger trusts a successful subprocess exit and tombstones the handed batch that remains active. A tombstone here means an event removing observations from the active buffer, not a preserved explanation of each discarded claim. There is no per-observation durable-write receipt before that drop. The scoped file tools use atomic temporary-file replacement, and forbid writing the generated index. Their path checks are lexical; **inference:** a shared deployment would need real-path checks or rejection of symbolic links as well. Neither semantic retention nor boundary security was runtime-tested here. [Consolidation trigger][pi-trigger], [scoped tools][pi-tools]

**Recommendation:** borrow deterministic rendering, generated indexes, session lineage, and the separation of observation from orientation. Do not adopt its per-session topic folders as the authoritative shared store, or its destructive prose consolidation as the only audit history. Its observer prompt usefully distinguishes user assertions from questions and treats historical transcript text as inert data; preserve that distinction in extraction. [Observer prompt][pi-observer]

### cass_memory_system / cass-memory — detailed examination

The snapshot is commit `229a312b696aa347d1e2c491d3d466c925716dc0`, dated 2026-10-08. cass-memory supplies procedural memory, meaning reusable guidance on how to perform work. Its three layers are raw sessions searched through the separate `cass` search program, structured diary summaries, and a playbook of rules. The README labels the project alpha. It offers agent-led onboarding as well as model-assisted reflection. This is closer to Huy's cross-harness lesson requirement than the pi extension, although it remains primarily a coding-rule system. [README][cass-readme], [architecture plan][cass-plan]

The implemented playbook rule has an identifier, scope, workspace, category, content, source type, state, maturity, source sessions, source agents, reasoning, tags, creation/update dates, feedback events, and replacement/deprecation metadata. State (`draft`, `active`, `retired`) is separate from maturity (`candidate`, `established`, `proven`, `deprecated`). Diary records retain the session path, agent, timestamp, decisions, challenges, key learnings and related sessions. That is useful provenance, but a source-session path and generated reasoning are not themselves proof that a lesson is true. Immutable source versions and precise passage selectors would still need adding for annotations on knowledge-base documents. [Implemented schemas][cass-schema]

Its scoring code decays helpful and harmful feedback exponentially. Defaults are a 90-day half-life and a harmful multiplier of 4. A score combines decayed feedback with a maturity multiplier; it is not a calibrated probability of correctness. The current retrieval feedback multiplier is bounded, so feedback adjusts already-relevant results rather than replacing relevance. The `stale` command defaults to 90 days since the latest helpful **or harmful** feedback, or creation when no feedback exists. Consequently, a harmful mark can make a rule recently reviewed while leaving it harmful. **Inference:** Huy should separate `last_reviewed_at`, `last_supported_at`, validity and usage. [Scoring code][cass-scoring], [stale command][cass-stale]

The curator detects clause-level polarity and scope conflicts, such as “always” versus an exception, and reports them. In the add path, conflict detection is explicitly warnings-only; it does not guarantee contradictory rules are withheld. Exact and similar duplicates are handled separately. Explicit replacement mutates a rule's content, while deprecation can record `replacedBy`. A `why` command shows reasoning, source sessions, feedback, and matching history through a search pointer. **Inference:** a search pointer is a useful recovery aid, but its results can change as the index changes; preserve evidence identifiers and source hashes too. [Curator][cass-curate], [why command][cass-why]

Access includes the command-line interface (`cm context`, playbook operations, feedback, outcome, stale, why), files, and an HTTP MCP server. The inspected server exposes `cm_context`, `cm_feedback`, `cm_outcome`, `memory_search`, `memory_reflect`, `cm_why`, and `cm_conflicts`. It intentionally disables stdio and SSE. Stdio means connecting a local process through standard input/output; SSE means Server-Sent Events. The tool list has no dedicated passage-comment or general annotation-create tool. Reflection can write rules, and CLI playbook operations can add them; this is different from saying every MCP client already has a direct lesson-creation tool. [Server implementation][cass-server]

The plan describes global and repository playbooks and deterministic updates rather than wholesale model rewriting. The implementation has file locks, atomic saving, blocklists, and an undo command. These are useful controls, but this run did not test concurrency, recovery, or complete version restoration. Agent-led onboarding documentation explicitly notes that its manually extracted rules lack the history-validation gate. Its claim of “free” reflection should not be treated as an operational cost guarantee. [Persistence code][cass-save], [undo code][cass-undo], [onboarding limitations][cass-onboard]

The README documents session-end reflection hooks for Claude Code and Gemini CLI, and a wrapper entry point for other agents. It describes a default diary input limit of 50,000 transcript characters, sampled from the beginning, end and selected middle lines. **Inference:** automatic reflection can miss supporting context and should produce candidates with evidence references. These hooks were not installed; enabling them would also exceed this unit's transcript-read scope. [Hook and reflection documentation][cass-readme]

**Recommendation:** borrow rule scope, provenance, feedback events, deprecation, and explain-why access. Consider cass as an optional session-search adapter, not as the owner of source data. Disable unrestricted transcript ingestion for an initial trial. Add the annotation types and source-version checks below, and do not promote a rule merely because agents repeated or retrieved it.

### Wider systems and storage conventions

**Letta / MemGPT.** MemGPT introduced management of multiple memory tiers; its original paper predates this survey. The inspected Letta documentation describes persisted messages/tool state, editable memory blocks pinned into context, shared blocks, and searchable archival passages with tags. Access is through the API and SDK; agent tools manipulate memory, and Letta agents can use MCP tools. Blocks can be read-only. Provenance exists in persisted interactions, but a mandatory evidence-to-claim record and automatic contradiction/expiry policy were **not found** in the inspected block/archive guides. Linking is through shared blocks and tagged passages rather than passage-level document annotations. **Inference:** useful context-management patterns, but adopting Letta's runtime is unnecessary to share memory across Huy's existing harnesses. [MemGPT paper][memgpt], [stateful agents][letta-state], [blocks][letta-blocks], [archive][letta-archive]

**Zep / Graphiti.** The 2025 Zep paper describes a temporal knowledge graph. Current Graphiti stores episodes (ingested source content), entities, and relationship facts with validity windows. Provenance links derived facts to episodes. Bi-temporal tracking distinguishes when a fact applied from when it entered storage. Changed facts can invalidate older edges while preserving history. Linking and retrieval combine entities, relationships, semantic search and keywords. Graphiti is an open-source library with an MCP server; Zep is managed infrastructure with its own production engine. Its MCP exposes source descriptions and event time, fact search and episode provenance lookup. **Inference:** the temporal model is valuable, but automatic fact invalidation should not settle an unresolved disagreement between independent sources. [2025 paper][zep-paper], [current Graphiti][graphiti], [MCP implementation][graphiti-mcp]

**Mem0.** Its 2025 paper describes extracting, consolidating and retrieving salient conversational facts, with a graph variant for relationships. SDK access includes memory add/search/update/history; user or agent scope and supplied metadata can carry provenance. The current update prompt in the code exposes decisions to add, update, delete, or retain a memory; these model judgments need review for contested claims. Current expiration documentation distinguishes expiry from deletion: an expired record is hidden from search/list by default, retained in storage, and fetchable by identifier. Platform decay reorders results rather than proving facts stale. **Inference:** a practical retrieval layer, provided Huy supplies evidence/version fields and preserves revisions outside automatic update decisions. [Paper][mem0-paper], [SDK guide][mem0-sdk], [update prompt code][mem0-update], [expiration][mem0-expiry]

**A-MEM.** The 2025 paper applies the Zettelkasten method: separate small notes connected into a network. Notes contain content, keywords, context and tags, with links generated from related memories. The public `MemoryNote` model adds timestamps, access counts and evolution history. Access is a Python library and its retrieval/storage implementation; a first-party universal harness MCP interface was **not found** in the inspected repository. Existing contexts/tags can evolve when new memories arrive. Mandatory session/evidence provenance, explicit stale status, expiry and adjudicated contradiction handling were **not found** in the inspected note schema. **Inference:** borrow atomic notes and proposed links, but do not let semantic similarity establish truth or authorize silent edits. [Paper][amem-paper], [code][amem-code]

**Cognee.** Current documentation describes documents/conversations transformed into graph and vector memory, accessed through Python, HTTP, CLI and MCP. A typed extraction example stamps source-document content hashes onto nodes, providing provenance that is stronger than a bare URL. The changing-facts guide documents opt-in contradiction edges, opt-in recency supersession for single-value relationships, and manual closure with `valid_to`; it preserves prior facts. Closure currently depends on the supported graph backend, so backend parity must be checked. Linking includes typed nodes/edges and datasets. **Inference:** useful document-oriented building blocks; source hashes and conflict records fit Huy well, while recency alone should not decide authority. The guide was read from Cognee's official full documentation export because its individual page was inaccessible through the browser tool. [Overview][cognee], [typed provenance][cognee-types], [changing facts][cognee-conflicts], [MCP][cognee-mcp]

**LangMem.** Released in February 2025, this SDK supplies active memory-management/search tools and background extraction/consolidation. It supports semantic facts, episodic examples and procedural prompt updates, using pluggable storage or LangGraph's store. Namespaces, meaning collections identified by scoped keys, separate memory domains. Access is Python tools/API; exposing those operations through Huy's MCP service would be an adapter to build, not an automatically installed harness integration. Provenance, links, expiry and contradiction policy depend on the supplied schema, prompts and store; a mandatory universal annotation/audit model was **not found** in the inspected guides. **Inference:** good extraction primitives if Huy controls the writer and schema. [Launch][langmem-launch], [SDK][langmem], [memory tools][langmem-tools]

**Anthropic memory tool.** The tool version is named `memory_20250818`. Claude requests file operations under `/memories`; the application executes them against its own storage. It is a client-side API tool, not Anthropic-managed shared storage or an automatic MCP service. Files can hold lessons and links, but provenance, stale flags, contradiction policy and expiry are the application's responsibility; required record shapes for them were **not found** in the tool specification. **Inference:** map its handler onto the same canonical memory service rather than creating a Claude-only store. [Tool specification][anthropic-tool]

**CLAUDE.md and Claude Code auto memory.** CLAUDE.md contains standing instructions; auto memory contains agent-written learnings. Both are context rather than enforced permissions. Auto memory uses a Markdown index plus topic files; current docs load only the first 200 lines or 25KB of the index, whichever is reached first. `autoMemoryDirectory` can choose a location. Ordinary Markdown links connect topic files, but mandatory claim provenance, expiry and resolved-contradiction records were **not found** in this format. **Inference:** use these as short bootstrap instructions and an adapter inbox, not as eight separately edited authorities. [Claude Code memory][claude-memory]

**Mastra Observational Memory — newer system.** Announced on 2026-02-09, it uses an Observer to produce observations and a Reflector to condense the log. The current Reflector rewrites the entire observation log; this is memory compaction rather than an immutable claim history. Current optional retrieval mode links observation groups to the original messages and provides recall, including browsing without a vector store. Access is through Mastra's memory API and configured storage. Provenance can therefore include source-message groups; explicit passage annotations, validity expiry and adjudication states were **not found** in the inspected guide. **Inference:** useful for active-session continuity; retain independent revisions for long-lived shared lessons. [Announcement][mastra-launch], [current guide][mastra-om]

**Hindsight — newer system.** Its paper was submitted on 2025-12-14. Current documentation distinguishes world facts, agent experiences, evidence-backed observations and synthesized mental models. Retain/recall/reflect operations use temporal and entity relationships; observations retain supporting evidence and can be refined by new evidence. Access includes SDKs, REST and a per-bank MCP endpoint; a bank is an isolated memory collection. Mental models and knowledge pages are derived summaries, including Markdown projections. A universal lesson-expiry policy was **not found** in the inspected README. **Inference:** its separation of experience, evidence and belief is a strong design example; verify detailed update semantics before adopting it as the canonical writer. [Paper][hindsight-paper], [current repository][hindsight]

**OpenViking — additional current system.** The current repository organizes resources, memories and skills through `viking://` identifiers. Directory summaries and full content form three loading levels; session commits can extract memories as Markdown. Access includes a server and CLI, scoped retrieval and agent integrations. Links are addressable context paths. Mandatory passage-level evidence provenance, expiry and a review-based contradiction policy were **not found** in the inspected README. **Inference:** useful navigation and resource/memory separation, but generated summaries need visible origin and revision metadata. A first publication date was **not found**; the inspected material is dated by observation, not an invented launch date. [Repository][openviking]

**Obsidian conventions.** YAML frontmatter is metadata at the top of a Markdown note. Properties support typed values; internal links can be quoted in properties. Wikilinks such as `[[lesson-id]]`, heading links and block links connect notes; tags classify them. The property editor does not support nested properties. None of these conventions provides automatic provenance, contradiction adjudication or staleness management. **Recommendation:** use flat frontmatter, stable identifiers, quoted links and normal Markdown links alongside wikilinks. Do not insert block identifiers into immutable source files just to anchor comments. [Properties][obsidian-properties], [links][obsidian-links], [tags][obsidian-tags]

**Selection judgment (inference):** no inspected system already meets the complete combination of unchanged sources, passage annotations, auditable lessons, stale-state separation and shared access from all eight installed harnesses. Start with a small explicit record/writer contract. Reuse cass's lesson workflow, Graphiti/Cognee's temporal and provenance ideas, and Hindsight's experience-versus-belief separation. Evaluate extraction or graph engines later against that contract rather than making an engine's mutable summary the source of truth.

## Lesson-source inventory

These are existing authorized paths. Counts and byte sizes come from the earlier `inventory.json` snapshot, whose file timestamp is 2026-10-09 17:36:35 UTC (2026-10-10 00:36:35 in Huy's timezone). They are snapshot values, not current disk-usage claims. Existence was checked again during this run. Recursive inventory excludes symbolic-link entries and does not follow linked directories. Bytes are logical file sizes, not allocated storage.

| Path | What it holds | Count/size at snapshot | Format |
|---|---|---|---|
| `~/Documents/Work/tools/agent-workflow/skills` | Direct child skills' real-use evolution records; count covers only `EVOLUTION.md` files | 28 files; 424,733 bytes | Markdown |
| `~/Documents/Work/tools/agent-workflow/skills/dev/EVOLUTION.md` | Engineering lessons and historical relocation notes | 1 file; 39,837 bytes | Markdown |
| `~/Documents/Work/tools/agent-workflow/skills/evolution/EVOLUTION.md` | Lessons about the learning/review process itself | 1 file; 19,366 bytes | Markdown |
| `~/Documents/Work/tools/agent-workflow/wiki` | Decisions, work log, goal record and retired-repository list | 4 files; 10,928 bytes | Markdown and text |
| `~/Documents/Work/tools/knowledge-base/wiki` | Knowledge-base decisions, gotchas, logs, goals and technical notes | 19 files; 246,819 bytes | Markdown |
| `~/Documents/Work/products/litgraph/wiki` | Product decisions, gotchas, logs and research/goal records | 12 files; 138,322 bytes | Markdown |
| `~/.claude/CLAUDE.md` | Owner's global instructions; a symbolic link into agent-workflow | 1 target file; 9,012 bytes | Markdown |
| `~/.claude/projects` | Per-project folders, memories and session artifacts | 112 direct project folders; 8,297 recursive files; 2,859,689,990 bytes | Markdown, JSON Lines and other artifacts |
| `~/.claude/projects/-Users-GaryT-Documents-Study-Azure` | Project folder whose memory index was sampled | 5 files; 3,017 bytes | Markdown |
| `~/.claude/projects/-Users-GaryT-Documents-Study-Azure/memory/MEMORY.md` | Four links to user, project, feedback and reference memories | 1 file; 439 bytes | Markdown link index |
| `~/.claude/projects/-Users-GaryT-Documents-Work-AI-Recursive-Data-Cleaner/memory/MEMORY.md` | Project scope, implementation patterns and dated evaluation claims | 1 file; 5,757 bytes | Markdown |
| `~/.codex/sessions` | Session artifact inventory; contents were not opened | 1,258 files; 10,406,590,178 bytes | Listed filenames are JSON Lines |

Within the Claude project inventory, memory-path entries total 186 files and 324,184 bytes; this includes non-Markdown artifacts identified by location. Session filenames ending in `.jsonl` total 6,856 files and 2,616,142,321 bytes. JSON Lines means one JSON object per line. Those totals are subsets of the project total and must not be added to it.

The earlier script opened exactly two memory files. It read the first three lines of one Claude transcript, which showed two `queue-operation` records followed by a `user` record with session/message identifiers. This establishes only a small schema sample, not representative transcript content or outcomes. This run replayed the saved samples and opened no additional memory files or transcript lines; Codex sessions remained listing/counting only. No folders belonging to other research units were read.

The dev evolution sample preserves older file references and adds a dated relocation note rather than rewriting history. That is a useful local precedent for annotations. Wiki gotchas supply concrete failure lessons; wiki decisions supply scope and rejected alternatives. The two memory samples show both a compact link index and a long mixed document of state, instructions and historical measurements. **Inference:** importing these without separating observation, preference, instruction and tested lesson would carry stale project state into future tasks. Their evaluation claims were not independently verified in this unit.

**Recommended inventory use:** first import selected evolution entries and wiki gotchas as candidate lessons with file versions and exact supporting passages. Import owner instructions as read-only policy references. Preserve the originals. Treat transcript mining as a separate, explicitly scoped future job; the existing inventory does not authorize bulk transcript ingestion. Compare source versions before trusting old measurements or paths.

## Edit vs annotate

| Option | Trust and provenance | Staleness | Rollback and maintenance |
|---|---|---|---|
| Agents edit source data directly | A generated interpretation can become indistinguishable from original evidence unless every edit has retained attribution | Sources look current, but the change may conceal an unresolved contradiction | Requires complete before/after history; concurrent edits and re-ingestion complicate recovery |
| Agents write notes and labels beside sources | Original evidence stays intact; agent claims can be visibly identified and reviewed | Explicit stale flags can cite changed source versions without asserting falsity | Retract an annotation revision and rebuild indexes; source bytes remain available |
| A mix with review | Agents annotate immediately and propose a concrete source patch; Huy decides what becomes authoritative | Review can retire a claim, close a validity interval, or update a source with an explanation | Keep proposal, approval, source versions and supersession links; more workflow, clearer authority |

**Recommend the mix, with annotation-only agent permissions by default.** Agents should be able to record what they learned immediately. That write is permission to contribute evidence or an inference, not permission to rewrite a book, imported paper, reference document, owner decision, or skill's standing rules. A review queue should show the exact proposed change, its evidence, affected source version, conflicting claims and rollback revision. Approval should apply to that concrete patch only.

For agent-owned scratch summaries, rewriting is reasonable when they are explicitly labeled generated, replaceable, and derived from preserved records. For actual source corrections or promotion into instructions, append a reviewed decision and retain the prior version. A new timestamp must not automatically outrank an older authoritative statement. A later scoped exception may coexist with a general lesson; an unresolved contradiction should show both claims.

This unit applies the run's stricter read-only rules: it proposes policy and writes only research artifacts in R4. It performs no source edits or promotions. The future review workflow is a recommendation, not an approval request in this run.

## Annotation model

The following is a proposed logical model, not an existing product schema. Use one immutable revision per record and stable identifiers independent of filenames. A content hash is a digest of exact source bytes used to detect a version change. Server-generated provenance should identify the actual authenticated writer; a model-supplied agent name is only claimed identity.

Every record shares this envelope. Angle-bracket values indicate schema placeholders, not measured examples:

```json
{
  "schema_version": 1,
  "id": "<stable-record-id>",
  "revision": 1,
  "kind": "lesson | passage_comment | staleness_flag | tag_link",
  "origin": "agent_generated",
  "scope": {"owner": "Huy", "project_id": "<project-or-global>"},
  "provenance": {
    "agent": "<harness-and-agent>", "model": null,
    "session_id": "<actual-session-id-or-not-found>",
    "run_id": "<run-id>", "created_at": "<UTC-time>",
    "evidence_ids": ["<versioned-evidence-id>"],
    "assertion_type": "observation | inference | user_statement"
  },
  "status": "candidate",
  "last_reviewed_at": null,
  "review_due_at": "<UTC-time-or-null>",
  "expires_at": null,
  "supersedes": [], "contradicts": [], "related": []
}
```

`candidate` means recorded but unvalidated; `verified` means a named review or check supports the claim in its recorded scope; `contested` means an unresolved conflicting claim exists; `superseded` means a replacement is identified; `retired` means excluded from normal guidance. Review history must preserve who changed the status and why. Source authority is separate from lesson status. A verified lesson can still need review after a dependency changes.

Expiry ends normal applicability at a known time. A review due date asks for checking without deleting evidence. A stale flag has its own lifecycle and may apply to only one passage or claim. Null expiry means no known expiry, not eternal truth. Reads should show expiry, stale flags and unresolved contradictions; searches may omit retired/expired guidance by default but must offer an explicit history view.

| Kind | Additional record shape | Interpretation and lifecycle |
|---|---|---|
| Lesson | `claim`, `context`, `trigger`, `recommended_action`, `limits`, `observed_outcome`, `evidence_ids` | One reusable lesson, with the circumstances in which it worked. Store failed attempts and user corrections as evidence; missing evidence leaves it candidate. |
| Comment on a passage | `body`, `target: {source_id, source_version, source_uri, selector: {exact, prefix, suffix, start, end}}`, `relation` | A comment attached to a specific source version. `relation` can be question, clarification, disagreement or supporting example. Character offsets help locate text but are never its sole identity. |
| Staleness flag | `target`, `reason_code`, `detected_at`, `old_version`, `observed_version`, `evidence_ids`, `resolution`, `resolved_at` | Reasons include changed source, broken evidence, expired dependency, due review or disputed claim. A changed hash signals possible staleness, not a proven contradiction. Closure records the recheck outcome. |
| Tag/link | `subject_id`, `tag`, `predicate`, `object_id`, `rationale`, `evidence_ids` | A tag classifies; a link asserts a typed relationship such as related-to, supports, contradicts or supersedes. A semantic-similarity suggestion starts candidate. Expiry can be inherited from a temporary relationship's applicability. |

For example, a lesson from this research can say that the inspected pi implementation scopes durable notes by session, with its commit and `session.ts` evidence. A comment can flag the README's consolidation description for comparison with the trigger implementation. A stale flag can identify a future changed source hash. A tag/link can connect that lesson to “shared-memory” and to the cass survey. These are distinct records; none alters the upstream repository or pretends a future stale event already happened.

Passage anchoring should use exact text plus surrounding text and a source version, inspired by the Web Annotation model's quote and position selectors. Reattachment after a source update should be a separate recorded operation: a unique exact match may relocate the comment; ambiguous or missing matches leave it detached and visibly stale for review. Do not silently attach it to a merely similar paragraph. [Web Annotation model][annotation-standard]

For storage, use one Markdown note per revision with flat YAML frontmatter: `id`, `revision`, `kind`, `origin`, `agent`, `session_id`, `created_at`, `status`, `source_id`, `source_version`, `evidence_ids`, `tags`, `related`, `review_due_at`, `expires_at`. Put detailed target selectors and structured payload in a clearly labeled JSON block in the body. This maps the logical record above into readable notes without relying on nested Obsidian properties. Use separate records for comments and flags rather than adding fields to original source frontmatter. [Obsidian property constraints][obsidian-properties]

**Visible separation:** keep the memory namespace distinct from the source namespace. Every note and search result should begin “Agent-generated lesson” or “Agent annotation,” name its writer/date/status, and link to the original evidence. A source view should show annotations in a side panel or separate section. Generated indexes and summaries must link back to record revisions and state that they are derived. Huy can draft an Obsidian note into a separate inbox; the same writer validates it and records his authorship before making it searchable.

**Write and rollback contract:** one service validates all writes, assigns identifiers/dates, checks scope and source hashes, prevents duplicate submissions with an idempotency key, and appends revisions plus an audit event. Idempotency means a retried request does not create duplicate records. Concurrency uses an expected prior revision; conflicting updates return both versions for reconciliation. A record and its audit receipt must commit together. Indexing can follow afterward, but the receipt distinguishes saved from searchable. Retraction creates a new revision; rollback never erases old evidence. File/API path checks must enforce real boundaries, including symbolic links. These are proposed requirements, not tested implementation claims.

Avoid false reinforcement: two agents summarizing the same event count as one evidence origin, not two independent validations. Reading a lesson is usage, not helpful feedback. Positive feedback must name the outcome; harmful feedback must name the failure and scope. Contradictions form a review queue, and engine-generated confidence remains a model judgment rather than a measured correctness probability.

## Access from every harness

**Proposed shared interface:** expose `memory.search`, `memory.read`, `memory.create_lesson`, `memory.comment`, `memory.flag_stale`, `memory.link`, `memory.feedback`, and `memory.propose_source_change` through one MCP endpoint. Also provide a small `memoryctl` command-line client with the same operations and JSON responses. These names are proposed, not tools currently installed here. Every write returns record identifier, revision, provenance, save state and index state; every read returns source and annotation separately.

A shared skill should explain the same procedure: search relevant lessons at task start; read their evidence and scope before relying on them; record a candidate lesson after a concrete success, failure or correction; report evidence-backed feedback; propose source changes only through review. Hooks, meaning actions run at harness lifecycle events, may remind or submit a draft, but must not silently certify lessons. All adapters point to one owner/project namespace. A local read cache is disposable; an offline outbox contains unsent drafts, not a second authoritative memory.

The local `agent-workflow/AGENTS.md` gives the following skill routes. These are local repository instructions, not a claim that every upstream release discovers identical paths. Existing links should be reused; no new skill links or harness settings were written in this run. Installed versions, credentials and live MCP availability were **not found within the authorized inventory**, so the table is an integration plan rather than an end-to-end compatibility test.

| Harness | Local skill route stated in AGENTS.md | Shared reads and writes | Special handling / evidence |
|---|---|---|---|
| Claude Code | `~/.claude/skills` | Connect the shared MCP server; use its read and write tools. Put a short bootstrap in owner-controlled CLAUDE.md. | Keep native auto memory as an adapter inbox or read projection, not an independent authority. `autoMemoryDirectory` exists but pointing it at the canonical records does not supply the writer's validation. [Memory docs][claude-memory], [MCP setup][claude-mcp] |
| Codex | `~/.codex/skills` | Connect through Codex MCP configuration and guide use through AGENTS.md; same tools and receipts. | Sandbox permission to write a local folder and permission to call a remote tool are separate deployment checks. Use `memoryctl` when the connector is unavailable. [Official MCP documentation][codex-mcp], [AGENTS.md][codex-agents] |
| Gemini CLI | `~/.gemini/skills` | Configure the shared server under `mcpServers`; read/write through its tools, with a short GEMINI.md bootstrap. | Current upstream memory uses direct edits to Markdown files. Use native memory as an adapter inbox or read projection; send durable lessons through the shared writer. [MCP guide][gemini-mcp], [memory files][gemini-memory] |
| Antigravity | `~/.gemini/config/skills` | Configure a custom MCP server and use the same record operations. A file/CLI client can be a fallback where shell access exists. | Current docs put global MCP config at `~/.gemini/config/mcp_config.json`; remote connections use `serverUrl`, not Gemini CLI's assumed schema. IDE and CLI settings must be checked separately. [MCP docs][antigravity-mcp] |
| pi | `~/.agents/skills` | Current upstream supports MCP via `mcp.json`; alternatively register the server with `pi.registerMcpServer` or register tools wrapping `memoryctl`. | Extensions can inject startup context and collect lesson drafts. Older installed builds may need the extension/CLI fallback. Keep pi-observational-memory's session ledger distinct from shared lessons. [Extension API][pi-extensions], [CLI/config documentation][pi-cli] |
| omp | `~/.claude/skills` | Configure the same endpoint through OMP's MCP support; its documented native user file is `~/.omp/agent/mcp.json`. CLI fallback uses the same writer. | OMP can discover other tools' MCP configs; named profiles isolate native settings. Check that the winning config connects once to the intended namespace. “omp” is interpreted as oh-my-pi for this plan; installed binary identity was not inspected. [OMP configuration][omp-mcp] |
| opencode | `~/.claude/skills` | Configure a local or remote server under `mcp` in OpenCode config; tools provide identical reads/writes. Use AGENTS.md for the bootstrap. | Do not copy Gemini's `mcpServers` shape into OpenCode. Enable required tools in the chosen agent configuration. [MCP docs][opencode-mcp], [rules][opencode-rules] |
| grok | `~/.claude/skills` | For superagent-ai/grok-cli, its README documents MCP via `/mcps` or project settings. Otherwise use the shared skill plus `memoryctl` from the shell. | Exact installed implementation is **not found**. That upstream now documents `.agents/skills`, unlike the local shared-skill mapping; retain the local route until an installation-specific discovery check establishes a change. Do not assume xAI's API alone provides the CLI's MCP behavior. [Candidate CLI repository][grok-cli] |

The Anthropic API memory tool is another adapter: map `/memories` operations into the same writer or a controlled inbox, preserving the structured record and authenticated provenance. It does not require giving Claude unrestricted source-edit access. [Client-side tool][anthropic-tool]

**Proposed rollout and acceptance:** begin with selected evolution/wiki records, a CPU-only writer, Markdown records and keyword lookup. A future extraction experiment can run on the authorized workstation under its own unit directory; no such experiment ran here. Add graph or embedding retrieval only when keyword retrieval misses useful evidence. Test each of the eight harnesses by writing a uniquely identified candidate, then reading it from every other harness. Include duplicate retry, simultaneous revision, source-hash change, detached comment, contradictory lesson, expiry, and writer outage cases. Inspect evidence and receipts as well as tool connection status. This is the concrete acceptance work still required before claiming shared memory is operational.

## Output sample

Real output read from `inventory-output.txt`, reproduced without rounding:

```text
/Users/GaryT/Documents/Work/tools/agent-workflow/wiki | files=4 | bytes=10928
/Users/GaryT/Documents/Work/tools/knowledge-base/wiki | files=19 | bytes=246819
/Users/GaryT/Documents/Work/products/litgraph/wiki | files=12 | bytes=138322
/Users/GaryT/Documents/Work/tools/agent-workflow/skills | EVOLUTION.md files=28 | bytes=424733
/Users/GaryT/.claude/projects | files=8297 | bytes=2859689990
/Users/GaryT/.codex/sessions | files=1258 | bytes=10406590178
read_limits={"claude_memory_files_opened": 2, "claude_transcript_lines_read": 3, "codex_session_contents_opened": 0}
```

Real archive metadata and hashes produced in this run:

```text
pi-observational-memory commit_date=2026-08-24T23:43:17Z
pi-observational-memory sha=78a1efcfdd46332253fb289724f05b26dfc7769e
cass_memory_system commit_date=2026-10-08T07:15:47Z
cass_memory_system sha=229a312b696aa347d1e2c491d3d466c925716dc0
research/pi-observational-memory/src/memory/session.ts 765ce5f2bda05e2227bfb5d6a6ddeae4d2ee59d360f5e174c8e37f19e53255f5
research/cass_memory_system/src/types.ts c36bdfd807a31810cf7e6f32aeef68a589d324068eb71d5efe1d8083381ba3aa
```

The metadata is saved in `research/*-snapshot.json`; the hashes describe the inspected bytes. They do not certify the code's correctness. Local sample text remains in the reused `inventory.json`.

Local acceptance output produced after the citation checks, saved in `verification-output.txt`:

```text
12 / 12 inventory paths exist
VERDICT: PASS
```

This checks the report's required structure, minimum length, URL count, output sample and inventory-path existence. Live cross-harness memory behavior remains proposed rollout work.

## Sources

All external sources below were accessed on **2026-10-10**. For undated living documentation, publication/update date is **not found** unless stated. A pointer-code “snapshot date” is the repository snapshot commit date, not the individual file's last-change date. Paper dates are first submissions. The local inventory date is recorded above. No secondary-source benchmark claims are used.

| Source | Source date / role |
|---|---|
| [pi-observational-memory README][pi-readme] | Snapshot 2026-08-24; pointer system overview |
| [pi implementation plan][pi-plan] | Snapshot 2026-08-24; design/data-model intent |
| [pi ledger schema][pi-schema] | Snapshot 2026-08-24; implemented observation fields |
| [pi session lineage][pi-session] and [paths][pi-paths] | Snapshot 2026-08-24; isolation, metadata and filesystem behavior |
| [pi consolidator prompt][pi-prompt] and [observer prompt][pi-observer] | Snapshot 2026-08-24; extraction/update policy |
| [pi trigger][pi-trigger], [tools][pi-tools], [index renderer][pi-index] | Snapshot 2026-08-24; drop, write and linking behavior |
| [cass-memory README][cass-readme] and [plan][cass-plan] | Snapshot 2026-10-08; architecture and lifecycle intent |
| [cass implemented schemas][cass-schema] | Snapshot 2026-10-08; provenance, state, diary and rule shapes |
| [cass scoring][cass-scoring] and [stale command][cass-stale] | Snapshot 2026-10-08; exact implemented aging behavior |
| [cass curator][cass-curate] and [why][cass-why] | Snapshot 2026-10-08; conflict reporting and evidence access |
| [cass MCP server][cass-server] | Snapshot 2026-10-08; actual tools and transport |
| [cass persistence][cass-save], [undo][cass-undo], [onboarding][cass-onboard] | Snapshot 2026-10-08; controls and onboarding limitation |
| [MemGPT paper][memgpt] | 2023-10-12; revised 2024-02-12; historical background |
| [Letta stateful agents][letta-state], [memory blocks][letta-blocks], [archival memory][letta-archive] | Publication date not found; current pages label this the V1 SDK |
| [Zep paper][zep-paper] | 2025-01-20 |
| [Graphiti repository][graphiti] and [MCP code][graphiti-mcp] | Publication date not found; current implementation/documentation |
| [Mem0 paper][mem0-paper] | 2025-04-28 |
| [Mem0 SDK reference][mem0-sdk], [update prompt code][mem0-update], [expiration][mem0-expiry] | Publication date not found; current operation semantics |
| [A-MEM paper][amem-paper] | 2025-02-17; revised 2025-10-08 |
| [A-MEM note implementation][amem-code] | Publication date not found; current public code |
| [Cognee overview][cognee], [typed extraction][cognee-types], [changing facts][cognee-conflicts], [MCP][cognee-mcp] | Publication date not found; changing-facts text read from [official full export][cognee-full] |
| [LangMem launch][langmem-launch] | 2025-02-18 |
| [LangMem SDK][langmem] and [memory tools][langmem-tools] | Publication date not found; current SDK guides |
| [Anthropic memory tool][anthropic-tool] | Page date not found; version identifier `memory_20250818` is not treated as a publication date |
| [Claude Code memory][claude-memory] and [MCP][claude-mcp] | Publication date not found; current harness guides |
| [Mastra announcement][mastra-launch] | 2026-02-09 |
| [Mastra observational memory guide][mastra-om] | Publication date not found; current guide including retrieval mode |
| [Hindsight paper][hindsight-paper] | 2025-12-14 |
| [Hindsight repository][hindsight] | Publication date not found; current memory/access model |
| [OpenViking repository][openviking] | First publication date not found; current additional-system survey |
| [Obsidian properties][obsidian-properties], [internal links][obsidian-links], [tags][obsidian-tags] | Publication date not found; official help-source files |
| [Web Annotation model][annotation-standard] | Recommendation date 2017-02-23; selector design background |
| [MCP architecture][mcp] | Documentation protocol version 2026-07-28; page publication date not found |
| [Codex MCP][codex-mcp] and [AGENTS.md][codex-agents] | Publication date not found; official OpenAI documentation |
| [Gemini CLI MCP][gemini-mcp], [memory files][gemini-memory], [Antigravity MCP][antigravity-mcp] | Publication date not found; official Google harness documentation |
| [pi extensions][pi-extensions] and [CLI][pi-cli] | Publication date not found; current upstream API/config documentation |
| [OMP MCP configuration][omp-mcp] | Publication date not found; current upstream guide |
| [OpenCode MCP][opencode-mcp] and [rules][opencode-rules] | Publication date not found; current upstream guide |
| [grok-cli README][grok-cli] | Publication date not found; candidate implementation, local identity unverified |

Local evidence: `inventory.py`, `inventory.json`, and `inventory-output.txt` in R4; authorized evolution/wiki excerpts inside that inventory; and `~/Documents/Work/tools/agent-workflow/AGENTS.md` read directly on 2026-10-10 for the harness skill routing. No external URL is available for these private local files.

[pi-readme]: https://github.com/amosblomqvist/pi-observational-memory/blob/78a1efcfdd46332253fb289724f05b26dfc7769e/README.md
[pi-plan]: https://github.com/amosblomqvist/pi-observational-memory/blob/78a1efcfdd46332253fb289724f05b26dfc7769e/PLAN.md
[pi-schema]: https://github.com/amosblomqvist/pi-observational-memory/blob/78a1efcfdd46332253fb289724f05b26dfc7769e/src/ledger/types.ts
[pi-session]: https://github.com/amosblomqvist/pi-observational-memory/blob/78a1efcfdd46332253fb289724f05b26dfc7769e/src/memory/session.ts
[pi-paths]: https://github.com/amosblomqvist/pi-observational-memory/blob/78a1efcfdd46332253fb289724f05b26dfc7769e/src/memory/paths.ts
[pi-prompt]: https://github.com/amosblomqvist/pi-observational-memory/blob/78a1efcfdd46332253fb289724f05b26dfc7769e/agent/consolidator/prompt.ts
[pi-observer]: https://github.com/amosblomqvist/pi-observational-memory/blob/78a1efcfdd46332253fb289724f05b26dfc7769e/agent/observer/prompt.ts
[pi-trigger]: https://github.com/amosblomqvist/pi-observational-memory/blob/78a1efcfdd46332253fb289724f05b26dfc7769e/src/hooks/consolidator-trigger.ts
[pi-tools]: https://github.com/amosblomqvist/pi-observational-memory/blob/78a1efcfdd46332253fb289724f05b26dfc7769e/agent/consolidator/tools.ts
[pi-index]: https://github.com/amosblomqvist/pi-observational-memory/blob/78a1efcfdd46332253fb289724f05b26dfc7769e/src/memory/index-render.ts
[cass-readme]: https://github.com/Dicklesworthstone/cass_memory_system/blob/229a312b696aa347d1e2c491d3d466c925716dc0/README.md
[cass-plan]: https://github.com/Dicklesworthstone/cass_memory_system/blob/229a312b696aa347d1e2c491d3d466c925716dc0/docs/planning/PLAN_FOR_CASS_MEMORY_SYSTEM.md
[cass-schema]: https://github.com/Dicklesworthstone/cass_memory_system/blob/229a312b696aa347d1e2c491d3d466c925716dc0/src/types.ts
[cass-scoring]: https://github.com/Dicklesworthstone/cass_memory_system/blob/229a312b696aa347d1e2c491d3d466c925716dc0/src/scoring.ts
[cass-stale]: https://github.com/Dicklesworthstone/cass_memory_system/blob/229a312b696aa347d1e2c491d3d466c925716dc0/src/commands/stale.ts
[cass-curate]: https://github.com/Dicklesworthstone/cass_memory_system/blob/229a312b696aa347d1e2c491d3d466c925716dc0/src/curate.ts
[cass-why]: https://github.com/Dicklesworthstone/cass_memory_system/blob/229a312b696aa347d1e2c491d3d466c925716dc0/src/commands/why.ts
[cass-server]: https://github.com/Dicklesworthstone/cass_memory_system/blob/229a312b696aa347d1e2c491d3d466c925716dc0/src/commands/serve.ts
[cass-save]: https://github.com/Dicklesworthstone/cass_memory_system/blob/229a312b696aa347d1e2c491d3d466c925716dc0/src/playbook.ts
[cass-undo]: https://github.com/Dicklesworthstone/cass_memory_system/blob/229a312b696aa347d1e2c491d3d466c925716dc0/src/commands/undo.ts
[cass-onboard]: https://github.com/Dicklesworthstone/cass_memory_system/blob/229a312b696aa347d1e2c491d3d466c925716dc0/docs/AGENT_NATIVE_ONBOARDING.md
[memgpt]: https://arxiv.org/abs/2310.08560
[letta-state]: https://docs.letta.com/v1-sdk/concepts/stateful-agents
[letta-blocks]: https://docs.letta.com/v1-sdk/memory/memory-blocks
[letta-archive]: https://docs.letta.com/v1-sdk/memory/archival-memory
[zep-paper]: https://arxiv.org/abs/2501.13956
[graphiti]: https://github.com/getzep/graphiti
[graphiti-mcp]: https://github.com/getzep/graphiti/blob/main/mcp_server/src/graphiti_mcp_server.py
[mem0-paper]: https://arxiv.org/abs/2504.19413
[mem0-sdk]: https://github.com/mem0ai/mem0/blob/main/skills/mem0/references/sdk-guide.md
[mem0-update]: https://github.com/mem0ai/mem0/blob/main/mem0/configs/prompts.py
[mem0-expiry]: https://docs.mem0.ai/platform/features/memory-expiration
[amem-paper]: https://arxiv.org/abs/2502.12110
[amem-code]: https://github.com/agiresearch/A-mem/blob/main/agentic_memory/memory_system.py
[cognee]: https://docs.cognee.ai/
[cognee-types]: https://docs.cognee.ai/examples/typed-extraction-pipeline
[cognee-conflicts]: https://docs.cognee.ai/guides/conflicting-and-outdated-memories
[cognee-full]: https://docs.cognee.ai/llms-full.txt
[cognee-mcp]: https://docs.cognee.ai/cognee-mcp/mcp-overview
[langmem-launch]: https://www.langchain.com/blog/langmem-sdk-launch
[langmem]: https://langchain-ai.github.io/langmem/
[langmem-tools]: https://langchain-ai.github.io/langmem/guides/memory_tools/
[anthropic-tool]: https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool
[claude-memory]: https://code.claude.com/docs/en/memory
[claude-mcp]: https://code.claude.com/docs/en/mcp
[mastra-launch]: https://mastra.ai/blog/observational-memory
[mastra-om]: https://mastra.ai/docs/memory/observational-memory
[hindsight-paper]: https://arxiv.org/abs/2512.12818
[hindsight]: https://github.com/vectorize-io/hindsight
[openviking]: https://github.com/volcengine/OpenViking
[obsidian-properties]: https://raw.githubusercontent.com/obsidianmd/obsidian-help/master/en/Editing%20and%20formatting/Properties.md
[obsidian-links]: https://raw.githubusercontent.com/obsidianmd/obsidian-help/master/en/Linking%20notes%20and%20files/Internal%20links.md
[obsidian-tags]: https://raw.githubusercontent.com/obsidianmd/obsidian-help/master/en/Editing%20and%20formatting/Tags.md
[annotation-standard]: https://www.w3.org/TR/annotation-model/
[mcp]: https://modelcontextprotocol.io/docs/2026-07-28/learn/architecture
[codex-mcp]: https://learn.chatgpt.com/docs/extend/mcp?surface=cli
[codex-agents]: https://learn.chatgpt.com/docs/agent-configuration/agents-md
[gemini-mcp]: https://google-gemini.github.io/gemini-cli/docs/tools/mcp-server.html
[gemini-memory]: https://github.com/google-gemini/gemini-cli/blob/main/docs/tools/memory.md
[antigravity-mcp]: https://antigravity.google/docs/mcp
[pi-extensions]: https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/extensions.md
[pi-cli]: https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/cli.md
[omp-mcp]: https://github.com/can1357/oh-my-pi/blob/main/docs/mcp-config.md
[opencode-mcp]: https://opencode.ai/docs/mcp-servers/
[opencode-rules]: https://opencode.ai/docs/rules/
[grok-cli]: https://github.com/superagent-ai/grok-cli
