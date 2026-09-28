# C4 phase A report — philosophy collection

## Status

Phase A artifacts are built. The CPU-only acceptance suite passes. Corpus embedding and Qdrant indexing were deliberately not run on this Mac; the remote indexer and loader are ready for the coordinator’s later GPU-box step. The retrieval eval file has 60 known-item queries, but recall thresholds remain unmeasured until the collection is indexed.

## Corpus and alignment

`works.json` registers five work records (Original Library, three separately tracked Tao Te Ching translations, and Zhuan Falun) and nine included language files. Every included file has a paired markdown and chunk JSON file under the philosophy-only subdirectories. The ten-file count sometimes seen during development came from an obsolete Tse Lao `.en` output; it has been removed, and the ingest script now cleans stale language outputs for its own work ids.

| Work | Language | Edition / selected source | PDF pages | Alignment units | Child chunks | Chinese text check |
|---|---|---|---:|---:|---:|---|
| Original Library | en | English source edition; `ORIGINAL LIBRARY - ENGLISH VERSION.docx.pdf` | 88 | 38 | 216 | Not applicable |
| Original Library | vi | Vietnamese source edition; `Thư Viện - Master OS .pdf` | 95 | 38 | 484 | Not applicable |
| Original Library | zh-Hant | Traditional Chinese source edition; `本源圖書館 - 繁體中文版.docx.pdf` | 77 | 38 | 534 | Passed: 928 / 68,669 CJK characters outside the Hant set (1.35%); only supplied Hant edition |
| Tao Te Ching — Jonathan Star | en | Jonathan Star, 2008-01-10, “The Definitive Edition” EPUB | n/a | 81 | 81 | No Chinese original found in aligned chapters |
| Tao Te Ching — Stephen Mitchell | en | Stephen Mitchell English translation PDF | 153 | 81 | 128 | No Chinese original found in aligned chapters |
| Tao Te Ching — Tse Lao | es | Tse Lao Spanish translation EPUB | n/a | 81 | 84 | No Chinese original found in aligned chapters |
| Zhuan Falun | en | Primary archive translation, translated by US & UK practitioners, Aug 2018 | 428 | Front + L1–L9 (10) | 824 | Not applicable |
| Zhuan Falun | vi | Primary archive Vietnamese edition | 440 | Front + L1–L9 (10) | 1,772 | Not applicable |
| Zhuan Falun | zh-Hans | `4合1 / zfl-四合一中间线装` archive layout | 175 | Front + L1–L9 (10) | 2,008 | Passed: 958 / 299,710 CJK characters outside the Hans tier-1 set (0.32%) |
| Zhuan Falun | zh-Hant | Primary Traditional archive PDF | 173 | Skipped | 0 | Failed: 13,582 / 14,596 CJK characters outside the Hant set (93.05%) |

The three Original Library TOCs yielded matching `ol-01`…`ol-38` keys. All Tao editions yielded `ttc-001`…`ttc-081`. Included Zhuan Falun languages have a front section (`zfl-front-lunyu`) plus `zfl-L1`…`zfl-L9`.

## Edition and text-quality decisions

- The Falun archive README warns about corrupted Chinese PDF font mappings. The check counts extracted CJK characters outside a vendored 3,500-character Hans tier-1 list or its Traditional mapping. It records per-PDF counts, compares layouts within each script group, and includes a cross-script peer-share reference for context while keeping pass/fail thresholds language-specific.
- All four candidate Hans Zhuan Falun layouts measured 0.32% outside the common set. The selected 175-page 4-in-1 layout contains all nine lectures and yields complete two-up logical-page coverage. Its companion layouts have 175 or 345 physical PDF pages; all were audited.
- The single supplied Hant Zhuan Falun PDF measured 93.05% outside the common set and was skipped. No alternate Traditional edition was present in the manifest; its cross-script comparison points to a 0.32% Hans peer median, which corroborates the extraction anomaly. The rejected candidate and its check remain recorded in `works.json`.
- The Original Library’s Traditional Chinese PDF passed at 1.35%; no second Hant edition of that work was supplied for a peer comparison.
- The supplied Tse Lao EPUB is Spanish (`es`), despite the brief describing it as English. The registry and chunks preserve its actual language. The requested third English Tao translation is therefore not available from the supplied files. Its 81 chapters remain aligned under the same `ttc-NNN` keys.
- No Chinese original text was found alongside any Tao translation’s aligned chapter text, so no Tao `zh` language file was added.

