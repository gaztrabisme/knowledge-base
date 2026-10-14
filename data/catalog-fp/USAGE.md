# FP P2 catalog

The registry binds fixed logical IDs to SHA-256 revisions. Each `source_hash` names
the exact `revisions/*.json` manifest, which binds the frozen indexed payload
inventory and separately observed normalized source files. It does not claim an
original edition. Every bulk row has that same source ID/revision/hash. The reader
returns exact frozen UTF-8 evidence; locator failures and source drift remain
visible in read metadata. `verification: exact` concerns frozen payload identity,
not an original-edition quote check.

```sh
bash scripts/fp/check-catalog.sh
python3 -m knowledge_base.evidence --chunk-id clean-code-p0-c0
python3 -m knowledge_base.evidence --source-id book:clean-code \
  --locator '{"kind":"legacy-chunk","chunk_id":"clean-code-p0-c0","parent_id":"clean-code-p0","page_mapping":"not found"}'
```

For source-plus-locator reads, pass the locator recorded in the map. A Markdown
line range matching more than one frozen span returns ambiguity; use its old
chunk ID to select a single exact span. Reads of those overlapping spans return
a preserved legacy locator so that their returned locator can be read again
unambiguously. The bulk map still retains the best available source line witness. A legacy locator names an existing preserved chunk and must carry its exact
parent ID and `page_mapping: not found`; the read returns the recorded best locator. The optional `--revision` rejects mismatched revisions.
The CLI emits a v1 `evidence-read` record. Python callers use `EvidenceReader`
(context manager for repeated reads), or `read_evidence`. This is a local read
library, not an authenticated gateway; the existing MCP server is unchanged.

Small records are versioned here. Large evidence/maps and verified controls are
in `catalog.sqlite` and `gate/` under `data/fp/`, ignored by git. Copy that directory
at acceptance to the main checkout's `data/fp/`. The checker prints its resolved
location: `FP_DATA_DIR`, otherwise the permanent main-checkout directory, otherwise
this worktree's staging directory while acceptance transfer is pending.
`FP_MAIN_CHECKOUT`, `FP_QDRANT_URL`, `FP_BPPC_ROOT`, `FP_BPPC_HOST`, `FP_PYTHON` override
read locations. The reader shares `FP_DATA_DIR` and `FP_MAIN_CHECKOUT`.

```sql
SELECT chunk_id, role, source_id, source_revision, source_hash,
       content_sha256, locator, status, reason
FROM chunks WHERE chunk_id = 'postgresql-14-internals-p6-c4';
```

`points` has one row per Qdrant point (339,210 across v10 and philosophy); `chunks`
adds unique parents (425,307 total rows). `payload` and parent `text` use standard
zlib compression. Every frozen payload and evidence text has a SHA-256. Primary
keys reject duplicate point/chunk IDs. The database is opened read-only by readers
and checkers. `storage.json` pins its bytes, SHA-256 and all table counts.

Catalog `ordered_membership` consists of indexed parent IDs in numeric legacy
order. `inventory_complete` applies to that frozen indexed scope. Archive counts
refer to preserved frozen child payloads; index counts refer to observed child
points. Historical parse and extraction counts remain null with reason `not found`.
The `truncation` boolean records whether P2 truncated its copied evidence (false);
historical source truncation extent remains explicitly `not found` in the ledger
and gaps. Original assets and physical PDF/EPUB mappings were not discovered in
the requested main `Library/`. Existing Markdown lines are verified normalized
text witnesses. Preserved legacy locators are used where there is no unique line
mapping. No page number is inferred from printed numerals or chunk IDs.

Rebuild in a **new** staging directory and records directory; builders refuse to
replace frozen generations. A failed/incomplete discovery cannot become an empty
membership update. Capture uses only Qdrant scroll/GET and hash-pinned bppc file
reads, without models, GPU usage or remote writes:

```sh
python3 scripts/fp/capture_catalog.py /path/to/new-staging
python3 scripts/fp/build_catalog_fp.py --database /path/to/new-staging/catalog.sqlite \
  --records /path/to/new-small-records
```

The `philosophy` collection has 10 language editions. Shared titles/work aliases
can be ambiguous; the reader reports alternatives. The unpromoted `philosophy_b`
candidate is not part of this scope. Live redirects are empty because every v10
ID is retained; nonempty redirect and cycle fixtures exercise resolution.
