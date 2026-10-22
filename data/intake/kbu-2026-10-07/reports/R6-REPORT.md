# R6 — Repository inventory and joining options

Owner: Huy. Run: kbu-2026-10-07. Inspection date: 2026-10-10.

**Recommendation: Option C.** Keep the repositories separate and make them one usable project through a shared document format, one Model Context Protocol (MCP) interface, and one installation entry point. MCP is the interface through which an agent discovers and calls tools. This recommendation is an inference from the inspected code and the owner's constraints. It preserves the public LitGraph project and the two private distribution channels while concentrating changes on the connections between them.

This is an inventory and a proposed design, not a migration. All writes are inside the R6 workspace. No installer, application server, model, repository test suite, network request, or secure-shell connection was run. Existing repository changes were recorded before inspection. The requested `bash verify.sh` returned `VERDICT: PASS`.

Counts mean **tracked file paths returned by `git ls-files`**, including fixtures, assets, and tracked links; they do not mean functions, runnable programs, or installed files. Untracked files are excluded. Full listings are saved in [evidence/](evidence/), alongside source copies and a dated [source catalog](evidence/source-catalog.json). A source's last commit date identifies its recorded version; it does not establish the date of an uncommitted edit. The catalog separately records local file modification dates and content fingerprints.

## knowledge-base

**Purpose.** This private Python project retrieves passages from curated books. Hybrid search combines meaning-based retrieval with keyword matching. An embedding is a numeric representation of text used for meaning-based matching. Qdrant stores those representations and associated passage metadata. The keyword representation uses BM25, a word-based relevance scoring method. Distribution-Based Score Fusion (DBSF) combines the two result streams, and a reranker scores query-passage pairs to reorder them. Technical and philosophy collections have separate tools. [K1, K2, K6]

**Main modules and counts.** The repository has 507 tracked paths. Of these, `knowledge_base/` has 20 Python files, `scripts/` has 74 paths, `tests/` has 22 paths, `data/` has 365 paths, and `wiki/` has 18 paths. The remaining 8 are root files. The package contains 13 files directly under `knowledge_base/` and 7 in `knowledge_base/philosophy/`. The test directory contains 14 Python test files and 8 input fixtures. These counts come from the saved tracked-file inventories, not the older prose inventories. [I1]

| Module or group | Responsibility |
|---|---|
| `config.py`, `books.py`, `headings.py` | Paths, model and collection settings, book lookup, generated catalog, and heading handling. |
| `ingest.py`, `chunk.py`, `enrich.py` | Convert source documents to Markdown, split sections into parent passages and smaller child passages, and optionally add generated context. Markdown is plain text with heading and formatting markers. |
| `embedder.py`, `index.py`, `search.py` | Produce embeddings, write passage representations and metadata to Qdrant, retrieve, combine, rerank, and filter results. |
| `server.py`, `calllog.py`, `qdrant_boot.py` | Expose agent tools, record calls, and optionally start the configured Qdrant binary. |
| `philosophy/` | Align translations, split sections, check extracted text, handle Chinese keyword representations, and return parallel passages. |
| `scripts/` | Ingestion, catalog building, release packaging, installation, quality checks, evaluation, and historical experiments. The 74 paths are not all production commands. |

**Entry points.** A command-line interface (CLI) is a program invoked with commands and arguments. `pyproject.toml` declares `kb-server = knowledge_base.server:main`; documentation also gives `python3 -m knowledge_base.server`. `main()` optionally starts Qdrant and then runs FastMCP, the Python framework used to expose MCP tools. [K3, K5]

The core edition registers 6 tools: `search`, `search_book`, `read_chunk`, `get_chapter`, `list_books`, and `grep_books`. Full adds `search_philosophy` and `list_philosophy`, for 8 tools. `KB_EDITION` selects the edition; without it, configuration checks whether the philosophy chunk directory exists. A joined interface should preserve these names and argument shapes for current callers. [K2, K4, K5]

The pipeline entry point is `scripts/ingest_all.py`, with ingest, chunk, enrich, and index steps documented in `CLAUDE.md`. Supporting commands include `scripts/test_search.py`, `scripts/audit_markdown.py`, `scripts/merge_collection.py`, `scripts/eval_retrieval.py`, `scripts/package_release.py`, and `scripts/install.py`. The release command creates a database snapshot, so it is not a harmless inspection command and was not run. [K1, K7]

**Data stores.** Converted text lives in `data/markdown/`, parent and child passages in `data/chunks/`, and generated book metadata in `data/catalog.json`. JSON, or JavaScript Object Notation, is a structured text format for records and lists. `index.py` stores child and parent identifiers, passage text, and book metadata with Qdrant points. `search.py` first connects to the configured Qdrant server and falls back to an embedded store at `KB_QDRANT_DIR`. The documented embedded fallback contains an older collection. This run did not query either store, so live corpus size and active collection version are **not found** by measurement. [K1, K4, K6, K10, K14]

