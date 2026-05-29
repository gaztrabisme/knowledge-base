# Plan — DSPy-Optimized Contextual Enrichment (future v6 work)

Status: **Phase 1 DONE; Phase 2 next.** Written 2026-05-29, updated same day. Picks up after v6.0 (48,009 chunks, not 19,728 as originally written below).

**Progress:**
- ✅ **Phase 1 (eval harness)** built and trustworthy. `scripts/build_golden_set.py` (201 q), `scripts/harden_golden_set.py` (vocab-gap paraphrase, −52% lexical overlap), `scripts/eval_retrieval.py` (NDCG@10/Recall@10/MRR + Recall@50 ceiling, parent-granularity). Two baselines recorded under `data/golden/eval_runs/`:
  - easy (chunk-vocab) = regression guard: NDCG 0.931 / R@10 0.975 / R@50 **1.000**
  - **hard (vocab-gap) = the gate**: NDCG **0.791** / R@10 0.925 / MRR **0.747** / R@50 0.960
- **LM changed: local Qwen → `deepseek-v4-flash`** (see decisions.md). Both DSPy and final enrichment run on DeepSeek API (cheap + 2500 concurrency). Task model thinking-OFF; instruction-proposer thinking-ON.
- ⏭️ **Phase 2 (DSPy)** is next; must beat the hard-set gate without regressing the easy set.

## Goal

Replace the hand-written contextual enrichment prompt (`enrich.py:CONTEXT_PROMPT`) with a
prompt discovered by DSPy that **maximizes downstream retrieval accuracy**, then re-enrich and
re-index all 19,728 chunks as v6.

## The Core Reframe (read this first)

The naive framing — "optimize the prompt to write better summaries" — optimizes the wrong
objective. Enrichment text is never returned to anyone; it exists only to improve the embedding
of the child chunk. A summary that reads beautifully but doesn't change retrieval is worthless;
an ugly fragment that pulls the right chunk to rank 1 is perfect.

**Therefore the metric is extrinsic (retrieval quality), not intrinsic (similarity to a gold
summary).** This has two consequences:

1. The golden set is **`query → relevant-chunk(s)`** pairs, NOT `chunk → gold-summary` pairs.
2. Evaluating one prompt variant requires: enrich candidate chunks with that prompt → embed →
   run the query set → score ranking. There is no shortcut through "does it match a reference summary."

This reframe is why **Phase 1 (the eval harness) is the real deliverable.** It is tool-agnostic:
the same harness lets us measure any future change — reranker swaps, chunking tweaks, embedding
model upgrades. DSPy (Phase 2) is just an optimizer that rides on top of it. If the harness exists
and DSPy disappoints, we fall back to hand-iterating prompts against the same harness and lose nothing.

---

## Phase 1 — Evaluation Harness (foundation, ~the bulk of the work)

### 1A. Build the golden query set

Target: **~150–200 queries** spanning all four domains (ML, databases, security, distributed
systems), weighted roughly by corpus size (ML is ~60% of the corpus).

Construction (hybrid, cheapest path to usable data):
1. **Sample** ~200 child chunks stratified across books.
2. **LLM-generate** a realistic developer question each chunk would answer (Qwen 27B or Claude).
   The source chunk is the automatic positive label. Prompt the generator for *specific* questions
   that target the chunk's unique content (generic questions create unlabeled-positive noise).
