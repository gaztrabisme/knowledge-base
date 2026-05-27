# Developer Knowledge Base — Project Wiki

Last updated: 2026-05-27

## Quick Links

- [Architecture](architecture.md) — Pipeline design, data flow, component interactions
- [Decisions](decisions.md) — Key technical decisions and their rationale
- [Gotchas](gotchas.md) — Known issues, workarounds, failure patterns
- [Ops Runbook](ops-runbook.md) — Common operations, remote GPU workflows, troubleshooting

## Project Summary

MCP server providing semantic search over 33 technical books to Claude Code. Pipeline: markitdown → chunker → enrichment → Jina v5 + FastEmbed BM25 → Qdrant (DBSF fusion) → FlashRank MiniLM-L-12 → FastMCP.

## Current State

| Metric | Value |
|--------|-------|
| Books indexed | 33 (19 ML + 5 DB + 7 security + 2 distributed) |
| Total vectors | 19,103 |
| Collection | `developer_knowledge` |
| MCP tools | 5 (search, search_book, get_chapter, list_books, grep_books) |
| Enriched chunks | 12,666 / 19,103 (ML only; new domains pending) |
| Index size | ~360MB |
