# Deployment & Operations

The operational layer that keeps a RAG system running reliably in production. From Dockerfiles to rollback procedures, this covers the infrastructure and operational practices that separate a working prototype from a production service.

---

## Dockerfile Best Practices for ML Services

From Q35: A production Dockerfile for an LLM/RAG service needs specific patterns beyond standard web application containers.

### The Recommended Pattern (Q35)

```dockerfile
# Stage 1: Build dependencies
FROM python:3.12-slim AS builder
WORKDIR /app

# Copy dependency files first (cache layer)
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev

# Stage 2: Runtime image
FROM python:3.12-slim AS runtime

# Create non-root user
RUN useradd -m -s /bin/bash appuser

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code last (most frequently changing layer)
COPY src/ ./src/

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT ["python", "-m", "claudie"]
```

### For GPU Inference (Q35)

```dockerfile
# Use NVIDIA CUDA base when GPU is required
FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04 AS runtime
# ... rest follows same pattern with CUDA-specific deps
```

### Layer Ordering Principle (Q35)

```
Most stable → Least stable (top → bottom):
  1. Base image (OS packages)           ← changes rarely
  2. System dependencies (apt install)  ← changes rarely
  3. Python dependencies (pip install)  ← changes on dep updates
  4. Application code (COPY src/)       ← changes on every commit

WHY: Docker caches layers from top down. Changing layer N
invalidates all layers below N. Code changes should only
rebuild the bottom layer, not reinstall all dependencies.
```

### Anti-Patterns (Q35)

| Anti-pattern | Why it fails |
|-------------|-------------|
| `FROM ubuntu:latest` | Non-reproducible; "latest" changes unpredictably |
| Running as root | Violates principle of least privilege; security risk |
| No HEALTHCHECK | Loses container-level health monitoring |
| Alpine Linux for Python/ML | musl vs glibc incompatibilities break many ML packages |
| Embedding model weights in image layers | Multi-GB images, slow to pull, impossible to update without rebuild |
| COPY source code before pip install | Every code change triggers full dependency reinstall |
| Single-stage build with build tools in final image | Bloated image, larger attack surface |

### Model Loading (Q35, Q43)

**Do:** Load model weights at runtime from object storage or a model registry.

**Do not:** Bake weights into the container image.

```
Container startup:
  1. Pull model weights from S3/GCS/model registry
  2. Load into memory/GPU
  3. Signal readiness via health check endpoint
  4. Start serving
```

This allows model updates without image rebuilds and keeps images small and fast to pull.

---

## Secrets Management for LLM API Keys

From Q37: Multiple LLM provider API keys need centralized, secure management.

### The Recommended Pattern (Q37)

```
External Secrets Manager (Vault, AWS Secrets Manager, Azure Key Vault)
  │
  ├── External Secrets Operator (or CSI Secrets Store Driver)
  │   └── Syncs secrets into Kubernetes as native Secret objects
  │
  ├── RBAC: Each service account only accesses its own secrets
  │
  ├── Automatic rotation policies
  │
  └── Audit logging for all secret access
```

### Key Principles

1. **Centralized management** -- One source of truth for all secrets
2. **Least privilege** -- Each service only accesses the API keys it needs
3. **Automatic rotation** -- Reduce exposure window from compromised keys
4. **Never logged** -- Secrets must never appear in logs, env dumps, error messages, or pod specs
5. **Audit trail** -- Track who accessed which secret and when

### Anti-Patterns (Q37)

| Anti-pattern | Why it fails |
|-------------|-------------|
| Base64-encoded Kubernetes Secrets only | base64 is encoding, not encryption; manual rotation is error-prone |
| API keys as Docker build arguments baked into images | Secrets in image layers, registries, CI logs; rotation requires rebuild |
| Vault sidecar with 1-hour dynamic secrets | Over-engineered; most LLM providers issue long-lived keys, not dynamic credentials |
| Sealed Secrets in Git without external rotation | GitOps-friendly but no external rotation mechanism at runtime |

---

## Rate Limiting and Circuit Breakers

From Q42 and Q58: LLM API calls have unique characteristics that standard rate limiting doesn't address.

### Token-Based Rate Limiting (Q58)

```
Why request-count limiting is insufficient:
  Request A: 100 input tokens, 50 output tokens     → cheap
  Request B: 50,000 input tokens, 4,000 output tokens → expensive
  Same "1 request" in both cases, wildly different resource consumption.

Solution: Track token consumption per tenant per time window.
```

