# RAG System Architecture

A comprehensive reference for designing production-grade Retrieval-Augmented Generation systems, distilled from engineering assessment questions spanning LLM features, backend system design, and MLOps.

---

## End-to-End Pipeline

```
                        INGESTION PIPELINE (offline/async)
                        ================================

  Source Documents ──> Fetching/Parsing ──> Cleaning ──> Chunking
  (PDF, HTML, MD,      (per-format         (PII,         (semantic,
   wikis, APIs)         parsers)            noise)        hierarchical)
        │                                                      │
        │                                                      v
        │                                            Contextual Enrichment
        │                                            (context prefix per chunk)
        │                                                      │
        │                                                      v
        │                                              Embedding Generation
        │                                              (batch, local or API)
        │                                                      │
        │                                                      v
        │                                              Indexing + Metadata
        │                                              (vector DB + FTS + graph)
        │                                              with ACL/tenant tags
        v
  ┌──────────────────────────────────────────────────────────────────┐
  │                     KNOWLEDGE STORE                              │
  │  Source of Truth: Markdown/files  ──rebuild──>  Derived indices  │
  │  Vector index (HNSW/IVF) │ FTS index (BM25) │ Knowledge graph   │
  └──────────────────────────────────────────────────────────────────┘
        │                         │                        │
        v                         v                        v
                        QUERY PIPELINE (online/sync)
                        ============================

  User Query ──> Auth + Tenant Resolution ──> [Query Rewrite (optional)]
        │
        v
  Embedding Generation (cached)
        │
        v
  Hybrid Retrieval ──────────────────────────────> Graph Expansion
  (vector + BM25,                                  (1-hop neighbors,
   metadata pre-filtering,                          score penalty)
   ACL enforcement)                                      │
        │                                                │
        v                                                v
  Reciprocal Rank Fusion (RRF)  <────────────────────────┘
        │
        v
  Reranking (optional, cross-encoder)
        │
        v
  Prompt Assembly
  (system prompt + retrieved context as DATA + conversation history)
        │
        v
  LLM Generation (with citations)
        │
        v
  Output Validation + PII Redaction + Audit Logging
        │
        v
  Response (answer + citations + relevance scores + timings + versions)
```

---

## Component Responsibilities

### Ingestion Layer
**Purpose:** Transform raw documents into searchable, embeddable chunks with metadata.

- **Fetching/Parsing (Q2):** Format-specific parsers for PDF, HTML, markdown, wikis. Each format has its own extraction challenges (ligatures, encoding, layout).
- **Cleaning:** Remove noise, strip PII before it enters the knowledge store (Q18), handle encoding issues.
- **Chunking:** Split documents into appropriately sized segments. Strategy depends on document structure. (Q2, Q17)
- **Contextual Enrichment:** Add context prefixes at indexing time -- e.g., "This passage is from Chapter 3 of Document X, discussing topic Y." This yields significant retrieval improvement when combined with BM25. (Q2)
- **Embedding:** Convert chunks to dense vectors. Model choice matters enormously. (Q3)
- **Indexing:** Store vectors + metadata (ACL tags, tenant IDs, source info) in vector DB. Build FTS index for keyword search. Build knowledge graph from entity relationships. (Q2, Q31)

### Retrieval Layer
**Purpose:** Given a query, find the most relevant chunks from the knowledge store.

- **Hybrid Search (Q2):** Combine vector similarity (semantic) with BM25 (keyword) for robust retrieval.
- **Metadata Pre-Filtering (Q31):** Enforce ACL/tenant isolation BEFORE retrieval, not after. Critical security boundary.
- **Reciprocal Rank Fusion:** Merge results from multiple retrieval methods. (Q2)
- **Graph Expansion:** After initial retrieval, traverse knowledge graph to find related chunks.
- **Reranking (Q7):** Optional second-stage scoring with cross-encoders. Use when precision is a bottleneck.

### Generation Layer
**Purpose:** Produce a grounded, cited answer from retrieved context.

- **Prompt Assembly (Q13):** Structure with objective, constraints, context (retrieved docs as DATA), examples, output format.
- **Instruction Hierarchy (Q19):** System > Developer > User > Retrieved content. Non-negotiable rules in system messages.
- **Citation (Q9):** Require inline citations to retrieved sources. This reduces hallucination and enables verification.
- **Streaming (Q57):** Stream LLM output to meet time-to-first-token SLA while full generation continues.

### Cross-Cutting Concerns
- **PII Handling (Q18):** Redact before data reaches the model, filter on input/output, mask in logs.
- **Audit Logging (Q2, Q46):** Structured logs with request IDs, timing breakdowns, model/index versions. Never log raw prompts in plaintext.
- **Rate Limiting (Q42, Q58):** Token-based quotas per tenant, not just request counts.
- **Observability (Q47):** Distributed tracing (OpenTelemetry) across the full pipeline.

---

## Decision Framework: RAG vs Fine-Tuning vs Hybrid

From Q1 and Q21, the decision depends on what you are optimizing for:

| Need | Best approach | Why |
|------|-------------|-----|
| Up-to-date factual answers | **RAG** | Knowledge base can be updated without retraining |
| Citations and traceability | **RAG** | Retrieved sources are citable; model weights are not |
| Reduce hallucination on facts | **RAG** | Grounds answers in retrieved evidence |
| Consistent tone/style | **Fine-tuning** | Bakes behavioral patterns into weights |
| Domain phrasing and terminology | **Fine-tuning** | Learns domain-specific language patterns |
| Classification tasks | **Fine-tuning** | Learns decision boundaries from examples |
| Both facts AND behavior | **Hybrid** | Fine-tune for behavior, RAG for knowledge |

