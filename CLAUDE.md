# Developer Knowledge Base — MCP Server

A local MCP server that serves semantic search over technical books to Claude Code during development sessions. 65 sources indexed across ML, databases, security, distributed systems, Rust, and software architecture.

## Status: v6.9 — Architecture Shelf

65 books indexed (55,113 vectors). 19 O'Reilly software-architecture books added and gated:
paired bootstrap + sign test + Wilcoxon over the 440-query hard set return *noise (n.s.)* on
every metric (NDCG delta -0.0057, below the gate's 0.0085 detection floor; 15 queries improved,
18 regressed). O'Reilly front matter is now stripped — the pattern list had been Packt-only.

PDF heading hierarchy comes from PyMuPDF TOC reconstruction, with a markitdown fallback when CID-font garble is detected. Chunk sizing uses real tiktoken counts (child max 250, parent max 1900). Chunks are embedded from heading_path + child_text; contextual enrichment is a deferred background pass (index-now-enrich-later).

## Architecture

```
EPUBs + PDFs + HTML
  → markitdown (EPUB/HTML) | PyMuPDF TOC reconstruction (PDF, markitdown fallback on CID-font garble)
  → HTML cleanup + front/back matter stripping
  → tiktoken-sized heading-aware parent/child chunker (H2-based splitting + small section merging + section overlap + hard-split oversized blocks)
  → (deferred) contextual enrichment via LLM
  → heading_path + context_text + child_text → Jina v5-text-small embeddings (1024-dim)
  → FastEmbed Qdrant/bm25 sparse vectors (proper tokenization + stopwords)
  → Qdrant hybrid index (dense + BM25 sparse, DBSF fusion, file-based)
  → HyDE + multi-query expansion (agent-provided, no LLM dependency)
  → Ettin-150m cross-encoder reranking (sentence-transformers, ModernBERT)
  → adaptive score cutoff (absolute floor + min results)
  → FastMCP server (5 tools)
  → Claude Code queries via MCP
```

## MCP Tools

- `search(query, top_k=10, book=None, hyde_passage=None, extra_queries=None)` — hybrid semantic + keyword search across all books
- `search_book(book, query, top_k=5)` — scoped search within a single book
- `get_chapter(book, chapter)` — full text of a specific chapter
- `list_books()` — all indexed books with chapter listings
- `grep_books(pattern, book=None, max_results=20)` — exact-match keyword search via ripgrep

## Running the Server

```bash
python3 -m knowledge_base.server
```

Configured in `.mcp.json` (project) and `~/.claude.json` (global, via PYTHONPATH).

## Pipeline Commands

```bash
# Full pipeline (ingest → chunk → index)
python3 scripts/ingest_all.py

# Individual steps
python3 scripts/ingest_all.py --step ingest
python3 scripts/ingest_all.py --step chunk
python3 scripts/ingest_all.py --step enrich   # requires LM Studio at localhost:1234
python3 scripts/ingest_all.py --step index

# Test search
python3 scripts/test_search.py "your query here" --top-k 5
python3 scripts/test_search.py "query" --book some-book-slug --no-rerank
```

### Remote GPU Indexing (RTX 5080)

Indexing is ~10x faster on the SSH GPU machine vs local CPU.

```bash
# Transfer chunks to remote
rsync -avz data/chunks/ bppc@100.106.185.34:~/kb-work/chunks/
rsync -avz scripts/remote_index.py bppc@100.106.185.34:~/kb-work/

# Run indexing on GPU
ssh bppc@100.106.185.34 "source ~/kb-env/bin/activate && cd ~/kb-work && python3 remote_index.py ."

# Pull Qdrant data back
rsync -avz bppc@100.106.185.34:~/kb-work/qdrant/ data/qdrant/
```

**Remote machine requirements:** `pip install fastembed sentence-transformers qdrant-client` in `~/kb-env/`.

### Remote Enrichment (llama-server)

```bash
# Start MTP-enabled llama-server (Qwen3.6-27B, 74 tok/s with MTP)
ssh bppc@100.106.185.34 "cd ~/projects/llm-server && docker compose --profile llama-cpp-s016 up -d"

# Transfer chunks, run enrichment, pull back
rsync -avz data/chunks/ bppc@100.106.185.34:~/kb-work/chunks/
ssh bppc@100.106.185.34 "source ~/kb-env/bin/activate && cd ~/kb-work && \
  nohup bash -c 'exec python3 -u remote_enrich.py . http://localhost:8081/v1 > enrichment.log 2>&1' &"
rsync -avz bppc@100.106.185.34:~/kb-work/chunks/ data/chunks/

# Then re-index
python3 scripts/ingest_all.py --step index
```

