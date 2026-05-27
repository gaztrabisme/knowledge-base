# Evaluation & Monitoring

The difference between a demo and a production system is whether you can answer the question: "Is it working well right now, and is it getting better or worse over time?" This document covers the full evaluation and monitoring surface for RAG systems.

---

## Retrieval Quality Metrics

From Q6: Separate retrieval evaluation from generation evaluation. If retrieval fails, generation cannot succeed -- but a good retrieval score with bad generation tells you exactly where to focus.

### Core Metrics

| Metric | Formula | What it measures | Interpretation |
|--------|---------|-----------------|----------------|
| **Recall@k** | \|relevant ∩ top_k\| / \|relevant\| | Did we find all the relevant chunks? | Low recall = missing relevant content |
| **Precision@k** | \|relevant ∩ top_k\| / k | How clean are the results? | Low precision = too much noise in context |
| **MRR** | (1/\|Q\|) * sum(1/rank_i) | How high is the first relevant result? | Low MRR = relevant results buried deep |
| **nDCG@k** | DCG@k / IDCG@k | Overall ranking quality | Low nDCG = poor ordering of results |

### When to Use Each

```
Building retrieval system → Recall@k (are we finding what exists?)
Optimizing context quality → Precision@k (are we sending junk to the LLM?)
Single-answer questions → MRR (is the first result the right one?)
Ranked results displayed to users → nDCG@k (full ranking quality)
```

### Anti-Patterns (Q6)

- **BLEU/ROUGE for retrieval evaluation:** These are surface-level token overlap metrics. A paraphrased correct answer scores low. Poorly suited for RAG.
- **Exact-match for retrieval evaluation:** Too strict. Relevant documents may not exactly match the query terms.
- **Skipping retrieval evaluation because end-to-end answers look good:** The LLM may be improvising. When it stops improvising (different query pattern), retrieval failures surface.

---

## Generation Quality Metrics

From Q6: Evaluate what the LLM produces, not just what it retrieves.

### Core Dimensions

| Dimension | What it measures | How to evaluate |
|-----------|-----------------|-----------------|
| **Groundedness/Faithfulness** | Is every claim supported by retrieved sources? | Check each claim against cited sources |
| **Factual correctness** | Is the answer actually correct? | Compare against golden reference answers |
| **Relevance** | Does the answer address the question asked? | Judge whether the response is on-topic |
| **Refusal quality** | Does it abstain when it should? | Test with questions outside the knowledge base |
| **Citation accuracy** | Do citations point to the right sources? | Verify each [Source N] reference |

### Evaluation Approaches

```
Automated metrics:
  - JSON schema validation (structured output conformance)
  - Citation verification (do cited sources exist and contain the claim?)
  - String matching against known answers (for extractive tasks)

LLM-as-judge (use cautiously):
  - Score groundedness, relevance, completeness on a rubric
  - Be aware of biases: position bias, verbosity bias, self-preference

Human evaluation:
  - Sample-based review of outputs
  - Catches quality issues automated metrics miss (tone, coherence, nuance)
  - Essential for model promotions (Q24)
```

---

## LLM-as-Judge Patterns and Limitations

From Q6: LLM-as-judge is a useful tool but NOT a replacement for golden test sets or human evaluation.

### How to Use It Well

```python
JUDGE_PROMPT = """
Rate the following answer on a scale of 1-5 for each criterion.

QUESTION: {question}
RETRIEVED SOURCES: {sources}
ANSWER: {answer}

Criteria:
1. Groundedness: Is every claim supported by the sources? (1=fabricated, 5=fully grounded)
2. Relevance: Does the answer address the question? (1=off-topic, 5=directly addresses)
3. Completeness: Does it cover the key points from the sources? (1=missing most, 5=comprehensive)

For each criterion, first explain your reasoning, then give the score.

Output as JSON: {"groundedness": {"reasoning": "...", "score": N}, ...}
"""
```

### Known Biases (Q6)

| Bias | Description | Mitigation |
|------|------------|------------|
| **Position bias** | Prefers options presented first or last | Randomize presentation order |
| **Verbosity bias** | Prefers longer, more detailed responses | Control for length in evaluation |
| **Self-preference** | Prefers outputs from the same model family | Use a different model as judge |
| **Sycophancy** | Reluctant to give low scores | Use strict rubrics with examples of each score level |