**Key insight (Q1):** RAG retrieves documents at query time and feeds them into the LLM's context. It does NOT fine-tune the model per query. It does NOT guarantee zero hallucinations. It DOES require a retrieval system.

**Anti-patterns to avoid:**
- Fine-tuning on factual corpora expecting the model to stay current (Q1) -- knowledge becomes stale immediately
- Using RAG alone when you need consistent style (Q21) -- retrieval augments knowledge, not behavior
- Claiming RAG+fine-tuning together is "always necessary" (Q1) -- combining both adds cost and complexity that may not be justified
- Relying on prompt engineering alone for production consistency (Q21) -- brittle across thousands of queries

---

## When to Use Agents vs Simple Tool-Calling

From Q4 and Q12:

### Simple Tool-Calling
A single-shot decision to invoke a function. The LLM decides which tool to call, calls it once, and incorporates the result.

**Use when:**
- Single retrieval step answers the question
- No multi-step reasoning required
- Read-only operations

### Agent Loop
An iterative cycle: plan, act (invoke tools), observe results, refine approach. Maintains state and memory across steps.

**Use when:**
- Multiple retrieval steps from different angles
- Reasoning across retrieved results
- Write operations or side effects
- Dynamic decision-making based on intermediate results

**Agent risks and mitigations (Q4):**

| Risk | Mitigation |
|------|-----------|
| Runaway loops | Max-step limits, timeouts |
| Tool-call hallucination | Strict JSON schemas, validation of all arguments |
| Unsafe/unintended actions | Tool allowlists, sandboxed execution |
| Cost explosion | Token budgets, turn count limits |
| State corruption | Idempotency keys on state-changing operations (Q54) |

**Anti-pattern (Q4):** Claiming agents and tool-calling are identical. They differ fundamentally in statefulness and loop behavior.

**Anti-pattern (Q4):** No runtime safeguards on agents because "the schema constrains inputs." LLMs can hallucinate tool names, arguments, or call tools unnecessarily.

---

## Architecture Patterns

### Modular Architecture (Q2, Q12)

Separate concerns into independently deployable, testable components:

```
┌─────────────┐  ┌──────────────┐  ┌─────────────┐  ┌────────────┐
│  Ingestion   │  │  Retrieval   │  │  Generation  │  │  Serving   │
│  Service     │  │  Service     │  │  Service     │  │  API       │
│              │  │              │  │              │  │            │
│ - Parse      │  │ - Vector     │  │ - Prompt     │  │ - Auth     │
│ - Chunk      │  │ - BM25       │  │ - LLM call   │  │ - Rate     │
│ - Embed      │  │ - Graph      │  │ - Citation   │  │   limit    │
│ - Index      │  │ - Rerank     │  │ - Validate   │  │ - Stream   │
└─────────────┘  └──────────────┘  └─────────────┘  └────────────┘
```

**Key principle (Q12):** Avoid deep lock-in to any one framework. Use adapter patterns or thin abstraction layers. LangChain for orchestration, HF Transformers for local models, direct SDK for hosted APIs -- each has its sweet spot.

### Layered Prompt Architecture (Q13, Q19)

Assemble the system prompt from modular sections based on interaction needs:

```
┌────────────────────────────────────────────┐
│ SYSTEM MESSAGE (highest priority)          │
│ - Core constraints (non-negotiable)        │
│ - Safety rules                             │
│ - Output format specification              │
├────────────────────────────────────────────┤
│ DEVELOPER MESSAGE                          │
│ - Business logic                           │
│ - Retrieved context (marked as DATA)       │
│ - Behavioral instructions                  │
├────────────────────────────────────────────┤
│ USER MESSAGE (lowest priority)             │
│ - User query                               │
│ - Conversation history                     │
└────────────────────────────────────────────┘
```

**Critical (Q19):** This hierarchy ensures user input or retrieved content cannot override system-level constraints. Retrieved documents must be treated as untrusted data, not as instructions.

---

## API Design for RAG Endpoints

From Q52, a production `/ask` endpoint should include:

**Request:**
- Auth/tenant header
- Query string
- Optional conversation context (not mandatory)
- Streaming flag
- Trace ID for observability

**Response:**
- Generated answer
- Source citations with relevance scores
- Processing timings (retrieval latency, generation latency)
- Model version and index version metadata
- Structured error responses with retry guidance

**Rate limiting:** Per-tenant, token-aware (Q42, Q58)

**Anti-patterns (Q52):**
- Returning 200 for all responses with success/failure in the JSON body -- use proper HTTP status codes
- Forcing mandatory conversation history on every request
- Exposing internal pipeline state (embeddings, full prompt) in responses
- Splitting sources into a separate endpoint (creates race conditions, extra round trips)

---

## Cross-References

- Ingestion and indexing details: [02-ingestion-and-indexing.md](./02-ingestion-and-indexing.md)
- Retrieval and ranking strategies: [03-retrieval-and-ranking.md](./03-retrieval-and-ranking.md)
- Prompt engineering: [04-prompt-engineering.md](./04-prompt-engineering.md)
- Safety and security: [05-safety-and-security.md](./05-safety-and-security.md)
- Deployment and operations: [08-deployment-and-operations.md](./08-deployment-and-operations.md)
- Decision framework: [00-decision-framework.md](./00-decision-framework.md)
