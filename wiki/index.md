# Developer Knowledge Base — Project Wiki

Last updated: 2026-05-28

## Quick Links

- [Architecture](architecture.md) — Pipeline design, data flow, component interactions
- [Decisions](decisions.md) — Key technical decisions and their rationale
- [Gotchas](gotchas.md) — Known issues, workarounds, failure patterns
- [Ops Runbook](ops-runbook.md) — Common operations, remote GPU workflows, troubleshooting

## Project Summary

MCP server providing semantic search over 33 technical books to Claude Code. Pipeline: markitdown → chunker (with overlap) → enrichment → heading_path + Jina v5 + FastEmbed BM25 → Qdrant (DBSF fusion) → HyDE/multi-query → Ettin-150m reranking → adaptive cutoff → FastMCP.

## Current State

| Metric | Value |
|--------|-------|
| Version | v5.0 |
| Books indexed | 33 (19 ML + 5 DB + 7 security + 2 distributed) |
| Total vectors | ~19,728 |
| Collection | `developer_knowledge` |
| MCP tools | 5 (search, search_book, get_chapter, list_books, grep_books) |
| Reranker | Ettin-150m (ModernBERT, 0.5994 NDCG@10) |
| Enriched chunks | all (Qwen3.6-27B MTP) |
| Downloaded (awaiting ingestion) | 7 PDFs + 118 OWASP cheat sheets + 2 scraped web books |
