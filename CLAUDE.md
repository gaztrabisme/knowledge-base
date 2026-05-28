# Developer Knowledge Base — MCP Server

A local MCP server that serves semantic search over technical books to Claude Code during development sessions. 33 sources indexed across ML, databases, security, and distributed systems.

## Status: v4.1 — Fully Enriched, Expansion Sources Downloaded

33 books indexed (19,103 vectors), all chunks contextually enriched. 10 new sources downloaded (7 PDFs + 118 OWASP cheat sheets + 2 scraped web books) awaiting ingestion pipeline. Search pipeline: FastEmbed BM25, Qdrant DBSF fusion, MiniLM-L-12 reranker, grep_books tool.

## Architecture

```
EPUBs + PDFs + HTML
  → markitdown (format → markdown, preserves heading hierarchy)
  → HTML cleanup + front/back matter stripping (EPUBs only)
  → heading-aware parent/child chunker (H2-based splitting + small section merging)
  → (optional) contextual enrichment via LLM
  → Jina v5-text-small embeddings (1024-dim)
  → FastEmbed Qdrant/bm25 sparse vectors (proper tokenization + stopwords)
  → Qdrant hybrid index (dense + BM25 sparse, DBSF fusion, file-based)
  → MiniLM-L-12 FlashRank cross-encoder reranking
  → FastMCP server (5 tools)
  → Claude Code queries via MCP
```

## MCP Tools

- `search(query, top_k=10, book=None)` — hybrid semantic + keyword search across all books
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
  search.py    — hybrid search (DBSF fusion) + FlashRank MiniLM-L-12 reranking
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
- `flashrank` — MiniLM-L-12 cross-encoder reranking (34MB)
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

### Distributed Systems (2 sources) — `knowledge-base/distributed-systems/`

| Book | Topic |
|------|-------|
| designing-distributed-systems | Distributed system patterns (Burns/Microsoft) |
| distributed-systems-fun-profit | Distributed systems theory |

## Corpus Stats

- 33 sources indexed (18 EPUBs + 14 PDFs/HTML + 1 markdown guide)
- 5,825 parent chunks, 19,103 child chunks (vectors)
- **All 19,103 chunks contextually enriched** (Qwen3.6-27B MTP, no-think mode)
- Embedding: Jina v5-text-small (677M params, 1024-dim)
- Sparse: FastEmbed Qdrant/bm25 (proper tokenization, stopwords, IDF)
- Reranker: FlashRank MiniLM-L-12-v2 (34MB, 12-layer cross-encoder)
- Fusion: Qdrant DBSF (Distribution-Based Score Fusion) via prefetch API
- Vector store: Qdrant file-based, collection `developer_knowledge` (~370MB)

## Version History

- **v1 (pandoc):** Flat H1 headings → tiny chunks (parent avg 295, child avg 35 tokens). 23,009 children.
- **v2 (markitdown):** Proper H1/H2/H3 hierarchy → right-sized chunks. 12,666 children.
- **v3 (enrichment):** Contextual enrichment via Qwen3.6-27B MTP. All 12,666 ML chunks enriched.
- **v4 (multi-domain + pipeline upgrade):** Expanded to 33 books (19,103 vectors). Upgraded reranker (TinyBERT → MiniLM-L-12), BM25 tokenizer (regex → FastEmbed), fusion (client-side RRF → Qdrant DBSF). Added grep_books tool. PDF/HTML ingestion support.
- **v4.1 (full enrichment + expansion downloads):** All 19,103 chunks enriched (ML + databases + security + distributed systems). Re-indexed with enriched embeddings. Downloaded 7 free PDFs, 118 OWASP cheat sheets, and 2 scraped web books for next ingestion batch.

## Known Limitations

- **PDF heading structure:** markitdown extracts text but loses heading hierarchy from PDFs. Chunker falls back to paragraph-based splitting. Chunks are well-sized but metadata (chapter, section) is empty for PDF-sourced books.

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
- Rust Systems Programming Bundle — 13 Packt books

**Individual books (~$237 total):**
| Book | Author | Price | Domain |
|------|--------|-------|--------|
| Programming Massively Parallel Processors 5th ed | Hwu/Kirk | ~$62 | GPU/CUDA |
| Designing Data-Intensive Applications | Kleppmann | ~$45 | Distributed Systems |
| Database Internals | Petrov | ~$45 | Databases |
| Serious Cryptography 2nd Ed | Aumasson | ~$30 | Security |
| API Security in Action | Madden | ~$40 | Security |
| Microservices Patterns | Richardson | ~$50 | Distributed Systems |

## Research Decisions (from v4 sprint)

- **GraphRAG/LightRAG:** Skipped. Our structured books + enrichment + hybrid search already handles cross-concept queries. LLM cost for graph construction not justified. Lighter alternatives (concept tagging, entity-to-chunk index) available if needed later.
- **TurboVec:** Not a fit at our scale (~19K chunks). Impressive Rust ANN index but replaces only the dense vector part of Qdrant. Revisit at 100K+ chunks.
- **SPLADE++:** Available via FastEmbed if BM25 quality isn't sufficient. Current Qdrant/bm25 is the pragmatic choice.
- **Larger rerankers (BGE, Jina):** Better NDCG but blow the 500ms latency budget on Apple Silicon. MiniLM-L-12 is the sweet spot for local Mac use.