## Project Structure

```
knowledge_base/
  config.py    — paths, model names, book metadata (33 entries)
  ingest.py    — EPUB/PDF/HTML → clean markdown (markitdown)
  chunk.py     — heading-aware parent/child chunker
  enrich.py    — contextual enrichment via LM Studio
  index.py     — Jina v5 dense + FastEmbed BM25 sparse → Qdrant
  search.py    — hybrid search (DBSF fusion) + Ettin-150m cross-encoder reranking + adaptive cutoff
  server.py    — FastMCP MCP server (5 tools)
scripts/
  ingest_all.py    — end-to-end pipeline runner
  test_search.py   — manual search testing
  remote_index.py  — standalone GPU indexing script (self-contained, rsync-deployable)
  remote_enrich.py — standalone enrichment script
```

## Key Dependencies

- `markitdown` — EPUB/PDF/HTML to markdown conversion
- `fastmcp` — MCP server framework
- `qdrant-client` >= 1.12 — file-based vector store with native hybrid search + DBSF fusion
- `sentence-transformers` — Jina v5-text-small embedding model (677M params, 1024-dim)
- `fastembed` — Qdrant/bm25 sparse text embeddings (proper tokenization + stopwords)
- `sentence-transformers` — Ettin-150m cross-encoder reranking (ModernBERT, 151M params)
- `openai` — LM Studio / llama-server client for contextual enrichment

## Source Library

### ML (19 sources) — `knowledge-base/applied-ml/` + `production-rag-guide/`

| Book | Topic |
|------|-------|
| kagglebook_secondedition | Competition tactics, ensembling, feature eng |
| machinelearningwithpytorchandscikit-learn | Core ML with PyTorch + sklearn |
| masteringpytorch_secondedition | Advanced PyTorch patterns |
| bayesiananalysiswithpython_thirdedition | Bayesian methods, PyMC |
| moderntimeseriesforecastingwithpython_secondedition | Time series, forecasting |
| causalinferenceanddiscoveryinpython | Causal ML |
| deepreinforcementlearninghands-on_thirdedition | Deep RL |
| graphmachinelearning_secondedition | Graph neural networks |
| machinelearningengineeringwithpython_secondedition | MLOps, pipelines, deployment |
| scikit-learncookbook_thirdedition | sklearn recipes |
| pythonmachinelearningbyexample_fourthedition | Applied ML patterns |
| mathematicsofmachinelearning | Math foundations |
| pandascookbook_thirdedition | Data manipulation |
| machinelearningforalgorithmictradingsecondedition | Quant ML |
| artificialintelligenceforcybersecurity | Security ML |
| hands-onartificialintelligenceforiot_secondedition | Edge/IoT ML |
| azureai-102certificationessentials | Azure AI services |
| hands-onmachinelearningwithcplusplus_secondedition | C++ ML implementations |
| production-rag-guide | Production RAG systems (9 chapters) |

### Databases (5 sources) — `knowledge-base/databases/`

| Book | Topic |
|------|-------|
| postgresql-14-internals | PostgreSQL internals (MVCC, WAL, indexes, vacuum) |
| database-design-2nd-ed | Relational database design |
| redis-for-dummies | Redis fundamentals |
| little-redis-book | Redis concise guide |
| digitalocean-redis | Redis operations guide |

### Security (7 sources) — `knowledge-base/security/`

| Book | Topic |
|------|-------|
| boneh-shoup-applied-cryptography | Graduate-level cryptography (Boneh & Shoup) |
| crypto-101 | Cryptography fundamentals |
| joy-of-cryptography | Provable security, formal crypto |
| owasp-developer-guide | OWASP secure development |
| owasp-wstg-v4.2 | Web security testing methodology |
| owasp-asvs-v5 | Application security verification standard |
| oauth-rfcs-book | OAuth 2.0 RFC compilation |

### Architecture (19 sources) — `knowledge-base/architecture/`