```python
class TokenRateLimiter:
    """Rate limiter that tracks both request count and token usage."""

    def __init__(self, config: TenantConfig):
        self.max_requests_per_minute = config.rpm
        self.max_tokens_per_minute = config.tpm
        self.max_tokens_per_day = config.tpd

    async def check(self, tenant_id: str, estimated_tokens: int) -> bool:
        """Check if request is within budget.

        Returns True if allowed, raises RateLimitError if not.
        """
        current = await self.get_usage(tenant_id, window="1m")

        if current.requests >= self.max_requests_per_minute:
            raise RateLimitError("Request limit exceeded", retry_after=60)

        if current.tokens + estimated_tokens > self.max_tokens_per_minute:
            raise RateLimitError("Token limit exceeded", retry_after=60)

        daily = await self.get_usage(tenant_id, window="1d")
        if daily.tokens + estimated_tokens > self.max_tokens_per_day:
            raise RateLimitError("Daily token budget exceeded", retry_after=3600)

        return True
```

### Circuit Breakers (Q42)

```
Per-provider circuit breaker:
  CLOSED (normal):
    → Requests flow to provider
    → Track error rate and latency

  OPEN (provider is down):
    → Triggered when error rate or latency exceeds threshold
    → Fail fast — don't wait for timeout
    → Route to fallback provider or cached response
    → Periodically enter HALF-OPEN to test recovery

  HALF-OPEN (testing recovery):
    → Allow a small number of requests through
    → If they succeed → return to CLOSED
    → If they fail → return to OPEN
```

### Retry Strategy (Q42, Q51)

```python
async def call_with_retry(provider: str, request: dict,
                         max_retries: int = 3) -> dict:
    """Exponential backoff with jitter for LLM API calls."""

    for attempt in range(max_retries):
        try:
            return await providers[provider].call(request)
        except RateLimitError as e:
            # Use provider's retry-after header if available
            wait = e.retry_after or (2 ** attempt + random.uniform(0, 1))
            await asyncio.sleep(wait)
        except ProviderError as e:
            if attempt == max_retries - 1:
                # Fall back to alternative provider
                return await call_fallback(request)
            wait = 2 ** attempt + random.uniform(0, 1)
            await asyncio.sleep(wait)
```

### Anti-Patterns (Q42, Q51)

| Anti-pattern | Why it fails |
|-------------|-------------|
| Fixed request-per-minute quotas ignoring token count | A 50K-token request and a 100-token request consume vastly different resources (Q58) |
| Linear backoff | Slower convergence, wastes more requests than exponential (Q42) |
| Aggressive retries (100ms intervals, 10+ attempts) | Thundering herd; amplifies load on struggling provider (Q51) |
| Sending every request to all providers simultaneously | Doubles/triples cost on every request, not just during failures (Q51) |
| In-memory rate limiting per pod (no coordination) | Each pod tracks independently; total cluster usage uncontrolled (Q42) |
| Pre-computing cached responses for "all known queries" | Impractical for open-ended LLM queries (Q51) |

---

## Fallback Providers and Graceful Degradation

From Q42 and Q51: When a provider goes down, the system should not go down with it.

### Fallback Strategy (Q51)

```
Priority list:
  1. Primary provider (Claude Sonnet) — best quality
  2. Fallback provider (GPT-4) — comparable quality
  3. Cached responses — for frequent queries
  4. Self-hosted model (smaller, lower quality) — always available
  5. Graceful degradation message — honest about limitations

Each tier triggers when the one above is unavailable.
Non-critical features degrade first.
```

**Anti-pattern (Q51):** "Maintain a self-hosted fallback, making all other resilience patterns unnecessary." Self-hosted models can also fail. You still need circuit breakers, caching, and graceful degradation.

---

## Autoscaling Considerations

From Q36: LLM inference workloads have unique scaling characteristics.

### Custom Metrics for HPA (Q36)

```yaml
# Standard CPU-based scaling is WRONG for LLM inference
# GPU may be saturated while CPU is idle

apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: llm-inference-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: llm-inference
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Pods
      pods:
        metric:
          name: request_latency_p95_ms
        target:
          type: AverageValue
          averageValue: "1000"    # Scale up if P95 > 1s
    - type: Pods
      pods:
        metric:
          name: inference_queue_depth
        target:
          type: AverageValue
          averageValue: "5"       # Scale up if queue > 5
```

