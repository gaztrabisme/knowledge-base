# Developer Knowledge Base — Project Wiki

Last updated: 2026-05-30 (v6.4 gate-audit round: **audited the golden gate itself — overall grade D+**. The gate cannot resolve the ~0.01-NDCG deltas it has been adjudicating: per-query NDCG σ=0.31, n=200 → paired MDE ≥0.0195 at 80% power *even at ρ=0.95*. **v6.3's embedding-upgrade "rejection" (0.802 vs 0.790, gap 0.012) is downgraded to INCONCLUSIVE — below the discrimination floor, never significance-tested.** Also: 44.4% of sampled queries have an unlabeled-but-relevant top-10 hit (single-positive labels deflate NDCG; the "8 never-retrieved" may be label artifacts), query realism LOW (100% long why/how, 0 keyword/error/navigational). Added significance harness (`significance.py`, `--per-query`) + report card [gate-audit.md](gate-audit.md). **The gate's late-chunking rejection stands** (those gaps −0.06 to −0.09 are above the floor). Prior v6.3: late chunking rejected (ConTEB dilution); Jina v3 non-deployable.)

## Quick Links

- [Architecture](architecture.md) — Pipeline design, data flow, component interactions
- [Decisions](decisions.md) — Key technical decisions and their rationale
- [Gotchas](gotchas.md) — Known issues, workarounds, failure patterns
- [Ops Runbook](ops-runbook.md) — Common operations, remote GPU workflows, troubleshooting
- [RAG Frontier Survey 2025–26](rag-frontier-2026.md) — Cutting-edge scan mapped to this system; embedding-upgrade + late-chunking levers; the pooling fork
- [Gate Audit Report Card](gate-audit.md) — **v6.4.** Rigorous audit of the golden eval gate (D+): statistical power, label completeness (44% incomplete), query realism, coverage. Significance harness. Why v6.3's embedding rejection is inconclusive.
- [DSPy Enrichment Plan](dspy-enrichment-plan.md) — **CLOSED.** Phase 1+2 done (DSPy lost the prompt gate); Phase 3 done — full-index enrichment regressed the hard gate (0.7907→0.7759) so it was **reverted**. Corpus stays no-enrichment. Post-mortem in [decisions.md](decisions.md).

## Project Summary

MCP server providing semantic search over 46 technical books to Claude Code. Pipeline: markitdown/PyMuPDF-TOC → tiktoken-sized chunker (with overlap) → enrichment → heading_path + Jina v5 + FastEmbed BM25 → Qdrant (DBSF fusion) → HyDE/multi-query → Ettin-150m reranking → adaptive cutoff → FastMCP.

## Current State

| Metric | Value |
|--------|-------|
| Version | v6.1 |
| Books indexed | 46 (19 ML + 5 DB + 7 security + 2 distributed + 13 Rust) |
| Total vectors | 48,056 (postgres re-chunked: 1,113→1,160) |
| Collection | `developer_knowledge` |
| MCP tools | 5 (search, search_book, get_chapter, list_books, grep_books) — `get_chapter`/`list_books` now work for postgres |
| Reranker | Ettin-150m (ModernBERT) — **per-domain input (v6.2): heading_path for ml/rust, child-only for security/db/distributed** (`descriptive-heading`, supersedes ⚡1's global heading) |
| Search latency | MCP search ≈3.2s (was ≈10.2s) after ⚡2 client singleton — lands on next server restart |
| Hard gate (NDCG@10) | **0.8021** (v6.1 0.7921) · easy 0.9379 (v6.1 0.9434, R@10 intact at 0.975) |
| Token counting | tiktoken cl100k_base (child max 250, parent max 1900) |
| PDF headings | PyMuPDF TOC reconstruction (markitdown fallback on CID-font garble) |
| Enriched chunks | **None (by decision).** Full-index enrichment was tested (problem-symptom prompt, 48K, DeepSeek) and REGRESSED the hard gate (0.7907→0.7759) → reverted. Corpus is index-now-enrich-never. Rejected enriched chunks preserved at `data/chunks_enriched_rejected/`. |
| Eval harness | `eval_retrieval.py` (+ `--hyde` mode, `KB_RERANK_INPUT` A/B) + 2× golden sets (`data/golden/`); hard-set gate NDCG 0.802 / R@10 0.930 |
| Enrichment LM | `deepseek-v4-flash` (thinking-off), replaces local Qwen |
| Downloaded (awaiting ingestion) | 7 advanced-ML PDFs + 118 OWASP cheat sheets + 2 scraped web books |
