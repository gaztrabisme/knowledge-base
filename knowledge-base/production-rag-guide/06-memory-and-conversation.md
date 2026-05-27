# Memory & Conversation Management

LLMs are stateless -- every request starts fresh. Memory is an engineering problem: how do you give the model enough context to be useful without exceeding budgets, leaking data, or drowning signal in noise?

---

## Short-Term vs Long-Term Memory

From Q10: A production system needs both, with clear boundaries.

### Short-Term Memory (Context Window)

**What:** Recent conversation turns maintained within the current context window.

**Management strategies:**
- Keep the last N turns of conversation in the message list
- When approaching the token budget, summarize older turns
- Inject summarized context as a system/developer message

**Tradeoffs:**
```
More context = better continuity BUT higher cost + latency + noise
Less context = cheaper + faster BUT model forgets important details

Sweet spot: enough recent turns for coherent conversation,
with summaries of older material
```

### Long-Term Memory (Persistent Store)

**What:** Stored memories, insights, conversation archives that persist across sessions.

**Management strategies (Q10):**
- Per-tenant/per-user memory store with strict namespace isolation
- Access control lists on all memory operations
- Encryption at rest for all stored memories
- Retention and expiration policies to limit data exposure
- Audit logs for memory access

**Anti-pattern (Q10):** "Use a global vector store for all conversation memories and rely on embedding similarity to naturally retrieve only relevant memories for the current user." Embedding similarity is NOT a security boundary. Similar conversations across users could surface cross-user data.

**Anti-pattern (Q10):** "Always send the entire conversation history in every request." Impractical and costly for long conversations. A separate LLM instance per user is massively over-engineered.

**Anti-pattern (Q10):** "Fine-tune a per-user model checkpoint after each conversation." Absurdly expensive, slow, and operationally unmanageable.

---

## Conversation History Management

### Sliding Window

The simplest approach: keep the last N messages.

```python
def sliding_window(messages: list, max_messages: int = 20) -> list:
    """Keep the system prompt + last N messages."""
    system_msgs = [m for m in messages if m["role"] == "system"]
    conversation = [m for m in messages if m["role"] != "system"]
    return system_msgs + conversation[-max_messages:]
```

**Limitation:** Abrupt context loss. The model has zero memory of anything beyond the window.

### Summarization / Compaction

From Q10 and the project's architecture: Summarize older turns to preserve essential context while reducing token count.

```
Conversation Step 1-5:  [FULL — recent, high fidelity]
Conversation Step 6-10: [COMPRESSED — summarized by Haiku]
Conversation Step 11+:  [PLACEHOLDER — "Earlier, you discussed X"]
```

### The Fidelity Scoring Pattern

From the project's memory system, assign fidelity tiers based on recency and importance:

```
Score = 2^(-age_minutes / 30) * token_factor

Tiers:
  FULL:        Score > 0.7  → Include complete messages
  COMPRESSED:  Score 0.3-0.7 → Summarize with a fast model
  PLACEHOLDER: Score < 0.3  → Brief reference only
```

**Why this works:** Recent messages get full fidelity (the model needs them for coherent continuation). Older messages get progressively compressed. Very old messages become brief references that the model can use as retrieval cues.

### Compaction Implementation

```python
async def compact_messages(steps: list[ConversationStep],
                          token_budget: int) -> list:
    """Compact conversation history to fit within token budget.

    Triggered when history reaches >= 10 ConversationSteps.
    """
    total_tokens = sum(s.token_count for s in steps)

    if total_tokens <= token_budget:
        return steps  # No compaction needed

    scored_steps = [(s, fidelity_score(s)) for s in steps]

    result = []
    for step, score in scored_steps:
        if score > 0.7:
            result.append(step)  # FULL
        elif score > 0.3:
            summary = await summarize_turns([step])  # COMPRESSED
            result.append(inject_summary(summary))
        else:
            result.append(placeholder_step(step))  # PLACEHOLDER

    return result
```

---

## Session Boundaries and Archival

### Session Detection