**Install and distribution.** Shell and PowerShell installers download the private repository's source archive and invoke the Python installer. Data ships separately as GitHub Release parts, with manifests identifying collections, sizes, and SHA-256 hashes. SHA-256 is the content fingerprint checked to detect a changed download. The packaging code splits bundles into numbered `kb-core.part*` and `kb-philosophy.part*` files; the installer selects the edition, verifies parts, restores snapshots, obtains the pinned Qdrant binary, and registers the server with Claude Code. Model warm-up and a smoke query are part of installation. Even `--skip-models` leaves the required smoke query, so installation was not used as a lightweight probe. [K7, K8, K9]

There is a release-version conflict: `CLAUDE.md` and the wiki index describe `data-v9`, while the current installer and packager default to `data-v10`. The locally modified README also names `data-v10`. These are source observations, not confirmation of what is currently published. `README-core.md` and `scripts/build_core_transfer.py` exist locally but are untracked; they document/build a core-only transfer containing `core-source.tar.gz`, a core manifest, and release parts. They are migration candidates that must be accounted for separately from tracked code. [K1, K2, K7, K8, K11, K12]

**Tests and dependencies.** `pyproject.toml` declares pytest, a Python test runner, and adds the repository root to Python's import path. `uv run pytest tests` is the inventory's proposed suite command, inferred from that configuration. `uv` is the Python environment and package manager used in these projects. Retrieval evaluation commands are separate from unit tests and require the corpus and models. No suite was run because this task permits repository reads only and forbids model loading. [K1, K3]

The declared Python minimum is 3.11.4. Runtime requirements are `fastmcp>=2.13`, `qdrant-client>=1.12`, `openai>=1.0`, `sentence-transformers>=5.5`, `markitdown>=0.1`, `fastembed>=0.3`, `opencc-python-reimplemented>=0.1.7`, `tiktoken>=0.7`, and `pymupdf>=1.24`. They support the tool interface, storage access, model calls, embeddings/reranking, document conversion, Chinese text conversion, token counting, and PDF extraction. These are declared lower bounds, not measured installed versions. [K3]

## litgraph

**Purpose.** LitGraph builds a knowledge graph over research papers, blog posts, and repository descriptions. A knowledge graph records named entities and typed relationships between them. Here, entities include methods, problems, datasets, metrics, claims, and assumptions. The system explores underconnected regions, proposes research gaps, and subjects proposals to critics that try to refute them using indexed evidence. A large language model (LLM) is the text-generating model used for extraction, proposals, and criticism. [L1, L2, L5]

The owner identifies LitGraph as public. Its README and `LICENSE` specify MIT licensing. The license text requires preservation of its copyright and permission notice in copies or substantial portions of the software. The report relies on that local text and the owner's public-status constraint; it did not inspect GitHub visibility. [T1, L2, L9]

**Main modules and counts.** LitGraph has 76 tracked paths: 20 under `src/`, 14 under `tests/`, 14 under `prompts/`, 12 under `wiki/`, 4 under `data/`, 3 under `docs/`, 1 under `.github/`, and 8 at the root. All 20 source paths and all 14 test paths are Python files. Within `src/litgraph/`, 17 files are directly in the package and 3 are in `sources/`. [I1]

| Module or group | Responsibility |
|---|---|
| `sources/arxiv.py`, `sources/seeds.py` | Fetch papers and curated blog/repository sources. |
| `db.py`, `models.py`, `llm.py` | Define storage, extraction record shapes and model names, call models, and log calls. |
| `extract.py`, `resolve.py` | Extract entities/relations and map alternative names to canonical entities. This mapping is entity resolution. |
| `graph.py`, `embeddings.py`, `communities.py` | Build the graph, represent nodes as vectors, and group related nodes into communities. |
| `templates.py`, `proposer.py`, `frontier.py` | Compute structural leads and run proposal workflows. |
| `tools.py`, `verify.py`, `assassin.py`, `backtest.py` | Retrieve evidence, check quoted text, run the refutation process, and evaluate against a historical cutoff. |
| `cli.py` | Dispatch user commands. |

There is an architectural documentation conflict. `AGENTS.md` says structure proposes gaps and the LLM only refutes them. The later README describes an inversion: structure supplies leads, models propose, and critics filter. `frontier.py` implements structural-hole leads and model-driven proposal sessions. The joining design should reflect this later implementation and retain the charter as historical context. This conclusion is an inference from the conflicting documents and inspected code. [L1, L2, L7]

**Entry points.** `pyproject.toml` declares `litgraph = litgraph.cli:main`. The CLI includes `ingest arxiv`, `ingest seeds`, `extract`, `resolve`, `graph`, `stats`, `embed-nodes`, `communities`, `propose`, `frontier leads`, `frontier qwen`, `assassinate`, `gaps`, and `backtest snapshot`/`backtest score`. `--db` selects the DuckDB file. DuckDB is the embedded database storing the project's tables. The parser accepts `ingest arxiv --max`; the README's `--max-results` example does not match that parser. [L3, L6]

