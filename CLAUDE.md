# Developer Knowledge Base — MCP Server

A local MCP server that serves semantic search over technical books to Claude Code during development sessions. 126 sources indexed across ML, AI engineering, databases, security, distributed systems, Rust, software architecture, software engineering, and systems/ops.

## Status: v7.1 — Manning AI shelf

126 books are indexed (132,623 vectors). v7.1 adds 17 books: 16 from Manning and one from O'Reilly. Fourteen cover AI and LLM
engineering, one covers optimization algorithms, and two cover software engineering (platform engineering and code
review). It also removes the two sources we wrote ourselves: the production RAG guide and the VinSpace research notes.
The corpus now contains published books only.

The hard gate is a 438-query benchmark, and it reads **NDCG 0.7704**. That is 0.0042 below v7.0 on the same queries,
a statistically significant drop: 30 queries regressed and 8 improved. Recall@10 (0.9680) and the retrieval ceiling
(0.9886) did not move. The benchmark cannot give credit for a new book, because every query was drawn from the original
46 books (see Known Limitations). The easy set reads 0.9108 (v7.0: 0.9115).

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

### ML (19 sources) — `knowledge-base/applied-ml/`

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
| optimization-algorithms | Search, metaheuristics, evolutionary and ML-based optimization (Khamis) |

### Databases (8 sources) — `knowledge-base/databases/`

| Book | Topic |
|------|-------|
| postgresql-14-internals | PostgreSQL internals (MVCC, WAL, indexes, vacuum) |
| database-design-2nd-ed | Relational database design |
| redis-for-dummies | Redis fundamentals |
| sql-relational-theory | SQL and Relational Theory, 3rd ed (Date) |
| use-the-index-luke | SQL indexing and tuning |
| postgresql-internals-interdb | The Internals of PostgreSQL (Suzuki) |
| little-redis-book | Redis concise guide |
| digitalocean-redis | Redis operations guide |

### Security (8 sources) — `knowledge-base/security/`

| Book | Topic |
|------|-------|
| boneh-shoup-applied-cryptography | Graduate-level cryptography (Boneh & Shoup) |
| crypto-101 | Cryptography fundamentals |
| joy-of-cryptography | Provable security, formal crypto |
| owasp-developer-guide | OWASP secure development |
| owasp-wstg-v4.2 | Web security testing methodology |
| owasp-asvs-v5 | Application security verification standard |
| oauth-rfcs-book | OAuth 2.0 RFC compilation |
| owasp-cheat-sheets | OWASP Cheat Sheet Series (118 documents) |

### AI Engineering (17 sources) — `knowledge-base/ai-engineering/`

| Book | Topic |
|------|-------|
| ai-engineering-huyen | Building applications on foundation models (Huyen) |
| designing-ml-systems-huyen | Production ML system design (Huyen) |
| agentic-design-patterns | Agent architecture patterns (Gulli) |
| ai-powered-search | Semantic search, learning to rank, RAG over search engines (Grainger et al.) |
| llms-in-production | Serving, evaluating and operating LLMs (Brousseau & Sharp) |
| building-reliable-ai-systems | LLM reliability, guardrails, evaluation in production (Shahani) |
| generative-ai-in-action | Enterprise generative AI patterns and RAG (Bahree) |
| transformers-in-action | Transformer architecture, fine-tuning, alignment (Koenigstein) |
| illustrated-guide-ai-agents | Agent anatomy: tools, memory, planning (Grootendorst & Alammar) |
| human-in-the-loop-ml | Active learning and annotation (Monarch) |
| interpretable-ai | Explainability methods for ML models (Thampi) |
| ml-platform-engineering | Building an MLOps platform from scratch (Tan, Padmanabha) |
| effective-conversational-ai | Designing and improving chatbots and assistants (Freed et al.) |
| coding-with-ai | AI-assisted software development (Morgan) |
| software-testing-with-genai | Using LLMs in software testing (Winteringham) |
| art-of-ai-product-development | AI product discovery and delivery (Lipenkova) |
| financial-ai-in-practice | ML and LLM applications in finance (Kim; early-access edition) |

### Software Engineering (24 sources) — `knowledge-base/software-engineering/`

The classic canon: Clean Code / Clean Architecture (Martin), DDD (Evans), PoEAA and Refactoring
(Fowler), Design Patterns (GoF), Enterprise Integration Patterns (Hohpe), Release It! (Nygard),
Continuous Delivery (Humble & Farley), Google SRE, CLRS, AIMA, SWEBOK, Pro Git, TDD by Example
(Beck), Growing OO Software Guided by Tests, REST in Practice, NoSQL Distilled, three
microservices titles, Effective Platform Engineering (Chankramath et al.), and "Looks Good to Me"
(Braganza) on code review.

### Systems / Ops (9 sources) — `knowledge-base/systems-ops/`

