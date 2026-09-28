# C3 candidate collection merge

**Verdict:** Functional acceptance passed with a local test-runner caveat. The exact requested command cannot start in this workspace because `.venv` does not contain pytest and has no pip; writes to `.venv` are denied. The same `.venv/bin/python` passed the integration test when pytest was supplied from `/private/tmp`.

## Change

- Added `scripts/merge_collection.py` with `build`, `verify`, and atomic alias `promote` commands.
- Added server-backed scratch coverage in `tests/test_merge_collection.py`.
- `knowledge_base/config.py` remains unchanged; `KB_COLLECTION` still defaults to `developer_knowledge` and remains environment-overridable.
- No embedding or reranking model is loaded. The live `developer_knowledge` collection is only read by the test setup; all build, overwrite, alias, and cleanup operations target `c3_scratch_*` collections and aliases.
- The build reads the source collection settings from Qdrant, including dense/sparse vectors, HNSW, optimizer, WAL, quantization, and payload-index configuration. It copies points with `with_vectors=True`, enforces the `sha256(child_id)[:8] >> 1` ID scheme for additions, and refuses undeclared collisions. Resume skips matching IDs and repairs existing points whose vectors or payloads differ. Verification uses exact payload and sparse-index comparisons plus float32 vector comparisons, matching Qdrant's vector storage representation.
- The project Knowledge Base lookup was attempted, but tool execution was denied by the session's `approval policy is never`; implementation follows the existing Qdrant copy pattern in `scripts/migrate_to_server.py`.

## Promotion configuration

First run `.venv/bin/python scripts/merge_collection.py promote --alias developer_knowledge_live --to developer_knowledge` to point the alias at the current collection, then add this property inside the `knowledge-base` object in `.mcp.json`:

```json
"env": {
  "KB_COLLECTION": "developer_knowledge_live"
}
```

After the server starts with that environment setting, promote a candidate with `.venv/bin/python scripts/merge_collection.py promote --alias developer_knowledge_live --to developer_knowledge_v8`. Later alias switches do not require a `.mcp.json` or server configuration change. `.mcp.json` has not been edited.

## Verification

The exact command `.venv/bin/python -m pytest tests/test_merge_collection.py -q` failed immediately with `No module named pytest`. `.venv/bin/python -m pip install pytest` was unavailable because `.venv` has no pip; `uv` could not write to the protected environment. The isolated runner was installed under `/private/tmp/c3-test-deps`, then this passed with exit code 0:

```sh
PYTHONPATH=/private/tmp/c3-test-deps .venv/bin/python -m pytest tests/test_merge_collection.py -q
```

Output: `1 passed in 16.50s`. The test covered 50 source points + 20 normalized synthetic points, schema and payload-index copying, fresh build, non-empty refusal, repair of a corrupted source point and add point on resume, undeclared collision refusal, declared overwrite and verification, sampled vector/payload verification, rejection of `--sample 0`, alias creation and switch, and cleanup. The scratch fixture confirmed the server collection list returned to only `developer_knowledge` and the live point count remained 132,623. Independent final checks: `/collections` listed only `developer_knowledge`; `/aliases` was empty; `/collections/developer_knowledge` reported `points_count: 132623`.