From the project's architecture: Sessions are detected by conversation gaps (e.g., > 2 hours of silence).

```python
def detect_session_boundary(last_message_time: datetime,
                           now: datetime,
                           gap_threshold_hours: float = 2.0) -> bool:
    """A gap longer than threshold indicates a new session."""
    gap = (now - last_message_time).total_seconds() / 3600
    return gap > gap_threshold_hours
```

### Session Archival

When a session ends:
1. Summarize the full session conversation
2. Save as a knowledge base note (e.g., `conversations/YYYY-MM/session-{uuid}.md`)
3. Include YAML frontmatter (date, topics, key insights)
4. The archived session becomes searchable via the knowledge retriever
5. Clear the active conversation context

**This closes the loop:** Past conversations feed into the knowledge base, which feeds future retrieval, creating a growing memory.

---

## Multi-Turn Context Preservation

### Typed Memory Steps

From the project's architecture: Instead of a flat message list, use typed steps that carry metadata.

```
ConversationStep:   User message + assistant response
RetrievalStep:      Search query + retrieved chunks + relevance scores
ReflectionStep:     Agent's internal reasoning
InsightStep:        Captured insight with evidence
PlanningStep:       Action plan with reasoning

Each step carries:
  - timestamp
  - token_count
  - metadata (source, confidence, etc.)
```

**Why typed steps matter:** Intelligent pruning. When compacting, you can make smarter decisions -- e.g., always keep InsightSteps but compress routine ConversationSteps.

### Passive Context Injection

From the project's architecture: Before generating a response, inject relevant memories without explicit retrieval:

```python
async def build_passive_context(user_message: str) -> str:
    """Embed user message → query retriever → filter by threshold.

    Returns a 'You recall...' context block for the system prompt.
    """
    results = await retriever.search(
        query=user_message,
        config=retrieval_config
    )

    relevant = [r for r in results if r.score > threshold]

    if not relevant:
        return ""

    context = "You recall the following relevant information:\n"
    for r in relevant:
        context += f"- {r.chunk.text}\n"

    return context
```

This creates the feeling of a companion that naturally remembers relevant context, rather than explicitly searching on every query.

---

## Caching Strategies

From Q11 and Q56: Multi-layer caching is essential for performance and cost.

### Layer 1: Embedding Cache

```python
# Cache computed embeddings for repeated queries
embedding_cache = {}  # Or Redis, with TTL

def get_embedding(text: str) -> list[float]:
    cache_key = hash(text)
    if cache_key in embedding_cache:
        return embedding_cache[cache_key]

    embedding = model.encode(text)
    embedding_cache[cache_key] = embedding
    return embedding
```

### Layer 2: Retrieval Result Cache

```python
# Cache retrieval results with versioned keys
def retrieval_cache_key(query: str, index_version: str, model_version: str) -> str:
    query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
    return f"retrieval:{query_hash}:idx_{index_version}:model_{model_version}"
```

### Layer 3: Completion Cache (Q11)

```python
# Cache LLM completions — with privacy awareness
def should_cache_completion(query: str, response: str) -> bool:
    """Never cache responses containing sensitive data."""
    if contains_pii(query) or contains_pii(response):
        return False
    return True

def completion_cache_key(query: str, context_hash: str,
                        model_version: str, index_version: str) -> str:
    return f"completion:{hash(query)}:{context_hash}:{model_version}:{index_version}"
```

### Cache Invalidation (Q11, Q56)

```
Trigger: Knowledge base update (reindex)
  → Invalidate retrieval cache (index version changed)
  → Invalidate completion cache (answers may be stale)
  → Embedding cache remains valid (query embeddings unchanged)

Trigger: Model version change
  → Invalidate completion cache
  → Retrieval cache may remain valid (if embedding model unchanged)

Safety net: TTL on all entries
  → Embeddings: long TTL (model rarely changes)
  → Retrieval: medium TTL (index updates are known events)
  → Completions: shorter TTL (answers should be fresh)
```

### Stampede Protection (Q56)