### Cold Start Mitigation (Q36)

LLM models take minutes to load. New replicas are useless until the model is ready.

```
Strategies:
  1. Model preloading in init containers
  2. Warm pools (keep N idle replicas ready)
  3. Readiness probes that verify model is loaded
  4. Startup probes with generous timeouts for slow-starting containers
```

**Anti-pattern (Q36):** "Scale from zero with KEDA." Multi-minute model loading times make scale-from-zero impractical for LLM services.

**Anti-pattern (Q36):** "Use Vertical Pod Autoscaler (VPA)." VPA requires pod restarts for most resource changes and you cannot add GPUs to a running pod.

**Anti-pattern (Q36):** "Scale based on CPU utilization at 70%." CPU is a poor proxy for GPU-based LLM inference; the CPU may be idle while the GPU is saturated.

---

## CI/CD Pipeline Design for ML Services

From Q48: A well-designed pipeline for RAG services has quality gates at each stage.

### Pipeline Stages

```
┌─────────────────────────────────────────────────────────────────┐
│ Stage 1: Fast checks (< 2 min)                                 │
│   - Lint (ruff, mypy)                                          │
│   - Unit tests                                                 │
│   - Fail fast — don't waste time building if basics are broken │
├─────────────────────────────────────────────────────────────────┤
│ Stage 2: Build (< 5 min)                                       │
│   - Build container image (multi-stage)                        │
│   - Security scan (Trivy, Snyk)                                │
├─────────────────────────────────────────────────────────────────┤
│ Stage 3: Staging deployment (< 10 min)                         │
│   - Deploy to staging environment                              │
│   - Integration tests against staging vector DB + LLM          │
├─────────────────────────────────────────────────────────────────┤
│ Stage 4: Quality evaluation (< 30 min)                         │
│   - Run golden test set against staging                        │
│   - Quality gates: recall@10 > 0.8, MRR > 0.7, etc.          │
│   - Block promotion if thresholds not met                      │
├─────────────────────────────────────────────────────────────────┤
│ Stage 5: Canary deployment                                     │
│   - Deploy to production at 1-5% traffic                       │
│   - Monitor latency, error rate, quality scores                │
│   - Automated rollback if KPIs degrade                         │
├─────────────────────────────────────────────────────────────────┤
│ Stage 6: Full promotion                                        │
│   - Gradually increase to 100% traffic                         │
│   - Heightened monitoring for 24-72 hours                      │
└─────────────────────────────────────────────────────────────────┘
```

**Key principle (Q48):** Fail fast with cheap checks first. Don't run the expensive evaluation suite before linting and building.

### Anti-Patterns (Q48)

| Anti-pattern | Why it fails |
|-------------|-------------|
| Run expensive eval suite before lint/build | Wastes compute on commits that might fail basic checks |
| Deploy directly to production behind feature flag | Skips all pre-production validation |
| Manual QA gating every deployment | Bottleneck that doesn't scale |
| A/B testing replaces offline evaluation | You need automated quality gates BEFORE reaching production |

---

## Rollback Procedures

From Q49 and Q40: When a deployment degrades quality, you need fast, reliable rollback.

### The Rollback Strategy (Q49)

```
Prerequisites:
  ✓ Previous model artifacts stored as immutable, versioned assets
  ✓ Previous deployment configs preserved
  ✓ Traffic routing can switch between versions

Rollback procedure:
  1. Automated trigger detects quality degradation
     (quality metric drops, error rate spikes, latency increase)
  2. Traffic routing switches to previous version
     (NOT re-running CI/CD — that's too slow)
  3. Previous version starts serving immediately
     (immutable artifacts are always ready)
  4. Alert on-call team for investigation
  5. Postmortem to identify root cause

Key insight: Rollback should be a traffic routing change,
not a rebuild. If you have immutable artifacts, you should
route traffic directly rather than rebuild.
```

### Anti-Patterns (Q49)

| Anti-pattern | Why it fails |
|-------------|-------------|
| Re-run full CI/CD pipeline with prior commit | Adds unnecessary delay during an incident |
| Shadow deployment (always run both models) | Doubles inference cost permanently for a rare event |
| Retrain the model before investigating root cause | Premature and backwards — investigate first |
| Scale down new, scale up old (K8s only, no quality triggers) | Narrow mechanism; misses broader practices like automated triggers and postmortem |