`tools.py` provides 4 internal read functions: `subgraph_around`, `full_text`, `evidence_for`, and `who_tried_this`. They take a database connection or cursor and return dictionaries. They are not currently an MCP entry point. A static scan of all 20 tracked source files found none of the inspected MCP markers: `FastMCP`, `@mcp.tool`, `from mcp`, or `import mcp`. This is a scoped source finding, not a claim about untracked integrations. A joined MCP service must wrap these functions. [L4, I2]

**Data stores.** `db.py` defines 10 tables: `documents`, `extractions`, `mentions`, `canonical_nodes`, `aliases`, `node_embeddings`, `communities`, `gap_candidates`, `backtest_results`, and `verdicts`. They separate acquired texts, raw model outputs, canonical entities, and later judgments. The default file is `litgraph.duckdb`. Node vectors have 1,024 values. NetworkX, a Python graph library, builds graph structures over the stored relationships. [L3, L5, L8]

The README says full databases and model-call logs are excluded from public distribution because they contain full source texts. `.gitignore` excludes `*.duckdb` and `logs/`. Tracked outputs include the gap dossier JSON files and seed list, rather than the database itself. Their reported corpus and evaluation numbers were not reproduced in this run. [L2, L10]

**Install and distribution.** The documented setup uses `uv sync`, environment variables for model endpoints and API keys, and an authenticated Claude CLI for selected judging stages. Repository-root working directory matters: prompts, seeds, and model logs use relative paths. There is no KB-style database release installer in the inspected tracked inventory. An installed package alone therefore does not supply the corpus, prompts in an arbitrary working directory, or authenticated services. [L2, L6, L11]

`db.connect()` opens the database and executes schema-creation statements. Even CLI commands presenting statistics pass through that connection helper. A future read-only MCP adapter should explicitly open an existing database in read-only mode rather than treating this helper as a pure read. This is a proposed implementation requirement inferred from the helper's behavior. [L8]

**Tests and dependencies.** The README documents `uv run pytest` and describes the tests as offline with model calls faked. It reports 180 tests; that is a documentation claim, while this run measured 14 tracked test files and did not collect or execute tests. Ruff, the Python code checker declared for development, can be invoked with `uv run ruff check src tests`; this command is inferred from the tool configuration. [L2, L3, I1]

Python must be at least 3.12. Declared runtime requirements are `defusedxml>=0.7.1`, `duckdb>=1.0`, `httpx>=0.27`, `networkx>=3.3`, `numpy>=2.5.1`, `openai>=1.40`, `pydantic>=2.7`, `pyyaml>=6.0`, and `trafilatura>=1.12`. They support XML handling, storage, network fetching, graph operations, numeric work, model calls, structured record validation, seed configuration, and web-text extraction. Development dependencies are `pytest>=8.0` and `ruff>=0.6`; Hatchling builds the Python package. [L3]

## agent-workflow

**Purpose.** This private repository is the owner's canonical collection of agent skills and supporting tools. A skill is an instruction package whose `SKILL.md` tells an agent when and how to use it. `skills.txt` contains 28 nonempty names. `install.sh` connects those folders to agent discovery locations with symbolic links, or symlinks: filesystem references to the original folders rather than copied contents. Editing a linked skill therefore changes the instructions each local agent reads after reloading them. [A1, A2, A3, A4]

**Main modules and counts.** There are 10,636 tracked paths: 10,450 under `skills/`, 169 under `tools/`, 4 under `config/`, 4 under `wiki/`, 2 under `scripts/`, and 7 at the root. The skills include instructions, reference texts, scripts, tests, and course assets; this is not 10,450 independent skills. [I1]

| Component | Tracked paths | Purpose |
|---|---:|---|
| `skills/color-theory/` | 1,717 | Colour instruction and reference material. |
| `skills/information-design/` | 1,000 | Charts and information graphics. |
| `skills/motion/` | 1,095 | Motion planning and checks. |
| `skills/photo/` | 1,834 | Photography workflows and references. |
| `skills/ux/` | 840 | User experience methods and content. |
| `skills/visual-design/` | 1,604 | Composition, typography, and identity. |
| `skills/zalo-platform/` | 2,064 | Platform documentation and workflow references. |
| Remaining 21 skill folders | 296 | Engineering, research, consulting, planning, and other methods. |
| `tools/render-kit/` | 88 | Render documents and inspect output. |
| `tools/scene-engine/` | 72 | Produce video explanations and editable presentations. |
| `tools/brand-profile/` | 9 | Personal visual-direction records, tokens, and samples. |