**Critical (Q6):** LLM-as-judge "correlates highly with human judgment" does NOT mean it is sufficient alone. It should complement, not replace, golden test sets and human review.

---

## Golden Test Set Construction and Maintenance

From Q6, Q24, Q33: The foundation of systematic evaluation.

### Building the Test Set

```
1. Collect queries
   - Sample real user queries (anonymized)
   - Add edge cases identified during development
   - Include adversarial/tricky queries
   - Cover all topic areas in the knowledge base

2. Annotate expected results
   - For retrieval: which chunks/documents should be retrieved
   - For generation: what the answer should contain (not exact text)
   - For refusal: which queries should result in abstention

3. Categorize by difficulty
   - Easy: single relevant chunk, direct answer
   - Medium: multiple relevant chunks, synthesis needed
   - Hard: requires multi-hop reasoning, ambiguous queries

4. Include negative examples
   - Queries outside the knowledge base scope
   - Queries that look relevant but should trigger abstention
   - Adversarial/injection attempts

5. Size guideline
   - Minimum: 100 queries for meaningful signal
   - Recommended: 200-500 for production systems
   - Update as knowledge base grows
```

### Maintenance

- **Version the test set** alongside the codebase
- **Update when knowledge base changes** (new topics, restructured content)
- **Review quarterly** for staleness
- **Track test set coverage** against the full knowledge base

### Usage in CI/CD (Q48)

```
CI Pipeline:
  1. Lint + unit tests                  (fast, cheap)
  2. Build container image              (medium)
  3. Security scans                     (medium)
  4. Deploy to staging                  (medium)
  5. Run golden test set against staging (slow, comprehensive)
     → Quality gates: recall@10 > 0.8, MRR > 0.7
  6. Canary deploy to production        (slow, careful)
  7. Promote to full production         (slow)
```

---

## Data Drift and Concept Drift Detection

From Q33: Over months of operation, the inputs your system receives and the relationship between inputs and correct outputs can shift.

### Types of Drift

| Type | What changes | Example | Detection signal |
|------|-------------|---------|-----------------|
| **Data drift** | Input distribution | Users start asking about new topics | Embedding distribution shifts, new clusters |
| **Concept drift** | Input-output relationship | Correct answers change (regulations updated) | Declining quality scores, user complaints |
| **Index staleness** | Knowledge base gaps | New products/topics not yet indexed | Retrieval miss rate increases, abstention rate rises |

### Multi-Signal Detection (Q33)

```
Signal 1: Input distribution monitoring
  - Track embedding distribution over time (centroid shift, variance change)
  - Detect new query clusters that don't match known patterns

Signal 2: Retrieval quality signals
  - Monitor retrieval hit rate (are queries finding relevant chunks?)
  - Track average relevance scores over time
  - Alert when retrieval confidence drops

Signal 3: User feedback and error trends
  - Thumbs up/down, explicit corrections
  - Error rate trends (parsing failures, timeout increases)
  - Support ticket volume related to AI quality

Signal 4: Quality metrics with thresholds
  - Run golden test set periodically (weekly or on significant changes)
  - Define thresholds: alert when recall@10 drops below 0.75
  - Automated investigation trigger when thresholds are breached
```

### Anti-Patterns (Q33)

| Anti-pattern | Why it fails |
|-------------|-------------|
| "LLM providers have built-in drift detection" | They do not. This responsibility falls on the platform team. |
| "Concept drift isn't a concern for LLM systems" | The retrieval corpus, user behavior, and domain knowledge can all shift. |
| "Run a nightly KS test on raw token distributions, auto-retrain on p < 0.05" | Raw token distributions are noisy for LLM systems; auto-retraining without human review is reckless. |
| "Re-embed a golden test set periodically to detect embedding model drift" | If using the same model version, re-embedding produces identical results. The concern is query/data shift, not model determinism. |

---

## Production Monitoring Signals

From Q45 and Q47: What to monitor for a running RAG service.

### The Complete Monitoring Dashboard

