# P1 contract approval — Gary, 2026-10-14

**Decision requested:** approve the v1 shapes in `contracts/v1/` and the explicit differences below. Status: **pending**; the mechanical gate does not approve contracts or claim installed product features. Gary's approved repo/host choices apply: pi-mind owns the harness and shared contract/interface; KB and archive retain their repos; the Mac owns infrastructure, bppc only the sandboxed LLM engine. This KB copy is a review pack for transfer to pi-mind, with byte-identical W1 imports.

| Contract | What it fixes |
|---|---|
| `source-identity` | Logical ID, immutable revision/hash, kind, aliases, privacy, selected scope, original/translation/derived labels; unknown dates have a reason. |
| `locator` | Explicit Markdown lines, physical PDF page/rectangle, EPUB resource/offset, lesson cue/time, commit/file/lines, or preserved legacy chunk with unavailable page mapping. |
| `evidence-read`, `source-evidence-reference`, `contribution-evidence-reference` | Source revision, locator, content hash, selected snapshot versus producing revision, exact/fuzzy/failed/unchecked tier; annotations remain separate. |
| `catalog-entry` | Ordered membership and separate archive/parse/index/extraction states and known/unknown counts; omissions remain visible. |
| `memory-record`, `lesson-record`, `stale-flag-record`, `feedback-record` | Exact pi-mind W1 envelopes; immutable ID/integer revision, provenance, scope, assertion type, status, expiry/support dates. |
| `annotation-record`, `shared-memory-record` | Proposed comment/tag/link/patch/review and closable-stale extensions; source patches remain unapplied proposals. |
| `memory-write-receipt`, `memory-write-error`, `memory-receipt-lookup`, `memory-audit-event`, `memory-provenance` | Exact W1 receipt/audit fields: `request_key`, provenance, independent `saved`/`indexed`, error and availability; receipt-first recovery. |
| `target-reference`, `evidence-reference`, `comment-selector`, `lesson-payload`, `stale-flag-payload`, `feedback-payload`, `reviewer-or-check`, `lesson-revision-request` | Exact W1 value/payload shapes, including quoted selectors and expected prior revision. |
| `read-metadata` | One pinned read, snapshots, sources, privacy, omissions, cursor, errors and optional experiment budget. |
| `request.*` / `response.*` (32 pairs; `tools-v1.json`) | Eight legacy KB tools; legacy_read/read_metadata/mind_status; source/figure/coverage/graph reads; memory reads/writes; review and archive jobs. Original Python arguments/defaults and legacy payload types stay intact; `_meta.mind` is separate. |
| `tested-release` | P7 component/file/model/data pins, routing, tested machine matrix, explicit pending gates and rollback; replaceable data excludes journal/outbox. |

**Differences requiring explicit agreement** (full field-level record: `disagreements.json`):

1. Design placement in agent-workflow is superseded by Gary's pi-mind repo decision. P1 stages a copy here; canonical ownership and copy checks move to pi-mind.
2. W1 is a configured-writer prototype; authenticated writers and owner-only review are future service gates. Request `context` is server-bound adapter context, never authorization from model text.
3. W1 stores only lessons/open flags/feedback and unchecked evidence; proposed annotation kinds, source-span evidence, separate authority and stale closure have new schemas. Existing W1 shapes are unchanged.
4. W1 rejects source targets in its service although its target schema permits them. Source annotations wait for P2 identities. Verified support/promotion needs recorded review beyond W1's `support: not found`.
5. `memory_search` adds history/cursor alongside W1 statuses/limit/offset; cursor and offset cannot coexist. `memory_read` requires an ID or receipt key. `mind_status` adds component selection. Gateway read responses add metadata; W1's current response envelope needs an explicit adapter.
6. C101's illustrative metadata uses `omitted_source_spans`, `graph_snapshot: unavailable` and Markdown `start/end`; drafts use pi-mind's `omitted_count`, nullable optional snapshots and explicit `start_line/end_line`. Legacy opaque payload fields are preserved; per-hit semantics need gateway compatibility tests.

`bash scripts/fp/check-baseline.sh` checks hashes, live identity, schema references and positive/negative cases. It cannot prove authentication, source reattachment, atomic recovery or eight-harness compatibility. Those service checks belong to later phases. The 6,000-token cap applies only to the answer-benefit experiment. The original v10 index-build checkpoint provenance is unavailable; the exact release bytes and current offline control checkpoints are pinned separately.