**Entry points.** `bootstrap.sh` clones or updates the private checkout, fetches Git Large File Storage (Git LFS) assets, and invokes `install.sh`. Git LFS stores large file contents separately from the ordinary Git history. `install.sh` reads `skills.txt`, links skills into the supported agent directories, removes retired links, and sets `~/.agent-workflow` to the checkout. It also links global Claude instructions and merges hooks and plugin settings. These are documented and inspected behaviors; neither script was executed. [A1, A2, A4, A5]

Claude's skill directory is always handled; Codex, `.agents`, and Gemini paths are conditional on the corresponding directories existing. A real folder at a target skill path is left alone with a warning, so a stale copied skill can survive installation. The stable `~/.agent-workflow/tools/...` path is important when choosing a joined layout. [A4]

`render-kit` exposes the `rk` command. `scene-engine` exposes its Node-based CLI and npm script. `tools/brand-profile/` is a collection of documents and design tokens rather than a service. The skill entry points remain individual `SKILL.md` files. Agent-workflow currently supplies no KB or LitGraph MCP service; its README explicitly lists MCP servers as per-machine setup outside this repository. [A1, A2, A8, A9, A10]

**Data stores and distribution.** Skills and references are files, not a shared research database. Large course assets use Git LFS. The local installation follows symlinks, whereas claude.ai uses separately uploaded ZIP archives, which are compressed file bundles. The task's 200-file cap is also stated in the repository documentation. It applies per uploaded skill, not to the total repository. [T1, A1, A2]

`scripts/make-cloud-zips.sh` packages each named skill and excludes images, PDFs, audio, video, ZIP files, and selected local directories. It invokes `cloud_merge.py` for `color-theory`, `photo`, and `zalo-platform`. The merger combines small reference files, rewrites links, renames nested `SKILL.md` files, and checks a stricter 190-file ceiling. The ordinary ZIP branch has no equivalent rejection gate for exceeding 200; its displayed entry count also includes directory entries, unlike the merged branch's file count. A joined project should add a uniform actual-file count check to every archive. This is an inference from the scripts. Raw tracked counts above are not cloud ZIP counts, and this run did not build ZIPs. [A6, A7]

**Tests and dependencies.** No repository-wide test command was found in the requested root documentation. The component commands are `npm test` in `tools/render-kit/` and `tools/scene-engine/`; scene-engine also declares `npm run selftest`. There are additional skill-specific Python tests in the tracked inventory. npm is the Node.js package command used to install and test those tools. [A8, A9, I1]

Bootstrap prerequisites are Git, Git LFS, Python 3, and curl. Both executable tools declare Node.js 24 or later. Render-kit declares Playwright 1.63.0, an automated browser library, and `@axe-core/playwright` 4.13.0 for accessibility checks. Scene-engine declares Ajv 8.17.1 for record validation, GSAP 3.13.0 for animation, Hyperframes 0.8.78, and Playwright 1.63.0. Both declare TypeScript 5.9.3 for development. The optional tool install creates a Python environment with `python-pptx==1.0.2`. Documentation also requires browser binaries, FFmpeg/ffprobe for media processing, and Python with NumPy and Pillow for selected checks. It describes the tools as tested on macOS only and identifies scene-engine's macOS browser-cache assumption. A repository merger does not resolve that portability issue. [A2, A4, A8, A9]

## Reuse

“Yes” means keep the component for its current role. “With changes” means preserve useful behavior while adapting paths, record shapes, packaging, or interfaces. “No” means exclude it from the shared/public product in its present form; it can remain in its original private environment. These are design judgments, not executed migrations.

