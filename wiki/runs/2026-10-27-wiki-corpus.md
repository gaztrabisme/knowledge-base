# Project wiki corpus implementation report

Date: 2026-10-27. Owner: knowledge-base maintainers; implementation by Codex on `wiki-corpus`. Status: implementation and offline checks complete; full acceptance pending coordinator execution. No commit.

**Follow-up (2026-10-27):** The six independent-review findings are fixed; the manifest and update behavior described below are historical. See the [review fixes report](2026-10-27-wiki-corpus-fixes.md) for current behavior, 44 passing focused cases, the full-suite result (75 known failures), and blocked live index/query attempts.

## Behavior

The separate `wiki` collection uses the configured main embedding model (default `google/embeddinggemma-2`) through its existing adapter, plus its own FastEmbed `Qdrant/bm25` encoder. Wiki queries have their own DBSF fusion and server client. Ettin reranking defaults on; `KB_WIKI_RERANK=0` (also `false`, `no`, `off`) disables it. `KB_WIKI_COLLECTION` overrides the collection name. `KB_QDRANT_URL` defaults to `http://127.0.0.1:6333`; wiki operations never use the embedded book store.

`KB_WIKI_ROOTS` overrides `data/wiki/roots.txt`, including an empty value to disable wiki tools. The file supports comments and home expansion. Only the explicitly selected wiki folders are scanned. Git worktree copies are logged and skipped by comparing absolute common and per-worktree Git directories. `inputs/`, `raw/` and symlinks are excluded from indexing.

H1/H2 boundaries define sections, preserving H3+ content inside them. Heading paths and the first date in the heading path or filename enter the payload. A 6,000-character budget approximates 1,500 tokens; oversized sections split by paragraph and oversized single paragraphs split to the cap. Fenced example headings do not define sections. `wiki_read` accepts the absolute search-result path and optionally an exact heading path/title, including its descendants; resolved paths must stay inside a configured root.

The manifest maps absolute file paths to SHA-256 digests. Files with unchanged digests need no embeddings. Changes delete all old points for that path before inserting deterministic `(path, chunk index)` IDs. Missing pages delete their points and manifest entries. A pending empty digest is saved before writes, so even an interrupted new-page upsert can be retried or deleted later. A recreated collection invalidates the old digests. A missing root raises before mutation; it does not imply all its pages were deleted. A selected-root run preserves other roots' pages.

## Key decisions and verification boundaries

- Grounded: supplied philosophy and book implementations → separate collection/model/client/fusion; existing embedding prompts, device choice and Ettin loader reused. Books were not consulted, per the task instruction.
- Root confinement → `test_wiki_read_whole_page_section_and_root_boundary` covers sibling-prefix paths and symlink escapes.
- Interrupted external writes → `test_interrupted_new_page_can_be_deleted_on_next_pass` injects a lost upsert response after points were actually written, then deletes the source and confirms cleanup.
- Failure state → `test_missing_root_fails_without_deleting_points` and `test_server_down_raises_clear_error_without_embedded_fallback` cover unavailable inputs/server.
- Units → counters count files, except skipped worktree roots; budget and snippets count characters, and scores are DBSF or reranker scores according to the setting.
- Dry run reports planned changes without opening Qdrant, loading models, or writing a manifest. Use one indexer at a time; concurrent manifest writers and switching between existing collections with a shared manifest are outside this change's guarantees.

## LOAD usage

| Requested source | Used | Application |
| --- | --- | --- |
| `CLAUDE.md` | Yes | Corpus isolation, current models, server versus embedded behavior, project conventions |
| `wiki/index.md` | Yes | Architecture and durable wiki records; linked report from the index |
| `knowledge_base/philosophy/search.py` | Yes | Own collection/client/model, hybrid prefetch and DBSF fusion, reranker API compatibility |
| `knowledge_base/philosophy/sparse.py` | Yes | Self-contained corpus pattern; wiki uses the requested FastEmbed BM25 instead of its CJK tokenizer |
| `knowledge_base/index.py` | Yes | Parameterized `ensure_collection`; payload/vector/upsert pattern; avoided its embedded fallback |
| `knowledge_base/search.py` | Yes | Dense `""` plus sparse `"bm25"` DBSF and existing Ettin loader |
| `knowledge_base/embedder.py` | Yes | Existing query/passage encoding and `KB_DEVICE`/CUDA/CPU selection |
| `knowledge_base/config.py` | Yes | Main model/dimension, BM25 model, root path and edition behavior |
| `knowledge_base/server.py` | Yes | Lazy tool implementations and conditional registration |
| External wiki folders | No | Automatic command review refused optional read attempts as unclassifiable/read-write-capable; local wiki structure was sufficient |
| Books | No | None needed or requested |

Applied the dev skill. Implementation was coordinator-direct. The skill-requested independent review was attempted but the automatic approval reviewer rejected `collaboration.spawn_agent` as an unrecognized tool whose safety it could not verify. Independent review is deferred; the direct code audit and executable checks do not substitute for it.

## Verification

Commands ran from this worktree with `UV_CACHE_DIR` inside `.cache/uv`; `--offline`, `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` prevented package/model downloads.

