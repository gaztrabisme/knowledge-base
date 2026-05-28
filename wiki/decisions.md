# Technical Decisions

## Pipeline

### markitdown over pandoc (v2)
**Context:** pandoc flattened EPUB heading hierarchy (all H1), producing tiny chunks (parent avg 295 tokens, child avg 35). markitdown preserves H1/H2/H3.
**Decision:** Switched to markitdown. Chunk quality jumped to parent avg 467, child avg 187 tokens.

### Custom chunker over Chonkie
**Context:** Evaluated `RecursiveChunker.from_recipe("markdown")`. It splits on heading boundaries but has no parent-child support.
**Decision:** Keep custom chunker. It does heading-aware splitting with parent-child linking, which is our core retrieval pattern.

### Single Qdrant collection over per-domain split
**Context:** Expanding from ML-only to 4 domains. Per-domain collections allow independent rebuild but complicate cross-domain search.
**Decision:** Single collection. Corpus is small (<20K vectors). Cross-domain results are valuable ("regularization" should hit both ML and security books). Domain filtering available via payload field if needed.

## Search Pipeline (v4)

### FastEmbed Qdrant/bm25 over custom regex tokenizer
**Context:** Custom tokenizer was `re.findall(r"[a-z0-9]+")` with hash-based indices. No stopwords, no stemming, hash collisions.
**Decision:** FastEmbed's `Qdrant/bm25` model. Proper tokenization, 29-language stopword lists, no collisions. Drop-in replacement for `text_to_sparse_vector()`.

### DBSF fusion over client-side RRF
**Context:** Had two separate `query_points` calls merged with custom RRF (k=60). Qdrant has built-in fusion via `prefetch` API.
**Decision:** Qdrant's DBSF fusion. Normalizes dense/sparse score distributions automatically. Single API call. Deleted `_rrf_fusion()` entirely.

### MiniLM-L-12 reranker over TinyBERT-L-2
**Context:** FlashRank default `Ranker()` loaded TinyBERT-L-2 (4MB, 2-layer) — weakest tier. Larger models (BGE 568M, Jina 278M) exceed 500ms latency on Apple Silicon.
**Decision:** `ms-marco-MiniLM-L-12-v2` (34MB, 12-layer). Best FlashRank English model. ~50-100ms for 50 candidates on CPU. One-line change.

### rank-T5-flan as future option
**Context:** As we expand beyond ML into security/databases, out-of-domain generalization matters more. `rank-T5-flan` (110MB) has better zero-shot performance.
**Decision:** Deferred. MiniLM-L-12 is good enough for now. Config makes it a one-line swap.

## Search Pipeline (v5)

### Ettin-150m over MiniLM-L-12 / Jina v3 / Qwen3-Reranker
**Context:** MiniLM-L-12 (34MB, FlashRank) was the v4 reranker. Researched modern alternatives: Jina v3 (278M, 0.5856 NDCG@10), Qwen3-Reranker-0.6B (0.5940), Ettin family (6 ModernBERT models, 17M-1B, Apache 2.0, distilled from mxbai-rerank-large-v2).
**Decision:** Ettin-150m (151M, 0.5994 NDCG@10). Beats Jina v3 at half the size. PyTorch at 0.17s/50-docs on Apple Silicon. sentence-transformers CrossEncoder replaces FlashRank (FlashRank has a fixed model list that can't load Ettin).

### Absolute score floor over gap-based cutoff
**Context:** Planned gap detection (1.5x median gap) for adaptive cutoff. Calibrated on 14 diverse queries with full 50-candidate score distributions.
**Decision:** Absolute floor (score >= 4.0) + min results (3). Gap detection triggers at position 1-2 for most queries because Ettin's smooth distributions put the largest gap between #1 and #2 — too aggressive. Score floor of 4.0 perfectly separates nonsense (max 3.68) from real queries (min top score 8.36).

### HyDE/multi-query as agent-provided parameters over local LLM
**Context:** HyDE traditionally requires a local LLM to generate hypothetical answers. Multi-query needs a model to reformulate queries.
**Decision:** Expose `hyde_passage` and `extra_queries` as MCP tool parameters. The calling agent (Claude) generates these directly — zero latency overhead, zero dependency on LM Studio or any inference server. BM25 leg still uses original query for keyword matching.

### ONNX acceleration deferred
**Context:** Ettin-150m (ModernBERT) on ONNX would give 2-3x speedup via `sentence-transformers[onnx]`.
**Decision:** Blocked. `optimum` requires `transformers<4.58`, ModernBERT needs `>=5.2.0`. Hard conflict, no compatible version exists (as of 2026-05-28). PyTorch at 0.17s is fast enough. Revisit when optimum supports transformers 5.x.

### Parent chunk overlap at H2 boundaries
**Context:** Cross-section answers (where the answer spans two consecutive H2 sections) get split across chunks, degrading retrieval for boundary content.
**Decision:** Copy last 2 sentences of each section into the start of the next section (within same chapter). +3.3% chunk count (19,103 → 19,728). PDF-sourced books with empty chapter metadata are skipped (can't determine section boundaries).

### Heading path in embeddings
**Context:** Section titles carry strong semantic signal ("MVCC and Transaction Isolation") but weren't included in the embedded text.
**Decision:** Prepend `heading_path` before `context_text` and `child_text` when constructing the embedding input. Both `index.py` and `remote_index.py` updated in sync.

## Rejected Approaches

### GraphRAG / LightRAG
**Why considered:** Cross-book concept linking (e.g., "regularization" in 8 books).
**Why rejected:** Our structured books + enrichment + hybrid search already handles this. LightRAG needs another LLM pass (~11 hours) for graph construction. Marginal quality gain for our query patterns (single-concept lookups, not multi-hop reasoning over unstructured corporate docs).
**Lighter alternatives if needed later:** Concept tagging during enrichment pass, entity-to-chunk side index via spaCy NER, cross-book "see also" links via embedding similarity.

### TurboVec
**Why considered:** Rust ANN index, 8-16x vector compression, faster than FAISS on M-series.
**Why rejected:** Pure dense index — no BM25, no hybrid, no metadata filtering. We'd lose everything Qdrant gives us. Only relevant at 100K+ vectors for memory pressure.

### SPLADE++ learned sparse retrieval
**Why considered:** Term expansion handles vocabulary mismatch ("overfitting" → "regularization", "dropout").
**Why rejected for now:** 532MB model vs zero-cost BM25. Available via same FastEmbed interface if BM25 quality proves insufficient. Dense retrieval already handles semantic matching.

### Grep replacing BM25 (Anthropic "grep beats RAG")
**Why considered:** Anthropic's Claude Code team found grep outperformed RAG for codebases.
**Why rejected for primary search:** That finding is specific to codebases with literal identifiers. Our queries are conceptual ("how does batch normalization work"). Added `grep_books()` as a complement for exact-match lookups, not a replacement.
