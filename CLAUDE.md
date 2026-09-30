# Developer Knowledge Base — MCP Server

A local MCP server that serves semantic search over technical books to Claude Code during development sessions. 320 technical sources are indexed across 19 domains. A separate philosophy collection holds the Original Library, three Tao Te Ching translations and Zhuan Falun, searchable in English, Vietnamese and Chinese.

## Status: v9 — sales and research-methods shelves

**Technical collection.** 320 books are indexed (286,723 vectors). v9 adds 29 books (20,076 vectors): two new domains, sales (10 books) and research methods (6 books), plus 13 books across the existing domains (management, security, systems/ops, software engineering, AI engineering, design, frontend, C++).

The v9 gate compares the candidate with v8 on the same GPU:

| Set | Metric | v8 | v9 |
|---|---|---|---|
| Hard (438 queries) | NDCG@10 | 0.7429 | 0.7409 |
| | Recall@10 | 0.9521 | 0.9521 |
| Easy (199 queries) | NDCG@10 | 0.9043 | 0.9044 |
| Sanity (29 queries written from the new books) | Recall@10 | — | 0.793 |

The candidate failed one of three promotion conditions set in advance: sanity recall@10 was 0.793 (23/29) against a threshold of 0.80, while both hard-set conditions passed. A blind review of the sanity queries afterwards scored 0.821 (23/28). Gary promoted the candidate on 2026-09-30 despite the failed condition, as happened for v8. See `data/bench/gate-v9.md` and Known Limitations.

The live name `developer_knowledge` is a Qdrant alias for the collection `developer_knowledge_v9`. The v8 collection stays on the server for rollback.

**Philosophy collection.** `philosophy` holds 8,432 vectors, kept apart from technical search so it cannot dilute it. It covers:
- the Original Library in Vietnamese (the source), English and Traditional Chinese, 38 sections each;
- Tao Te Ching translations by Stephen Mitchell and Jonathan Star (English) and Tse Lao (Spanish);
- Zhuan Falun in English, Vietnamese and Simplified Chinese, plus a Traditional Chinese text converted from the Simplified.

Sections are aligned across translations, so a hit returns the matching passages in the other languages. The 60-query multilingual eval reads recall@10 of 0.867 for English, 0.867 for Vietnamese, 0.800 for Chinese and 1.000 cross-language.

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
  → FastMCP server (8 tools: 6 technical, 2 philosophy)
  → Claude Code queries via MCP

Philosophy collection (separate Qdrant collection `philosophy`):
  PDF/EPUB per work and language → markdown sections keyed for alignment (ol-01…38, ttc-001…081, zfl-L1…L9)
  → Chinese text check (share of characters outside a common-character list; garbled editions rejected)
  → Jina v5 dense + custom sparse (words; CJK unigrams+bigrams after OpenCC Traditional→Simplified) + FastEmbed BM25
  → reranker routed by query language: Ettin for plain-ASCII (English) queries, BGE-reranker-v2-m3 otherwise
  → each hit carries up to two aligned passages from every other translation of the same work
