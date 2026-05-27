# Decision Framework for Production RAG Systems

A quick-reference guide for the key architectural decisions you will face when building a production RAG system. Each decision tree references the detailed treatment in the companion documents.

---

## 1. RAG vs Fine-Tuning vs Hybrid

**Start here:** What problem are you solving?

```
Is the knowledge base dynamic (updates weekly or more)?
  YES --> RAG is required for freshness
  NO  --> Could go either way

Do you need citations and traceability?
  YES --> RAG is required (fine-tuning cannot cite sources)
  NO  --> Continue

Is the problem about behavior/style/format (e.g., tone, classification)?
  YES --> Fine-tuning is the right tool
  NO  --> Continue

Is the problem about factual accuracy on domain-specific content?
  YES --> RAG (grounds answers in retrieved evidence)
  NO  --> Prompt engineering may be sufficient
```

**The hybrid sweet spot (Q21):** Fine-tune for consistent tone, domain phrasing, and classification behavior. Use RAG to ground responses in up-to-date knowledge and provide citations. This is the pragmatic split for most production systems.

**Anti-pattern:** Fine-tuning on factual corpora alone. The model's knowledge becomes stale immediately, and it cannot cite sources. (Q1, Q21)

**Anti-pattern:** Using RAG to try to control output style or classification behavior. Retrieval augments knowledge, not style. (Q21)

See: [01-architecture.md](./01-architecture.md), [02-ingestion-and-indexing.md](./02-ingestion-and-indexing.md)

---

## 2. Embedding Model Selection Checklist

Evaluate these criteria in order of importance for your use case (Q3, Q26):

| Criterion | What to evaluate | Trap to avoid |
|-----------|-----------------|---------------|
| **Domain retrieval quality** | Evaluate on YOUR data, not just MTEB | Trusting leaderboard scores blindly -- they don't transfer to all domains (Q3) |
| **Multilingual coverage** | Test all required languages explicitly | Assuming multilingual support from marketing claims |
| **Dimensionality** | Higher dims != better. Evaluate cost/quality tradeoff | 1536-dim when 768-dim performs equally on your data (Q3) |
| **Inference latency/cost** | Local vs API, batch throughput, cold start | Choosing a closed-source API without evaluating on your own data (Q3) |
| **Licensing** | Commercial use, data processing terms | Open-weights != open-license for commercial use (Q26) |
| **Context length** | Must cover your chunk sizes | Truncation without awareness |

**Decision:** If you have domain-specific content, always run a retrieval evaluation on a sample of your own queries before committing to a model. Published benchmarks are necessary but not sufficient. (Q3)

See: [02-ingestion-and-indexing.md](./02-ingestion-and-indexing.md)

---

## 3. Vector Database Selection Matrix

Key factors from Q3, Q29, Q31, Q59:

| Factor | HNSW-based (Pinecone, Weaviate, Qdrant) | IVF-based (Faiss, Milvus) | Embedded (LanceDB, ChromaDB) |
|--------|------------------------------------------|---------------------------|------------------------------|
| **Query latency** | Low (sub-ms for small-medium scale) | Low-medium (depends on nprobe) | Low (single-process, no network) |
| **Memory footprint** | Higher (full graph in memory) | Lower (can quantize, disk-backed) | Low (embedded, lazy-loading) |
| **Scale ceiling** | Billions (managed services) | Billions (with sharding) | Millions (single-node) |
| **Metadata filtering** | Usually native pre-filtering | Varies by implementation | Usually native |
| **Multi-tenancy** | Namespace/collection isolation | Application-level | Application-level |
| **Ops complexity** | Low (managed) to Medium (self-hosted) | High (cluster management) | Very low (embedded library) |
| **Persistence** | Durable (managed) | Varies | File-based, durable |

**Decision tree:**

