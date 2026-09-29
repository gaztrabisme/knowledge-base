# v9 indexing and collection build report

**Run date:** 2026-09-30  
**Verdict:** FAIL — all index/build/verify count gates passed, but bppc did not have the required `developer_knowledge` alias before the run and still does not.

## Preflight

- Manifest rows with `action: ingest`: 29.
- Local v9 chunk files found: 29; summed `children`: 20,076.
- Remote chunk transfer: 29/29 SHA-256 matches; remote child total: 20,076.
- bppc `~/kb-work/v9/` received the 29 chunk files, `remote_index.py`, its repo dependency `embedder.py`, and `merge_collection.py` for the required remote build/verify.
- Pre-run `developer_knowledge_v8`: 266,647 points on both bppc and Mac.
- GPU before indexing: 3,802 MiB used, 12,063 MiB free.
- Indexer: `~/kb-env/bin/python` with `KB_INDEX_BATCH=48`, collection `developer_knowledge_v9_add`, output directory `~/kb-work/v9/qdrant`, log `~/kb-work/v9/index.log`; `index.exit` was `0`, and the log ended `Done. 20076 vectors indexed in /home/bppc/kb-work/v9/qdrant`.
- Exact count from the bppc embedded Qdrant store: 20,076.
- Embedded store transfer to `data/qdrant-v9-add/`: rsync completed successfully (375,865,957 bytes transferred; local `du -sh` reports `369M`).
- Mac alias before run: `developer_knowledge` → `developer_knowledge_v8`.
- bppc alias preflight and final state: `/aliases` returned `[]`; the Qdrant collection list includes a regular collection named `developer_knowledge`. No existing collection or alias was changed.

## Results

The exact counts on both Qdrant servers are:

| Collection / set | Points |
| --- | ---: |
| `developer_knowledge_v8` | 266,647 |
| v9 added points (`developer_knowledge_v9_add`) | 20,076 |
| `developer_knowledge_v9` | 286,723 |

Build on bppc exited 0:

```json
{"add_collection": "developer_knowledge_v9_add", "add_count": 20076, "copied_from_src": 266647, "dst": "developer_knowledge_v9", "dst_count": 286723, "expected_dst_count": 286723, "overwrites": 0, "repaired_add_existing": 0, "repaired_src_existing": 0, "skipped_add_existing": 0, "skipped_src_existing": 0, "src": "developer_knowledge_v8", "src_count": 266647, "upserted_from_add": 20076}
```

Verify on bppc exited 0:

```json
{"add_count": 20076, "dst_count": 286723, "expected_dst_count": 286723, "identical": true, "overwrites": 0, "sampled_add": 100, "sampled_src": 100, "src_count": 266647}
```

Build on the Mac exited 0 with the same counts and zero overwrites. The requested command
`.venv/bin/python scripts/merge_collection.py verify --src developer_knowledge_v8 --dst developer_knowledge_v9 --add data/qdrant-v9-add --add-collection developer_knowledge_v9_add`
exited 0:

```json
{"add_count": 20076, "dst_count": 286723, "expected_dst_count": 286723, "identical": true, "overwrites": 0, "sampled_add": 100, "sampled_src": 100, "src_count": 266647}
```

Final HTTP counts were `points_count: 286723` for `developer_knowledge_v9` and `points_count: 266647` for `developer_knowledge_v8` on both servers. The Mac alias remains `developer_knowledge` → `developer_knowledge_v8`. On bppc, the alias is absent and a same-named collection already exists. The alias acceptance condition therefore fails on bppc. Correcting it would require altering/removing the existing collection or changing alias state; neither was done because the task explicitly forbids modifying it and excludes promotion.

## Notes

- `wiki/index.md` currently says 20,381 v9 children; the 29 manifest-selected chunk files present for this run sum to 20,076. The task-specified files/count were used. No files under `wiki/` were edited.
- The existing `developer_knowledge_v8`, `philosophy`, and `developer_knowledge` collection/alias state was not modified. No containers were stopped or restarted, and no commit was made.
