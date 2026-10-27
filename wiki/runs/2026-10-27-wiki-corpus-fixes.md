# Wiki corpus review fixes

Date: 2026-10-27. Owner: knowledge-base maintainers. Worktree: `wiki-corpus`. No commit. Acceptance status: **FAIL / BLOCKED** on live verification: localhost Qdrant connections are denied by this environment. All six fixes and focused offline checks PASS; the full suite retains the 75 reported pre-existing failures.

## Findings, changes and regression tests

Reviewer locations refer to the original implementation.

| Finding | Change | Regression test in `tests/test_wiki_corpus.py` |
| --- | --- | --- |
| 1 High, `index.py:144` | Atomically save an empty manifest before creating a missing collection, so a crash after creation cannot preserve trusted old hashes. | `test_recreated_collection_crash_leaves_cleared_manifest` |
| 2 Medium, `index.py:168` | Store each file's hash and point IDs. Check an unchanged file's IDs in one batched `retrieve`, with payloads and vectors disabled; repair the file if any IDs are missing. CLI reports files reconciled and missing point count. | `test_unchanged_page_reconciles_ids_and_restores_missing_point` |
| 3 Medium, `index.py:175` | Prepare every dense and sparse embedding before any upsert; upsert new points, then delete path-matching points excluding the new IDs. Keep a pending hash until writes and cleanup succeed. | `test_update_embeds_all_batches_before_upsert_and_keeps_page_on_failure`; `test_update_upserts_before_deleting_only_obsolete_ids` |
| 4 Medium, `index.py:22` | Use `data/wiki/manifest-<16-hex-hash>.json`, keyed by Qdrant URL, collection, model and dimension. Move legacy `manifest.json` to the default profile only, without overwriting an existing default manifest; old hash-only entries re-index to acquire IDs. | `test_manifest_profile_isolates_url_collection_model_and_dimension`; `test_legacy_manifest_migrates_to_default_profile_only` |
| 5 Medium, `roots.py:44` | Check the nearest repository and then the parent of every enclosing repository's top level; skip if any is a linked worktree. Retain the nearest repository's project name. | `test_nested_repo_inside_linked_worktree_is_skipped` |
| 6 Low, `chunk.py:10` | Strip closing hashes only when whitespace precedes the hash run. Preserve `C#` and attached hashes. | `test_heading_closing_hashes_require_whitespace` (six cases) |

## Decisions and scope

Grounded: requested source files, shared `ensure_collection`, model registry, and [original implementation report](2026-10-27-wiki-corpus.md) → kept server-only Qdrant, deterministic point IDs and the existing embedding adapter. Books: none. Pattern: coordinator-direct; fixes share the indexer/test contracts and the user specified their behavior.

Crash/restart durability is proved by `test_recreated_collection_crash_leaves_cleared_manifest` and the existing interrupted-new-page test. Failure-state preservation is proved by the multi-batch embedding-failure test and search probe. Manifest profile identity is proved by the four-axis isolation test. Counts measure files, except `missing points` which counts missing IDs. Dry runs do not reconcile, connect or migrate manifests. Concurrent indexers and transactional visibility across an interrupted multi-batch upsert remain outside the contract.

## Verification

- Before implementation, the focused regression selection produced **10 failed, 3 passed**, reproducing every finding. Log: `.cache/wiki-corpus-red.txt`.
- `UV_CACHE_DIR=.cache/uv HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 uv run --offline pytest -q tests/test_wiki_corpus.py tests/test_editions.py`: **44 passed in 7.61 s**. Real in-memory Qdrant, fake dense/sparse encoders, temporary Git fixtures. Log: `.cache/wiki-corpus-focused.txt`.
- Coordinator full-suite command: `UV_CACHE_DIR=.cache/uv uv run --offline python .cache/offline_suite.py -q` → **75 failed, 247 passed, 3 skipped, 6 warnings in 21.40 s**. No test modules were excluded. The scratch runner sets Hugging Face offline flags and disables socket connections; wiki tests use the in-memory Qdrant/fake encoders. Log: `.cache/wiki-corpus-full.txt`.
- Comparison with the 75 known failures reported on main: **73** failures in `tests/test_fp_baseline.py` stop at `FAIL: changed baseline: validator.jsonschema`; **2** in `tests/test_philosophy.py` lack `original-library.en.json` and `tao-te-ching-stephen-mitchell.en.md`. No failures outside those categories. The failing test sources, `scripts/fp` and philosophy implementation have no diff against `main`. This comparison uses the supplied 75-failure baseline and unchanged failing sources; main was not rerun in another checkout.
- `git diff --check`: PASS.
- `wiki log wiki fix "<one line>"`: completed; the worktree-aware command wrote `wiki/log.wiki-corpus.md`. `wiki lint wiki` reports only the same six pre-existing undated-page notices recorded in the original report; unrelated pages were left unchanged.
- Independent code review: automatic approval review rejected `collaboration.spawn_agent` because the tool was unrecognized and its effects could not be verified. Independent review remains unavailable; direct inspection and tests do not replace it.

## Live acceptance attempts

The coordinator ran the real index twice, sequentially, using `UV_CACHE_DIR=.cache/uv HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 uv run --offline python -m knowledge_base.wiki.index`. Both exited **1**, reporting that wiki indexing/search requires the Qdrant server at `http://127.0.0.1:6333`. Logs: `.cache/wiki-corpus-live-first.txt` and `.cache/wiki-corpus-live-second.txt`. Legacy manifest migration runs before connection; it preserves the original contents under the default profile's filename.

The coordinator then attempted all three queries from the original report, with normal encoders/reranking and no fake client:

| Query | Project | Result |
| --- | --- | --- |
| `current architecture` | `Linkcruiser` | BLOCKED, localhost connection denied |
| `recent decisions` | `Linkcruiser` | BLOCKED, localhost connection denied |
| `skill workflow` | `agent-workflow` | BLOCKED, localhost connection denied |

Each query's underlying cause is `ResponseHandlingException(ConnectError('[Errno 1] Operation not permitted'))`. Captured in `.cache/wiki-corpus-live-queries.json`; the runner exits 1. This is a sandbox connection restriction, not evidence that the host Qdrant service is stopped.

**Outstanding acceptance:** from an environment allowed to connect to the host Qdrant, rerun the real index twice. The second successful pass must show `re-embedded=0`, a nonzero `reconciliation checked` count for indexed files, and `missing points=0` for both configured roots. Then rerun the three queries and read the top returned heading. Neither the live second-pass condition nor retrieval quality is claimed as verified here.

## LOAD usage

| Requested source | Used | Application |
| --- | --- | --- |
| `knowledge_base/wiki/index.py` | Yes | Findings 1–4, manifest migration/reconciliation/update ordering and CLI evidence |
| `knowledge_base/wiki/roots.py` | Yes | Finding 5, enclosing repository walk |
| `knowledge_base/wiki/chunk.py` | Yes | Finding 6, heading parsing |
| `knowledge_base/wiki/search.py` | Yes | Verified caller contracts; searchability probe during failed update; live query entry point; no source changes |
| `tests/test_wiki_corpus.py` | Yes | Offline fixture reused and regression cases added |

All source changes and report artifacts stay in this worktree. Books were neither read nor queried.