| Category | Metrics | Why | Source |
|----------|---------|-----|--------|
| **Latency** | P50, P95, P99 (NOT average) | Averages hide tail latency problems | Q45 |
| **Errors** | Error rate by type (LLM, retrieval, parsing, timeout) | Distinguish failure modes | Q45 |
| **Tokens** | Input/output tokens per request, total daily usage | Cost tracking and anomaly detection | Q45 |
| **Cost** | Cost per request, daily/monthly spend | Budget management | Q45 |
| **Cache** | Hit rate by layer (embedding, retrieval, completion) | Optimization signal | Q45 |
| **Retrieval** | Hit rate, average relevance score, empty result rate | Quality signal for the retrieval layer | Q45 |
| **Quality** | Groundedness proxy, abstention rate, citation accuracy | Quality signal for the generation layer | Q45 |
| **User feedback** | Thumbs up/down, explicit corrections, complaints | Ground truth from users | Q45 |

### Anti-Patterns (Q45)

| Anti-pattern | Why it fails |
|-------------|-------------|
| "Monitor only GPU utilization and memory" | Misses application-level quality signals entirely |
| "Standard SRE golden signals are sufficient" | LLMs need token cost, retrieval quality, and groundedness monitoring |
| "Model perplexity and BLEU/ROUGE daily" | Offline metrics don't capture real-time production behavior |
| "Only token throughput and cost per request" | Dismisses output quality monitoring |
| "Average latency instead of percentiles" | Averages hide tail latency that affects real users |

---

## User Feedback Integration

### Feedback Collection

```
Explicit:
  - Thumbs up/down on responses
  - "Was this helpful?" prompt
  - Correction submissions
  - Report buttons for bad answers

Implicit:
  - Follow-up questions (may indicate insufficient answer)
  - Session length and engagement
  - Reformulated queries (may indicate failed retrieval)
  - Copy/paste behavior (may indicate useful answer)
```

### Feedback Loop

```
User feedback → Tagged in logging system with trace_id
  → Aggregated into quality dashboards
  → Negative feedback triggers:
     a. Manual review of the interaction
     b. Potential addition to golden test set
     c. Knowledge base update if content gap identified
     d. Retrieval tuning if relevant content exists but wasn't found
```

---

## Alerting and Quality Thresholds

### Threshold Design

```yaml
alerts:
  # Operational
  latency_p95_ms:
    warning: 2000
    critical: 5000
  error_rate_percent:
    warning: 2
    critical: 5

  # Quality
  retrieval_empty_result_rate:
    warning: 0.15  # 15% of queries return no results
    critical: 0.30
  golden_set_recall_at_10:
    warning: 0.75  # Below 75% recall
    critical: 0.65
  user_negative_feedback_rate:
    warning: 0.20
    critical: 0.35

  # Cost
  daily_token_spend:
    warning: budget * 0.8
    critical: budget * 1.0
```

### Escalation Path

```
Warning threshold breached:
  → Slack notification to on-call
  → Investigate within 4 hours

Critical threshold breached:
  → PagerDuty alert
  → Investigate immediately
  → Consider automated rollback if deployment-correlated
```

---

## Distributed Tracing for RAG Pipelines

From Q47: Correlating metrics, logs, and traces across multiple services.

### The Correct Pattern: OpenTelemetry

```
Trace: One end-to-end user request
  ├── Span: API Gateway (auth, rate limiting)
  │     latency: 15ms, tenant_id: abc
  ├── Span: Embedding Generation
  │     latency: 50ms, cache_hit: true
  ├── Span: Vector Search
  │     latency: 120ms, results: 20, avg_score: 0.82
  ├── Span: BM25 Search
  │     latency: 30ms, results: 15
  ├── Span: RRF Fusion
  │     latency: 5ms, fused_results: 25
  ├── Span: Reranking
  │     latency: 180ms, input: 25, output: 5
  ├── Span: LLM Generation
  │     latency: 890ms, model: claude-sonnet, tokens_in: 2500, tokens_out: 350
  └── Span: Post-processing
        latency: 10ms, pii_detected: false
```

### Key Properties of Each Span