| component | repo | path | reusable in the joined project? (yes / with changes / no) | reason |
|---|---|---|---|---|
| Book conversion | knowledge-base | `knowledge_base/ingest.py` | with changes | Useful book ingestion; normalize shared source identity and provenance. |
| Parent/child passages | knowledge-base | `knowledge_base/chunk.py` | with changes | Preserve passage context; identifiers can change on rechunking, so retain corpus-version references. |
| Catalog lookup | knowledge-base | `knowledge_base/books.py` | with changes | Reuse titles and chapters; add mappings to shared document identifiers. |
| Hybrid search and reranking | knowledge-base | `knowledge_base/search.py` | yes | Keep the existing book backend and established search behavior. |
| Technical MCP tools | knowledge-base | `knowledge_base/server.py` | with changes | Preserve compatibility and add an adapter to common result records. |
| Translation alignment | knowledge-base | `knowledge_base/philosophy/` | yes | Keep as an optional, separate collection and tool family. |
| Verified release transport | knowledge-base | `scripts/package_release.py`, `scripts/install.py` | with changes | Retain parts, hashes, editions, and snapshot restoration; adjust locations if code moves. |
| Core-only transfer | knowledge-base | `scripts/build_core_transfer.py`, `README-core.md` | with changes | Existing local work is untracked and uses source-text transformations; preserve and review before moving code. |
| Private book snapshots in public output | knowledge-base | release `kb-core.part*`, `kb-philosophy.part*` | no | Keep access-controlled data distribution separate from public LitGraph output. |
| Typed graph records | litgraph | `src/litgraph/models.py`, `src/litgraph/db.py` | with changes | Add book/skill source types through explicit migrations; retain raw extraction records. |
| Source fetching | litgraph | `src/litgraph/sources/` | yes | Retain paper and curated web-source ingestion as separate adapters. |
| Entity resolution | litgraph | `src/litgraph/resolve.py` | with changes | Valuable for aliases; adding book and skill vocabularies needs evaluation. |
| Graph evidence tools | litgraph | `src/litgraph/tools.py` | with changes | Wrap as MCP calls with explicit read-only connections and common identifiers. |
| Quote verification | litgraph | `src/litgraph/verify.py` | with changes | Preserve exact/fuzzy/failed labels and adapt document lookup; fuzzy evidence must not be presented as an exact quote. |
| Gap exploration and criticism | litgraph | `frontier.py`, `assassin.py`, `backtest.py` under `src/litgraph/` | with changes | Keep as opt-in research jobs; parameterize resources, providers, and working directories. |
| Full database in public release | litgraph | local `*.duckdb`, `logs/llm/` | no | The README excludes full texts and logs; publish approved outputs separately. |
| Canonical skill folders | agent-workflow | `skills/`, `skills.txt` | yes | Preserve names and direct agent discovery. |
| Stable symlink installer | agent-workflow | `install.sh` | with changes | Keep skill linking; add optional joined-project orchestration without forcing model installation. |
| Private bootstrap | agent-workflow | `bootstrap.sh` | with changes | Reuse token-based installation while pinning component versions and selecting features. |
| Cloud skill packaging | agent-workflow | `scripts/make-cloud-zips.sh`, `scripts/cloud_merge.py` | with changes | Preserve exclusions and merging; apply one file-count and link gate to all skills. |
| Rendering/media tools | agent-workflow | `tools/render-kit/`, `tools/scene-engine/` | with changes | Retain optional tools; address documented platform-specific paths separately. |
| Personal brand records | agent-workflow | `tools/brand-profile/` | no | Owner-specific draft material should not become mandatory shared defaults or public LitGraph content. |

Sources for these judgments are the repository sections above and the source catalog. The reusable boundary is principally documents and evidence, not a single database or model runtime.

## Repo-layout options

All sketches below are proposed layouts. A common document record would include a schema version, namespaced identifier such as `kb:...` or `litgraph:...`, source kind, title, source location, publication date where known, language, content fingerprint, access/distribution label, and passage references. Namespacing means prefixing identifiers to prevent collisions between repositories. Evidence records should include document and passage identifiers, quoted text, verification tier, and corpus version. Missing publication dates remain unknown rather than being inferred from file timestamps.

The two search systems should retain their native stores. Book passages and graph-node descriptions are different indexed units. Both use Jina-family embeddings with 1,024 values, but KB runs an embedding library while LitGraph calls a separately named model endpoint. Matching dimensions do not demonstrate interchangeable vectors. Reuse of one embedding store or provider remains unproven. A shared result interface should retain backend rank and score rather than combine incomparable scores without evaluation. These are design inferences from their configuration and storage code. [K4, K6, L5, L8, L11]

### Option A — KB and litgraph code move into agent-workflow

```text
agent-workflow/                     private repository
  skills/  skills.txt  config/      existing skill discovery contract
  tools/                           existing optional design tools
  services/knowledge-base/          own Python package, scripts and tests
  services/litgraph/                own Python package, prompts and tests
  contracts/                       shared document/evidence definitions
  integration/                     joined MCP adapters and setup
  install.sh  bootstrap.sh
external install data/             Qdrant storage and DuckDB files
```

**Effect on install.sh and symlinks.** Keeping root `skills/`, `skills.txt`, `config/`, and `tools/` allows the existing links and `~/.agent-workflow` convention to continue. Add optional service installation rather than placing services inside skill folders. Keep separate Python environments, because a joined dependency resolution has not been tested. KB's package-root-relative paths can remain valid if its whole service root moves together. LitGraph needs explicit prompt, seed, log, and database paths or a launcher that chooses its service root.

**KB release data.** Continue separate private release bundles. Moving the source download to agent-workflow requires changing hard-coded repository URLs and archive extraction assumptions in both KB bootstrappers and the Python installer. Either keep the existing release repository as a data host or relocate releases with an explicit transition plan. In both cases, pin source and data versions together and preserve hashes, core/full selection, alternate ports, and updates that retain local data. Do not pull book bundles during a skills-only installation.

**claude.ai ZIPs.** Per-skill packaging remains unchanged if service code and data stay outside `skills/`. Add a small integration skill, if wanted, containing instructions rather than databases or the full service tree. It must independently pass the 200-file cap; any local-tool expectation needs a cloud-appropriate explanation.

