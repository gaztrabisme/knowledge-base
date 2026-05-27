# Developer Knowledge Base — MCP Server

A local MCP server that serves semantic search over technical books and guides to Claude Code during development sessions. Currently indexed: 19 ML sources with contextual enrichment. Expanding to Rust, databases, distributed systems, and security.

## Status: ML Collection Complete — Expansion In Progress

ML collection (19 sources) fully built with contextual enrichment applied (Qwen3.6-27B MTP, no-think mode). MCP server configured in `.mcp.json`, all 4 tools verified working. New domain sources (14 PDFs) downloaded, awaiting pipeline integration.

## Architecture

```
EPUBs (1.1GB, 18 books) + RAG Guide (9 markdown files)
  → markitdown (EPUB → markdown, preserves heading hierarchy)
  → HTML cleanup + front/back matter stripping
  → heading-aware parent/child chunker (H2-based splitting + small section merging)
  → (optional) LM Studio / llama-server contextual enrichment
  → Jina v5-text-small embeddings (1024-dim, sentence-transformers)
  → Qdrant hybrid index (dense + BM25 sparse, file-based)
  → FlashRank cross-encoder reranking
  → FastMCP server (4 tools)
  → Claude Code queries via MCP
```

## MCP Tools

- `search(query, top_k=10, book=None)` — hybrid semantic + keyword search across all books
- `search_book(book, query, top_k=5)` — scoped search within a single book
- `get_chapter(book, chapter)` — full text of a specific chapter
- `list_books()` — all indexed books with chapter listings

## Running the Server

```bash
python3 -m knowledge_base.server
```

Configured in `.mcp.json` for automatic Claude Code integration.

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
```

### Remote GPU Indexing (RTX 5080)

Indexing is ~10x faster on the SSH GPU machine vs local MPS.

```bash
# Transfer chunks to remote
rsync -avz data/chunks/ bppc@100.106.185.34:~/kb-work/chunks/

# Run indexing on GPU
ssh bppc@100.106.185.34 "source ~/kb-env/bin/activate && cd ~/kb-work && python3 remote_index.py ."

# Pull Qdrant data back
rsync -avz bppc@100.106.185.34:~/kb-work/qdrant/ data/qdrant/
```

### Remote Enrichment (llama-server)

```bash
# Start llama-server on remote (Qwen3.5-35B-A3B, ~50 tok/s)
ssh bppc@100.106.185.34 "cd ~/projects/llm-server && docker compose --profile llama-cpp up -d"

# Transfer chunks, run enrichment, pull back
rsync -avz data/chunks/ bppc@100.106.185.34:~/kb-work/chunks/
ssh bppc@100.106.185.34 "source ~/kb-env/bin/activate && cd ~/kb-work && python3 remote_enrich.py . http://localhost:8080/v1"
rsync -avz bppc@100.106.185.34:~/kb-work/chunks/ data/chunks/

# Then re-index (locally or remote)
python3 scripts/ingest_all.py --step index
```

## Project Structure

```
knowledge_base/
  config.py    — paths, model names, book metadata
  ingest.py    — EPUB → clean markdown (markitdown)
  chunk.py     — heading-aware parent/child chunker
  enrich.py    — contextual enrichment via LM Studio
  index.py     — Jina v5 embeddings + Qdrant indexing
  search.py    — hybrid search + FlashRank reranking
  server.py    — FastMCP MCP server
scripts/
  ingest_all.py    — end-to-end pipeline runner
  test_search.py   — manual search testing
  remote_index.py  — standalone GPU indexing script
  remote_enrich.py — standalone enrichment script
