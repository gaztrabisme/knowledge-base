# P2: Catalog and locator backfill

Status: READY FOR COORDINATOR ACCEPTANCE. Both connected checks PASS. Branch: `unit/fp-P2`. Run: FP, design phase 2. Coordinator commits and accepts the staged data.

## Result and scope

A fixed registry, v1 catalog, complete frozen chunk map, completeness ledger and local evidence reader cover physical `developer_knowledge_v10` and the same server's live `philosophy` collection. No ID was changed and no live redirect is needed. Missing and drifted source evidence remains readable from exact frozen payloads. The unpromoted `philosophy_b` candidate is excluded.

| Collection | Sources / editions | Child points | Parents | Child mapped | Child drifted | Child locator not found | Parent mapped | Parent drifted |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| developer_knowledge_v10 | 328 | 330,778 | 84,761 | 329,618 | 697 | 463 | 84,618 | 143 |
| philosophy | 10 | 8,432 | 1,336 | 8,432 | 0 | 0 | 1,336 | 0 |

The 143 distinct drifted PostgreSQL parents affect 1,160 child-point parent payloads, exactly P1's count. The current source chunks contain 518 children excluded from frozen v10; these are accounted for, not inserted. Every point has one child-map row; all 86,097 parents are referenced by points. The bulk map has 425,307 rows. Of these, 375,258 have verified Markdown line witnesses; the remainder preserve v1 legacy chunk locators. No physical page is inferred from printed numerals or chunk indices.

## Grounding and decisions

- Pattern: intrinsic-artifact gate. The approved main-checkout design sections and product brief, P1 report/baseline/contracts/disagreements, `CLAUDE.md`, existing catalog/checker and chunk/ingest/index/book/server code supply project-specific grounding. No search model, embedding model or general literature query was loaded. The user-designated durable record is this report; wiki edits are excluded.
- The requested main checkout `Library/` contains four runtime files and no book assets. This was checked directly and a path clarification was offered. Existing read-only `data/markdown/` and `data/chunks/` supply normalized location witnesses. Original asset, verified edition binding and physical PDF/EPUB mapping remain **not found**, with reasons. No outside book location was silently adopted.
- Fixed logical IDs are `book:<existing-slug>` and `philosophy:<work.language>`. Existing slugs, payload book titles, configured names and philosophy work aliases are recorded. Exact aliases are case-insensitive; ambiguous titles/work names report alternatives instead of choosing an edition or language.
- A `source_hash` names the exact small `revisions/*.json` frozen-source manifest. That manifest binds the ordered frozen payload inventory and the separately observed source-file hashes. `source_revision` is `sha256:<source_hash>` and every bulk map row explicitly carries it. This is an immutable revision of indexed derived text, not a claimed original edition. Historical publication/revision/acquisition dates remain null with reason `not found`; v1 `acquired_at` records acquisition of this frozen snapshot.
- Source witness files may differ from the indexed generation. The reader never substitutes their text for frozen text. Its `verification: exact` certifies returned frozen UTF-8 text identity; original-edition quotation checks remain unknown. Source drift and locator failure appear separately in metadata.
- Catalog ordered membership lists frozen indexed parents in numeric legacy order. Archive and index counts use child units. Archive `completed` means these selected frozen payloads were preserved; it does not certify an original book archive. Historical parse and extraction receipts/counts are unknown and pending. `inventory_complete` concerns the selected frozen parent inventory. `truncation: false` records that P2 copied evidence without truncation; historical source truncation extent remains explicitly not found.
- All legacy child and parent IDs survive. P1's M1c correspondence records remain separate; no candidate-source redirect is activated. Nonempty redirect fixtures exercise the reader without inventing live identity changes.

## Artifacts and storage

Small git records: [registry](../../../data/catalog-fp/registry.json), per-source `catalog/`, `revisions/`, [ledger](../../../data/catalog-fp/ledger.json), [storage manifest](../../../data/catalog-fp/storage.json), `source-manifests.json`, `redirects.json`, supplementary schemas and [usage](../../../data/catalog-fp/USAGE.md).

The gitignored staged directory is `/Users/GaryT/Documents/Work/tools/knowledge-base-wt/P2/data/fp/`. The coordinator moves its `catalog.sqlite`, `gate/` verified controls and `frozen-manifest.json` to `/Users/GaryT/Documents/Work/tools/knowledge-base/data/fp/`, which outlives this worktree. No write to that permanent directory was attempted.

The database is **1,755,533,312 bytes**, SHA-256 **`128bebd4731169b35fd6974e2576cf99e66a345ff36f26961120b650dfd07d88`**. Table counts: `points` 339,210; `chunks` 425,307; `source_manifests` 338. Exact payloads and parent text use standard zlib compression. Git stores the size, SHA-256 and row counts. The large database and controls are confirmed ignored by git; small records total about 5.7 MB.

`check-catalog.sh` prints its chosen directory. It uses `FP_DATA_DIR` when set, otherwise the main checkout's permanent `data/fp/` when installed, otherwise this worktree's staging directory for pre-transfer acceptance. Read-location overrides and rebuild instructions are in `USAGE.md`. Builders refuse to replace a completed generation.

## Evidence library and CLI