**LitGraph public status.** Moving code into private agent-workflow removes the public canonical implementation unless a public LitGraph copy is maintained. A proposed one-way export would need retained MIT notices, public documentation/tests, and a reliable method of excluding private material and history. That export is extra work, not an existing capability. Public contributions and issue handling would need an explicit ownership path.

**Migration effort and risks.** Qualitatively medium-to-high; elapsed time and cost estimates are **not found**. Work includes importing code/history, changing source bootstraps, preserving untracked core-transfer work, testing relocated resources, separating data, and maintaining a public LitGraph export. Risks are private data leaking through export, broad private downloads for simple installs, and conflicting top-level guidance. This option benefits the owner's existing installation root but compromises the clean public boundary.

### Option B — all three move into a new repo

```text
joined-project/                    proposed private canonical repository
  skills/  skills.txt  config/      migrated agent instructions/settings
  tools/                           migrated design tools
  packages/knowledge-base/          package, scripts and tests
  packages/litgraph/                package, prompts and tests
  contracts/  integration/          shared records and joined MCP service
  install.sh  bootstrap.sh
public-litgraph-export/             separately maintained public output
external install data/              private books and research database
```

**Effect on install.sh and symlinks.** Preserve root skill and tool paths, and point `~/.agent-workflow` to the new checkout as a compatibility link. Rerunning a relocated installer would replace managed skill symlinks, but real folders still require explicit handling. Existing hook commands include resolved checkout paths; changing the installation root can leave old commands alongside new ones because the installer deduplicates by exact command. Migration must identify its old managed entries and replace them without removing user settings. All private bootstrap repository URLs and instructions need updating. [A4]

**KB release data.** The new repository can host private release parts, but the transition must handle legacy installers and access-token scope. Retain core/full manifests and separate component release identifiers even if code shares a repository. Releasing a new skill should not require rebuilding Qdrant snapshots. The source archive layout and KB's installation directory assumptions require verification, including the untracked core-transfer builder.

**claude.ai ZIPs.** Keep the packager rooted at `skills/`, with explicit exclusions and a uniform file-count gate. The new repository's total size is irrelevant to the per-skill cap. Avoid copying joined source packages into every cloud skill; copied code would create duplicate versions and does not supply the needed databases or local runtime.

**LitGraph public status.** A private new repository protects private books and personal configuration, but again requires a public LitGraph export to preserve the stated public project. Making the whole new repository public is not justified by the inspected private inputs. A public source repository with private data could be designed, but publishing the owner's skill/configuration material would first require a separate content review. The sketch deliberately retains a private canonical repository and acknowledges the resulting public-export maintenance.

**Migration effort and risks.** Qualitatively highest among these three choices; no exact schedule is supported. Every checkout/bootstrap root changes, three histories need deliberate treatment, and existing documentation, symlinks, hooks, resource paths, and distribution workflows must converge. Benefits are neutral naming and one place for cross-component changes. Risks are making installation a large all-or-nothing operation, accidental publication of private content/history, and a public export falling behind. A shared repository also does not by itself create shared identifiers, reliable MCP adapters, or compatible dependency versions.

### Option C — three repos stay separate, joined by one shared data format and MCP interface

```text
agent-workflow/                     private skills and user setup
  skills/  tools/  install.sh       existing paths
  contracts/                       proposed canonical shared record format
  integration/                     proposed joined launcher and MCP service
knowledge-base/                     private book search and release data
litgraph/                           public MIT research implementation
local joined-project config/         component versions and data locations
local data/                         Qdrant storage and DuckDB kept separate
```

**Effect on install.sh and symlinks.** Preserve current skill links and `~/.agent-workflow`. Add one optional setup command that validates required component versions, accepts explicit arguments for skills, book search, and research features, and writes machine configuration during an authorized installation. Runtime configuration should resolve service locations without embedding the owner's Mac path in instructions. The joined MCP service exposes namespaced tool families while preserving the original KB interface for existing callers. Its LitGraph adapter uses the 4 existing functions with an existing read-only database. Research ingestion and model-driven jobs remain explicit commands, rather than side effects of loading skills.

**Shared format.** Agent-workflow can hold the canonical integration contract for this private joined setup. Publish a versioned, reviewed copy of the contract alongside public LitGraph, with a check that copies match; LitGraph's standalone CLI must not require access to the private repository. Adapters map KB books/passages, LitGraph documents/entities/evidence, and selected skill references to the common record. The format must add book and skill kinds without rewriting LitGraph's immutable extraction outputs. Schema changes need version identifiers and migrations. Only metadata and explicitly permitted text cross the adapters; storage files stay native and access-controlled.