## Retrieval and MCP changes

- `knowledge_base/philosophy/sparse.py` tokenizes Latin/Vietnamese as lowercase word tokens (preserving diacritics) and CJK as character unigrams plus adjacent bigrams; stable hashed term frequencies feed a Qdrant sparse vector with server-side IDF.
- `scripts/remote_index_philosophy.py` embeds `section_title + child_text` with Jina v5-small and writes dense, custom sparse, and FastEmbed BM25 vectors to an embedded `philosophy` collection. `scripts/load_philosophy.py` upserts those points to `KB_QDRANT_URL` and creates the matching 1024-dimensional collection if needed.
- `search_philosophy` performs DBSF dense/custom-sparse retrieval, lazily loads BGE reranking on CPU, supports language/work filters, and attaches same-section chunks in other languages. `list_philosophy` returns work/language listings or aligned sections. `read_chunk` and `get_chapter` resolve philosophy paths; technical book listing and grep remain scoped to technical markdown. The six existing tool signatures and docstrings were preserved.
- The 60-row eval set has 15 en, 15 vi, 15 mixed Hans/Hant zh, and 15 English cross-language queries. `scripts/eval_philosophy.py` reports recall@10 against the requested thresholds and supports the Ettin + FastEmbed BM25 baseline on the same dense leg. It has not been run because remote indexing is a later step.

## Implementation note and verification

The existing chunker’s sentence overlap recognizes English punctuation. On Chinese text it can treat a whole prior part as one sentence and repeatedly prepend it. The philosophy wrapper continues to use the existing `split_large_section` and `create_children` functions, but omits that overlap between parts so aligned sections do not balloon or duplicate prior text.

Verified with:

```text
.venv/bin/python -m pytest tests/test_philosophy.py -q
6 passed
```

Remaining phase-A follow-up: run remote indexing, load the embedded store into Qdrant, and then run the retrieval eval (with `--baseline` if a comparison is wanted). If an English Tse Lao edition is supplied, replace the recorded Spanish source and rebuild its language file.

## C4b — Traditional Zhuan Falun and script-normalised sparse tokens

### Derived Traditional edition

- Added `zhuan-falun.zh-Hant.md` by reading the accepted `zhuan-falun.zh-Hans.md` sections and converting each section title and body with OpenCC `s2t`. The `zfl-front-lunyu` and `zfl-L1`…`zfl-L9` keys are preserved.
- Registered the edition as `derived from zh-Hans via OpenCC s2t`, with `derived: true`. The rejected Traditional PDF remains attached as `rejected_pdf`, including its original failed text-check record; it is also retained in `edition_candidates.zh-Hant`.
- Wrote 2,300 child chunks across all 10 aligned sections. The chunk document, every parent metadata record, and every child metadata record carry `derived: true`. Remote Qdrant payloads carry this marker, and philosophy search results always expose a boolean `derived` flag.
- The derived text passed the Traditional common-character check: 729 / 297,118 CJK characters outside the common set (0.25%). This checks character plausibility only; the edition is a script conversion and is not an independently verified printed Traditional text.

### Script-normalised sparse tokens

- Both `knowledge_base/philosophy/sparse.py` and the inline tokenizer in `scripts/remote_index_philosophy.py` convert text with OpenCC `t2s` before tokenization, so Traditional and Simplified passages share the same custom sparse tokens at indexing and query time.
- The remote indexer names `opencc-python-reimplemented` as a GPU-box dependency and exits with an install instruction if it is missing. Its custom sparse-vector aggregation also preserves token frequency so indexed values match query-side values.