3. **Human spot-check** every query: discard vague ones, fix leading phrasing, and for ~30–40 of
   them add 1–2 hand-identified **hard negatives** (chunks that look relevant but aren't).
4. Store as JSONL: `{query, positive_child_ids: [...], hard_negative_child_ids: [...], domain}`.

Known noise source: a generated query may have *other* relevant chunks we didn't label
(unlabeled positives → counted as false negatives). Mitigate with ranking metrics that tolerate
this and by keeping queries specific. Accept residual noise — it's constant across prompt variants,
so it doesn't bias the *comparison*.

### 1B. Metric implementation

`scripts/eval_retrieval.py` — given a Qdrant collection + the golden JSONL, run every query
through `hybrid_search()` and compute:
- **NDCG@10** (primary — rewards ranking positives high)
- **Recall@10** (did we retrieve the positive at all)
- **MRR** (reciprocal rank of first positive)

Report per-domain and aggregate. This is the number every future change gets measured against.
First action once built: **record the v5.0 baseline** so we know what we're beating.

---

## Phase 2 — DSPy Prompt Optimization

Depends on Phase 1. Do not start until the harness reports a stable v5.0 baseline.

### 2A. Signature — feed it the metadata we currently withhold

The current prompt only sees `parent_text` + `child_text`. Add the structured metadata as
explicit input fields so the optimizer can learn to use them:

```python
class EnrichChunk(dspy.Signature):
    """Write a 1-2 sentence context placing this chunk within its book and section,
    resolving ambiguous references. Optimize for making the chunk retrievable."""
    book_title: str    = dspy.InputField()
    heading_path: str  = dspy.InputField()   # e.g. "MVCC > Snapshot Isolation"
    parent_text: str   = dspy.InputField()
    child_text: str    = dspy.InputField()
    enrichment: str    = dspy.OutputField(desc="1-2 sentences, no restating the chunk")
```

### 2B. Metric wrapper (cost is the trap here)

DSPy calls the metric for many candidate programs × many trainset examples. A faithful metric
re-enriches the relevant chunks with the candidate prompt, embeds them, and scores ranking against
a **bounded distractor pool** (~500 fixed chunks shared across queries) so per-trial cost stays sane.

Fidelity note: ideally distractors are enriched with the *same* candidate prompt too (in production
all chunks use the winning prompt). Enriching only positives against fixed-enrichment distractors
introduces a distribution mismatch that can create artifacts. Decision: **enrich both positives and
the distractor pool per candidate prompt**, bound the pool to ~500–1000 chunks, and run the whole
optimization as a batch job on the RTX 5080 overnight (free on owned hardware).

Rough cost: ~1k chunks × ~20 candidate evaluations ≈ 20k enrichment calls → hours on local Qwen,
not minutes. Acceptable as an overnight job; expensive on a paid API.

### 2C. Optimizer + LM

- Start with **BootstrapFewShot** (cheap, fast, validates the harness end-to-end).
- Escalate to **MIPROv2** (joint instruction + few-shot Bayesian search) once the pipeline works.
- LM: **`deepseek-v4-flash` via OpenAI passthrough** (`dspy.LM("openai/deepseek-v4-flash", api_base="https://api.deepseek.com", extra_body={"thinking":{"type":"disabled"}})`). Task model = thinking-OFF; MIPROv2 `prompt_model` (instruction proposer) = thinking-ON for stronger candidates. Cheap + 2500-concurrency, so the per-trial distractor-pool cost is no longer a GPU-time concern (still bound the pool ~500–1000 to keep token spend sane). Original plan's local-Qwen note is superseded; see decisions.md.

### 2D. Checkpoint (honest gate)

After the first optimized prompt, compare harness scores vs the v5.0 baseline AND vs a couple of
hand-written prompt variants run through the same harness. **If DSPy doesn't beat careful manual
iteration, stop and just ship the best manual prompt.** DSPy earns its place only if the systematic
search wins measurably.

---

## Phase 3 — Production Re-Enrichment (v6)

Depends on a winning prompt from Phase 2.

1. Drop the winning prompt into `enrich.py` (and `remote_enrich.py` — keep them in sync).
2. Re-enrich all 19,728 chunks on the GPU (existing remote enrichment pipeline).
3. Re-embed + re-index (existing remote GPU indexing pipeline).
4. **Validate against the Phase 1 harness** — v6 must beat the recorded v5.0 baseline on NDCG@10,
   or we don't ship it.
5. Bump CLAUDE.md to v6, log the decision in `wiki/decisions.md`.

---

## Sequencing & Dependencies

```
1A golden set ─→ 1B metric ─→ [record v5.0 baseline]
                                   │
                                   ├─→ 2A/2B/2C DSPy optimize ─→ 2D gate
                                   │                                │
                                   └────────── (manual prompt fallback uses same harness)
                                                                    │
                                                            3 re-enrich → v6 → validate vs baseline
```

## Risks / Open Questions

- **Unlabeled positives** inflate false-negative counts. Constant across variants, so comparisons
  stay valid; absolute scores look pessimistic. Fine.
- **Golden-set labeling is the real cost** (human time, not compute). Time-box it; 150 decent
  queries beat 400 rushed ones.
- **DSPy may not beat manual.** That's what gate 2D is for — the harness makes the answer measurable
  instead of a matter of faith.
- **Per-trial enrichment cost** could balloon if the distractor pool grows. Keep it bounded.

## Prerequisites

- `pip install dspy-ai` (Phase 2 only)
- llama-server running Qwen3.6-27B on the GPU box (already in the ops runbook)
- Existing `remote_enrich.py` + `remote_index.py` pipelines (already built)