[knowledge_base/evidence.py](../../../knowledge_base/evidence.py) provides `EvidenceReader` and `read_evidence`, without importing models or existing MCP tool code. It reads the database read-only, validates source-manifest/revision bindings and frozen text hashes, returns v1 `evidence-read` plus bound `read-metadata`, and rejects revision conflicts, bad source/parent bindings and redirect cycles.

```sh
python3 -m knowledge_base.evidence --chunk-id postgresql-14-internals-p6-c4
python3 -m knowledge_base.evidence --source-id book:postgresql-14-internals \
  --locator '{"kind":"legacy-chunk","chunk_id":"postgresql-14-internals-p6-c4","parent_id":"postgresql-14-internals-p6","page_mapping":"not found"}'
```

Source-plus-locator calls accept recorded unique source locators or explicit preserved legacy selectors. When a Markdown range overlaps multiple frozen chunks, a read returns its unambiguous legacy locator; the bulk map retains the best source-line witness. Every returned locator in the connected control test is read again and must return the same text hash. This avoids guessing a child versus parent span from shared lines.

Six real [evidence samples](P2-evidence-samples.json) cover mapped technical text, a missing child, drifted child/parent text, philosophy text and overlapping Markdown spans. The CLI output also validates against v1. This is a local library/CLI, not an authenticated gateway; gateway wiring remains a later phase.

## Contracts and baseline lock

No v1 schema or fixture was edited. Registry, catalog entries, locators and evidence responses use the existing v1 contracts. No v1.1 change is required. Two supplementary schemas describe P2's frozen-source manifest and redirect list; these do not extend or replace a v1 response. No new Python dependency was needed; the installed P1-pinned `jsonschema==4.23.0` is reused.

Adding `.gitignore`'s small-record exception initially failed P1's instrument hash check. P1's provided `refresh_contract_lock.py` refreshed the reviewed instrument lock and its release references. Only `contracts-lock.json` and `tested-release-v10.json` changed in `data/baseline/`; frozen `baseline.json`, controls, schema/fixture bytes and source observations were not recaptured. This records an intentional instrument update rather than bypassing the baseline gate.

## Proving cases and independent review

The acceptance command runs the nonempty fixture suite, including:

- `failed_discovery_never_deletes`: incomplete discovery leaves existing database and registry bytes intact, exercised twice. Corrupt source discovery is corrected and rerun successfully; repeated simulated publication I/O failures restore the prior state before successful retry.
- `old_chunk_id_same_evidence`: exact frozen text/hash survives old-ID resolution; the connected gate additionally covers every live child and parent and all 4,756 control hits.
- `unknown_page_stays_not_found`: legacy page mapping remains literal `not found`, including real missing PostgreSQL samples.
- `redirect_record_resolves`: a nonempty explicit redirect reaches the preserved target; a cycle fails visibly. Live redirect count remains zero.
- Invented registry revisions and altered payload bytes are rejected. A locator cannot attach to another source. Overlapping child/parent source spans return a locator that round-trips to the same evidence.

Independent reviewer `/root/p2_review` performed read-only code and actual-artifact checks without service/SSH/model/GPU operations. Pre-registered weaknesses were false-green collection/count checks, guessed locations, wrong revision bindings, failed discovery deleting evidence, misleading stage completion and substitution of current source text. Verified defects were fixed: unchecked reader registry revisions; capture mutation on failed build; partial small-record publication on I/O failure; ambiguous returned locator roundtrips; missing collection entries skipping live checks; and unverified excluded-child/drift summary counts. Regression fixtures and the connected checker cover the fixes. The reviewer reran 11 catalog tests and 30 baseline tests, reconciled actual point/parent/source bindings and the bulk hash, and reported no remaining consequential findings. Connected bppc comparison is the parent/coordinator's gate.

## Validation

- `bash scripts/fp/check-baseline.sh`: **PASS**, including 91 schemas, 32 pairs, 341 fixtures, physical v10 and 420 bppc file hashes. Log: [P2-check-baseline.txt](P2-check-baseline.txt).
- `bash scripts/fp/check-catalog.sh`: **PASS** after all review fixes: **4,756/4,756 frozen control hits**, every live point and all 425,307 locator/evidence rows. Log: [P2-check-catalog.txt](P2-check-catalog.txt).
- Focused catalog suite: **11 tests PASS**. Independent baseline suite: **30 tests PASS**. Python syntax and `git diff --check`: **PASS**.
- The catalog gate checks every live point ID/payload, every child/parent locator/text hash, v1 records, source-manifest/file hashes, ledger counts, all recorded bulk hashes and all hard/easy/sanity hits. bppc frozen per-source files are opened read-only and verified against P1 hashes before extracting evidence hashes; no stored metrics or snippets are substituted for full evidence.

## Preserved defects and handoff limits

The dropped short final group and repeated heading suffixes are listed in the ledger and catalog gaps, and remain in v10. They belong to a separately evaluated content generation in design phase 5. Unknown originals/edition/page facts remain not found. This catalog accounts for the frozen indexed scope, not the completeness of every original work or future graph extraction.

The coordinator must relocate the staged large data, rerun both acceptance commands with `FP_DATA_DIR` pointing to its permanent home, and inspect samples. No commit, merge, push, alias promotion, GPU/model use, remote write or Qdrant mutation was performed. Existing MCP tool behavior and all prohibited source/distribution/wiki/cache paths are unchanged.