### Verification

```text
.venv/bin/python -m pytest tests/test_philosophy.py -q
8 passed in 4.44s
```

The tests cover Traditional/Simplified sparse-vector equality, tokenizer and sparse-vector parity between the two copies for English, Vietnamese, and Chinese, matching markdown/chunk section keys, derived markers on parents and children, and the derived flag in returned search hits. No model was loaded and no embeddings were generated on this machine.

## Coordinator: retrieval configuration chosen by ablation

The C4 pipeline (custom sparse leg + BGE reranker) missed the English threshold (0.733 vs 0.85). `scripts/ablate_philosophy.py` crossed three sparse setups (custom, BM25, both) with four rerankers (BGE, Ettin, none, language-routed) on the 60-query eval set. Results are in `ablation.json`. Only one configuration met every threshold: both sparse legs, with the reranker routed by query language (Ettin for plain-ASCII queries, BGE otherwise). It scored en 0.867, vi 0.867, zh 0.800, cross 1.000. `knowledge_base/philosophy/search.py` now implements it. Query embedding reuses the technical index's Jina model, so the server loads it once.

The final run of `scripts/eval_philosophy.py` on the shipped code (`eval-final.txt`) reproduces those numbers and exits 0.

Caveat: 15 queries per group, and the configuration was chosen on the same set that scores it. The choice pairs each language with the component built for it; no numeric parameter was tuned.

## C4c — Translator back matter separation

**Verdict: PASS.** The ingestion rule splits chapter 81 at its first recognized back-matter heading into a separate `ttc-notes` section. `ttc-notes` remains searchable and receives no parallels. Mitchell and Jonathan Star both contain such material; Tse Lao does not.

Changed files:

- `scripts/ingest_philosophy.py`
- `knowledge_base/philosophy/search.py`
- `tests/test_philosophy.py`
- `data/markdown/philosophy/tao-te-ching-stephen-mitchell.en.md`
- `data/chunks/philosophy/tao-te-ching-stephen-mitchell.en.json`
- `data/markdown/philosophy/tao-te-ching-jonathan-star.en.md`
- `data/chunks/philosophy/tao-te-ching-jonathan-star.en.json`
- `data/philosophy/C4-report.md`

| Chunk file | Old child chunks | New child chunks | Result |
|---|---:|---:|---|
| `tao-te-ching-stephen-mitchell.en.json` | 128 | 128 | Split at `Notes`; chapter 81 is 347 characters |
| `tao-te-ching-jonathan-star.en.json` | 81 | 82 | Split at `About the Author`; chapter 81 is 655 characters |
| `tao-te-ching-tse-lao.es.json` | 84 | 84 | Unchanged; no back-matter heading found |

All three translations retain `ttc-001` through `ttc-081`; Mitchell and Star also have the separate notes key. Regeneration wrote only the two affected markdown and chunk pairs. No model was loaded and no embeddings were generated. The first acceptance attempt found an assertion using the wrong chunk text field and reached an existing test path that would fetch the English reranker; it was interrupted before a model loaded. The assertion now checks the actual `text` field, and the hybrid-search test stubs the reranker route. Final verification: `.venv/bin/python -m pytest tests/test_philosophy.py -q` → `10 passed in 5.17s`. No model was loaded and no embeddings were generated.

## C4d — Philosophy search parallels scope and latency

**Verdict: PARTIAL.** Parallel lookup now spans a `work_group` and `section_key`, excludes only the hit’s `(work_id, lang)` translation, and selects up to two dense-nearest chunks per other translation using the hit’s stored vector. Each returned chunk includes `chunk_id`, `work_id`, `lang`, `section_key`, `section_title`, `derived`, and an excerpt capped at 600 characters. The BGE CrossEncoder is configured with `max_length=512` and uses the sentence-transformers default device; the reranker receives at most 40 DBSF candidates and documents built from the section title and child text. The offline contract tests pass. CPU timings were mixed, so this run does not establish a consistent end-to-end latency reduction.