```
Are you a single developer or small team with < 10M vectors?
  YES --> Embedded DB (LanceDB, ChromaDB) — zero ops
  NO  --> Continue

Do you need managed multi-tenancy with ACL filtering at scale?
  YES --> Managed service (Pinecone, Weaviate Cloud)
  NO  --> Continue

Are you memory-constrained or at very large scale (100M+ vectors)?
  YES --> IVF-based (Faiss, Milvus) with quantization
  NO  --> HNSW-based for best latency
```

**Anti-pattern:** Encoding tenant/ACL metadata into embedding dimensions. This corrupts the semantic space. Use metadata fields with pre-filtering. (Q31)

**Anti-pattern:** Post-retrieval filtering for security (fetch unfiltered, then filter). This leaks data to the retrieval layer and may return too few results. (Q31, Q53)

See: [02-ingestion-and-indexing.md](./02-ingestion-and-indexing.md)

---

## 4. When to Add Reranking

**Decision (Q7, Q57):**

```
Is retrieval precision a bottleneck?
  (Users report irrelevant results, or evaluation shows low precision@k)
  YES --> Reranking will help
  NO  --> Skip it (unnecessary latency)

Can you tolerate the latency?
  Typical cross-encoder: 50-200ms for top-20 reranking
  YES --> Use a cross-encoder reranker
  NO  --> Use a lightweight/conditional reranker, or reduce top-k

Is latency critical (< 500ms total)?
  YES --> Reduce top-k candidates OR use a distilled reranker
  NO  --> Full cross-encoder reranking
```

**Key insight (Q7):** Reranking is a query-time second-stage operation using cross-encoders. It reorders top-N candidates from initial retrieval. It is NOT re-embedding, NOT temporal sorting, and NOT an indexing-time operation.

**Anti-pattern:** Always reranking. If initial retrieval is already high-precision, reranking adds latency without benefit. (Q7)

**Anti-pattern:** Reranking all retrieved chunks. Reduce top-k first, then rerank the reduced set. (Q57)

See: [03-retrieval-and-ranking.md](./03-retrieval-and-ranking.md)

---

## 5. When to Add a Knowledge Graph

```
Does your domain have rich entity relationships?
  (People <-> Organizations, Concepts <-> Subconcepts, etc.)
  YES --> Graph adds value
  NO  --> Vector + BM25 is likely sufficient

Do users ask relationship or traversal queries?
  ("What is connected to X?", "How are A and B related?")
  YES --> Graph is essential
  NO  --> Continue

Would graph traversal improve retrieval recall?
  (Related chunks are spread across documents, wikilinks exist)
  YES --> Graph-augmented retrieval (expand results via neighbors)
  NO  --> Pure vector/BM25 is sufficient
```

**Key pattern:** Graph expansion as a post-retrieval step: after RRF fusion, fetch 1-hop neighbor chunks with a score penalty (e.g., 0.5x). This augments semantic search with structural relationships without replacing it.

See: [03-retrieval-and-ranking.md](./03-retrieval-and-ranking.md)

---

## 6. When to Use Agents vs Simple Retrieval

**Decision (Q4, Q12):**

```
Is the task a single question with a single retrieval step?
  YES --> Simple tool-calling (one-shot retrieval + generation)
  NO  --> Continue

Does the task require multiple retrieval steps, reasoning across results, or tool use?
  YES --> Agent loop (plan-act-observe-refine)
  NO  --> Simple pipeline

Does the task require write operations or external side effects?
  YES --> Agent with safety controls (allowlists, sandboxing, max-steps)
  NO  --> Simpler is better
```

**Key distinction (Q4):** An agent operates in a loop (plan, act, observe, refine) maintaining state across steps. Simple tool-calling is a single-shot decision. The risks of agents (runaway loops, cost explosion, hallucinated tool calls) demand mitigations: max-step limits, timeouts, tool allowlists, schema validation, sandboxed execution.

**Anti-pattern:** Using agents when simple retrieval suffices. Agents add latency, cost, and risk. (Q4)

**Anti-pattern:** No safety controls on agent loops. Always implement max-step limits and cost caps. (Q4)

See: [01-architecture.md](./01-architecture.md), [05-safety-and-security.md](./05-safety-and-security.md)