**KB release data.** Existing repository URLs, private releases, edition selection, hash verification, and snapshot restoration remain in place. The joined setup pins a KB code version and release manifest instead of guessing the version from a README. Skills-only setup can skip book installation entirely. The discovered `data-v9`/`data-v10` documentation conflict should be resolved in a future authorized implementation before declaring a tested installation matrix.

**claude.ai ZIPs.** Existing per-skill exports remain separate from services and data. A cloud-facing integration skill can document the shared records and how supplied evidence is cited; it cannot assume the local symlink or MCP launcher exists in claude.ai. Apply the common file-count check to all archives and retain manual re-upload as the documented update mechanism.

**LitGraph public status.** The public repository, MIT notice, documentation, dossiers, and contribution entry points remain where they are. Its adapter and public contract copy can contain generic integration code and synthetic fixtures without private book texts, credentials, or personal configuration. Full DuckDB databases remain excluded as the README currently directs.

**Migration effort and risks.** Qualitatively lowest for relocation, but meaningful integration work remains. The main tasks are identifiers/provenance, a versioned schema, MCP wrapping, explicit resource paths, optional setup, and compatibility tests. Exact elapsed time and cost are **not found**. Risks shift to incompatible component versions, stale contract copies, unavailable backends, and confusing routing between book passages and graph evidence. Pin a tested component set, validate schema versions at startup, report backend availability explicitly, and reject identifiers belonging to the wrong backend.

For a future implementation, useful acceptance checks would prove that a KB hit opens the same passage through the joined interface; a LitGraph evidence record retains its document and verification tier; duplicate local identifiers cannot collide; graph reads do not change the database; skill-only installation avoids model/data downloads; every cloud ZIP is within the file cap; and public output excludes private fixtures. These are proposed checks, not results from this run.

**The option I would pick is Option C.** Huy can get one setup entry point, one agent-facing interface, and one evidence format while preserving the distribution boundaries that already work. Option A has an installation-root advantage but adds a public export problem. Option B offers a neutral root at the cost of changing every installation boundary. Start with integration because all three layouts require that work; reconsider physical consolidation only after the joined workflow demonstrates a benefit that outweighs public-export and installer migration costs. If “one project” must mean one Git repository, Option B fits that definition better, but it carries the unresolved public/private publication boundary described above.

## Output sample

The following lines are real output from the lightweight inventory script, saved in `evidence/count-output.txt`. Python-file counts are based on tracked filename suffixes; no project code was imported.

```text
knowledge-base knowledge_base/: 20 tracked paths; 20 Python files
knowledge-base scripts/: 74 tracked paths; 69 Python files
knowledge-base tests/: 22 tracked paths; 14 Python files
litgraph src/: 20 tracked paths; 20 Python files
litgraph tests/: 14 tracked paths; 14 Python files
litgraph prompts/: 14 tracked paths; 0 Python files
agent-workflow skills/: 10450 tracked paths; 54 Python files
agent-workflow tools/: 169 tracked paths; 2 Python files
litgraph tracked src/ MCP markers: none found
litgraph db.py CREATE TABLE statements: 10
agent-workflow skills.txt nonempty names: 28
```

The saved listings reproduce the requested commands:

```bash
git -C ~/Documents/Work/tools/knowledge-base ls-files -- knowledge_base/ scripts/ tests/
git -C ~/Documents/Work/products/litgraph ls-files -- src/
git -C ~/Documents/Work/tools/agent-workflow ls-files -- skills/ tools/
```

The actual calls also disabled optional Git locks. They only read repository indexes and wrote output files within R6.

## Validation

The requested `bash verify.sh` returned exit code 0 and the following output, saved in [acceptance.log](acceptance.log):

```text
VERDICT: PASS
```

The script checks headings, option labels, the sample section, minimum report length, and selected repository status against its supplied baselines. A separate check found all three repositories' Git status unchanged from the initial observation and all 41 inspected source fingerprints unchanged. Its output is saved in [evidence/final-readonly-check.txt](evidence/final-readonly-check.txt). There are exactly 3 option headings. Repository application tests were not run under this read-only inventory scope; this PASS establishes the report acceptance checks, not a tested migration or live retrieval result.

## Sources

No external research was used. Public status and the 200-file constraint are supplied by the task, with corroborating local documentation. URLs embedded in repository documentation were not visited and are not presented as independently verified external facts. All recommendations and future layouts are explicitly design inferences. Local sources were inspected on 2026-10-10; dates below are their last recorded commit dates unless stated otherwise. Full timestamps, local modification dates, and fingerprints for every copied source are in [evidence/source-catalog.json](evidence/source-catalog.json).

Repository roots: KB = `~/Documents/Work/tools/knowledge-base`; LG = `~/Documents/Work/products/litgraph`; AW = `~/Documents/Work/tools/agent-workflow`. Source paths below are relative to those roots.

