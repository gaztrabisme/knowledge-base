# Developer Knowledge Base — Project Wiki

Last updated: 2026-05-30 (DSPy sprint CLOSED — Phase 3: full-index enrichment lost the hard gate 0.7907→0.7759, REVERTED; corpus stays index-now-enrich-never)

## Quick Links

- [Architecture](architecture.md) — Pipeline design, data flow, component interactions
- [Decisions](decisions.md) — Key technical decisions and their rationale
- [Gotchas](gotchas.md) — Known issues, workarounds, failure patterns
- [Ops Runbook](ops-runbook.md) — Common operations, remote GPU workflows, troubleshooting
- [DSPy Enrichment Plan](dspy-enrichment-plan.md) — **CLOSED.** Phase 1+2 done (DSPy lost the prompt gate); Phase 3 done — full-index enrichment regressed the hard gate (0.7907→0.7759) so it was **reverted**. Corpus stays no-enrichment. Post-mortem in [decisions.md](decisions.md).

## Project Summary

MCP server providing semantic search over 46 technical books to Claude Code. Pipeline: markitdown/PyMuPDF-TOC → tiktoken-sized chunker (with overlap) → enrichment → heading_path + Jina v5 + FastEmbed BM25 → Qdrant (DBSF fusion) → HyDE/multi-query → Ettin-150m reranking → adaptive cutoff → FastMCP.

## Current State

| Metric | Value |
|--------|-------|
| Version | v6.0 |
| Books indexed | 46 (19 ML + 5 DB + 7 security + 2 distributed + 13 Rust) |
| Total vectors | 48,009 |
| Collection | `developer_knowledge` |
| MCP tools | 5 (search, search_book, get_chapter, list_books, grep_books) |
| Reranker | Ettin-150m (ModernBERT, 0.5994 NDCG@10) |
| Token counting | tiktoken cl100k_base (child max 250, parent max 1900) |
| PDF headings | PyMuPDF TOC reconstruction (markitdown fallback on CID-font garble) |
| Enriched chunks | **None (by decision).** Full-index enrichment was tested (problem-symptom prompt, 48K, DeepSeek) and REGRESSED the hard gate (0.7907→0.7759) → reverted. Corpus is index-now-enrich-never. Rejected enriched chunks preserved at `data/chunks_enriched_rejected/`. |
| Eval harness | `eval_retrieval.py` + 2× golden sets (`data/golden/`); hard-set gate NDCG 0.791 / R@10 0.925 |
| Enrichment LM | `deepseek-v4-flash` (thinking-off), replaces local Qwen |
| Downloaded (awaiting ingestion) | 7 advanced-ML PDFs + 118 OWASP cheat sheets + 2 scraped web books |