---

## 7. Caching Strategy Decision Tree

**Decision (Q11, Q56):**

```
Layer 1: Embedding Cache
  Are you seeing repeated or similar queries?
  YES --> Cache computed embeddings, keyed by query text
  NO  --> Skip (compute is cheap per-query)

Layer 2: Retrieval Cache
  Same queries hitting the vector DB repeatedly?
  YES --> Cache retrieval results with versioned keys
         (query_hash:index_version:model_version)
  NO  --> Skip

Layer 3: Completion Cache
  Deterministic settings (temperature ~0) with repeated queries?
  YES --> Cache LLM completions (NEVER cache PII-containing responses)
  NO  --> Skip (non-deterministic outputs are poor cache candidates)

Invalidation:
  On knowledge base update --> Invalidate retrieval + completion caches
  On model change --> Invalidate completion cache
  Safety net --> TTL on all cache entries
  Thundering herd --> Stampede protection (locking/coalescing)
```

**Anti-pattern:** Global cache shared across tenants. This is a data leakage vector. Always scope cache keys by tenant. (Q11, Q53)

**Anti-pattern:** Long TTLs without invalidation. Knowledge base updates make cached answers stale. (Q11, Q56)

**Anti-pattern:** Caching PII-containing responses. This violates data minimization principles. (Q11, Q18)

See: [06-memory-and-conversation.md](./06-memory-and-conversation.md), [05-safety-and-security.md](./05-safety-and-security.md)

---

## 8. Evaluation Strategy by Project Phase

| Phase | Strategy | Metrics | Source |
|-------|----------|---------|--------|
| **Prototype** | Manual spot-checking, 20-50 test queries | Subjective quality, basic latency | Q6 |
| **Pre-production** | Golden test set (100-500 queries), automated eval | Recall@k, MRR, nDCG, groundedness | Q6, Q24 |
| **Production launch** | Golden set regression + canary deploy + monitoring | All metrics + user feedback signals | Q6, Q24, Q45 |
| **Steady state** | Continuous monitoring + drift detection + periodic human eval | Latency percentiles, error rates, token cost, cache hits, retrieval quality, user feedback | Q33, Q45 |
| **Model/index updates** | Full eval suite + canary + rollback capability | Regression on golden set, human eval sample | Q24, Q40 |

**Key principle (Q6):** Combine automated metrics, regression testing on golden sets, targeted human evaluation, and LLM-as-judge used cautiously (aware of position bias, verbosity bias, self-preference).

**Anti-pattern:** Relying solely on LLM-as-judge. It has systematic biases and cannot replace golden test sets. (Q6)

**Anti-pattern:** Only evaluating end-to-end. Separate retrieval metrics from generation metrics to diagnose failure modes. (Q6)

See: [07-evaluation-and-monitoring.md](./07-evaluation-and-monitoring.md)

---

## Quick Reference: Technology Selection Summary

| Component | Path of least resistance | When to upgrade |
|-----------|-------------------------|-----------------|
| **Embedding model** | Local open-source (nomic, BGE, E5) | When domain eval shows API model is significantly better |
| **Vector DB** | Embedded (LanceDB, ChromaDB) | When you exceed single-node scale or need managed multi-tenancy |
| **Reranker** | None (start without) | When retrieval precision is measured as a bottleneck |
| **Knowledge graph** | None (start without) | When relationship queries or graph expansion would improve recall |
| **LLM** | API (Claude, GPT-4) | When latency, cost, or data residency demands self-hosted |
| **Orchestration** | Direct SDK calls | When multi-step agent workflows justify a framework (LangChain, etc.) |
| **Caching** | Embedding + retrieval cache | When repeated query patterns make completion caching cost-effective |
| **Monitoring** | Structured logging + basic metrics | When you need distributed tracing across services (OpenTelemetry) |

**Guiding principle (Q12):** Avoid deep lock-in to any one framework by using adapter patterns or thin abstraction layers. The intelligence should live in your prompts and tool definitions, not in framework-specific glue code.
