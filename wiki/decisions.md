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

## Enrichment / Eval Harness (v6.x — DSPy sprint)

### DeepSeek-v4-flash as the enrichment + DSPy LM (replaces local Qwen)
**Context:** The DSPy plan originally specced local Qwen3.6-27B via llama-server (free on owned GPU, but a ~13–20h serial enrichment pass for 48K chunks). DeepSeek V4 launched cheap with high concurrency.
**Decision:** Use `deepseek-v4-flash` (OpenAI-compatible, `base_url=https://api.deepseek.com`) for both DSPy optimization and the final enrichment. Pricing: input $0.14/M (cache miss), $0.0028/M (cache hit), output $0.28/M — the full 48K enrichment pass costs **under ~$15** and finishes in **~15–45 min** via async fan-out (concurrency cap is **2500** for flash, no RPM/TPM caps, 429 on overflow). This frees the GPU entirely and collapses the serial pass.
**Thinking control:** `extra_body={"thinking": {"type": "disabled"}}` — ⚠️ defaults to ENABLED, so non-thinking must be set explicitly. Task model (enrichment execution, many calls) runs thinking-OFF; MIPROv2 instruction-proposer (few calls) runs thinking-ON for better prompt candidates. `reasoning_effort` (high/max) only applies when thinking is on.
**Wiring:** DSPy→LiteLLM via the OpenAI passthrough (`dspy.LM("openai/deepseek-v4-flash", api_base=..., extra_body=...)`) rather than the native `deepseek/` provider, because the brand-new model ID may not be in LiteLLM's registry yet (would break cost-tracking / strip extra_body).
**Cache ordering:** order enrichment calls by parent so the stable prefix (instruction → metadata → parent_text) is prompt-cached across a parent's children — cache hit is 50× cheaper than miss.

