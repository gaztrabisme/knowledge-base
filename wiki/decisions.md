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

## Pipeline (v6)

### tiktoken token counting + "Option 1" chunk sizing
**Context:** Chunk sizes were estimated by word count, which undercounted real tokens by ~1.65x — children drifted well past their nominal target. Calibration showed tiktoken `cl100k_base` matches the Jina v5 tokenizer within ~2%.
**Decision:** Count tokens with tiktoken `cl100k_base`. Re-tightened thresholds to **Option 1**: children to a true `CHILD_MAX_TOKENS=250` (sharper match units), `CHILD_MIN_TOKENS=75`; parents kept near their prior effective size at `PARENT_MAX_TOKENS=1900` to preserve returned context. Rationale: the **child is the match unit** (embedded/retrieved/reranked) so it should be tight and focused, while the **parent is the context unit** returned to the agent, so it stays large. Smaller children = more precise reranking without sacrificing the context the agent actually reads.

### PDF heading recovery via PyMuPDF TOC bookmarks
**Context:** v5's known limitation — markitdown extracts PDF body text but drops heading hierarchy, so PDF-sourced books had empty chapter/section metadata. Compared 4 approaches (markitdown-only, PyMuPDF TOC, Docling, heuristic font-size detection) across 3 books.
**Decision:** PyMuPDF `doc.get_toc()` two-pass reconstruction. Inject TOC bookmark headings at their page-start positions; neutralize any body line that already looks like a markdown heading (`^#{1,6}\s` → prefixed with a space) so code comments like `# init` can't masquerade as structure. Body text never contributes headings. Result: 100% TOC coverage on the production PDF set; postgres/dist-sys/owasp/crypto all gained clean chapter/section paths with zero code-comment false H1s. Docling rejected — crashes on macOS MPS backend.

### PostgreSQL Internals → markitdown fallback (CID-font garble guard)
**Context:** postgresql-14-internals embeds subset fonts with no ToUnicode CMap. PyMuPDF maps those glyphs into the Armenian/Hebrew/extended-Cyrillic ranges ("PostgreSQL" → "PostgreԯԭԨ", "2022" → "ҁѿҁ҂"), garbling ~0.3-0.9% of chars including the flagship keyword. v5/markitdown rendered this book cleanly but flat. It's the only book of 46 affected.
**Decision:** Auto-detect garble — if PyMuPDF text exceeds `_GARBLE_RATIO_THRESHOLD=0.002` suspicious glyphs, discard the TOC headings and fall back to markitdown (clean body, no headings). General, not a hardcoded book name, so any future CID-broken PDF self-heals. Trade-off accepted: clean searchable body + intact BM25 keyword match beats structured-but-garbled text, since the agent reads returned snippets directly. Chose clean text over headings for this one book.

### Front-matter strip: position guard on "Chapter N" heading
**Context:** `strip_front_back_matter` used a first-pass "bare Chapter N / numeric heading = first real chapter" heuristic. creativeprojectsforrustprogrammers names real chapters descriptively but reserves "# Chapter N" headings for a back-matter answer key — the heuristic matched that late appendix heading and discarded the entire 713KB book as front matter, leaving only the 23KB answer key (26 chunks).
**Decision:** Only trust a numeric/"Chapter N" heading if it appears within the first 40% of lines; otherwise fall through to the descriptive-heading fallback. Recovered the book to 873 children.

### Index back-matter narrowing + hard-split oversized chunks
**Context:** A book's "Index" back-matter (page-number noise) and monster paragraphs were producing children far over 250 tokens (16.6% over, one 37,249-token chunk — an "# Index" page).
**Decision:** (1) Narrow exact-match back-matter cut to `index`/`subject index`/`author index` only, so mid-book "Index Scans"/"Indexing" headings don't trigger it. (2) `_hard_split_block()` token-bounded splitting of oversized paragraphs — code blocks split by line and re-fenced, prose split by sentence with a word-level fallback for monster sentences. Result: max child 946, p99 255, 3.3% over 250.

### BM25 keyword parameter + metadata-enriched enrichment prompt
**Context:** Two smaller v6 search-quality items.
**Decision:** (1) Expose a BM25 keyword customization parameter on search. (2) Enrichment prompt now includes the chunk's metadata fields (book/chapter/section) so generated context is grounded in document structure.

### Rust corpus expansion (33 → 46 books)
**Context:** Acquired 13 Rust EPUBs (Humble Bundle Packt Rust bundle). Generalized the EPUB ingestion loop to scan all `SOURCE_DIRS` (added `rust/`) rather than only `applied-ml/`.
**Decision:** Folded all 13 into the v6 re-index. BOOKS entries added in sync to both `config.py` and `scripts/remote_index.py`. Corpus is now 46 books, 48,009 vectors.

### Index now, enrich later
**Context:** Re-chunking invalidates the v5 enrichment context_text, which forces re-enrichment of all 47.6K chunks — a 13-20h serial GPU pass that would block every structural v6 win.
**Decision:** Re-index immediately with `heading_path + child_text` (empty context_text), defer enrichment to a separate background pass (`remote_enrich.py`, then re-index enriched chunks). The embedding-text builder already drops empty context_text, so no code change was needed for the index-now path. Structural improvements (tiktoken sizing, PDF headings, Rust books, bug fixes) ship now; enrichment quality returns later without blocking.

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