When a popular cache key expires, many concurrent requests may try to regenerate it simultaneously (thundering herd):

```python
# Request coalescing: only one request regenerates, others wait
async def get_or_generate(cache_key: str, generate_fn):
    cached = cache.get(cache_key)
    if cached:
        return cached

    # Acquire lock for this key
    async with cache.lock(cache_key, timeout=30):
        # Double-check after acquiring lock
        cached = cache.get(cache_key)
        if cached:
            return cached

        result = await generate_fn()
        cache.set(cache_key, result, ttl=TTL)
        return result
```

### Anti-Patterns (Q11, Q56)

| Anti-pattern | Why it fails |
|-------------|-------------|
| Global cache shared across tenants | Data leakage vector — tenant A sees tenant B's cached answers (Q11) |
| Long TTLs (30+ days) without invalidation | Stale answers to factual queries after knowledge base updates (Q11) |
| Caching PII-containing responses | Violates data minimization, compliance risk (Q11, Q18) |
| Only caching completions, not embeddings/retrieval | Missing easier wins at cheaper layers (Q11) |
| Never caching completions because "LLMs are non-deterministic" | At temperature=0 with deterministic settings, completion caching is valuable (Q11) |
| Short global TTL (60s) as sole invalidation strategy | Either serves stale data during TTL or has collapsed cache hit rates (Q56) |
| Write-through cache that regenerates answers during reindex | Cannot determine all queries referencing a document; enormously expensive (Q56) |

---

## Cache Invalidation on Knowledge Base Changes

From Q56: The specific problem of knowledge base updates making cached answers stale.

### Versioned Cache Keys (The Recommended Pattern)

```
Cache key structure:
  {query_hash}:{index_version}:{model_version}

When index version changes (reindex):
  All old cache keys automatically become stale
  New requests generate fresh entries with the new version
  No explicit invalidation sweep needed

Combined with TTLs:
  Even if version tracking fails, entries expire naturally
```

**Why this works (Q56):** Versioned keys naturally invalidate on reindex or model changes. TTLs provide a safety net. Stampede protection prevents thundering herd when many keys expire simultaneously.

---

## Data Isolation Patterns

From Q10 and Q53: Multi-tenant memory systems must prevent cross-tenant data leakage.

### Per-Tenant Isolation Requirements (Q10, Q53)

| Layer | Isolation mechanism |
|-------|-------------------|
| **Conversation history** | Per-tenant memory store with namespace isolation |
| **Long-term memory** | Separate collections/namespaces per tenant in vector DB |
| **Cache** | Tenant-scoped cache keys (`{tenant_id}:{query_hash}:...`) |
| **Logs** | Tenant-tagged log pipelines with access controls |
| **Encryption** | Tenant-scoped encryption keys |
| **Access control** | RBAC with ACLs on all data paths |
| **Audit** | Audit logs for all cross-tenant data access attempts |
| **Quotas** | Per-tenant limits on storage and compute |

### Anti-Patterns (Q10, Q53)

| Anti-pattern | Why it fails |
|-------------|-------------|
| Single shared table with tenant_id column, no other controls | Single query bug leaks all tenants' data (Q53) |
| Separate infrastructure stack per tenant | Massively over-engineered for logical isolation (Q53) |
| Post-retrieval filtering for tenant isolation | Vector DB retrieves cross-tenant documents first — data exposure (Q53) |
| Relying on embedding similarity for tenant isolation | Not a security boundary — similar conversations across tenants match (Q10) |
| Disabling caching entirely to prevent leakage | Sacrifices performance unnecessarily; tenant-scoped keys solve the problem (Q53) |

---

## Cross-References

- Caching strategy decisions: [00-decision-framework.md](./00-decision-framework.md)
- Privacy-aware logging: [05-safety-and-security.md](./05-safety-and-security.md)
- Retrieval that feeds context: [03-retrieval-and-ranking.md](./03-retrieval-and-ranking.md)
- Monitoring cache performance: [07-evaluation-and-monitoring.md](./07-evaluation-and-monitoring.md)