| ID | Local source | Source date | Use |
|---|---|---|---|
| T1 | Huy's R6 task and standing rules | Received for this run, 2026-10-10 | Scope, public/private constraint, ZIP cap, and acceptance. |
| I1 | `git ls-files` inventories, `evidence/inventory.json`, tracked listings | Measured 2026-10-10 | Exact tracked-path and module counts. |
| I2 | `evidence/count-output.txt` | Produced 2026-10-10 | Static MCP-marker scan and table/skill counts. |
| K1 | KB `CLAUDE.md` | 2026-10-01 | Pipeline, tools, releases, known limitations. |
| K2 | KB `README.md` | 2026-09-30; local modification 2026-10-06 | Installation, editions, and current local `data-v10` instructions. |
| K3 | KB `pyproject.toml` | 2026-09-28 | Python, dependencies, CLI, and pytest configuration. |
| K4 | KB `knowledge_base/config.py` | 2026-09-29 | Paths, collections, edition selection, embedding settings. |
| K5 | KB `knowledge_base/server.py` | 2026-10-01 | Actual tool registrations, result wrapper, and server entry point. |
| K6 | KB `knowledge_base/search.py` | 2026-09-27 | Hybrid retrieval and Qdrant fallback. |
| K7 | KB `scripts/package_release.py` | 2026-10-03 | Bundle construction, manifest, hashes, tag default. |
| K8 | KB `scripts/install.py` | 2026-10-03 | Verification, restoration, models, MCP registration, tag default. |
| K9 | KB `install.sh`, `install.ps1` | 2026-09-28 | Source archive download and bootstrap. |
| K10 | KB `knowledge_base/books.py`, `knowledge_base/chunk.py` | books.py: 2026-09-24; chunk.py: 2026-09-28 | Catalog and passage identifiers. |
| K11 | KB `README-core.md` | Commit date not found; local modification 2026-10-06 | Untracked core transfer instructions. |
| K12 | KB `scripts/build_core_transfer.py` | Commit date not found; local modification 2026-10-06 | Untracked source-only/core release packaging. |
| K13 | KB `wiki/index.md` | 2026-09-30 | Historical state and decision links; release-version conflict. |
| K14 | KB `knowledge_base/index.py` | 2026-06-26 | Qdrant passage identifiers and payload fields. |
| L1 | LG `AGENTS.md` | 2026-07-15 | Original charter and ontology. |
| L2 | LG `README.md` | 2026-08-03 | Later architecture, installation, public outputs, test claims. |
| L3 | LG `pyproject.toml` | 2026-07-17 | Dependencies, entry point, build and test settings. |
| L4 | LG `src/litgraph/tools.py` | 2026-07-16 | Four graph/evidence read functions and result caps. |
| L5 | LG `src/litgraph/models.py` | 2026-07-18 | Record types and model names. |
| L6 | LG `src/litgraph/cli.py` | 2026-07-19 | Actual commands and arguments. |
| L7 | LG `src/litgraph/frontier.py` | 2026-07-19 | Structural leads and model proposal workflow. |
| L8 | LG `src/litgraph/db.py` | 2026-07-16 | Ten tables, vector shape, connection side effects. |
| L9 | LG `LICENSE` | 2026-08-03 | MIT notice text. |
| L10 | LG `.gitignore` | 2026-07-17 | Excluded databases and logs. |
| L11 | LG `src/litgraph/llm.py` and README | 2026-08-03 | Endpoint/model logging and resource paths. |
| L12 | LG `src/litgraph/verify.py` | 2026-07-16 | Exact/fuzzy/failed evidence tiers. |
| L13 | LG `wiki/index.md` | 2026-08-03 | Lab notebook and untracked evidence explanation. |
| A1 | AW `AGENTS.md` | 2026-10-07 | Canonical skills, symlinks, paths, and cloud copies. |
| A2 | AW `README.md` | 2026-10-06 | Private distribution, prerequisites, portability, MCP exclusion. |
| A3 | AW `skills.txt` | 2026-10-03 | The 28 installed skill names. |
| A4 | AW `install.sh` | 2026-10-06 | Link behavior, settings merge, optional dependencies. |
| A5 | AW `bootstrap.sh` | 2026-10-06 | Private checkout installation/update. |
| A6 | AW `scripts/make-cloud-zips.sh` | 2026-10-04 | Per-skill ZIP selection/exclusion/counting. |
| A7 | AW `scripts/cloud_merge.py` | 2026-10-06 | Reference merging, link checking, and 190-file guard. |
| A8 | AW `tools/render-kit/package.json` | 2026-09-26 | Command, Node minimum, dependencies, tests. |
| A9 | AW `tools/scene-engine/package.json` | 2026-10-02 | Commands, Node minimum, dependencies, tests. |
| A10 | AW `tools/brand-profile/README.md` | 2026-10-02 | Owner-specific material and pending review. |

The source catalog supplies full timestamps for the grouped rows and the remaining supporting files. Source snapshots and inventories are retained in R6 so the report can be reviewed without changing the repositories.