```python
# Every span should include:
span.set_attribute("component", "retrieval")       # Which component
span.set_attribute("model_version", "v12")          # Model versions
span.set_attribute("index_version", "v3")           # Index versions
span.set_attribute("cache_hit", True)               # Cache performance
span.set_attribute("result_count", 20)              # Result metrics

# Every trace should include:
trace.set_attribute("tenant_id", "abc")             # Tenant context
trace.set_attribute("trace_id", "xyz")              # Correlation ID
```

### Why Other Approaches Fall Short (Q47)

| Approach | Limitation |
|----------|-----------|
| Request ID in logs only | No parent-child span relationships, no trace visualization |
| Service mesh (Istio/Linkerd) | Only captures network traffic, not application logic (vector queries, reranking) |
| Timestamp correlation | Unreliable with clock skew, fails at high throughput |
| Commercial APM auto-instrumentation only | Often can't trace external LLM API calls or custom retrieval logic |

**Best practice (Q47):** Use OpenTelemetry for instrumentation (open standard, vendor-neutral), export to your preferred backend (Jaeger, Grafana Tempo, Datadog). Propagate trace and span IDs across ALL components.

---

## Logging Strategy

From Q46: Balance observability with privacy.

### What to Log

```
Always log (structured metadata):
  - Request ID / Trace ID
  - Timestamp
  - Model version, index version
  - Timing breakdowns (embedding, retrieval, reranking, generation)
  - Token counts (input, output)
  - Retrieval statistics (result count, relevance scores, cache hit)
  - Error details (type, message — not stack traces with user data)

Sample log (detailed, low rate):
  - Masked/hashed prompts (for debugging specific issues)
  - Response quality scores

Never log:
  - Raw user prompts in plaintext
  - Raw LLM completions in plaintext
  - PII in any form
```

### Anti-Patterns (Q46)

| Anti-pattern | Why it fails |
|-------------|-------------|
| Log all prompts and completions in full | PII leakage, compliance violation (GDPR, HIPAA) |
| Log nothing except infrastructure metrics | Cannot debug quality issues, retrieval problems, or hallucinations |
| PII detection model on error-only logs | Survivorship bias — misses quality issues in successful-looking requests |
| 24-hour unredacted hot tier for debugging | Still creates compliance liability; adds operational complexity |

---

## Model Promotion Process

From Q24: The systematic process for promoting a new model to production.

### The Full Checklist

```
1. Task-specific benchmark
   → Did the target metric improve? (e.g., +12% on task benchmark)

2. Golden test set regression
   → No regressions on critical edge cases?
   → All quality thresholds still met?

3. Human evaluation
   → Sample of outputs reviewed for tone, coherence, hallucination
   → Catches issues automated metrics miss

4. Baseline comparison
   → Clear, documented comparison against current production model

5. Canary deployment
   → 1-5% traffic to new model
   → Monitor KPIs (latency, error rate, quality scores, feedback)
   → Automated rollback triggers if KPIs degrade

6. Progressive rollout
   → Gradually increase traffic (5% → 25% → 50% → 100%)
   → Each stage gated by metric thresholds

7. Post-promotion monitoring
   → Heightened monitoring for 24-72 hours after full promotion
```

### Anti-Patterns (Q24)

| Anti-pattern | Why it fails |
|-------------|-------------|
| "Ship if the benchmark improved" | Single metric can mask regressions elsewhere |
| "Manual testing only, automated metrics are unreliable" | Doesn't scale; good evaluation combines both |
| "A/B test at 50% traffic immediately" | Reckless exposure without pre-production validation |
| "Deploy to 100% with automated rollback, skip human review" | Automated metrics can't catch all generative output failures |

---

## Cross-References

- Retrieval metrics methodology: [03-retrieval-and-ranking.md](./03-retrieval-and-ranking.md)
- Privacy-aware logging: [05-safety-and-security.md](./05-safety-and-security.md)
- CI/CD pipeline integration: [08-deployment-and-operations.md](./08-deployment-and-operations.md)
- Evaluation strategy by phase: [00-decision-framework.md](./00-decision-framework.md)
- Drift detection triggers: [02-ingestion-and-indexing.md](./02-ingestion-and-indexing.md)