---

## Zero-Downtime Index Migration

From Q59: Migrating 10M+ documents to a new embedding model while maintaining full availability.

### Blue/Green Index Strategy (Q59)

```
Phase 1: Build (parallel to production)
  - Create new index (green) with new embedding model
  - Existing index (blue) continues serving all traffic
  - Dual-write: new documents go to both indexes

Phase 2: Validate
  - Shadow reads: run queries against green, compare to blue
  - Quality gates: relevance metrics, latency checks
  - Do NOT serve green results to users yet

Phase 3: Cutover
  - Switch traffic from blue to green
  - Maintain blue as rollback target

Phase 4: Cleanup
  - Monitor green in production for confidence period
  - Decommission blue when confidence established
```

### Anti-Patterns (Q59)

| Anti-pattern | Why it fails |
|-------------|-------------|
| In-place rolling update of embeddings | Mixed embedding spaces are mathematically incompatible; search quality degrades |
| Atomic swap with brief write pause | Not truly zero-downtime; skips validation step |
| Run both models permanently, merge results | Doubles cost; merging across different embedding spaces is mathematically unsound |
| Maintenance window reindex | Contradicts zero-downtime; 10M+ docs unlikely to complete in 2 hours |

---

## Model Runtime Conflict Management

From Q50: Different models may require incompatible CUDA/driver versions.

### The Pattern (Q50)

```
Per-model-version container:
  - Pinned base image (specific CUDA/cuDNN version)
  - Dependency lockfiles for all libraries
  - Compatibility tests in CI before deployment
  - Container isolation prevents cross-model conflicts
```

**Anti-pattern (Q50):** "Standardize on a single CUDA version." Different models genuinely require different CUDA versions. This blocks adoption of newer models.

**Anti-pattern (Q50):** "Use conda environments within a single container." CUDA toolkit versions involve system-level shared libraries that conda cannot fully isolate.

**Anti-pattern (Q50):** "NVIDIA MPS for CUDA version isolation." MPS allows GPU sharing but does NOT provide CUDA version isolation.

---

## Model Packaging (Q43, Q27)

### The Artifact Bundle

```
Model artifact (versioned):
  ├── model_weights/           # The actual model files
  ├── tokenizer/               # Tokenizer files and config
  ├── config.json              # Model configuration
  ├── requirements.lock        # Pinned Python dependencies
  └── metadata.json            # Version, training data hash, code commit
```

### The Deployment Container (Q27)

```
Container image:
  ├── Base image (CUDA/python version pinned)
  ├── Inference server (vLLM, TGI, Triton)
  ├── Pinned dependencies
  └── Application code

Model weights loaded at runtime from model registry.
```

**Anti-pattern (Q27, Q43):** "Upload weights to shared NFS, each team writes own loading code." Inconsistencies, versioning headaches, deployment fragility.

**Anti-pattern (Q27):** "Store model weights in a Git repository." Git was not designed for multi-gigabyte binary artifacts.

**Anti-pattern (Q27):** "Deploy as serverless function with weights loaded from S3." Cold starts with multi-GB weight loading create unacceptable latency.

---

## Model Versioning and Lineage (Q44)

### The Model Registry Pattern

```
Model registry entry:
  - Model version: v2.3.1
  - Dataset version: training_data_v5 (hash: abc123)
  - Code commit: def456
  - Training config: lr=2e-5, epochs=3, lora_rank=16
  - Evaluation results: recall=0.85, MRR=0.78
  - Deployment status: staging → canary → production
  - Promotion timestamps and approver
```

**Why lineage matters (Q44):** When a model in production starts degrading, you need to trace back to the exact dataset, code, and config that produced it. Without lineage, debugging is guesswork.

**Anti-pattern (Q44):** "Timestamp-based filenames and a spreadsheet for tracking." Error-prone, unscalable, no automated lineage.

**Anti-pattern (Q44):** "Docker images as the single source of truth for lineage." Bloats images with data snapshots, conflates deployment packaging with versioning.

---

## Cost Management and Token Budgets

From Q16, Q42, Q58: LLM costs scale with token usage, which is variable and unpredictable.

### Cost Control Strategies