```

## Key Dependencies

- `markitdown` — EPUB to markdown conversion (preserves heading hierarchy)
- `fastmcp` — MCP server framework
- `qdrant-client` >= 1.18 — file-based vector store with native hybrid search
- `sentence-transformers` — Jina v5 embedding model
- `flashrank` — lightweight cross-encoder reranking
- `openai` — LM Studio / llama-server client for contextual enrichment

## Source Library

Books at: `knowledge-base/applied-ml/` | RAG guide at: `knowledge-base/production-rag-guide/`

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

## Corpus Stats

- 19 sources indexed (18 EPUB books + 1 RAG guide)
- 5,114 parent chunks, 12,666 child chunks (all contextually enriched)
- Parent avg: 467 tokens | Child avg: 187 tokens
- Embedding: Jina v5-text-small (677M params, 1024-dim)
- Vector store: Qdrant file-based (243MB)
- Contextual enrichment: applied via Qwen3.6-27B MTP (no-think mode, ~11.5 hours, 3.3s/chunk)

## Rework History

- **v1 (pandoc):** Flat H1 headings → tiny chunks (parent avg 295, child avg 35 tokens). 23,009 children.
- **v2 (markitdown):** Proper H1/H2/H3 hierarchy → right-sized chunks (parent avg 467, child avg 187 tokens). 12,666 children. Fewer, meatier chunks = better retrieval.
- **v3 (enrichment):** Contextual enrichment via Qwen3.6-27B MTP on remote GPU (llama-cpp-s016 profile, no-think mode). All 12,666 chunks enriched with 1-2 sentence context preambles. Re-indexed on RTX 5080. numpy float32 serialization bug fixed in search.py.

## Expansion Plan — Beyond ML

Expanding from ML-only to a general developer knowledge base. New domains downloaded, awaiting ingestion.

### Downloaded Sources (pending ingestion)

**Databases** (`knowledge-base/databases/`):
| File | Source | Size |
|------|--------|------|
| postgresql-14-internals.pdf | Postgres Professional (Rogov) | 6.3 MB |
| database-design-2nd-ed.pdf | OpenTextBC (Watt & Eng) | 2.8 MB |
| redis-for-dummies.pdf | Redis Inc | 5.9 MB |
| little-redis-book.pdf | Karl Seguin | 154 KB |
| digitalocean-redis.pdf | DigitalOcean | 1.1 MB |

**Distributed Systems** (`knowledge-base/distributed-systems/`):
| File | Source | Size |
|------|--------|------|
| designing-distributed-systems.pdf | Microsoft (Brendan Burns) | 314 KB |
| distributed-systems-fun-profit.html | Mikito Takada | 193 KB |

**Security** (`knowledge-base/security/`):
| File | Source | Size |
|------|--------|------|
| boneh-shoup-applied-cryptography.pdf | Stanford (Boneh & Shoup) | 11 MB |
| crypto-101.pdf | lvh | 15 MB |
| joy-of-cryptography.pdf | Rosulek | 4.8 MB |
| owasp-developer-guide.pdf | OWASP | 5.5 MB |
| owasp-wstg-v4.2.pdf | OWASP | 9.7 MB |
| owasp-asvs-v5.pdf | OWASP | 502 KB |
| oauth-rfcs-book.pdf | Aaron Parecki | 1.0 MB |

### Still Needed — Full Shopping List

#### Free PDF Downloads

**Advanced ML / Deep Learning** (`knowledge-base/advanced-ml/`):
| Book | Author | Pages | URL |
|------|--------|-------|-----|
| Dive into Deep Learning | Zhang et al. | 574 | [d2l.ai/d2l-en.pdf](https://d2l.ai/d2l-en.pdf) |
| The Little Book of Deep Learning v1.3 | Fleuret | 179 | [fleuret.org/public/lbdl.pdf](https://fleuret.org/public/lbdl.pdf) |
| Understanding Deep Learning (2023) | Prince | MIT Press | [udlbook.github.io/udlbook](https://udlbook.github.io/udlbook/) |
| Probabilistic ML vol 1: An Introduction | Murphy | ~900 | [probml.github.io/pml-book](https://probml.github.io/pml-book/) |
| Probabilistic ML vol 2: Advanced Topics | Murphy | ~900 | [probml.github.io/pml-book](https://probml.github.io/pml-book/) |
| Pattern Recognition & ML | Bishop | 740 | [microsoft.com/research](https://www.microsoft.com/en-us/research/uploads/prod/2006/01/Bishop-Pattern-Recognition-and-Machine-Learning-2006.pdf) |
| NVIDIA CUDA Programming Guide | NVIDIA | ~400 | [docs.nvidia.com/cuda](https://docs.nvidia.com/cuda/cuda-programming-guide/pdf/cuda-programming-guide.pdf) |

**Registration-gated (free but manual download):**
- Google Building Secure and Reliable Systems — [sre.google/books](https://sre.google/books/)
- Distributed Systems 4th Ed — [distributed-systems.net](https://www.distributed-systems.net/index.php/books/ds4/)
- Confluent books (Kafka, Event-Driven, Stream Processing) — [confluent.io](https://www.confluent.io/resources/)
- Red Hat Istio — [developers.redhat.com](https://developers.redhat.com/e-books/introducing-istio-service-mesh-microservices)
- Aqua Security Kubernetes Security — [aquasec.com](https://info.aquasec.com/kubernetes-security)
- Isovalent Container Security — [isovalent.com](https://isovalent.com/books/container-security/)
- Curity OAuth book — [curity.io](https://curity.io/resources/documents/cloud-native-data-security-oauth/)

**Can scrape/clone (free):**
- OWASP Cheat Sheet Series — [GitHub markdown](https://github.com/OWASP/CheatSheetSeries)
- Use The Index, Luke — [use-the-index-luke.com](https://use-the-index-luke.com/)
- The Internals of PostgreSQL — [interdb.jp/pg](https://www.interdb.jp/pg/)
- OAuth 2.0 Simplified — [oauth.com](https://www.oauth.com/)
- MIT 6.5940 EfficientML slides — [hanlab.mit.edu/courses/2024-fall-65940](https://hanlab.mit.edu/courses/2024-fall-65940)

#### Paid

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

**Skipped (dated or too theoretical):**
- Neural Network Methods for NLP (Goldberg, 2017) — pre-transformer
- Principles of Deep Learning Theory (Roberts) — physics-heavy, not practitioner-oriented
- Goodfellow Deep Learning print ($100) — HTML version free but hard to ingest; lower priority given Prince + Murphy cover modern ground

### Pipeline Changes Needed for Expansion

1. **PDF ingestion** — markitdown already supports PDF; add PDF glob to `ingest_all()`
2. **HTML scraping** — For web-only books (Use The Index Luke, PostgreSQL Internals, etc.)
3. **Per-domain directories** — Update `config.py` to scan multiple source dirs
4. **Collection strategy** — Consider per-domain Qdrant collections for independent rebuild

## Remote Enrichment Details

Best config for enrichment on the SSH GPU machine:

```bash
# Start MTP-enabled llama-server (Qwen3.6-27B, 74 tok/s with MTP)
ssh bppc@100.106.185.34 "cd ~/projects/llm-server && docker compose --profile llama-cpp-s016 up -d"

# Run enrichment with no-think mode (port 8081 for s016)
ssh bppc@100.106.185.34 "source ~/kb-env/bin/activate && cd ~/kb-work && \
  nohup bash -c 'exec python3 -u remote_enrich.py . http://localhost:8081/v1 > enrichment.log 2>&1' &"

# Monitor progress
ssh bppc@100.106.185.34 "tail -f ~/kb-work/enrichment.log"
```

Key settings in `remote_enrich.py`:
- `extra_body={"chat_template_kwargs": {"enable_thinking": False}}` — disables thinking mode
- `temperature=0.7, top_p=0.8` — Qwen recommended non-thinking sampling
- Saves progress every 50 chunks (resumable)
- ~3.3 sec/chunk, ~11.5 hours for 12,666 chunks