| Book | Topic |
|------|-------|
| software-architect-elevator | The architect's role across org levels (Hohpe) |
| software-architecture-hard-parts | Distributed architecture trade-off analysis |
| building-evolutionary-architectures | Fitness functions, architectural change |
| software-architecture-metrics | Measuring architecture quality |
| facilitating-software-architecture | Decentralized architecture practice, ADRs |
| fundamentals-enterprise-architecture | EA concepts and practice |
| semantic-software-design | Design philosophy and semantics |
| learning-systems-thinking | Systems thinking for engineers |
| architecture-patterns-with-python | DDD/ports-and-adapters/CQRS in Python |
| learning-domain-driven-design | DDD strategic + tactical (Khononov) |
| building-microservices-2e | Microservices, 2nd ed (Newman) |
| building-event-driven-microservices | Event-driven microservices, 2nd ed |
| designing-distributed-systems-2e | Distributed patterns, 2nd ed (Burns) |
| building-multi-tenant-saas | Multi-tenant SaaS architecture |
| building-medallion-architectures | Bronze/silver/gold data architecture |
| flow-architectures | Event-driven integration, real-time flow |
| mastering-api-architecture | API design, testing, evolution, gateways |
| learning-api-styles | REST/GraphQL/gRPC/async API styles |
| building-green-software | Carbon-aware and energy-efficient systems |

### Distributed Systems (2 sources) — `knowledge-base/distributed-systems/`

| Book | Topic |
|------|-------|
| designing-distributed-systems | Distributed system patterns (Burns/Microsoft) |
| distributed-systems-fun-profit | Distributed systems theory |

### Rust (13 sources) — `knowledge-base/rust/`

| Book | Topic |
|------|-------|
| asynchronousprogramminginrust | Async/await, futures, executors |
| creativeprojectsforrustprogrammers | Project-based Rust (web, DB, WASM, ML) |
| designpatternsandbestpracticesinrust | Idiomatic patterns |
| gamedevelopmentwithrustandwebassembly | Rust + WASM game dev |
| hands-onconcurrencywithrust | Concurrency, parallelism |
| practicalsystemprogrammingforrustdevelopers | Systems programming |
| rust_ebook | Rust fundamentals (Nouman Azam) |
| rustforblockchainapplicationdevelopment | Blockchain in Rust |
| rustforcplusplusdeveloper | Rust for C++ devs |
| rustprogramminghandbook | Comprehensive Rust handbook |
| rustwebdevelopmentwithrocket | Web dev with Rocket |
| rustwebprogramming | Full-stack Rust web |
| speedupyourpythonwithrust | PyO3, Rust extensions for Python |

## Corpus Stats

- 65 sources indexed live (50 EPUBs + 14 PDFs/HTML + 1 markdown guide)
- 55,113 child chunks (vectors) in the live collection
- 115 sources chunked on disk (117,750 children) — 50 are staged but unindexed, see Known Limitations
- **Not yet enriched** — index-now-enrich-later: embedded with heading_path + child_text only; contextual enrichment is a deferred background pass
- Token counting: tiktoken `cl100k_base` (≈ Jina v5 tokenizer within ~2%). Child max 250 / min 75, parent max 1900 tokens
- Embedding: heading_path + context_text + child_text → Jina v5-text-small (677M params, 1024-dim)
- Sparse: FastEmbed Qdrant/bm25 (proper tokenization, stopwords, IDF)
- Reranker: Ettin-150m cross-encoder (ModernBERT, 151M params, 0.5994 NDCG@10)
- Fusion: Qdrant DBSF (Distribution-Based Score Fusion) via prefetch API
- Adaptive cutoff: score floor 4.0, min results 3
- Vector store: Qdrant server at `127.0.0.1:6333` (KB_QDRANT_URL), collection `developer_knowledge`;
  falls back to the embedded file store at `data/qdrant` when the server is down

## Version History