| Strategy | Level | Impact | Source |
|----------|-------|--------|--------|
| **Better retrieval precision** | Pipeline | Send fewer, more relevant chunks | Q16 |
| **Reranking to prune** | Pipeline | Only top candidates reach the prompt | Q16 |
| **Context compression** | Pipeline | Summarize before sending to LLM | Q16 |
| **Prompt caching** | API | Avoid re-processing identical prefixes | Q16 |
| **Token-based rate limiting** | API | Per-tenant token budgets | Q58 |
| **Completion caching** | API | Avoid re-generating identical answers | Q11 |
| **Cost monitoring** | Ops | Daily/monthly spend tracking with alerts | Q45 |
| **Model tiering** | Architecture | Use cheaper models for simple tasks | - |

### Token Budget Pattern

```python
class TokenBudget:
    """Track and enforce token budgets per tenant."""

    def __init__(self, daily_limit: int, monthly_limit: int):
        self.daily_limit = daily_limit
        self.monthly_limit = monthly_limit

    async def track(self, tenant_id: str, input_tokens: int, output_tokens: int):
        total = input_tokens + output_tokens
        await self.increment(tenant_id, "daily", total)
        await self.increment(tenant_id, "monthly", total)

    async def check(self, tenant_id: str) -> bool:
        daily = await self.get_usage(tenant_id, "daily")
        monthly = await self.get_usage(tenant_id, "monthly")

        if daily > self.daily_limit * 0.9:
            await self.alert("approaching_daily_limit", tenant_id)
        if monthly > self.monthly_limit:
            raise BudgetExceededError(tenant_id)

        return True
```

---

## Kubernetes Diagnostics (Q38)

### CrashLoopBackOff Systematic Debugging

From Q38, the methodical workflow:

```
Step 1: Check application logs
  kubectl logs <pod> --previous    # logs from crashed container

Step 2: Inspect pod events and config
  kubectl describe pod <pod>       # events, exit codes, probes

Step 3: Check for OOMKilled
  Look in container state for OOMKilled status
  → Increase memory limits if confirmed

Step 4: Verify configuration
  - Environment variables correct?
  - Mounted secrets exist and contain expected values?

Step 5: Check dependencies
  - Can the pod reach its database? Model storage? External APIs?

Step 6: Review resource requests/limits
  - Do they match the service's actual requirements?
```

**Anti-pattern (Q38):** "Delete the pod and let it recreate." Skips diagnosis, treats symptoms.

**Anti-pattern (Q38):** "Exec into the container." Cannot exec into a CrashLoopBackOff pod because the container is not running.

---

## Managed vs Self-Managed Infrastructure (Q39)

### Decision Framework

```
Default to managed unless you need:
  - Custom GPU schedulers
  - Multi-cloud deployment
  - Strict data residency requirements
  - Advanced GPU orchestration (MIG, multi-model serving)
  - Specific compliance controls not available on managed platforms

Evaluate:
  - Team expertise (do you have platform engineers?)
  - Operational overhead (is Kubernetes management your core business?)
  - Scale requirements (managed services have limits)
  - TCO (compute + networking + storage + personnel)
  - Time to market (managed is faster to get started)
```

---

## GPU Scheduling and Isolation (Q41)

### The Production Pattern

```
1. Taints on GPU nodes:
   nvidia.com/gpu=present:NoSchedule
   → Only pods with matching tolerations can schedule here
   → Prevents non-GPU pods from wasting expensive GPU nodes

2. NVIDIA device plugin:
   Exposes GPUs as schedulable resources
   → nvidia.com/gpu: 1 in pod resource requests

3. Multi-model serving (vLLM, Triton):
   Multiple models share a GPU efficiently
   → Application-level batching for higher utilization

4. ResourceQuotas per namespace:
   Prevent any team from monopolizing GPUs

5. PriorityClasses:
   Critical inference > batch processing
   Batch jobs get preempted when inference needs resources
```

---

## Cross-References

- Docker layer optimization impacts build speed: relates to CI/CD in this document
- Secrets feed into LLM API calls: [01-architecture.md](./01-architecture.md)
- Rate limiting design: [01-architecture.md](./01-architecture.md)
- Quality gates reference evaluation metrics: [07-evaluation-and-monitoring.md](./07-evaluation-and-monitoring.md)
- Index migration needs retrieval validation: [03-retrieval-and-ranking.md](./03-retrieval-and-ranking.md)
- Cost management through better retrieval: [03-retrieval-and-ranking.md](./03-retrieval-and-ranking.md)