Linux administration, security hardening, kernel programming, systemd, shell scripting, Ubuntu,
Python networking, network observability, and Serious Python.

### Advanced ML Theory (7 PDFs) — `knowledge-base/advanced-ml/`

Dive into Deep Learning (Zhang et al.), Understanding Deep Learning (Prince), Probabilistic ML
Introduction + Advanced (Murphy), Pattern Recognition & ML (Bishop), The Little Book of Deep
Learning (Fleuret), and the NVIDIA CUDA Programming Guide.

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

- 126 sources indexed live; 132,623 child chunks (vectors) in the live collection
- Disk chunks total 132,678; the 55-chunk gap is postgresql-14-internals, whose on-disk
  re-chunk is corrupt and deliberately not indexed (see Known Limitations)
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

- **v7.0 (full corpus):** Indexed the remaining 50 staged sources (62,582 vectors) → 115 books
  / 117,695 vectors. Hard gate 0.8161 → 0.7737 NDCG (significant); recall@10 0.9841 → 0.9705;
  retrieval ceiling barely moved (0.9909 → 0.9886), so the reranker is demoting known-good hits
  rather than the retriever losing them. Diagnosed the v6.8 databases collapse as a corrupt
  postgresql-14-internals re-chunk, not new-book distraction.
- **v7.1 (Manning AI shelf):** Added 17 books (15,237 vectors) and removed `production-rag-guide` and
  the five `space-edge-ai` notes (309 vectors), giving 126 books and 132,623 vectors. `ingest.py`
  now also treats Manning-style `# 1 Title` / `# Part 1` headings as the start of content. The
  golden sets drop the 2 rows whose only answers were in the RAG guide in each set: hard
  440 → 438, easy 201 → 199. Removing the sources had no measurable effect (NDCG +0.0002, n.s.).
  Adding the books cost NDCG 0.0042 (significant), with recall unchanged.

## Known Limitations

- **Two markitdown versions are in use.** The 17 v7.1 books were converted with markitdown
  0.1.7 from the project `.venv`. Every earlier book was converted with the global 0.1.4. If an
  older book is re-ingested under `.venv`, its markdown will not be byte-identical, because 0.1.7
  escapes periods and spaces headings differently.
- **Three systems-ops books still carry back-of-book index chunks:** `masteringlinuxadministration`,
  `masteringpythonnetworking` and `ultimateubuntuhandbook`, 2,477 chunks in total, all live.
  `strip_index_backmatter.py --dry-run` flags them. Stripping them means deleting the matching
  points from Qdrant as well, so that the chunk files on disk and the index stay in step.

- **CID-font PDFs lose headings:** PDFs whose embedded subset fonts lack a ToUnicode CMap garble under PyMuPDF, so they auto-fall back to markitdown (clean body, no heading metadata). Only postgresql-14-internals is currently affected — search/grep work, but `get_chapter()` and chapter/section metadata are empty for it.
- **The on-disk postgresql-14-internals chunks have corrupt headings — do not index them.**
  The heading-restoration pass mis-assigned headings wholesale: BRIN/Bloom-filter text is
  headed `B-tree > Indexing JSON`, WAL checkpoint text is headed `Vacuum and Autovacuum`,
  merge-join plans are headed `Bitmap Scans`. Since heading_path is prepended to the embedding,
  every chunk would be embedded under the wrong topic. This is what collapsed the databases
  domain to 0.607 NDCG in the v6.8 gate. The live index still carries the older flat-but-correct
  chapter headings (`2 Isolation`, `24 Hash`), the golden labels match it, and `index_book`
  skips already-indexed books — so production is unaffected. Re-derive the headings before
  re-indexing that book. It is the only book whose disk chunks diverge from the live index.
- **The gate cannot reward corpus growth.** All 637 golden queries (438 hard + 199 easy) were
  drawn from the original 46 books; zero have any later-added book as the labeled positive.
  A new source can therefore only ever lower the score, never raise it, however good it is.
  Sampling the v7.0 regressions shows roughly half are better answers being scored as misses —
  `understanding-deep-learning` returning the actual SGD update rule, AIMA answering the Turing
  test question — and roughly half are genuine dilution (a local-vs-global-maxima question
  drifting to CLRS maximum-subarray). Settling which is which needs `pool_and_judge.py` over a
  regenerated pool, not a raw NDCG diff.
- **`ai-modern-approach` carries OCR garble:** text shows artifacts like `%ring Test` for
  "Turing Test" and `195O` for "1950". Search still reaches it; exact-phrase grep may not.
- **Enrichment pending:** v6 chunks carry heading_path + child_text but no contextual `context_text` yet. Retrieval works; the enrichment background pass will further sharpen recall on vocabulary-gap queries.

## Downloaded — Awaiting Ingestion

Nothing. Everything previously listed here (the 7 theory PDFs, the OWASP cheat sheets, and the
two scraped web books) is ingested and live as of v7.0. Historical listing:

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