| Check | Result |
| --- | --- |
| `uv run --offline pytest -q` after the shared collection change | BLOCKED during collection: existing `knowledge_base/chunk.py` requests uncached `cl100k_base.tiktoken`; DNS to `openaipublic.blob.core.windows.net` unavailable |
| `uv run --offline pytest -q tests/test_wiki_corpus.py tests/test_editions.py` | PASS: 31 passed in 8.64 seconds; real `QdrantClient(":memory:")`, fake dense/BM25 encoders, temporary Git repo/worktree |
| `uv run --offline pytest -q --ignore=tests/test_philosophy_phase_b.py` | FAIL: 189 passed, 75 failed, 3 skipped in 20.74 seconds; this run preceded five added edge-case tests |
| Broad-run failures | 73 `tests/test_fp_baseline.py` cases stop at `validator.jsonschema`: environment has 4.26.0, baseline requires 4.23.0. Two philosophy tests need untracked markdown/chunk data absent here. These inputs/dependencies were not changed |
| `python -m knowledge_base.wiki.index --help` | PASS: repeatable `--root` and `--dry-run` exposed |
| `.venv/bin/python -m knowledge_base.wiki.index --root wiki --dry-run` | PASS on this actual checkout: `files seen=0, re-embedded=0, deleted=0, skipped (worktree)=1`; logged the distinct Git directories; no manifest written |
| `git diff --check` | PASS |
| `git check-ignore data/wiki/manifest.json` | PASS; roots config remains visible to Git |
| `wiki lint wiki` | Six existing undated-page notices; no new notice from this change |
| Live index / live repeat pass / real queries | NOT RUN: coordinator owns the live Mac/Qdrant execution |

The initial wiki run found two fixture issues (unsupported Qdrant context manager and inherited Git signing/hooks). The fixtures now explicitly close Qdrant and disable signing/hooks only inside the temporary test repository. All targeted tests pass after those corrections.

## Test names

`tests/test_wiki_corpus.py` has 27 cases, including five configurations of the last test:

- `test_ensure_collection_defaults_and_independent_name_dimension`
- `test_roots_file_comments_expansion_and_environment_override`
- `test_worktree_root_skipped`
- `test_chunk_log_entries_heading_paths_and_dates`
- `test_nested_wiki_uses_repository_folder_as_project`
- `test_chunk_caps_paragraphs_and_unbroken_text_without_losing_tail`
- `test_fenced_headings_do_not_split_sections`
- `test_inputs_raw_and_symlink_files_skipped`
- `test_incremental_second_pass_reembeds_zero`
- `test_changed_page_reembedded_and_old_points_removed`
- `test_deleted_page_points_removed_and_unselected_root_preserved`
- `test_interrupted_new_page_can_be_deleted_on_next_pass`
- `test_missing_root_fails_without_deleting_points`
- `test_dry_run_does_not_connect_embed_or_write_manifest`
- `test_dry_run_preserves_points_and_manifest_for_changes_and_deletions`
- `test_recreated_collection_reembeds_despite_existing_manifest`
- `test_cli_repeatable_roots_and_per_root_counts`
- `test_server_down_raises_clear_error_without_embedded_fallback`
- `test_project_filter_on_both_hybrid_legs`
- `test_rerank_defaults_on_and_disable_avoids_loading_ranker`
- `test_rank_api_orders_candidates_before_applying_limit`
- `test_wiki_read_whole_page_section_and_root_boundary`
- `test_tools_registered_only_with_nonempty_roots_config` (`missing`, `empty`, `comments`, `configured`, `env`)

The four edition cases cover `test_server_registers_the_requested_edition_tools` (`core`, `full`), `test_bundle_parts_hash_and_reassemble`, and `test_bundle_reassembly_rejects_corrupt_local_release_part`.

## Coordinator acceptance

Run `uv run pytest -q` with the real machine's dependencies, cached tokenizer and philosophy corpus data. Then:

```sh
uv run python -m knowledge_base.wiki.index --dry-run
uv run python -m knowledge_base.wiki.index
uv run python -m knowledge_base.wiki.index
```

The repeat pass must report `re-embedded=0` for both roots. Use three real queries, for example `wiki_search("current architecture", project="Linkcruiser", limit=3)`, `wiki_search("recent decisions", project="Linkcruiser", limit=3)`, and `wiki_search("skill workflow", project="agent-workflow", limit=3)`. Select precise terms from those projects if needed and check the returned page/heading using `wiki_read`. These are suggested probes, not claimed retrieval results.

## Changed files

Final line counts use `wc -l`; changes use `git diff --numstat`, with all lines counted as additions for new files.

| File | Final lines | Added / deleted |
| --- | ---: | ---: |
| `.gitignore` | 83 | +5 / -0 |
| `knowledge_base/index.py` | 197 | +6 / -4 |
| `knowledge_base/server.py` | 629 | +25 / -0 |
| `knowledge_base/wiki/__init__.py` | 1 | +1 / -0 |
| `knowledge_base/wiki/roots.py` | 74 | +74 / -0 |
| `knowledge_base/wiki/chunk.py` | 85 | +85 / -0 |
| `knowledge_base/wiki/index.py` | 207 | +207 / -0 |
| `knowledge_base/wiki/search.py` | 91 | +91 / -0 |
| `data/wiki/roots.txt` | 2 | +2 / -0 |
| `tests/test_wiki_corpus.py` | 400 | +400 / -0 |
| `tests/test_editions.py` | 88 | +2 / -0 |
| `wiki/index.md` | 81 | +1 / -0 |
| `wiki/active-work.md` | 107 | +5 / -0 |
| `wiki/log.md` | 269 | +6 / -0 |
| `wiki/runs/2026-10-27-wiki-corpus.md` | 123 | +123 / -0 |
