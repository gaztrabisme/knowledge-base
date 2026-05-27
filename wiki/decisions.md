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