```

## MCP Tools

- `search(query, top_k=10, book=None, hyde_passage=None, extra_queries=None, bm25_keywords=None, detail="brief")` — hybrid semantic + keyword search across all books. `brief` returns the matched passage; `full` returns the whole parent section. `book` takes a slug or a title and suggests near matches.
- `search_book(book, query, top_k=5, detail="brief")` — the same search scoped to one book
- `read_chunk(chunk_id, window=1)` — a search hit with its neighbouring passages
- `get_chapter(book, chapter)` — full text of a chapter, by title or number
- `list_books(book=None)` — the catalog (one line per book), or one book's chapters
- `grep_books(pattern, book=None, max_results=20)` — exact-match keyword search via ripgrep
- `search_philosophy(query, top_k=5, language=None, work=None, parallel=True)`: searches the separate philosophy collection. Each hit carries up to two aligned passages from each other translation. The Original Library is the entry point.
- `list_philosophy(work=None)`: the philosophy works and their languages, or one work's aligned sections.

The six technical tools never return philosophy content, and their signatures are unchanged from v7.1, the A1 interface.

`hyde_passage`, `extra_queries` and `bm25_keywords` are optional. The agent benchmark
(`wiki/interface-bench.md`) found that pushing small agents to write HyDE passages or to pick
books first loses answers, so the tool descriptions leave them as options.

## Running the Server

```bash
python3 -m knowledge_base.server
```

Configured in `.mcp.json` (project) and `~/.claude.json` (global, via PYTHONPATH).

`KB_EDITION=core|full` picks the tool set: core serves the 6 technical tools, full adds the 2 philosophy tools. Unset, it is full when `data/chunks/philosophy/` exists. When `KB_QDRANT_BIN` is set and nothing answers at `KB_QDRANT_URL`, the server starts that Qdrant binary itself on storage `KB_QDRANT_STORAGE` (`knowledge_base/qdrant_boot.py`); this Mac leaves it unset because launchd runs Qdrant.

## Distribution

The private repo is `gaztrabisme/knowledge-base`. Other machines install it with `install.ps1` (Windows) or `install.sh` (macOS/Linux) and a fine-grained GitHub token that can only read this repo; `README.md` is the guide for that reader.

- Data ships as GitHub Release `data-v9`: `kb-core.part00` (technical snapshot, markdown, chunks), `kb-philosophy.part00`, and `manifest.json` with point counts and sha256 per part.
- Rebuild the release after an index change: `uv run python scripts/package_release.py` (snapshots the live Qdrant, writes `dist/release/`), then upload under a new tag and bump the installer's `--release-tag` default.
- `scripts/install.py --dir <dir> --edition core|full [--update] [--qdrant-port N]` downloads and verifies the parts, fetches the pinned Qdrant binary, restores the snapshots, and runs `claude mcp add`.

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
  config.py    — paths, model names, SOURCE_DIRS (17 domains), BOOKS (291 entries)
  ingest.py    — EPUB/PDF/HTML → clean markdown (markitdown / PyMuPDF TOC), front/back-matter rules
  chunk.py     — heading-aware parent/child chunker (enforces the 250/1900-token caps)
  enrich.py    — contextual enrichment via LM Studio
  index.py     — Jina v5 dense + FastEmbed BM25 sparse → Qdrant
  search.py    — hybrid search (DBSF fusion) + Ettin-150m cross-encoder reranking + adaptive cutoff
  server.py    — FastMCP MCP server (8 tools)
  philosophy/  — alignment, chunking, Chinese text check, CJK sparse tokenizer, search with parallels
scripts/
  ingest_all.py            — end-to-end pipeline runner
  build_intake_manifest.py / check_intake.py — register a folder of new books (v8 intake)
  audit_markdown.py        — per-book ingest quality audit (--strict)
  regression_ingest.py     — re-ingest sample books and diff against data/markdown
  remote_index.py          — standalone GPU indexing script (self-contained, rsync-deployable)
  merge_collection.py      — build/verify a candidate collection; promote by Qdrant alias
  eval_retrieval.py        — the retrieval gate (--golden picks the query set)
  ingest_philosophy.py / remote_index_philosophy.py / load_philosophy.py / eval_philosophy.py
  remote_enrich.py         — standalone enrichment script
data/
  intake/       — v8 manifest, audit exceptions, C1/C2 reports (tracked)
  philosophy/   — works.json registry, eval set, ablation, C4 report (tracked)
  snapshots/    — developer_knowledge-v71.snapshot, the pre-v8 collection (not tracked)
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

### Frontend (17 sources) — `knowledge-base/frontend/`

CSS (The Definitive Guide; CSS in Depth, 2nd ed.), TypeScript (Effective TypeScript, TypeScript Cookbook),
React, Vue, Angular, Svelte, Node.js, JavaScript design patterns, micro-frontends, web animation, Three.js,
WebGPU, HTTP: The Definitive Guide, and two web-performance books.

### Design (19 sources) — `knowledge-base/design/`

UX and UI practice (Laws of UX, Refactoring UI, Designing Interfaces, Lean UX, UX for Lean Startups, Think
Like a UX Researcher, Design for How People Think, UI Design Principles, Effective UI), design systems and
decisions, UX writing, accessibility (two books), and data visualisation and storytelling (Storytelling with
Data, D3.js in Action, Introduction to Data Visualization & Storytelling, Storytelling in Design).

### Data Engineering (24 sources) — `knowledge-base/data-engineering/`

Fundamentals of Data Engineering, Spark (three books), Kafka, Delta Lake, lakehouse, data mesh (two books),
data governance (two books), data quality (two books), metadata management, Microsoft Fabric, knowledge graphs,
financial data engineering, enterprise data lakes, data/ML platforms, web scraping.

### Data Science (12 sources) — `knowledge-base/data-science/`

Statistics and EDA (Think Stats, Head First Statistics, Statistics by Simulation, Making Sense of Data, EDA with
visualisation), Data Science from Scratch, Data Science for Business, Data Science: The Hard Parts, predictive
analytics, and three Excel/VBA books.

### C++ (22 sources) — `knowledge-base/cpp/`

Modern C++ (STL, templates, memory management, concurrency, design patterns, refactoring, architecture,
low latency), CMake (two books), LLVM (two books), GPU programming with CUDA, Qt 6, bare-metal embedded C, x86
assembly (Irvine), and Fundamentals of Computer Graphics.

### Reverse Engineering (7 sources) — `knowledge-base/reverse-engineering/`

Practical Reverse Engineering, Reverse Engineering for Beginners, The Ghidra Book, Arm assembly internals (Blue
Fox), x86 cracking and countermeasures, Apple debugging, and reverse engineering for cybersecurity.

### Management (8 sources) — `knowledge-base/management/`

Learning Agile, The Scrum Master's Path, User Story Mapping, Holacracy, Project Management with AI, the
PMBOK Guide 7th Edition, Head First PMP, and Project Planning, Scheduling, and Control (Lewis).

### Sales (10 sources) — `knowledge-base/sales/`

MEDDICC (Whyte), The Challenger Sale (Dixon & Adamson), Getting to Yes (Fisher, Ury & Patton), Bargaining for
Advantage (Shell), Selling to Big Companies (Konrath), Key Account Management 2nd Edition (McDonald & Woodburn),
Value-Based Fees (Weiss), Flawless Consulting 3rd Edition and its Fieldbook Companion 2nd Edition (both Peter
Block), and the HBR Guide to Better Business Writing (Garner).

### Research Methods (6 sources) — `knowledge-base/research-methods/`

Research Methods in Psychology (Morling), Critical Thinking About Research (Meltzoff & Cooper), How to Read a
Paper (Greenhalgh & Dijkstra), Research Ethics and Integrity for Social Scientists 2nd Edition (Israel), Privacy
in Context (Nissenbaum), and The New Ethics of Journalism (McBride & Rosenstiel).

### v8 additions to existing domains

AI engineering +12 (LLM application design, RAG, GraphRAG, agents, LLMOps, reasoning models), applied ML +12,
architecture +6 (API strategy and design), data-intensive and scalable systems +2 (Kleppmann, Gorton),
databases +5 (Database Internals, CockroachDB, graph data, vector databases, SQL Server tuning), security +10
(zero trust, supply chain, cloud native, incident response, LLM security), systems/ops +7, software
engineering +5. Per-book rows are in `data/intake/v8-manifest.json`.

### v9 additions to existing domains

Management +3 (PMBOK Guide 7th Edition, Head First PMP, Project Planning Scheduling and Control), security +2
(Container Security, Practical Cloud Security), systems/ops +2 (Hands-On Site Reliability Engineering, Python
for DevOps), software engineering +2 (Software Engineering at Google, Real-World Software Development), and one
each in AI engineering (Agentic Mesh), design (Designing AI Interfaces), frontend (High Performance Browser
Networking) and C++ (The Art of Assembly Language). Per-book rows are in `data/intake/v9-manifest.json`.
Seven further files were skipped at intake: six are scanned or image-only with no usable text layer, and one is
a byte-identical duplicate.

## Philosophy Collection — `data/philosophy/works.json`

| Work | Languages | Aligned by |
|---|---|---|
| Original Library (Thư Viện Bản Nguyên / 本源圖書館) | vi (source), en, zh-Hant | 38 sections (ol-01…ol-38) |
| Tao Te Ching | en (Stephen Mitchell), en (Jonathan Star), es (Tse Lao) | 81 chapters; translators' back matter in `ttc-notes` |
| Zhuan Falun | en, vi, zh-Hans, zh-Hant (converted from zh-Hans) | Lunyu + lectures 1–9 |

## Corpus Stats

- 320 technical sources indexed live; 286,723 child chunks (vectors) in `developer_knowledge_v9`
  (266,647 carried over from v8 + 20,076 new)
- The 55 on-disk postgresql-14-internals chunks remain unindexed (corrupt re-chunk; see Known Limitations)
- Philosophy: 8,432 vectors in the `philosophy` collection (10 language files across 5 work records)
- **Not yet enriched** — index-now-enrich-later: embedded with heading_path + child_text only; contextual enrichment is a deferred background pass
- Token counting: tiktoken `cl100k_base` (≈ Jina v5 tokenizer within ~2%). Child max 250 / min 75, parent max 1900 tokens
- Embedding: heading_path + context_text + child_text → Jina v5-text-small (677M params, 1024-dim)
- Sparse: FastEmbed Qdrant/bm25 (proper tokenization, stopwords, IDF)
- Reranker: Ettin-150m cross-encoder (ModernBERT, 151M params, 0.5994 NDCG@10)
- Fusion: Qdrant DBSF (Distribution-Based Score Fusion) via prefetch API
- Adaptive cutoff: score floor 4.0, min results 3
- Vector store: Qdrant server at `127.0.0.1:6333` (KB_QDRANT_URL). `developer_knowledge` is an alias for
  `developer_knowledge_v9`; `philosophy` is its own collection. If the server is down, search falls back to
  the embedded store at `data/qdrant`, which still holds v7.1 (126 books) and no philosophy collection

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
- **v8 (technical shelf + philosophy):** 165 books from a flat 185-file folder, registered by manifest
  (`data/intake/v8-manifest.json`), 7 new domains, embedded on the RTX 5080 → 291 books / 266,647 vectors.
  Hard gate NDCG 0.7703 → 0.7429, recall@10 0.9680 → 0.9521; failed the pre-set dilution rule
  (22/40 > 20/40) and was promoted on Gary's decision. Promotion is a Qdrant alias switch.
  Separate multilingual `philosophy` collection with aligned translations and two new MCP tools.
- **v9 (sales + research methods):** 29 books registered by manifest (`data/intake/v9-manifest.json`), 2 new
  domains (sales, research-methods), embedded on the RTX 5080 → 320 books / 286,723 vectors. Hard gate
  NDCG 0.7429 → 0.7409 and recall unchanged (both pass); sanity recall@10 0.793 against a 0.80 threshold
  (fail). A blind review of the sanity queries scored 0.821 (23/28). Promoted on Gary's decision, as for v8.
  Promotion is a Qdrant alias switch; the release is `data-v9`.

## Known Limitations

- **v9 failed the sanity gate condition and was promoted anyway.** Sanity recall@10 on the 29 new books was 0.793 (23/29) against a 0.80 threshold; both hard-set conditions passed, and a blind review of the sanity queries scored 0.821 (23/28). Gary promoted v9 on 2026-09-30, as with v8.
- **Five v9 sanity queries still miss.** `agentic-mesh`, `head-first-pmp`, `python-for-devops`, `selling-to-big-companies` and `flawless-consulting-fieldbook-companion-2e` return no labelled passage in the top 10, in the original and the blind-reviewed set alike. Each is a retrieval miss. Details: `data/bench/gate-v9.md`.
- **Chunk heading paths repeat "(part 1) (part 1)".** The chunker in `knowledge_base/chunk.py` appends the ` (part N)` suffix in two passes, so oversized sections can carry it twice; 120 chunk files are affected, and heading_path is prepended to the embedding. Not fixed in v9.
- **v8 reranker dilution.** On the hard set, 88 queries got worse and 16 better. The labelled answer mostly stays in the top 10 but ranks lower. In a blind sample of 40 of those 88 queries, 17 had a complete answer pushed below a partial one. The pushing passage came from a new book in 22 of the 40, and from an old book in 18: 134,000 new candidates change which 50 passages reach the reranker. Broad new books displace most often (Designing Data-Intensive Applications, Essential Math for AI, Foundations of Scalable Systems). Rollback is to restore `data/snapshots/developer_knowledge-v71.snapshot` and point the alias at it. Details: `data/bench/gate-v8.md`.
- **Tukey's *Exploratory Data Analysis* is not indexed.** It is a scanned PDF with no text layer and needs OCR first.
- **15 v8 books are below the text-density floor.** They are image-heavy or sparse-layout PDFs, and each keeps 81–99% of its extractable text (`data/intake/audit-exceptions.json`).
- **Philosophy text caveats:**
  - Zhuan Falun zh-Hant is converted from zh-Hans with OpenCC and flagged `derived`, because the only Traditional PDF extracts as garbled characters.
  - The "Tse Lao" Tao Te Ching is a Spanish translation.
  - The philosophy eval has 15 queries per language group, and the reranker routing was chosen on that same set.
- **The embedded fallback store is stale.** `data/qdrant` holds v7.1 without philosophy. Run the Qdrant server; the fallback is for emergencies only.

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

- **Falun Dafa archive, phase B.** `~/Documents/books/falun-dafa-pdf-archive/` holds 616 PDFs in EN/VI/ZH-Hans/ZH-Hant (`manifest.json` lists every item). Phase A ingested Zhuan Falun only. The remaining lectures and writings go into the `philosophy` collection with one edition per work and language, through `scripts/ingest_philosophy.py` and the same Chinese text check.

Everything below was ingested by v7.0. Historical listing:

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
