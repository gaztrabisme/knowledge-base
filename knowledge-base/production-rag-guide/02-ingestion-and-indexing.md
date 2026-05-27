# Document Ingestion & Indexing

Everything that happens between raw source documents and a searchable knowledge store. This is where most RAG quality is won or lost -- if the right chunks don't exist in the index, no amount of retrieval or generation sophistication will produce good answers.

---

## Document Parsing Strategies

From Q2: An enterprise RAG pipeline spans PDFs, HTML pages, internal wikis, and markdown. Each format needs a dedicated parser.

### Format-Specific Considerations

| Format | Parser approach | Common pitfalls |
|--------|----------------|-----------------|
| **PDF** | pdfminer, PyMuPDF, markitdown | Ligature encoding (ff, fi, fl), null bytes, layout detection, table extraction |
| **HTML** | BeautifulSoup, trafilatura | Navigation/boilerplate removal, JS-rendered content, encoding issues |
| **Markdown** | python-frontmatter + regex | YAML frontmatter parsing, wikilink extraction, header hierarchy |
| **Wiki pages** | API-specific (Confluence, Notion) | Access controls, embedded media, nested pages |

**Anti-pattern (Q2):** Using an LLM to summarize every document into a single paragraph and only indexing summaries. This loses critical detail, eliminates the ability to answer specific questions, and incorrectly claims it removes the need for chunking and reranking.

**Anti-pattern (Q2):** Embedding entire documents as single vectors. Documents are too large for meaningful similarity search, exceed context windows, and lose granularity.

---

## Chunking Strategies

Chunking determines the granularity of your retrieval. The strategy should match your document structure and query patterns.

### Strategy Comparison

| Strategy | How it works | Best for | Pitfalls |
|----------|-------------|----------|----------|
| **Fixed-size** | Split every N tokens with overlap | Uniform text without clear structure | Splits mid-sentence, mid-paragraph |
| **Semantic** | Split at topic/meaning boundaries | Long-form prose, articles | Requires boundary detection, variable chunk sizes |
| **Header-based** | Split at section headers (H1, H2, etc.) | Structured documents with clear hierarchy | Uneven chunk sizes, some sections too large |
| **Hierarchical** | Parent chunks containing child chunks | Complex documents needing both overview and detail | More complex indexing, needs parent-child relationships |
| **Sentence-level** | One or few sentences per chunk | FAQ-style content, short passages | Too granular for complex topics |

### Chunk Size Tradeoffs (Q2, Q16)

```
Too small (< 100 tokens):
  - Loses context needed to understand the passage
  - Increases index size and retrieval noise
  - Anti-pattern from Q16: "100-token chunks with 20-30 retrieved"
    increases total token count and adds noise

Too large (> 1000 tokens):
  - Dilutes relevance signal (irrelevant text in the chunk)
  - Wastes context window space
  - Reduces retrieval precision

Sweet spot (200-500 tokens for most use cases):
  - Large enough to be self-contained
  - Small enough for precise retrieval
  - Overlap of 10-20% preserves context at boundaries
```

---

## Contextual Retrieval

One of the most impactful techniques for improving retrieval quality. From the project's architecture, this yields ~49% better retrieval when combined with BM25.

### How It Works

At indexing time, generate a context prefix for each chunk using a fast model (e.g., Haiku):

```
Original chunk:
  "The practice requires sitting in the lotus position
   with the eyes closed..."

After contextual enrichment:
  "This passage is from Lecture 3 of Zhuan Falun, discussing
   meditation postures and their significance in cultivation practice.

   The practice requires sitting in the lotus position
   with the eyes closed..."
```

### Why It Matters

- BM25 keyword search benefits enormously because the context prefix adds document-level terms that the chunk alone lacks
- Semantic search benefits because the embedding captures broader context
- Retrieval quality improves across both channels simultaneously

### Implementation Pattern

```python
# Pseudo-code for contextual retrieval at indexing time
for chunk in document_chunks:
    context = await fast_model.generate(
        prompt=f"""Document: {document.title}
Section: {chunk.section_header}
Surrounding text: {chunk.surrounding_context}

Write a concise context sentence for this passage:
{chunk.text}""",
        max_tokens=100
    )
    chunk.text_with_context = f"{context}\n\n{chunk.text}"
    chunk.embedding = embed(chunk.text_with_context)
```

---

## Embedding Model Selection

From Q3 and Q26, the choice of embedding model has outsized impact on retrieval quality.

### Evaluation Criteria (in order of importance)

1. **Domain retrieval quality** -- Evaluate on YOUR data, not just published benchmarks
   - Build a test set of 50-100 queries with known relevant passages
   - Measure recall@k, MRR on your own content
   - MTEB scores are a starting point, not a decision (Q3)

2. **Multilingual requirements** -- If you serve multiple languages, test each explicitly (Q26)

3. **Dimensionality tradeoffs** -- Higher dimensions are NOT always better (Q3)
   - Higher dims: more storage, more compute, potentially more semantic nuance
   - Lower dims: cheaper, faster, often comparable quality
   - Evaluate the quality/cost tradeoff empirically

4. **Inference latency and cost** -- Local vs API, batch throughput (Q26)
   - Local models (nomic-embed, BGE, E5): free, private, full control
   - API models (OpenAI, Cohere): convenient but per-call cost, data leaves your infra
   - Task prefixes: some models require them (e.g., nomic: "search_document:" for indexing, "search_query:" for retrieval)

5. **Licensing** -- Commercial use must be explicitly permitted (Q26)

**Anti-pattern (Q3):** "Always choose the highest MTEB score." Leaderboard performance doesn't directly translate to production quality on your domain.

