# M1 — EmbeddingGemma 2 re-embed and v10 promotion gate

Owner: Huy. Run: kbu-2026-10-07. Measurements: 2026-10-14. A knowledge base (KB) is the indexed document library used for retrieval. An embedding is a numeric vector representing text. This experiment compares new dense embeddings with the existing v10 retrieval pipeline. Artifacts use JSON files storing named fields, and JSONL files storing one record per line. File hashes are content fingerprints used to detect changed bytes.

## Build

Work ran on bppc, the remote workstation, under `/home/bppc/kb-work/kbu-2026-10-07/M1/`. Qdrant is its vector search database. A collection is a named search index; an alias is a stable name selecting a collection. The private code copy contains no Git version-control metadata. The Mac source repository was read only. R1's environment and model cache were copied into M1; NVIDIA CUDA software for graphics processing unit (GPU) execution was installed only in M1's copied environment. Existing collections and aliases received no write operations from these scripts.

The adapter explicitly registers `google/embeddinggemma-2` at 768 dimensions, meaning 768 coordinates, pinned to checkpoint `914f7f89142e33e77833254d9c9b90c3cef7303b`, a saved model version. It uses SearchQuery for questions and Document for passages, disables vision and audio encoders, loads float32 weights, the learned numbers in the model, and normalizes vectors to unit length. Float32 means 32-bit floating-point numbers. The model input limit is explicitly 8,192 tokens, where a token is a tokenizer input unit. The existing 8,000-character truncation and heading/context/text construction remain unchanged. These model conventions follow [Google's inference guide](https://ai.google.dev/gemma/docs/embeddinggemma/inference-embeddinggemma-with-sentence-transformers), updated 2026-10-06, and R1's pinned checkpoint record.

Books are divided into searchable child passages and larger parent context chunks. The freeze retains exactly 330,778 v10 points across 328 books. Current files contained 518 children absent from v10; v10 contained 463 missing PostgreSQL children and 697 PostgreSQL children with changed inputs. Source assumption (inference): stored v10 text and metadata represent the intended original v10 inputs when current files differ. The M1 operator chose to restore 1,160 PostgreSQL children and their 143 parents from those frozen payloads only in the private copy, to implement the original same-v10 instruction. Each restored text, context, heading, parent identifier and parent text was checked against v10. The current Mac files remain intact; their private-copy version is backed up under current-chunk-files/. source-policy.json labels this as the operator's inference and identifies Huy as the unit owner; separate owner confirmation was not received. The measured PASS verdict below applies to this explicitly described frozen-v10 corpus. This recovery changes no membership or gate criterion.

Payloads are document text and metadata. Every payload and BM25 sparse vector is copied exactly from v10. BM25 is the keyword ranking leg; sparse vectors hold selected terms and weights. The existing inverse document frequency correction accounts for collection term frequency. Distribution-based score fusion combines dense and sparse score distributions. The unchanged Ettin-150M cross-encoder scores a question and passage together to reorder results. The pipeline retains 50 candidates per leg, 50 fused candidates, top ten output, parent deduplication, score floor 4 and minimum result count 3. FastEmbed is pinned to the KB lockfile's 0.8.0. The only search-source change pins the downloaded reranker checkpoint and offline loading; the index-source change specifies its cache directory.

`kbu_m1_gemma768`: 330778 confirmed points; completed=True. Accumulated active embedding/write time: 2578.357935921842 seconds, measured with a monotonic clock. This includes embedding, vector-cache flushes, completed Qdrant writes; it excludes model loading, book reads and pauses. Peak GPU memory recorded by PyTorch, the library running these neural networks: 8060652032 allocated bytes and 16034824192 reserved bytes. Reserved memory is allocator capacity, including cached blocks; these values exclude driver/display memory. The graphics processing unit (GPU) was an RTX 5080.

Elapsed build interval: 4117 seconds, including pauses and restarts; timestamp resolution is one second. Sessions: 6; restart starting-point counts: 64, 128, 23235, 49680, 143277. GPU out-of-memory batch splits: 0.

Recovery records advance only after a completed Qdrant write. Dense caches are flushed first; replay uses the same deterministic point identifiers. Two controlled recovery exercises resumed at 64 and 128 points. A voluntary GPU pause resumed at 23,235 points. A Unicode line separator exposed a JSON record-reader bug at 49,680 points; reading physical JSON lines fixed it and that checkpoint resumed.

The text processor interpreted a literal media marker in book text as an image request at 143,277 points. The adapter now tokenizes the unchanged text as ordinary text pieces for literal image, video and audio markers, then uses the same text model, pooling and normalization. Pooling combines token outputs into one passage vector. A GPU probe found identical normal-text token identifiers and masks, with maximum coordinate difference 2.9802322387695312e-08 between the processor and direct text path. All three literal marker probes produced finite, unit-length 768-coordinate vectors without media token identifiers. A scan of the preceding 143,277 frozen inputs found zero active media markers, so the adapter migration retained those earlier outputs and resumed at that checkpoint. The probe tested Document mode; its query-mode probe result is not found. Final control and candidate gates use the identical final adapter source hash.

Finished books were skipped. A recall marker or termination signal stops at a batch boundary; a present recall marker prevents model loading on restart. Final audits compare every identifier, payload and sparse vector, and every dense vector against its saved output, with finite-value and unit-length checks. Negative-path checks verified that alias destinations, missing collections with recorded progress, and changed manifests are blocked before a model loads or a collection write occurs.

`kbu_m1_gemma256`: 330778 confirmed points; completed=True. It takes the first 256 coordinates of the accepted 768-coordinate outputs and renormalizes them, the Matryoshka transformation described in [Google's guide](https://ai.google.dev/gemma/docs/embeddinggemma/inference-embeddinggemma-with-sentence-transformers). Its active transformation/write time was 81.40381165171857 seconds. This build used CPU operations and loaded no GPU model; GPU model memory for this build was 0 bytes. It has separate progress and audit records. This build completed in one invocation with 0 resumes.

Completed audit for `kbu_m1_gemma768`: 330778 identifiers, 330778 exact payloads, 330778 exact BM25 vectors, and 330778 dense vectors checked against saved outputs. Maximum dense coordinate error: 2.9802322387695312e-08; maximum unit-length error: 1.1920928955078125e-07. Qdrant status: green; optimizer status: ok. Audit time: 80.0050052870065 seconds.

Completed audit for `kbu_m1_gemma256`: 330778 identifiers, 330778 exact payloads, 330778 exact BM25 vectors, and 330778 dense vectors checked against saved outputs. Maximum dense coordinate error: 8.940696716308594e-08; maximum unit-length error: 1.1920928955078125e-07. Qdrant status: green; optimizer status: ok. Audit time: 47.5709172670031 seconds.

## Gate results

The fresh control is **developer_knowledge_v10**, using Jina v5-text-small at 1,024 dimensions. All arms use the original evaluation script and identical query bytes, order and parent-level labels: 438 hard, 199 easy and 30 new-document sanity queries. Normalized discounted cumulative gain at ten (NDCG@10) rewards labeled relevant parents ranked higher. Recall@10 is the fraction of queries with a labeled positive parent in the delivered results. Ground-truth parent mappings were checked against frozen v10 and matched across arms. Run metadata binds results to query, corpus, code, package and audit hashes, and fixes reranker input formatting to descriptive-heading.

Table differences are candidate minus control. The displayed values below are the full floating-point values saved by the unrounded ranking recomputation. The original harness's four-decimal summaries remain in each set JSON. Easy results are informational.

Candidate: **kbu_m1_gemma768**.

| set | metric | developer_knowledge_v10 control | candidate | difference |
|---|---|---:|---:|---:|
| hard | NDCG@10 | 0.7392807563384192 | 0.7351196275326447 | -0.004161128805774461 |
| hard | recall@10 | 0.952054794520548 | 0.9497716894977168 | -0.0022831050228311334 |
| easy | NDCG@10 | 0.9044205070280983 | 0.9047024906120193 | 0.0002819835839210638 |
| easy | recall@10 | 1.0 | 1.0 | 0.0 |
| sanity | NDCG@10 | 0.6462904117686469 | 0.6476855790297742 | 0.001395167261127317 |
| sanity | recall@10 | 0.9333333333333333 | 0.9333333333333333 | 0.0 |


Hits: hard 416/438; easy 199/199; sanity 28/30. All individual hard NDCG losses are saved in gate/gemma768-hard-losses.json.

Sanity misses: 2.

- `web-dev-baseline` — web.dev Baseline and Web Performance Articles > Optimize Interaction to Next Paint (part 1); web.dev Baseline and Web Performance Articles > Optimize Interaction to Next Paint > Figure out what's causing poor INP; web.dev Baseline and Web Performance Articles > Optimize Interaction to Next Paint > Optimize interactions (part 1) (part 1); web.dev Baseline and Web Performance Articles > Optimize Interaction to Next Paint > Optimize interactions (part 1) (part 2); web.dev Baseline and Web Performance Articles > Optimize Interaction to Next Paint > Optimize interactions (part 2); web.dev Baseline and Web Performance Articles > Optimize Interaction to Next Paint > Conclusion: When optimizing INP, how can developers reduce the delay before an event handler begins running? Fusion top 50 contained the labeled parent: True.

- `whatwg-html` — WHATWG HTML Standard > User interaction > The `popover` attribute (part 3) (part 1): How can a button declare which popover it controls in HTML, including the relationship used to invoke it? Fusion top 50 contained the labeled parent: True.



Candidate: **kbu_m1_gemma256**.

| set | metric | developer_knowledge_v10 control | candidate | difference |
|---|---|---:|---:|---:|
| hard | NDCG@10 | 0.7392807563384192 | 0.7347523957146386 | -0.004528360623780592 |
| hard | recall@10 | 0.952054794520548 | 0.9497716894977168 | -0.0022831050228311334 |
| easy | NDCG@10 | 0.9044205070280983 | 0.9066030549313453 | 0.002182547903247012 |
| easy | recall@10 | 1.0 | 1.0 | 0.0 |
| sanity | NDCG@10 | 0.6462904117686469 | 0.6412622027057903 | -0.0050282090628566145 |
| sanity | recall@10 | 0.9333333333333333 | 0.9333333333333333 | 0.0 |


Hits: hard 416/438; easy 199/199; sanity 28/30. All individual hard NDCG losses are saved in gate/gemma256-hard-losses.json.

Sanity misses: 2.

- `web-dev-baseline` — web.dev Baseline and Web Performance Articles > Optimize Interaction to Next Paint (part 1); web.dev Baseline and Web Performance Articles > Optimize Interaction to Next Paint > Figure out what's causing poor INP; web.dev Baseline and Web Performance Articles > Optimize Interaction to Next Paint > Optimize interactions (part 1) (part 1); web.dev Baseline and Web Performance Articles > Optimize Interaction to Next Paint > Optimize interactions (part 1) (part 2); web.dev Baseline and Web Performance Articles > Optimize Interaction to Next Paint > Optimize interactions (part 2); web.dev Baseline and Web Performance Articles > Optimize Interaction to Next Paint > Conclusion: When optimizing INP, how can developers reduce the delay before an event handler begins running? Fusion top 50 contained the labeled parent: True.

- `whatwg-html` — WHATWG HTML Standard > User interaction > The `popover` attribute (part 3) (part 1): How can a button declare which popover it controls in HTML, including the relationship used to invoke it? Fusion top 50 contained the labeled parent: True.



## Verdict

**kbu_m1_gemma768: PASS.** All three fixed conditions must pass.


- hard NDCG@10 drop: 0.004161128805774461; required ≤ 0.010; PASS.

- hard recall@10 drop: 0.0022831050228311334; required ≤ 0.005; PASS.

- sanity recall@10: 0.9333333333333333; required ≥ 0.80; PASS.



**kbu_m1_gemma256: PASS.** All three fixed conditions must pass.


- hard NDCG@10 drop: 0.004528360623780592; required ≤ 0.010; PASS.

- hard recall@10 drop: 0.0022831050228311334; required ≤ 0.005; PASS.

- sanity recall@10: 0.9333333333333333; required ≥ 0.80; PASS.



Promotion was not performed. The task permits new bppc collections and prohibits changes to existing collections and the Mac's live alias. Paired significance diagnostics from the original significance.py are informational; they do not alter these fixed thresholds. Jina uses R1's pinned checkpoint `6856e76bb72982e58de0620458a4e8b3614da340`, and Ettin uses `025501c4e0f9bbeb4c5b198318e0089ff061cc14`. The historical index checkpoint identifier was not found in the inspected source. The fresh control reproduced gate-v10.md's reported hard, easy and sanity scores.

Final checks confirmed the Mac's live alias `developer_knowledge` points to `developer_knowledge_v10`. On bppc, v10's 330,778-point count, collection configuration and payload-index schema match the pre-run snapshot. Both new collections are green. All nine copied gate output pairs and their metadata hashes match; the two CPU samples contain 100 matched queries each. The final GPU observation was 120 MiB, 0 %. These observations are saved in gate/final-state.json and gate/transfer-verification.json; acceptance command output is retained in logs/verify.log.

## Query latency

Query embedding was timed on bppc's AMD Ryzen 9 9950X central processing unit (CPU) with GPU visibility disabled. Both models were configured for 16 compute threads, one inter-operation thread and float32 parameters. Threads are program execution lanes; inter-operation threads schedule parallel operations. Calls include tokenization, inference, normalization and vector conversion, excluding loading, retrieval and reranking. Each model discarded three warm-ups, then timed one single-query call for each of the same first 100 unique hard-set questions with a monotonic nanosecond clock. The 95th percentile is the 95th sorted observation. Raw timings and identical query-list hashes are retained. Final accepted timings were collected after all M1 builds, gates and significance calculations finished; provisional timings are retained under logs/latency-provisional/. **Mac timing is out of scope; no Mac model was loaded.**

| model | queries | median, ms | 95th percentile, ms | mean, ms |
|---|---:|---:|---:|---:|
| Jina v5-text-small | 100 | 103.090394 | 111.883183 | 103.59394687 |
| EmbeddingGemma 2, 768 | 100 | 42.723459000000005 | 48.769132 | 43.77797973 |

## Output sample

These are real lines printed from saved results and runtime logs:

```text

v10-hard: n=438 {"ndcg": 0.7393, "recall10": 0.9521, "mrr": 0.8302, "recall_ceiling": 0.9749}

v10-easy: n=199 {"ndcg": 0.9044, "recall10": 1.0, "mrr": 0.9639, "recall_ceiling": 1.0}

v10-sanity: n=30 {"ndcg": 0.6463, "recall10": 0.9333, "mrr": 0.7261, "recall_ceiling": 1.0}

gemma768-hard: n=438 {"ndcg": 0.7351, "recall10": 0.9498, "mrr": 0.8277, "recall_ceiling": 0.9703}

gemma768-easy: n=199 {"ndcg": 0.9047, "recall10": 1.0, "mrr": 0.9709, "recall_ceiling": 1.0}

gemma768-sanity: n=30 {"ndcg": 0.6477, "recall10": 0.9333, "mrr": 0.7233, "recall_ceiling": 1.0}

gemma256-hard: n=438 {"ndcg": 0.7348, "recall10": 0.9498, "mrr": 0.8268, "recall_ceiling": 0.9703}

gemma256-easy: n=199 {"ndcg": 0.9066, "recall10": 1.0, "mrr": 0.9709, "recall_ceiling": 1.0}

gemma256-sanity: n=30 {"ndcg": 0.6413, "recall10": 0.9333, "mrr": 0.7233, "recall_ceiling": 1.0}

cpu-v10: queries=100 threads=16 median_ms=103.090394 p95_ms=111.883183

cpu-gemma768: queries=100 threads=16 median_ms=42.723459000000005 p95_ms=48.769132

```

## Sources

- Local KB: CLAUDE.md; knowledge_base/embedder.py, config.py, index.py and search.py; scripts/remote_index.py, ingest_all.py, eval_retrieval.py and significance.py; data/bench/gate-v10.md; uv.lock. Read 2026-10-14; publication dates not found. Unmodified and adapted source pairs are in reference-code/ and private-code/.

- [R1 report](../R1/REPORT.md): dated 2026-10-10. [D1 specification](../D1/design-spec.md): revision v2, evidence/correction dated 2026-10-10. Both read 2026-10-14. Used for checkpoint selection, explicit model registration and the fixed storage/search comparison.

- [Google inference guide](https://ai.google.dev/gemma/docs/embeddinggemma/inference-embeddinggemma-with-sentence-transformers): last updated 2026-10-06 UTC; accessed 2026-10-14. Used for native dimensions, text-only loading, precision, prompts and normalized Matryoshka prefixes.

- [Pinned Gemma checkpoint](https://huggingface.co/google/embeddinggemma-2/tree/914f7f89142e33e77833254d9c9b90c3cef7303b): R1 records repository update 2026-10-06; individual file publication dates not found. The copied checkpoint was loaded offline on 2026-10-14.

- [Ettin repository metadata](https://huggingface.co/api/models/cross-encoder/ettin-reranker-150m-v1): API last-modified timestamp 2026-05-19 13:59:34 UTC, retrieved 2026-10-14; pinned revision recorded in gate/reranker-model.json.

- bppc Qdrant database observations, GPU/CPU platform logs, freeze/progress records, exact collection audits, gate JSON/JSONL, CPU samples, negative-path checks and source-restoration verification: produced 2026-10-14. These are measured operational evidence. REVIEW.md records independent code reviews and fixes. RUNBOOK.md records reproduction and recovery commands.