- **v1 (pandoc):** Flat H1 headings → tiny chunks (parent avg 295, child avg 35 tokens). 23,009 children.
- **v2 (markitdown):** Proper H1/H2/H3 hierarchy → right-sized chunks. 12,666 children.
- **v3 (enrichment):** Contextual enrichment via Qwen3.6-27B MTP. All 12,666 ML chunks enriched.
- **v4 (multi-domain + pipeline upgrade):** Expanded to 33 books (19,103 vectors). Upgraded reranker (TinyBERT → MiniLM-L-12), BM25 tokenizer (regex → FastEmbed), fusion (client-side RRF → Qdrant DBSF). Added grep_books tool. PDF/HTML ingestion support.
- **v4.1 (full enrichment + expansion downloads):** All 19,103 chunks enriched (ML + databases + security + distributed systems). Re-indexed with enriched embeddings. Downloaded 7 free PDFs, 118 OWASP cheat sheets, and 2 scraped web books for next ingestion batch.
- **v5 (search intelligence):** Reranker upgraded to Ettin-150m (ModernBERT, +0.093 NDCG@10 over MiniLM-L-12). Adaptive score cutoff filters noise (absolute floor 4.0). HyDE and multi-query exposed as agent-provided input parameters (no LLM dependency). Parent chunk overlap at H2 section boundaries. Heading path prepended to embeddings. Re-chunked to 19,728 vectors. Dev skill integration (KB in Available Tools + Research Subagent briefs).
- **v6 (corpus expansion + ingestion quality):** Expanded to 46 books / 48,009 vectors (added 13 Rust books). PDF heading hierarchy recovered via PyMuPDF TOC reconstruction (resolves v5 PDF limitation). tiktoken-based chunk sizing (child max 250, parent max 1900). Hard-split for oversized blocks. Fixed two ingestion bugs: "Chapter N" appendix misfire in front-matter stripping, and CID-font garble auto-fallback to markitdown (postgresql-14-internals). BM25 keyword parameter + metadata-enriched enrichment prompt. Indexed without enrichment (index-now-enrich-later); enrichment is a deferred background pass.
- **v6.7 (index-chunk strip):** Removed 6,276 back-of-book index chunks — page-number noise that
  was displacing real content. Gate restored to 440 queries by regenerating 12 dropped ones (v6.7.1).
- **v6.8 (staged expansion):** Ingested and chunked 50 more sources (ai-engineering,
  software-engineering, systems-ops, space-edge-ai, 7 theory PDFs, OWASP cheat sheets) and added
  the `read_chunk` MCP tool. The corpus is on disk; the index build was gated and not promoted.
- **v6.9 (architecture shelf):** Added 19 O'Reilly architecture/microservices/API books
  (13,333 vectors) → 65 books / 55,113 vectors. O'Reilly front-matter stripping added to
  `ingest.py` (praise pages, revision history, "How to Contact Us"), plus a positive
  content-start rule for titled `Part I.` / `Chapter 1.` headings. Dropped
  `building-microservices.pdf`, a 102-page CID-garbled preview sampler, in favour of the
  full 2nd-edition EPUB. Gate: noise (n.s.) on all metrics vs v6.7.1.

## Known Limitations

- **CID-font PDFs lose headings:** PDFs whose embedded subset fonts lack a ToUnicode CMap garble under PyMuPDF, so they auto-fall back to markitdown (clean body, no heading metadata). Only postgresql-14-internals is currently affected — search/grep work, but `get_chapter()` and chapter/section metadata are empty for it.
- **50 books staged but unindexed:** the ai-engineering / software-engineering / systems-ops /
  space-edge-ai batch and the 7 theory PDFs are ingested and chunked but not in the live index.
  The v6.8 gate scored them as a regression (hard NDCG 0.8218 → 0.7871); that verdict is not
  trustworthy — see the next two entries.
- **Golden labels for postgresql-14-internals are stale:** that book was re-chunked during the
  heading-restoration work, which renumbered its chunk ids. All 6 hard-set and both easy-set
  postgres queries now point at dead ids or unrelated sections, so the gate scores correct
  retrievals as misses. This alone produced the v6.8 databases collapse (0.888 → 0.607 NDCG).
  Regenerate those labels before trusting any databases-domain gate number.
- **Single-book ground truth penalizes better answers:** on the v6.8 run, `d2l-en` took 70 of
  the displaced top-10 slots, with `probml-*`, `understanding-deep-learning` and the OWASP
  cheat sheets behind it. Sampled cases are mostly equal-or-better answers scored as misses
  because only one book's parent is labeled positive. Settling this needs `pool_and_judge.py`,
  not a raw NDCG diff.
- **Enrichment pending:** v6 chunks carry heading_path + child_text but no contextual `context_text` yet. Retrieval works; the enrichment background pass will further sharpen recall on vocabulary-gap queries.

