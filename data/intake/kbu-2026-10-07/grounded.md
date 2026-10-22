# Grounded — run kbu-2026-10-07 (unified archive + knowledge base research)

Reader: the coordinator and every lane in this run. Written before the Plan Block, 2026-10-07.

## Input 1 — Huy's request (2026-10-07, conductor prompt)
- **Claims:** the archive skills and the knowledge-base MCP are too intertwined and should become one project; everything archived as PDF should also be embedded into the KB; `google/embeddinggemma-2` embeds text, code, images, video and audio; the whole KB will be re-embedded; ingestion, querying and storage must be fast even on CPU; the archiving skill should be one reusable tool with per-platform parts.
- **Evidence:** none attached; the model claim was checked (Input 4).
- **Implications:** this run is research. It ends in a recommended design with measured numbers, not in a migration.
- **MISSING:** what "one project" means for the git repos and distribution; CPU speed targets; whether private course content may enter the distributed KB release; what a multimodal hit should return; which platforms beyond Domestika and Coursera. These go to the intent interview.

## Input 2 — knowledge-base repo (`~/Documents/Work/tools/knowledge-base`)
- **State:** live alias `developer_knowledge` → `developer_knowledge_v10` (CLAUDE.md still says v9; `data/bench/gate-v10.md` and commit `a7d5a90` show v10). Collections kept: v8, v9, v10, `philosophy` (8,432 points), candidate `philosophy_b` (52,122, not promoted).
- **Pipeline:** markitdown / PyMuPDF → tiktoken parent/child chunker → Jina v5-text-small 1024-dim dense + FastEmbed BM25 sparse → Qdrant hybrid (DBSF) → Ettin-150m cross-encoder rerank. Indexing runs on bppc's RTX 5080; queries embed on the Mac.
- **Gate:** hard set 438 queries (v9 NDCG@10 0.7409, recall@10 0.9521), easy set 199, plus a sanity set per intake. Promotion limits used in v9: hard NDCG drop ≤ 0.010, recall drop ≤ 0.005.
- **Recorded constraint** (`wiki/rag-frontier-2026.md` §"Hard constraint for any embedding change"): the same model must embed index and query; query embedding on the Mac must be about 300 ms or less.
- **Rejected before** (`wiki/decisions.md`): late chunking, corpus-wide HyDE, GraphRAG, TurboVec, SPLADE. A new design must not reopen these without new evidence.
- **Distribution:** data ships as GitHub Release parts installed on other machines with a read-only token (`scripts/package_release.py`, `install.sh` / `install.ps1`).
- **Open defects:** `chunk.py` drops a short final paragraph group; `(part 1) (part 1)` heading paths; four books with no headings.
- **Disk:** `data/` holds about 8 GB, including 2.2 GB `qdrant-v8new`, 1.7 GB snapshots, 0.7 GB `qdrant-v10-add`.

## Input 3 — agent-workflow repo and the archive skill
- `skills/domestika-course-archive`: collector JS (browser), packager (yt-dlp HLS → MP4 + VTT, per-unit PDF), reading-copy tool (1,159 lines) with marketing rules. Rules: use the user's signed-in session, never extract cookies, no DRM bypass, manifest with signed URLs stays private.
- Distribution: symlinked into every agent; claude.ai zips capped at 200 files.
- `color-theory` keeps a course PDF local-only: precedent for private course material.

## Input 4 — google/embeddinggemma-2 (Hugging Face API, checked 2026-10-07)
- Exists, public (not gated), Apache-2.0, last modified 2026-10-06. Tags: multimodal, vision, audio, video, multilingual, sentence-transformers.
- **MISSING:** parameter count, dimensions, Matryoshka support, context length, CPU speed, retrieval quality on our gate. Unit R1 settles these.

## Input 5 — Coursera probe (this session, 2026-10-07)
- Org account (FPT Software), 6 courses. Course tree from `onDemandCourseMaterials.v2`; lecture MP4 (720p max) by signed CloudFront URL, no encryption, curl works without cookies; VTT and TXT captions in about 25 languages; readings as HTML via `onDemandSupplements.v1`; `ungradedWidget` readings unresolved; labs and quizzes locked (session ended).
- Implication: Coursera needs no HLS step; a shared archive core plus per-platform collectors is feasible.

## Input 6 — lanes (doctor 2026-10-07 12:23 +07)
- Open: codex, gemini, bppc. Closed: glm (429 fair-usage limit), deepseek (402 balance), omlx (server not answering).

Grounded: request, both repos, the model card metadata, the Coursera probe and today's lane check are read; the model's real properties and the CPU targets are not yet known.

## Intent — Huy's answers (2026-10-07)
1. Private course content in releases → "go over too since all others are my machines". Course content ships in the release.
2. Video/audio → unsure whether it makes sense when the reader is an LLM; "Embed the images inside the PDF actually makes more sense". Image embedding of PDF figures and saved frames replaces the video/audio pilot.
3. "Fast on CPU" → a way of saying: use advanced techniques to optimize the whole pipeline. No numeric target; measure before/after.
4. One project, expanded: much more data is coming; consider a knowledge graph; integrate litgraph (`~/Documents/Work/products/litgraph`) so the model knows what it knows and does not know; define the product shape with the relevant skill; end users are the agent and Huy ("a more organized mind"); the agent ingests its own lessons, clearly annotated (Obsidian style?), may comment on or label existing data for staleness, tag related resources. Needs deep research and design.
5. Quality bar → same as v9/v10 gate.

## Input 7 — litgraph (`~/Documents/Work/products/litgraph`, AGENTS.md, wiki/active-work.md)
- **Claims:** typed entity graph (Paper, Method, Problem, Claim, Assumption…) over RAG/agent literature in DuckDB; "structure proposes, LLM disposes"; closed-world absence is an index property ("MATCH … gives a complete answer over the indexed world; 'I searched and found nothing' does not"); entity resolution is a first-class subsystem.
- **Evidence:** 1,285 docs, 24,782 nodes / 29,749 edges; graph-tools proposer lifted hit rate (Claude 13/30, Qwen 10/44 vs 1/23 without tools). Public MIT repo since 2026-07-25. MCP surface assessed 2026-09-18, not built.
- **Implications:** the "knows what it does not know" ability comes from typed coverage over a closed index, not from vector search.
- **Context/contradiction:** KB `wiki/decisions.md` rejected GraphRAG/LightRAG for single-concept lookups at 320 books. Huy reopens it on new grounds (much more data, self-knowledge). Research must answer the prior rejection reasons, not ignore them.
- **MISSING:** how a public MIT repo and the private KB combine; which lesson sources exist on this machine.

## Intent — follow-up answers (2026-10-07, after the walkthrough)
1. Data coming: more courses, books, papers, and repos.
2. Graph building runs on the local LLM lanes, omlx (this Mac) and bppc (GPU PC); no paid extraction.
3. Whether the agent may change source data or only annotate beside it: open. Research the current state of agent memory systems and design it. Starting pointers: github.com/amosblomqvist/pi-observational-memory, github.com/Dicklesworthstone/cass_memory_system.
4. Every agent harness that uses the skills reads and writes the same mind.
