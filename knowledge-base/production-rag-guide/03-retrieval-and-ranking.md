# Retrieval & Ranking

Retrieval is where RAG systems succeed or fail. If the right chunks are not surfaced, no amount of generation sophistication will produce a good answer. This document covers the full retrieval pipeline from query to ranked results.

---

## Hybrid Search: Vector + BM25

From Q2 and Q3: Production RAG systems should use hybrid search combining semantic (vector) and keyword (BM25) retrieval.

### Why Hybrid?

| Retrieval method | Strengths | Weaknesses |
|-----------------|-----------|------------|
| **Vector (semantic)** | Understands meaning, handles paraphrases, catches conceptual matches | Misses exact keywords, struggles with rare terms, acronyms, proper nouns |
| **BM25 (keyword)** | Exact term matching, fast, deterministic, handles rare terms well | Misses semantic equivalents, no understanding of meaning |
| **Hybrid** | Covers both semantic and lexical matches | Slightly more complex, needs fusion strategy |

**Anti-pattern (Q2):** Using only BM25. "Keyword search alone misses semantic matches." Dogmatically rejecting vector search limits retrieval quality.

**Anti-pattern (Q2):** Skipping BM25 entirely. Keyword matching catches exact-match queries that vector search may miss, especially for domain-specific terminology, codes, and identifiers.

---

## Reciprocal Rank Fusion (RRF)

RRF merges ranked lists from multiple retrieval methods into a single ranked list. It is simple, effective, and requires no learned parameters.

### The Formula

```
RRF_score(d) = Σ  1 / (k + rank_i(d))
               i
```

Where:
- `d` is a document/chunk
- `rank_i(d)` is the rank of document `d` in the i-th ranked list (1-indexed)
- `k` is a constant (typically 60) that controls how much weight is given to lower-ranked results
- The sum is over all ranked lists (e.g., vector results + BM25 results)

### How k Affects Behavior

```
k = 1:   Top-ranked results dominate heavily
          rank 1 score: 1/2 = 0.500
          rank 10 score: 1/11 = 0.091 (18% of rank 1)

k = 60:  More democratic, lower-ranked results still contribute
          rank 1 score: 1/61 = 0.016
          rank 10 score: 1/70 = 0.014 (87% of rank 1)

k = 60 is the standard default. It prevents any single retrieval
method from dominating and allows consensus across methods.
```

### Implementation Pattern

```python
def reciprocal_rank_fusion(ranked_lists: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    """Fuse multiple ranked lists using RRF.

    Args:
        ranked_lists: List of ranked document ID lists
        k: RRF constant (default 60)

    Returns:
        List of (doc_id, score) tuples, sorted by score descending
    """
    scores: dict[str, float] = {}
    for ranked_list in ranked_lists:
        for rank, doc_id in enumerate(ranked_list, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

**Note:** Some vector databases offer native hybrid search with built-in RRF. When available, use it. When not, implement manual RRF as a fallback -- this is the pattern used in Claudie's architecture.

---

## Reranking with Cross-Encoders

From Q7: Reranking is a second-stage relevance scoring step that improves precision at the cost of additional latency.

### How It Works

```
Stage 1 (Bi-encoder retrieval):
  Query → embedding → top-N candidates via ANN search
  Fast but approximate relevance scoring

Stage 2 (Cross-encoder reranking):
  For each candidate: (query, chunk) → cross-encoder → relevance score
  Slow but precise relevance scoring (sees query and chunk together)
```

### When to Use Reranking (Q7, Q57)

**Use when:**
- Initial retrieval returns noisy results (low precision@k)
- Retrieval quality is a measured bottleneck
- Latency budget allows 50-200ms additional overhead

**Skip when:**
- Initial retrieval already has high precision
- Strict latency constraints leave no room (Q57)
- Small knowledge base where top-k is already highly relevant

### Precision-Latency Tradeoff (Q57)

```
Scenario from Q57:
  Reranking takes 800ms on full candidate set

  Optimization: Reduce top-k candidates + conditional/lightweight reranker
  Result: Reranking drops to ~200ms

  Technique: Only rerank when initial retrieval confidence is low
  (conditional reranking)