### Extrinsic eval harness, scored at parent granularity
**Context:** Enrichment text is never read by anyone — it only shifts the child embedding. So the metric must be extrinsic (retrieval quality), and the golden set is `query → relevant-chunk` pairs, not `chunk → gold-summary`.
**Decision:** `scripts/eval_retrieval.py` runs the golden queries through the REAL `hybrid_search()` and scores **NDCG@10 / Recall@10 / MRR** plus a **Recall@50 ceiling** (fusion-only, no rerank). Matching is at **parent** granularity — the pipeline dedups by parent and the agent receives parent content, so parent-level is the meaningful unit. The ceiling-vs-delivered gap separates "never retrieved" (embedding/recall lever — enrichment's target) from "retrieved but reranked out" (reranker lever). Added `parent_id`/`child_id` to `SearchResult` (dataclass only; `to_dict` unchanged, so the MCP contract is untouched) so eval can match without re-querying internals.

### Vocab-gap hardening of the golden set (the harness's first real finding)
**Context:** The first golden set was LLM-generated FROM each chunk, so queries inherited the chunk's rare terms. Baseline came back near-ceiling — NDCG@10 0.931, Recall@10 0.975, **Recall@50 1.000**. That means retrieval already wins on chunk-vocabulary queries AND enrichment's lever (recall) is maxed, so the set literally **cannot measure enrichment**.
**Decision:** Build a second set (`golden_queries_hard.jsonl`) that paraphrases each query into developer problem/symptom framing, deliberately avoiding the chunk's signature terminology (`scripts/harden_golden_set.py`). Verified objectively: mean query→chunk content-word overlap dropped **52%** (0.649→0.313). The hard baseline exposes real headroom — **NDCG@10 0.791, Recall@10 0.925, Recall@50 0.960** — with the 15 misses splitting into **8 never-retrieved** (enrichment's target) + **7 reranked-out** (reranker's target).
**Use:** the **hard set is the gate** any enrichment/DSPy change must beat (NDCG 0.791 / MRR 0.747); the **easy set is a regression guard** (don't regress the already-solved case). Both baselines recorded under `data/golden/eval_runs/`.

### DSPy/MIPROv2 did NOT beat the hand-written prompt → ship a manual prompt (gate 2D)
**Context:** Phase 2 ran DSPy on a self-contained mini-retrieval metric: a **frozen distractor background** (~800 chunks, baseline-enriched, embedded once into an in-memory Qdrant with the production dense+BM25+DBSF+Ettin pipeline) plus a **freshly candidate-enriched positive** temp-inserted per query. This makes the global retrieval metric per-example so DSPy can average it, while embedding only one chunk per example. `scripts/dspy_enrich.py` (`--smoke`/`--build-bg`/`--bootstrap`/`--mipro`/`--manual`).
**Finding 1 — hard negatives are mandatory:** A flat random distractor pool scored a useless flat **1.0000** (the positive is the only on-topic chunk, wins trivially). Seeding the pool with each positive's same-book/same-chapter **siblings** (the real competitors) dropped the baseline off the ceiling and made the metric discriminate. Same "measure-the-wrong-thing" trap as the golden-set vocab bias, one level down.
**Finding 2 — DSPy lost:** On the hard pool (100-dev), MIPROv2 (`auto=light`, task-LM thinking-OFF, proposer thinking-ON) tied the incumbent exactly (0.9615 → 0.9615, **Δ +0.0000**). Two hand-written variants beat it: **problem-symptom 0.9678**, query-anticipation 0.9676, baseline 0.9615, entity-dense 0.9461 (the keyword-stuffing variant — worst). BootstrapFewShot also showed no durable gain.
**Decision:** Per the pre-registered gate 2D, **DSPy does not earn its place — ship a hand-written prompt.** The DSPy harness is kept as reusable infrastructure (re-runnable if the corpus/objective changes), but the v6.x enrichment prompt is manual.
**The meaningful signal is directional, not absolute:** the two **problem/query-vocabulary** framings both beat baseline and the keyword-stuffing one lost — 3/3 in the direction Phase-1 theory predicts (match the searcher's vocabulary, since that's how the golden set and real devs phrase queries). Each individual margin (~+0.006) is within the 100-query mini-harness noise, so the mini-harness can *rank* prompts but cannot *confirm* a sub-0.04 win. **The decisive test is the full 48K index** (Phase 3): enrich with the chosen problem-symptom framing, re-index, and require beating the no-enrichment hard baseline (NDCG 0.791) — else enrichment isn't worth shipping and we keep index-now-enrich-never.

### Phase 3 — enrichment LOST the full-index gate → REVERTED, ship no-enrichment (2026-05-30)
**Context:** Per the Phase-2 plan, all 48,009 chunks were enriched with the gate-winning **problem-symptom** prompt (run via the DSPy `Enricher`, Envelope A, on `deepseek-v4-flash` thinking-OFF; ~$13, two passes — the first stalled at 72% on an "Insufficient Balance" API error, resumed cleanly after top-up). Re-indexed on the RTX 5080 (fresh remote qdrant; `remote_index.py` builds `[heading_path, context_text, child_text]`). Then re-ran the eval harness against the no-enrichment baseline.
**Finding — enrichment made retrieval WORSE on the gate:** hard-set **NDCG 0.7907 → 0.7759 (−0.0148)**, **MRR 0.7468 → 0.7267 (−0.0201)**, Recall@10 unchanged (0.925), Recall@50 +0.005. Per-domain NDCG: ml +0.008 and distributed +0.044 (n=6, noise), but **databases −0.060, security −0.061, rust −0.018** — it regressed the largest-n domains. Critically, it *hurt the vocab-gap (hard) set* — the exact case enrichment was supposed to help most.
**Decision:** Per the pre-registered ship rule, **enrichment does not ship. Reverted to the no-enrichment index (NDCG 0.7907).** The repo stays **index-now-enrich-never** for this corpus. The enriched chunks are preserved at `data/chunks_enriched_rejected/` (gitignored) for any future revisit; canonical `data/chunks` were stripped back to `context_text=""` so disk ↔ shipped index stay consistent.
**Why it failed — the lesson:** the mini-harness (Phase 2) gave a **false positive**. An 800-chunk in-memory pool with a single freshly-enriched positive rewards any prompt that makes the positive *distinctive*; the full 48K index instead exposes the real cost — enriching **every** chunk with an LLM-written "problem/symptom" gloss adds correlated, model-voiced boilerplate that **blurs inter-chunk distinctions** and pulls the embedding toward the enrichment's vocabulary rather than the chunk's actual content. Heading-path + raw child text (already in the embed input since v5) carries the signal; the extra LLM sentence is net noise here. This is exactly why the full-index gate was reserved as decisive over the cheap proxy metric — and why the gate was pre-registered before seeing the result.

## Search Pipeline (v6.1 — search-path quality + PostgreSQL rescue, 2026-05-30)

Sprint after the enrichment revert closed that lever. An architecture review (diagram +
live-code read) surfaced five search-path hotspots; each was measured against the registered
golden gate (hard NDCG **0.7907**, easy **0.9311**) — nothing shipped that didn't clear it.
Search-path only, no corpus rebuild, no GPU.

### ⚡2 — long-lived Qdrant client singleton (the headline)
**Context:** `server.py` did `get_client()` … `client.close()` on every MCP search. Pre-flight
measured the real cost: opening a **48K-point file-based collection re-scans all segment
metadata ≈ 5.9 s**. So every search paid that twice (open+close) — reopen-per-call **~10.2 s**
vs reused client **~3.2 s** per query.
**Decision:** `search.py:get_client()` is now a module-level singleton; `server.py` drops the
per-call `close()`. **~3× latency cut, zero quality risk** (identical results — same client, same
data). The architecture review had filed this as a minor tidy-up; measurement made it the
single biggest win of the sprint. Realized when a server next restarts (running servers hold
old code). The file-based singleton holds the lock for the process lifetime — the server must
be down during any offline delete/index (already true).
**Latent follow-up:** the 5.9 s open is a local-mode symptom of >20K points; Qdrant-in-Docker
would make opens instant *and* speed queries — bigger than ⚡2 but more infra.

### ⚡4 — batch the query-variant embeds
**Decision:** `hybrid_search` embeds the primary query + all `extra_queries` in one
`embed_texts` batch instead of one call per variant. Zero risk on the gate/normal path (a
list of one → byte-identical). Batch-vs-single differs by ≤5e-3 only when `extra_queries` is
actually passed (attention masking under padding) — negligible, well below reranker score
gaps. Minor latency win, only on the rarely-used multi-query path.

### ⚡1 — reranker reads heading_path (SHIPPED, mixed per-domain)
**Context:** the dense embedding includes `heading_path`, but the Ettin cross-encoder reranked
**bare `child_text`** (`context_text` empty post-enrichment-revert) — blind to the section
breadcrumb. Fixed `_rerank` to build documents as `heading_path + context_text + child_text`,
mirroring `index.py`'s embed input.
**Result:** **hard NDCG 0.7887 → 0.7921 (+0.0034 over post-postgres, +0.0014 over the 0.7907
gate), MRR 0.7441 → 0.7504; easy 0.9311 → 0.9434 (+0.0123)**, easy databases perfect (1.0).
**Honest caveat — it's a mixed trade, not a uniform win.** On the hard set it helped where
headings are descriptive (rust 0.793→0.823) but *hurt* generic-heading domains (databases
0.848→0.809, security 0.773→0.742, +1 miss). Aggregate clears the gate on both sets, which is
the ship criterion. The dip suggests the `(part N)` suffixes in heading_paths are partly
fighting the reranker — cleaning that noise before reranking is a candidate follow-up.

### ⚡3 — candidate depth 50→75→100 (REJECTED, keep 50)
**Context:** hard fusion ceiling is 0.96–0.97 at k=50, so ~3–4% of positives never reach the
reranker. A cheap no-rerank headroom probe showed real headroom: ceiling @50=0.97, **@75=0.98**,
@100=0.98 (75→100 adds nothing).
**Finding:** the headroom does **not** convert. Full hard eval at candidates=75: **NDCG 0.7921 →
0.7778 (−0.0143)**, Recall@10 0.92→0.905. Feeding the cross-encoder 25 extra candidates adds
more distractors than true positives it surfaces — the reranker gets noisier and pushes
positives out of the top-10.
**Decision:** **Keep candidates=50.** Ceiling recall ≠ delivered NDCG; the reranker is the
binding constraint, not retrieval depth. Added a `--candidates` arg to `eval_retrieval.py` so
the sweep is re-runnable (default 50, pipeline unchanged).

### PostgreSQL 14 Internals — heading rescue + full re-chunk (the one CID-font book)
**Context:** postgres fell back to markitdown (CID-font garble guard, v6) → clean body but
**zero headings**, so its 1,113 chunks carried `heading_path=" (part N)"` / `chapter="0"`, and
`get_chapter`/`list_books` were empty for it — the corpus's worst-indexed book. Pre-flight
showed only **4 of 200** golden queries touch postgres and databases was already at ceiling 1.0,
so this is a **regression-guard + navigation fix, not a metric win**.
**Decisions:**
- **Full path over minimal.** Stripped the 682-line front matter (title page + two TOCs, pure
  navigation noise) and restored structure by promoting the 29 chapter titles — which exist in
  the body as bare `N Title` lines — to markdown headings (a regex pass located all 29 uniquely
  in book order; manual sign-off gate before editing). No OCR: zero content pages were lost, the
  garble is ~0.9% digit glyphs that don't affect search.
- **H1 chapters, not H1-book + H2-chapters.** H1+H2 gives a richer `heading_path`
  ("PostgreSQL 14 Internals > 2 Isolation") but `list_books`/`get_chapter` match `^#\s+` (H1
  only), so H2 chapters wouldn't surface — and widening that regex regresses `get_chapter` for
  every multi-H2 book. Chose **all-H1 chapters** (matches the working database-design book);
  `get_chapter`/`list_books` now work, heading_path = "2 Isolation". The retrieval difference is
  unmeasurable here (4 queries, domain at ceiling).
- **Chunker bug found:** restoring headings alone wasn't enough — `split_large_section` →
  `_force_split` set `heading_path = f"{heading} (part N)"`, but oversized headingless chapters
  had empty `heading`, yielding `" (part N)"`. With headings restored, paths are now informative
  (`"2 Isolation (part 3)"`). (The underlying force-split-clobbers-heading behavior is a known
  limitation for any heading-sparse oversized chapter; postgres now carries the chapter name.)
- **Golden re-anchor.** Re-chunking shifts every parent boundary, so the 4 postgres golden
  `positive_child_ids` (in both sets) dangled; `eval_retrieval.py` *silently skips* queries whose
  positives aren't in the chunk map (would drop databases n=13→9). Re-anchored all 4 by
  `source_text` match — one needed care (the answer passage straddled a chunk boundary; matched
  on the distinctive `cost=21.03..21.04` line + answer prose).
**Result:** re-chunked 135→**143 parents / 1,113→1,160 children**; index 48,009→**48,056**;
`get_chapter`/`list_books` restored (30 entries). **Retrieval-neutral:** identical 15 hard misses
(zero postgres misses in either run), Recall@10 and ceiling unchanged; NDCG −0.0020 from a pure
within-top-10 ordering shift on re-anchored databases positives. Verdict: guard satisfied in
substance — the nav/heading wins are banked, retrieval didn't move.
**Safety:** fresh pre-mutation index backup at `data/qdrant.v6-pre-postgres.bak` (gitignored).
The markdown fix lives in gitignored `data/markdown/` (survives pipeline re-runs since ingest
skips existing markdown, but is lost if regenerated from source — see ops-runbook for re-apply).

## Search Pipeline (v6.2 — measure-first optimization round, 2026-05-31)

### Fresh diagnostic re-anchored the miss taxonomy (8 / 8, not reranker-dominated)
**Context:** entered another optimization round. The v6.1 snapshot read "reranker is the binding
constraint" (from the ⚡3 candidate-depth rejection). A fresh full eval on both gates
(hard NDCG **0.7921** / easy **0.9434**, n=200/201) reclassified the **16 hard misses** as an
even **8 never-retrieved** (not in top-50 fusion — recall/embedding lever) + **8 reranked-out**
(retrieved @50, ranked below top-10 — reranker lever). The "reranker is binding" verdict was
specific to *candidate depth* (more candidates = more distractors); per-miss, the two levers are
**co-equal**. Security/crypto is the weakest domain (NDCG 0.742, `boneh-shoup` ×3) and bleeds on
both. Easy ceiling is a perfect **1.000** → when query vocab matches the chunk, recall is maxed,
so every easy miss is a reranker drop and the hard never-retrieved are *purely* vocab-gap.

### HyDE is NOT a corpus-wide lever — REJECTED both modes (the round's main finding)
**Context:** `eval_retrieval.py` tests the bare-query path, but production exposes `hyde_passage`
(Claude generates it). The 8 never-retrieved looked like textbook HyDE wins, so before paying for
an embedding swap we measured the HyDE-augmented path. Built `gen_hyde.py` (DeepSeek generates a
hypothetical answer from the **query alone** — `source_text` never shown, no gold leakage) +
a `--hyde` flag on the harness.
**Finding:** HyDE **lost** on the hard gate in both variants.

| Variant | NDCG@10 | Ceiling | Misses |
|---|---|---|---|
| Bare query (baseline) | **0.7921** | **0.960** | **16** |
| HyDE replace | 0.7753 | 0.950 | 20 |
| HyDE augment | 0.7809 | 0.955 | 19 |

**Mechanism — a clean domain split:** HyDE helps **ML** (broad conceptual; generated passage lands
near textbook prose — rescued the neural-style-transfer never-retrieved miss, ml ceiling
0.966→0.978) and **harms Rust** (precise borrow-checker/async semantics; generic passage drifts
to wrong chunks — broke 3 working rust queries clean out of top-50, rust ceiling 0.946→0.911).
Of the 8 never-retrieved, augment-HyDE reached only **2/8** at recall, delivered **1/8**.
**Why it loses structurally:** Jina v5's bare-query ceiling is already 0.96 — little recall
headroom to capture — while HyDE's drift cost is real and concentrated in precise-vocab domains.
**Decision:** HyDE does **not** ship as a default. It is a **selective, caller's-discretion** tool
(good on ML-conceptual queries, bad on Rust-precise) — exactly the per-query judgment an agent
should make, never corpus-wide. The 8 never-retrieved are confirmed **real recall failures**:
HyDE, the standard free fix, can't reach them, so the only path to them is an embedding upgrade.

### HyDE replace→augment: a production footgun fixed (search.py, SHIPPED)
**Context:** `hybrid_search` did HyDE by *replacement* — `dense_text = hyde_passage if hyde_passage
else query` — so a supplied passage **removed the original query vector from the prefetch entirely**.
That's the weak variant: when Claude passes a HyDE passage on a query that already retrieves well,
it could silently make results *worse* (the 5 broken queries under replace-mode).
**Decision:** changed to **augment** — the original query is always a dense leg (the anchor); a
`hyde_passage` adds a *second* dense leg via Qdrant multi-prefetch (same mechanism as
`extra_queries`). Strict improvement to the exposed param (0.7809 > 0.7753 when used); the
no-HyDE **gate path is byte-identical** (verified: `dense_texts=[query]` → same two prefetches).
Kept even though HyDE-default lost, because it de-risks the API Claude already calls.

### Reranker input: per-domain heading (`descriptive-heading`, SHIPPED — the round's win)
**Context:** the user pushed back on "swap the reranker" — Ettin-150m is current (2025 ModernBERT),
so *tune before replace*. The `diag_rerank.py` rank-position probe on the 8 reranked-out misses
showed the cross-encoder ranks the positives at 9–28 (close, not fundamentally disagreeing) and —
the smoking gun — **child-only input beat ⚡1's heading-aware input on 7 of 8 misses** (joy-of-crypto
positive 23→9, deep-rl 20→10). ⚡1 shipped heading_path *globally*; the probe showed it helps where
headings are descriptive and hurts where they're formal/generic.
**A/B over both gates (env `KB_RERANK_INPUT`, default now the winner):**

| reranker input | hard NDCG | easy NDCG | note |
|---|---|---|---|
| heading (⚡1 v6.1) | 0.7921 | 0.9434 | global heading_path |
| child (pre-⚡1) | 0.7887 | 0.9311 | loses both — heading carries vocab the easy set + ml/rust need |
| rust-heading | 0.7989 | 0.9333 | wins hard, regresses easy; leaves ml on child |
| **descriptive-heading** | **0.8021** | **0.9379** | **SHIPPED** — heading for {ml,rust}, child for {security,databases,distributed} |

**Decision:** ship `descriptive-heading`. **+0.0100 hard gate** (rescued 2 positives into top-10,
R@10 0.920→0.930) for **−0.0055 easy** — and the easy regression is benign: **easy R@10 unchanged
at 0.975, no positive lost, pure within-top-10 reorder**. It dominates every other variant
(strictly beats rust-heading on both axes). The mechanism: heading_path is a *vocabulary* signal —
it reinforces the match when the query shares the chunk's vocab (descriptive ml/rust titles, and
the whole vocab-matched easy set) and adds orthogonal noise when the heading is formal/generic
(crypto formalism, OWASP section numbers, redis ops) against a developer-symptom query.
**Implementation:** `search.py:_rerank_doc()` — `_GENERIC_HEADING_BOOKS` (14 security/db/dist slugs)
get child-only; everything else (ml + rust) keeps heading. No model swap, no re-index.
**Caveat (anti-overfit):** the per-domain hypothesis rests on the robust cells (ml n=89, rust n=56,
security n=36); databases n=13 and distributed n=6 are noisy and align directionally but don't
drive the decision. The easy guard (R@10 intact) is the check that this isn't hard-set overfitting.
**Supersedes ⚡1** (which is now the `heading` fallback mode, retained for A/B reproducibility).

## Rejected Approaches

### Corpus-wide HyDE (query→hypothetical-passage on the dense leg)
**Why considered:** standard fix for vocab-gap recall; the 8 never-retrieved hard misses looked like textbook HyDE wins.
**Why rejected:** measured net-negative on the hard gate (NDCG 0.7921 → 0.7809 augment / 0.7753 replace). Domain-split mechanism — helps ML-conceptual, drifts on Rust-precise — and Jina v5's 0.96 bare-query ceiling leaves too little recall headroom to offset the drift. Kept as a **selective caller-side param** (augment-mode), not a default. Full record in the v6.2 section above.

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