## Downloaded — Awaiting Ingestion

### Advanced ML / Deep Learning (7 PDFs) — `knowledge-base/advanced-ml/`

| File | Source | Size |
|------|--------|------|
| d2l-en.pdf | Dive into Deep Learning (Zhang et al.) | 43MB |
| lbdl.pdf | The Little Book of Deep Learning (Fleuret) | 4.5MB |
| understanding-deep-learning.pdf | Understanding Deep Learning (Prince) | 21MB |
| probml-intro.pdf | Probabilistic ML: Introduction (Murphy) | 19MB |
| probml-advanced.pdf | Probabilistic ML: Advanced Topics (Murphy) | 71MB |
| bishop-prml.pdf | Pattern Recognition & ML (Bishop) | 17MB |
| cuda-programming-guide.pdf | NVIDIA CUDA Programming Guide | 4.4MB |

### Scraped Web Sources — already in source dirs

| File | Source | Size |
|------|--------|------|
| `security/owasp-cheat-sheets/` (118 .md files) | OWASP Cheat Sheet Series | 2.5MB |
| `databases/use-the-index-luke.md` | Use The Index, Luke (SQL indexing) | 62KB |
| `databases/postgresql-internals-interdb.md` | The Internals of PostgreSQL (Suzuki) | 31KB |

**To ingest:** Add BOOKS entries to `config.py` + `remote_index.py`, run `ingest_all.py --step ingest`, chunk, index.

## Expansion — Still Needed

**Registration-gated (free but manual download):**
- Google Building Secure and Reliable Systems — [sre.google/books](https://sre.google/books/)
- Distributed Systems 4th Ed — [distributed-systems.net](https://www.distributed-systems.net/index.php/books/ds4/)
- Confluent books (Kafka, Event-Driven, Stream Processing) — [confluent.io](https://www.confluent.io/resources/)

**Can scrape/clone (free):**
- MIT 6.5940 EfficientML slides — [hanlab.mit.edu](https://hanlab.mit.edu/courses/2024-fall-65940)

### Paid

**Humble Bundle ($18, expires June 4 2026):**
- ~~Rust Systems Programming Bundle — 13 Packt books~~ ✅ ingested in v6

**Individual books (~$237 total):**
| Book | Author | Price | Domain |
|------|--------|-------|--------|
| Programming Massively Parallel Processors 5th ed | Hwu/Kirk | ~$62 | GPU/CUDA |
| Designing Data-Intensive Applications | Kleppmann | ~$45 | Distributed Systems |
| Database Internals | Petrov | ~$45 | Databases |
| Serious Cryptography 2nd Ed | Aumasson | ~$30 | Security |
| API Security in Action | Madden | ~$40 | Security |
| Microservices Patterns | Richardson | ~$50 | Distributed Systems |

## Research Decisions

### v5 sprint
- **Ettin-150m over Jina v3 / Qwen3-Reranker:** Ettin-150m (ModernBERT, 151M, Apache 2.0) beats Jina v3 (0.5994 vs 0.5856 NDCG@10) at fraction of size. PyTorch at 0.17s/50-docs on Apple Silicon — no ONNX needed.
- **ONNX/CoreML acceleration:** Blocked. `optimum` requires `transformers<4.58`, ModernBERT needs `>=5.2.0`. PyTorch is fast enough (sub-200ms reranking). Revisit when optimum supports transformers 5.x.
- **Gap-based adaptive cutoff:** Rejected after calibration. Ettin's smooth score distributions make median-gap detection trigger at position 1-2 (too aggressive). Absolute score floor (4.0) cleanly separates noise from signal across all query types.
- **HyDE/multi-query as agent params:** Better than local LLM. Zero latency overhead — Claude generates the hypothetical passage and query expansions as part of the tool call. No dependency on LM Studio or any inference server.

### v4 sprint
- **GraphRAG/LightRAG:** Skipped. Our structured books + enrichment + hybrid search already handles cross-concept queries. LLM cost for graph construction not justified.
- **TurboVec:** Not a fit at our scale (~19K chunks). Impressive Rust ANN index but replaces only the dense vector part of Qdrant. Revisit at 100K+ chunks.
- **SPLADE++:** Available via FastEmbed if BM25 quality isn't sufficient. Current Qdrant/bm25 is the pragmatic choice.