```

### Anti-Patterns (Q7)

| Anti-pattern | Why it's wrong |
|-------------|---------------|
| "Always use reranking" | Cross-encoders add significant latency/cost; only use when precision needs it |
| "Reranking = re-embedding with query" | Reranking uses cross-encoders that see query+doc together, not re-embedding |
| "Reranking is done at index time" | It is a query-time operation. Precomputing all query-document pairs is infeasible |
| "Use the LLM itself to rerank" | Cross-encoders are faster and more cost-effective for top-N reranking |
| "Reranking = sorting by timestamp" | That is temporal sorting, a completely different concept |

---

## Graph-Augmented Retrieval

When your knowledge base has rich entity relationships (e.g., wikilinks, concept hierarchies), knowledge graph traversal improves recall by finding related chunks that keyword/semantic search alone would miss.

### Pattern: Post-Retrieval Graph Expansion

```
1. Run hybrid retrieval (vector + BM25)
2. Apply RRF fusion to get initial ranked results
3. For top-N results:
   a. Look up each chunk's node in the knowledge graph
   b. Fetch 1-hop neighbors (directly connected nodes)
   c. Retrieve those neighbors' chunks
   d. Apply a score penalty (e.g., 0.5x the parent's score)
4. Merge expanded results with initial results
5. Deduplicate and re-sort by score
```

### Why Score Penalty Matters

Graph neighbors are related but not directly matched by the query. Without a score penalty, they would rank equally with directly relevant chunks, diluting precision. A 0.5x penalty ensures they augment results without dominating them.

### When to Use

- Knowledge base has explicit relationships (wikilinks, citations, entity links)
- Users ask questions that span multiple related topics
- Retrieval recall is a bottleneck (relevant chunks exist but are not found by keyword/semantic search)

---

## Metadata Filtering and ACL Enforcement

From Q2, Q31, and Q53: In multi-tenant systems, security filtering must happen BEFORE retrieval, not after.

### The Correct Pattern (Q31)

```python
# Pre-filtering: ACL is part of the query
results = vector_db.search(
    query_embedding=query_vec,
    filter={
        "tenant_id": current_tenant,
        "acl_ids": {"$in": user_acl_list}
    },
    top_k=20
)
```

### Why Pre-Filtering is Critical (Q31, Q53)

Post-retrieval filtering is dangerous:
1. The vector DB retrieves cross-tenant documents (data exposure in memory)
2. After filtering, you may have too few relevant results (or none)
3. A single query bug leaks data

**Anti-pattern (Q2):** "ACL filtering should be applied post-generation by redacting unauthorized content from the final response." This means the LLM has already seen unauthorized content -- a critical security flaw.

**Anti-pattern (Q31):** "Fetch top-1000 without filters, then filter in application code." This wastes compute and momentarily exposes unauthorized data in memory.

### Metadata Schema Design (Q31)

```
Good:
  - Small, indexed scalar fields (tenant_id, project_id, acl_ids)
  - Consistent schema across all vectors
  - Enforce at query time via filter predicates

Bad:
  - Nested JSON ACL trees (not efficiently filterable)
  - Full permission hierarchies in metadata (belongs in application layer)
  - Metadata encoded in embedding dimensions (corrupts semantic space)
```

---

## Query Routing and Intent Classification

From Q4 and the project's architecture: The agent decides depth through tool use. No external router classifies messages.

### Approaches

| Approach | How | When |
|----------|-----|------|
| **Agent-driven** | LLM decides when/what to retrieve based on the query | Flexible, handles diverse query types naturally |
| **Keyword-based routing** | Route by detected keywords/patterns | Simple but brittle |
| **Classifier-based routing** | Trained classifier selects retrieval strategy | Predictable but requires training data |
| **Hybrid** | Classifier for common patterns, agent fallback for others | Balance of predictability and flexibility |

**The project's approach:** "Trust the agent. Give Claude tools and context, let it decide what to do. No pre-built routing logic that second-guesses the model." For "I want cake," it never calls the retriever. For deep questions, it may retrieve multiple times from different angles.

---

## Multi-Stage Retrieval Pipelines

From Q2 and Q57: Complex queries may benefit from multiple retrieval stages.

### Pipeline Stages

```
Stage 1: Broad retrieval
  - Hybrid search (vector + BM25)
  - Generous top-k (e.g., 50-100)
  - Fast, high recall

Stage 2: Reranking
  - Cross-encoder scores each candidate
  - Prunes to top-k (e.g., 5-10)
  - Slower, high precision

Stage 3: Graph expansion (optional)
  - Expand via knowledge graph neighbors
  - Add related chunks with score penalty
  - Improves coverage for multi-faceted queries

Stage 4: Context assembly
  - Select final chunks for the prompt
  - Order by relevance or document position
  - Fit within token budget
```

### Latency Budget Allocation (Q57)

From the profiling scenario in Q57 (target: P95 < 1s):

```
Original:  Embed(150ms) + Search(200ms) + Rerank(800ms) + LLM(1200ms) = 2350ms

Optimized:
  - Embed: 150ms (cache frequent queries)
  - Search: 200ms (already fast)
  - Rerank: 200ms (reduce top-k + conditional/lightweight reranker)
  - LLM: streaming (time-to-first-token meets SLA)
  - Total to first token: ~550ms
```

**Key insight (Q57):** Stages are inherently sequential in RAG -- the LLM needs retrieved context. You cannot run retrieval and generation in parallel. Focus optimization on reducing each stage rather than parallelizing incompatible stages.

---

## Retrieval Evaluation Metrics

From Q6: Rigorous evaluation separates good RAG from "it looks good."

### Core Metrics

| Metric | What it measures | When to use |
|--------|-----------------|-------------|
| **Recall@k** | Fraction of relevant docs in top-k results | Are we finding what we should find? |
| **MRR (Mean Reciprocal Rank)** | Average of 1/rank for the first relevant result | How high is the first relevant result? |
| **nDCG (Normalized Discounted Cumulative Gain)** | Quality of ranking considering position | Are relevant results ranked higher than irrelevant ones? |
| **Precision@k** | Fraction of top-k results that are relevant | How clean are the results? |

### Formulas

```
Recall@k = |relevant ∩ retrieved_top_k| / |relevant|

MRR = (1/|Q|) * Σ (1 / rank_i)  where rank_i is position of first relevant doc

nDCG@k = DCG@k / IDCG@k
  where DCG@k = Σ (2^rel_i - 1) / log2(i + 1)
  and IDCG@k is DCG of the ideal ranking
```

### Anti-Patterns in Retrieval Evaluation (Q6)

| Anti-pattern | Why it fails |
|-------------|-------------|
| Using BLEU/ROUGE for retrieval | Surface-level token overlap; paraphrased correct answers score low |
| Skipping retrieval evaluation because final answers look good | Retrieval failures may be masked by LLM improvisation |
| Exact-match only for retrieval evaluation | Too strict; relevant documents may not exactly match |
| Only evaluating end-to-end | Cannot diagnose whether failures are retrieval or generation problems |

---

## Golden Test Sets

From Q6 and Q24: The foundation of systematic retrieval evaluation.

### How to Build a Golden Test Set

1. **Collect representative queries** -- Cover common patterns, edge cases, domain-specific questions
2. **Annotate relevance** -- For each query, identify the chunks/documents that should be retrieved
3. **Include difficulty levels** -- Easy (single relevant chunk), medium (multiple relevant chunks), hard (requires synthesis across chunks)
4. **Include negative examples** -- Queries where the system should abstain (no relevant content exists)
5. **Version the test set** -- Update as the knowledge base grows, track changes

### How to Use Golden Test Sets

```
Development:  Run after every significant change to retrieval
CI/CD:        Automated regression test on every deployment (Q48)
Monitoring:   Periodic runs to detect drift (Q33)
Comparison:   A/B testing different retrieval configurations
```

**Key insight (Q6):** Golden test sets are NOT optional overhead. They are essential for regression testing. Without them, you only discover quality degradation from user complaints.

---

## Cross-References

- How retrieval feeds into generation: [04-prompt-engineering.md](./04-prompt-engineering.md)
- ACL and security enforcement: [05-safety-and-security.md](./05-safety-and-security.md)
- Evaluation framework: [07-evaluation-and-monitoring.md](./07-evaluation-and-monitoring.md)
- When to add reranking/graph: [00-decision-framework.md](./00-decision-framework.md)
- Ingestion that feeds retrieval: [02-ingestion-and-indexing.md](./02-ingestion-and-indexing.md)
