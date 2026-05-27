# Architecture

## Pipeline Overview

```
Source Files (EPUBs, PDFs, HTML, Markdown)
    │
    ▼
[ingest.py] markitdown conversion → clean markdown
    │         - EPUB: heading hierarchy preserved (H1/H2/H3)
    │         - PDF: text extracted, headings lost (flat text)
    │         - Front/back matter stripped (EPUBs only)
    │
    ▼
[chunk.py] heading-aware parent/child chunker
    │         - Split on ## (H2) → parents (600-1200 tokens)
    │         - Split parents into children (100-250 tokens)
    │         - Small sections merged, large ones split on ### or paragraphs
    │         - Code blocks preserved as atomic units
    │
    ▼
[enrich.py] contextual enrichment (optional)
    │         - LLM generates 1-2 sentence context per child chunk
    │         - Resolves ambiguous references, adds book/topic context
    │         - Saves progress every 50 chunks (resumable)
    │
    ▼
[index.py] dual vector embedding
    │         - Dense: Jina v5-text-small (1024-dim, sentence-transformers)
    │         - Sparse: FastEmbed Qdrant/bm25 (proper tokenization, stopwords, IDF)
    │         - Both stored in Qdrant file-based collection
    │
    ▼
[search.py] hybrid retrieval + reranking
    │         - Single Qdrant query with prefetch (dense + sparse)
    │         - DBSF fusion (normalizes score distributions)
    │         - MiniLM-L-12 FlashRank cross-encoder reranking
    │         - Parent deduplication (returns parent text, not child)
    │
    ▼
[server.py] FastMCP → Claude Code
              - 5 tools: search, search_book, get_chapter, list_books, grep_books
```

## Data Flow

```
knowledge-base/
  applied-ml/*.epub          ─┐
  databases/*.pdf             │  SOURCE FILES (gitignored, ~1.9GB)
  security/*.pdf              │
  distributed-systems/*.pdf   │
  production-rag-guide/*.md  ─┘
         │
         ▼
data/markdown/*.md           ─── Intermediate (gitignored, ~24MB)
         │
         ▼
data/chunks/*.json           ─── Intermediate (gitignored, ~68MB)
         │                       Each JSON: {parents: [...], children: [...]}
         ▼
data/qdrant/                 ─── Index (gitignored, ~360MB)
                                 Collection: developer_knowledge
```

## Search Pipeline Detail

Query arrives via MCP → `hybrid_search()`:

1. **Embed query** — Jina v5 dense vector (retrieval.query task) + FastEmbed BM25 sparse vector
2. **Qdrant prefetch** — Two parallel retrievals in one API call:
   - Dense: cosine similarity, top-50 candidates
   - Sparse (BM25): IDF-weighted term matching, top-50 candidates
3. **DBSF fusion** — Distribution-Based Score Fusion normalizes dense [-1,1] and BM25 [unbounded] scores into comparable ranges using 3-sigma distribution bounds
4. **FlashRank rerank** — MiniLM-L-12 cross-encoder scores each candidate against the query. Reranks on `context_text + child_text`. Returns top-k.
5. **Parent dedup** — Multiple children from same parent collapse into one result. Returns parent text (full section) with the best-matching child highlighted.

## Key Design Choices

- **Parent/child chunking** — Children are the indexed unit (small, focused). Parents are the returned unit (full section context). This gives precise retrieval with rich results.
- **File-based Qdrant** — No server process needed. Index lives in `data/qdrant/` directory. Opened/closed per query. Works for our scale (<100K vectors).
- **Standalone remote scripts** — `remote_index.py` and `remote_enrich.py` are self-contained (no package imports). Deployed via rsync. Avoids needing `pip install -e .` on the GPU machine.