**Anti-pattern (Q3):** "Higher dimensions always capture more semantic nuance." They increase cost and can hurt performance without proportional gains.

**Anti-pattern (Q3):** "Embedding model choice doesn't matter much." It significantly impacts retrieval quality.

---

## Vector Database Selection

From Q3, the key evaluation criteria:

### Indexing Algorithms: HNSW vs IVF (Q3)

| Property | HNSW | IVF |
|----------|------|-----|
| **Query latency** | Very low (graph traversal) | Low-medium (depends on nprobe) |
| **Memory usage** | Higher (graph structure in memory) | Lower (centroids + quantization) |
| **Build time** | Medium | Fast |
| **Update support** | Good (incremental insert) | Poor (rebuild needed for major updates) |
| **Best for** | Low-latency, frequently updated indices | Very large scale, memory-constrained |

**Key insight (Q3):** HNSW is not universally superior. IVF can be better for very large-scale or memory-constrained settings.

### Selection Criteria Checklist (Q3)

- [ ] Metadata filtering support (pre-filtering is critical for multi-tenancy) (Q31)
- [ ] Persistence and durability (not just in-memory)
- [ ] Horizontal scaling capacity
- [ ] Multi-tenancy isolation (namespace/collection level)
- [ ] Operational complexity (managed vs self-hosted)
- [ ] Hybrid search support (vector + keyword in one query)
- [ ] Upsert operations (for incremental updates) (Q29)

### Multi-Tenant Metadata Design (Q31)

```
Correct pattern:
  - Minimal, consistent metadata schema
  - Indexed scalar fields: tenant_id, project_id, acl_ids
  - Small metadata payloads (avoid bloating the index)
  - ACL enforcement at query time via filter predicates

Anti-patterns:
  - Nested JSON ACL trees in metadata (not filterable) (Q31)
  - Separate index per tenant (operational explosion at scale) (Q31)
  - Encoding metadata into embedding dimensions (corrupts semantic space) (Q31)
  - Post-retrieval filtering (security risk, poor recall) (Q31)
```

---

## Index Update Strategies

From Q29: In a system where documents are frequently updated and occasionally deleted, ingestion must handle incremental updates and deletes.

### The Recommended Approach (Q29)

1. **Stable document/chunk IDs** -- Assign persistent IDs that survive content updates
2. **Version tracking** -- Know what version of each document is currently indexed
3. **Upsert operations** -- Update existing vectors without full reindex
4. **Tombstone markers** -- Soft-delete documents without immediate index compaction
5. **Periodic reindex passes** -- Compact the index by removing tombstones and garbage
6. **Cutover consistency** -- Drain in-flight queries before switching to a compacted index

### Anti-Patterns for Index Updates (Q29)

| Anti-pattern | Why it fails |
|-------------|-------------|
| Full reindex on every change | Impractical at scale -- slow, expensive, causes downtime |
| Append-only + query-time dedup | Index bloat grows unbounded, similarity-based dedup is fragile |
| Content-hash as vector ID | Chunk boundaries shift on update, zero-vectors match unpredictably |
| CDC with immediate delete-then-insert | CDC is at-least-once (not exactly-once), race conditions under load |

### Zero-Downtime Reindex (Q59)

For major changes (e.g., new embedding model), use a blue/green index strategy:

```
1. Build new index (green) alongside existing (blue)
2. Dual-write new documents to both indexes during transition
3. Run shadow reads against green to validate quality
4. Quality gates: relevance metrics, latency checks
5. Cut over traffic to green once validation passes
6. Maintain blue as rollback target until confident
7. Decommission blue
```

**Critical (Q59):** You cannot do an in-place rolling update when changing embedding models. Vectors from different models are mathematically incompatible in the same index space.

---

## FTS Index Management

Full-text search (BM25) is the complement to vector search in hybrid retrieval.

### Key Practices

- Rebuild FTS index after adding chunks (e.g., `create_fts_index("text", replace=True)`)
- FTS benefits enormously from contextual retrieval prefixes (document-level terms appear in chunk text)
- BM25 catches exact keyword matches that semantic search may miss
- Combined via Reciprocal Rank Fusion at query time

---

## Reproducibility: Making Everything Rebuildable

From Q34 and the project's core architectural decision: **Markdown is the source of truth. Everything derived is rebuildable.**

### Principles

1. **Source of truth is the raw documents** -- Delete all derived indices, re-ingest from source, get the same result
2. **Version both pipeline code and input data** (Q34) -- Pinned library versions, fixed random seeds, deterministic transforms
3. **Validate data at each stage** (Q34) -- Schema checks, statistical validation, catch corruption early
4. **Maintain lineage tracking** (Q34) -- From raw document through chunks to vectors to model artifacts
5. **Store outputs as immutable, versioned artifacts** (Q34) -- No mutable shared tables

**Anti-patterns for reproducibility (Q34):**
- Mutable shared database tables (re-running may produce different results)
- Docker alone does not guarantee reproducibility (non-deterministic code, unseeded randomness)
- Versioning only the final output, not intermediate stages
- Microservices architecture for transforms (massive over-engineering for ETL)

---

## Cross-References

- Retrieval strategies using these indices: [03-retrieval-and-ranking.md](./03-retrieval-and-ranking.md)
- Vector DB selection matrix: [00-decision-framework.md](./00-decision-framework.md)
- Zero-downtime reindex procedures: [08-deployment-and-operations.md](./08-deployment-and-operations.md)
- Evaluation of ingestion quality: [07-evaluation-and-monitoring.md](./07-evaluation-and-monitoring.md)
