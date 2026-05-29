# Developer Knowledge Base — Project Wiki

Last updated: 2026-05-29

## Quick Links

- [Architecture](architecture.md) — Pipeline design, data flow, component interactions
- [Decisions](decisions.md) — Key technical decisions and their rationale
- [Gotchas](gotchas.md) — Known issues, workarounds, failure patterns
- [Ops Runbook](ops-runbook.md) — Common operations, remote GPU workflows, troubleshooting
- [DSPy Enrichment Plan](dspy-enrichment-plan.md) — Planned v6 work: eval harness + prompt optimization

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
| Enriched chunks | none yet — index-now-enrich-later (deferred background pass) |
| Downloaded (awaiting ingestion) | 7 advanced-ML PDFs + 118 OWASP cheat sheets + 2 scraped web books |