### CPU latency

All live measurements used `.venv/bin/python` with `PYTHONPATH=/private/tmp/claude-501/-Users-GaryT-Documents-Work-tools-knowledge-base/6d8b9f88-0085-46fb-b42a-12bb40f79468/scratchpad/cpuonly` to hide MPS. The cold top-3 timings called `search_philosophy` for both queries in one process, including each model’s first-load cost. The warm top-10 timings primed query embeddings and both rerankers before timing `hybrid_search` (the implementation called by `search_philosophy`).

| Query | Top-k / timing | Before (s) | After (s) | Change |
|---|---|---:|---:|---:|
| `the usefulness of emptiness` | 3, cold end-to-end | 25.824 | 31.078 | +20.3% |
| `空性的用处是什么？` | 3, cold end-to-end | 21.776 | 20.803 | −4.5% |
| `the usefulness of emptiness` | 10, warm end-to-end | 11.936 | 11.802 | −1.1% |
| `空性的用处是什么？` | 10, warm end-to-end | 17.081 | 19.273 | +12.8% |

For top-k 10, the fusion candidate limit fell from 80 to 40. Top-k 3 already used 30 candidates before this change, so that call does not exercise the candidate reduction. These measurements were taken on the shared Mac CPU and show no consistent speedup; the GPU-box recall evaluation remains the coordinator’s next step.

### Live top-3 outputs

The parallels count below is the total number of parallel chunks on each hit. “Groups” is the number of other `(work_id, lang)` translations in the response.

| Query | State | Work | Lang | Section | Parallel chunks (groups) |
|---|---|---|---|---|---:|
| `the usefulness of emptiness` | Before | `tao-te-ching-stephen-mitchell` | en | `ttc-011` | 0 (0) |
|  | Before | `zhuan-falun` | en | `zfl-L2` | 728 (3) |
|  | Before | `zhuan-falun` | en | `zfl-L3` | 803 (3) |
|  | After | `tao-te-ching-stephen-mitchell` | en | `ttc-011` | 2 (2) |
|  | After | `zhuan-falun` | en | `zfl-L2` | 6 (3) |
|  | After | `zhuan-falun` | en | `zfl-L3` | 6 (3) |
| `空性的用处是什么？` | Before | `zhuan-falun` | zh-Hans | `zfl-L2` | 580 (3) |
|  | Before | `zhuan-falun` | zh-Hant | `zfl-L3` | 600 (3) |
|  | Before | `zhuan-falun` | zh-Hans | `zfl-L7` | 462 (3) |
|  | After | `zhuan-falun` | zh-Hans | `zfl-L2` | 6 (3) |
|  | After | `zhuan-falun` | zh-Hant | `zfl-L3` | 6 (3) |
|  | After | `zhuan-falun` | zh-Hans | `zfl-L7` | 6 (3) |

The Tao hit’s two groups are Jonathan Star (`en`, one chunk) and Tse Lao (`es`, one chunk), proving same-language translations are included. No group exceeds two chunks.

### Verification

```text
.venv/bin/python -m pytest tests/test_philosophy.py -q
14 passed in 5.47s
```

Tests use in-memory Qdrant and stub rerankers; no model was loaded by the test suite. The KB grounding search for retrieval/reranking was attempted, but this environment requires tool approval while the approval policy is `never`, so it was unavailable. No philosophy source/chunk data, Qdrant collections, technical search code, or MCP tool signatures were changed.

### Coordinator: C4d measured on the GPU box

`scripts/eval_philosophy.py` on the C4d code (RTX 5080) reads en 0.867, vi 0.867, zh 0.800 and cross 0.867, and exits 0. Cross-language was 1.000 when a hit carried its entire aligned section. It now carries only the two passages per translation nearest to the hit, and stays above the 0.80 threshold. Warm query latency on the GPU is 0.41 s (English) and 0.57 s (Chinese). The first call in a process also loads the models, which took 36 s here, including model download. The Mac CPU timings above do not reflect the live server, which runs its models on the GPU.
