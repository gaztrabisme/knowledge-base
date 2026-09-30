# U7 — Philosophy B candidate build

**Verdict: FAIL / PARTIAL.** The resumable builder, sparse cache, local Qdrant load tests, search collection override, and eval options are implemented. Dense embedding could not start because the Jina model was not cached and Hugging Face DNS/network access was unavailable. No live collection was loaded or changed.

## Completed checks

- Phase B input count: **42,188** chunks: en 7,490; vi 14,316; zh-Hans 9,120; zh-Hant 11,262.
- Sparse and FastEmbed BM25 stage: `.venv/bin/python .claude/plan-goal/verify/cpu.py scripts/build_philosophy_candidate.py --stage sparse` processed **42,188/42,188** chunks. The finalized cache-recipe run measured **969.96 chunks/s** cumulative CPU throughput (the stage logs throughput after every batch).
- Cache check: `.venv/bin/python .claude/plan-goal/verify/cpu.py scripts/build_philosophy_candidate.py --check`

```text
en: total=7490 sparse=7490 bm25=7490 dense=0
vi: total=14316 sparse=14316 bm25=14316 dense=0
zh-Hans: total=9120 sparse=9120 bm25=9120 dense=0
zh-Hant: total=11262 sparse=11262 bm25=11262 dense=0
```

- CPU dense acceptance attempt: `.venv/bin/python .claude/plan-goal/verify/cpu.py scripts/build_philosophy_candidate.py --stage dense --device cpu --limit 96` stopped while loading `jinaai/jina-embeddings-v5-text-small-retrieval`; Hugging Face DNS was unavailable (`[Errno 8] nodename nor servname provided`). No dense vectors were produced.
- Dense CPU throughput: **not measurable**; the model failed to load before the first batch.
- Vector equality against `remote_index_philosophy.py`: **0/5 compared**; cosine results are `[N/A, N/A, N/A, N/A, N/A]` because there are no dense vectors. This gate remains unverified.
- Focused tests: **6 passed**. Three local fixture tests compare the custom sparse and FastEmbed BM25 vectors against their production code paths, verify resumability, copy phase A points into local Qdrant unchanged, reconcile a stale point, check phase B payload/IDs, and check refusal for `philosophy` and missing vectors. Three evaluator/search tests cover short custom files, filter removal, hit/miss diagnostics, JSON output, and the collection environment override/default.
- Full suite: `.venv/bin/python .claude/plan-goal/verify/cpu.py -m pytest tests -q` → **145 passed, 1 skipped**.
- Static checks: Ruff passed; Bandit reported no findings. Pyright reports four issues: two pre-existing Qdrant condition typing errors in `search.py`, and unresolved `fastembed` imports in its environment.
- Live Qdrant check: `curl -sS --max-time 3 http://127.0.0.1:6333/collections` was refused by the environment. The expected phase A baseline is **8,432** points per `baseline.json`; live counts and absence of `philosophy_b` could not be confirmed here. This run did not invoke the load stage against the server.
- Review note: the optional `--baseline` evaluator path still cannot count parallel-only cross-language hits because it does not request candidate dense vectors for `_attach_parallels`; the primary evaluator path is unaffected.

## Coordinator run order

Sparse vectors and BM25 are already cached. Before allocating the GPU window, make the Jina v5 weights available to this environment; this run could not retrieve them. Then run only the dense passage stage during the GPU window:

```bash
# GPU window: full Phase B dense passage embeddings; run without cpu.py only in the announced window.
.venv/bin/python scripts/build_philosophy_candidate.py --stage dense --device mps

# After the GPU stage, confirm all vectors are cached (CPU only).
.venv/bin/python .claude/plan-goal/verify/cpu.py scripts/build_philosophy_candidate.py --check

# After dense is complete, create/load the isolated candidate collection (CPU only).
.venv/bin/python .claude/plan-goal/verify/cpu.py scripts/build_philosophy_candidate.py --stage load --collection philosophy_b
```

To evaluate a custom file against the candidate, use its path in place of `PATH` and write diagnostics to a chosen output path:

```bash
KB_PHILOSOPHY_COLLECTION=philosophy_b .venv/bin/python .claude/plan-goal/verify/cpu.py scripts/eval_philosophy.py --eval-file PATH --no-filters --json-out data/philosophy/phase-b/candidate-eval.json
```

`data/philosophy-vectors/` is ignored by git and contains the sparse/BM25 cache. Cache fingerprints include the vector recipe and text hash; loading reconciles the candidate's IDs after copying/upserting. Dense cache completion, five-vector cosine equality, candidate load, and live collection invariants remain outstanding until the model is available and Qdrant is reachable.

Custom eval files may be short; their recall is diagnostic and does not apply the phase A thresholds. Empty eval files are rejected.
