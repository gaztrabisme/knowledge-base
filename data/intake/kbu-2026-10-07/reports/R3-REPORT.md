# R3 — A knowledge graph for Huy's organized mind

Owner: Huy. Research date: 2026-10-10. Decision: **build a small, evidence-linked coverage graph beside the existing search system; defer a corpus-wide graph retrieval replacement.** This is a research recommendation, not a measured local-model performance result.

The knowledge base (KB) is Huy's indexed library. A knowledge graph represents named things as nodes and specific relationships as edges. Retrieval-augmented generation (RAG) gives a language model retrieved source material before it answers. Hybrid search combines semantic vector similarity with keyword matching. These solve related but different problems: search finds passages; a coverage graph inventories what was indexed, what was extracted, and which relationships have supporting evidence. The graph should make those distinctions available to the model through tools.

A vector is a numerical representation used to compare meaning. A large language model (LLM) reads and generates text in tokens, its own small text units. A prompt is the instructions and input sent to that model. A schema specifies allowed record types and fields; structured output here uses JSON, a machine-readable text format. A cache hit reuses a stored result instead of making a new model request. Recall at 10 means the fraction of labeled relevant items retrieved within the first ten results. Model names use B for billions of parameters; A marks the active portion in a mixture-of-experts model, which activates selected parts for each token. oMLX is the named local model-serving system. A graphics processing unit (GPU) is the accelerator used for model computation.

The reduced question is whether adding an evidence-linked graph to the current KB improves library coverage answers and relational questions without losing existing lookup quality. Inputs are versioned books, course lessons, papers, and repository files; outputs are cited answers and explicitly scoped unknowns for Huy. The comparison is the existing hybrid search and reading tools. A larger library alone is not evidence that a graph will improve retrieval. Rejected framing: extracting every possible relationship before establishing what coverage decisions the graph must support.

Grounding: read the KB's `CLAUDE.md`, `wiki/decisions.md`, and `wiki/architecture.md`; litgraph's `AGENTS.md`, decisions, active work, phase designs, schema, extraction, resolution, graph, templates, frontier, and tool code. Reused `cached_sources/` and ran the existing `inspect_corpus.py` with a read-only database connection. Added a bounded storage audit and cached primary upstream code in this workspace. No models were loaded, no inference endpoints were called, no GPU or remote services were touched, and no repository was changed. The only output writes are in R3.

The KB's current status page reports **320 technical books and 286,723 vectors**, promoted on 2026-09-30. Its architecture page is dated 2026-05-30 and still describes 46 books. Use the current status for scale and the older page for pipeline design, not current inventory. The storage audit measured **1,285 litgraph documents and 24,782 canonical nodes**; these are storage counts, not independently audited knowledge coverage. Local sources and their dates are listed below.

Before selecting a mechanism, the fit check is:

| Dimension | Current evidence and consequence |
|---|---|
| Signal volume | Existing lookup evaluations exist; human labels for coverage and cross-source relationships were not found in the inspected task material. Create a separate evaluation set. |
| Signal latency | Extraction validity can be checked immediately; whether a proposed research gap matters requires later human judgment. Do not combine these outcomes. |
| Signal breadth | Text is inspectable, but course visuals and repository behavior can remain unindexed. Record these omissions. |
| Budget | Local models only: the specified 27B Qwen on bppc and 35B-A3B mixture-of-experts model on oMLX. No paid extraction API. Local throughput for this proposed workload: not found. |
| Failure mode | Missing relations and mistaken synonym merges silently create false gaps. Coverage status must accompany every absence answer. |
| Instrument stability | Freeze source versions, extraction prompts, model configuration, and evaluation labels. Count actual tokens, requests, failures, and source spans. |

## Prior rejection reasons

These are the three complete recorded rejection sentences, quoted exactly from KB `wiki/decisions.md`, lines 749–752. The passage itself has no decision date; it was read on 2026-10-10. Its historical time estimate is quoted as written, not adopted as a new forecast.

| Reason | Still true at the new scale? | Evidence | Answer |
|---|---|---|---|
| “Our structured books + enrichment + hybrid search already handles this.” | Partly. Book structure and hybrid search remain relevant; the enrichment premise is stale. | KB `wiki/architecture.md` explicitly says enrichment was reverted; decisions record a later paired re-test rejecting it. `CLAUDE.md` still contains a conflicting deferred-enrichment description. Current lookup evaluation reports recall at 10 of 0.9521 on 438 hard questions. | Keep hybrid search as the baseline. Cross-book lookup success does not establish complete topic coverage or reliable absence. Build coverage records without inserting generated enrichment into the search embeddings. |
| “LightRAG needs another LLM pass (~11 hours) for graph construction.” | Additional extraction remains true. The quoted time cannot be carried forward. | LightRAG's pinned extraction implementation makes an initial call for each chunk and can make a second recovery call. Document lengths, chunk counts, prompts, retries, and consolidation affect cost. LazyGraphRAG instead uses zero indexing LLM calls. [LightRAG extraction code](https://github.com/HKUDS/LightRAG/blob/770a21972425a72433b24e1a526204322f9271da/lightrag/operate.py); [LazyGraphRAG](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/). | Retain the cost objection to exhaustive typed extraction. Replace the historical time estimate with measured calls and tokens per extraction section and a measured extrapolation to the inventory. |
| “Marginal quality gain for our query patterns (single-concept lookups, not multi-hop reasoning over unstructured corporate docs).” | Still a credible objection for ordinary lookups; it does not cover the new objective. | The new request includes library coverage, gaps, and relationships across books, courses, papers, and code. HippoRAG 2 addresses linked-passage retrieval; this is evidence of a different query regime, not a result on this KB. [HippoRAG 2](https://arxiv.org/abs/2502.14802). | Do not reverse the rejection globally. Add graph tools for inventory and relationships, then test them on those query types. A larger corpus and a changed question mix are separate reasons to reassess. |

The lighter alternatives recorded immediately below the rejection are concept tagging, a named-entity-to-chunk index, and embedding-based cross-book links. A named entity is an explicitly named thing such as a method or product. These alternatives are sensible first layers, but co-occurrence and similarity do not prove a typed relationship or an absence.

## Approaches

The following fit judgments are **inferences for Huy's corpus**, not vendor claims. Dates describe the cited publication or pinned code revision; all external sources were accessed on 2026-10-10. A chunk is a bounded piece of text. An extraction section should usually be larger than the KB's search child chunk so that a definition and its conditions remain together.

For cost formulas, let **C** be the number of extraction chunks in a document, **G** the maximum recovery rounds, and **S** the number of model calls used to consolidate descriptions or summarize communities. Recovery, sometimes called gleaning, asks the model to extract items it missed. Embedding computation, retries, and entity resolution are additional costs unless stated otherwise. A universal cost per book or per original source token is **not found**: papers use different lengths, prompts, models, and chunking.

### Microsoft GraphRAG, including fast indexing

Microsoft GraphRAG builds an entity-and-relationship graph, hierarchical communities, and generated community reports. Standard indexing extracts each text unit with a model, can run recovery rounds, and summarizes descriptions and communities. Its call count is therefore **at least C + S**, with recovery and optional claim extraction adding calls. A fixed calls-per-document value is not found. Official documentation also describes FastGraphRAG: linguistic processing replaces model-based graph extraction and claims are skipped, but community-report generation remains. Fast indexing therefore does not imply a completely model-free index. Official documentation is undated; accessed 2026-10-10. [Index dataflow](https://github.com/microsoft/graphrag/blob/main/docs/index/default_dataflow.md); [indexing methods](https://microsoft.github.io/graphrag/index/methods/).

It helps corpus-wide synthesis, such as summarizing recurring themes across a collection, and entity-centered questions. **Fit inference:** useful as a later global-summary comparison; expensive as the default over technical books already organized by headings. Generated reports are not a coverage certificate. Defer full community summarization until global questions earn its cost.

### LazyGraphRAG

LazyGraphRAG uses noun phrases and their co-occurrences to build a concept graph and communities, deferring model work to queries. **Indexing extraction cost is zero LLM calls**; linguistic analysis and embeddings still cost computation. Microsoft reports indexing cost at 0.1% of full GraphRAG in its experiment. Query cost is controlled by a relevance-test budget, followed by claim extraction and answer generation; the tested budgets were 100, 500, and 1,500 relevance tests, not equivalent numbers of API requests. Publication: 2024-11-25; availability note: 2025-06-06. [Microsoft research article](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/).

It targets both focused and global exploratory questions. **Fit inference:** borrow cheap concept indexing and selective query-time reading for the broad library; retain durable typed facts only after verification. A co-occurrence graph cannot certify that a method was applied to a problem. Microsoft's reported comparison used 5,590 news articles and 100 synthetic questions, not technical books. A local downloadable release of the complete LazyGraphRAG mechanism was **not found** in the inspected official documentation; the availability note names Microsoft services. Treat it as a design to reproduce and evaluate, not an assumed installable local dependency.

### LightRAG

LightRAG combines an entity-and-relation graph with vector indexes and retrieval at entity and higher relationship levels. The paper describes incremental insertion. The pinned 2026-09-13 extraction code makes **one initial call per chunk**, plus **one additional call when recovery is enabled and its input budget permits**: **C to 2C extraction calls**, excluding cache hits, retries, and description consolidation. This bound is specific to the inspected implementation; it is not the historical implementation's universal formula. [LightRAG code](https://github.com/HKUDS/LightRAG/blob/770a21972425a72433b24e1a526204322f9271da/lightrag/operate.py). The paper was submitted 2024-10-08 and the project identifies its EMNLP 2025 publication. [Paper](https://arxiv.org/abs/2410.05779); [official project](https://github.com/HKUDS/LightRAG).

It helps related-entity questions and broad thematic synthesis. **Fit inference:** a useful baseline and source of incremental-update ideas, but its general graph needs custom teaching, evidence, version, and coverage records. Its paper's one-call keyword retrieval result is not its ingestion cost or the total cost of generating an answer. Do not interpret “Light” as extraction-free.

### HippoRAG 2

HippoRAG 2 adds passage nodes to a phrase graph, matches queries against factual triples, filters matches with a model, and retrieves through Personalized PageRank, which spreads relevance from selected starting nodes along graph links. A triple is a subject, relationship, and object. Its current OpenIE implementation, dated 2026-09-29, makes **two extraction calls per passage: named-entity extraction followed by triple extraction**, or **2C**, before retries. OpenIE means open information extraction without a fixed small relation vocabulary. [Extraction code](https://github.com/OSU-NLP-Group/HippoRAG/blob/94bd935fd236950d51ec822d94f7d0d357eefe15/src/hipporag/information_extraction/openie_openai.py).

The paper, submitted 2025-02-20 and revised 2025-06-19, evaluates factual, discourse, and associative questions. Its cost comparison is reproduced below. [HippoRAG 2 paper](https://arxiv.org/html/2502.14802v2). **Fit inference:** the most relevant later comparison for retrieving evidence across distant sources. Borrow passage linkage and fallback to ordinary retrieval. Open triples and graph ranking still do not produce typed, exhaustive library coverage. Quality with Huy's specified models and existing embedder is **not found**.

### Graphiti / Zep

Zep describes a temporal agent-memory architecture built around Graphiti. It stores episodes, entities, and facts with both when facts apply and when the system recorded them. Publication: 2025-01-20. [Zep paper](https://arxiv.org/abs/2501.13956). Graphiti's inspected code, dated 2026-10-09, separates node extraction, node resolution, edge extraction, and edge resolution. A fixed **LLM calls per episode or per token is not found**: work depends on extracted items, matching candidates, batching, and optional enrichment. Source evidence shows multiple stages, so budgeting one call per document would be unsupported. [Node operations](https://github.com/getzep/graphiti/blob/6ba19a1b4d860c1b72aec8f099f458d424bac90f/graphiti_core/utils/maintenance/node_operations.py); [edge operations](https://github.com/getzep/graphiti/blob/6ba19a1b4d860c1b72aec8f099f458d424bac90f/graphiti_core/utils/maintenance/edge_operations.py).

It helps questions about changing facts and history across conversations. **Fit inference:** carry over time and provenance ideas for software versions, revised papers, and course updates. Static textbook coverage needs source spans and section completeness more than conversational episodes. Litgraph already rejected Graphiti as its library dependency because of episodic abstractions and server-store coupling; keep that local decision unless an integration pilot supplies contrary evidence.

### KAG — Knowledge Augmented Generation

KAG combines a domain schema, links between graph facts and original chunks, knowledge alignment, and a logical-form-guided reasoning engine. A logical form is a structured representation of the operations a question requires. The relevant paper is **arXiv 2409.13731**, submitted 2024-09-10; the cached helper's attempted [2410.05904 lookup is an astronomy paper](https://arxiv.org/abs/2410.05904). [KAG paper](https://arxiv.org/abs/2409.13731); [official project](https://github.com/OpenSPG/KAG).

The pinned schema-free extractor, dated 2025-06-19, invokes named-entity recognition, triple extraction, and name standardization for an ordinary text chunk: **3C model-client invocations**, excluding retries, table processing, external graph enrichment, and later alignment. Transport-level calls per original token are **not found**. [KAG extractor](https://github.com/OpenSPG/KAG/blob/fc98ad136e1bc4a3379b789152d1618707e1b197/kag/builder/component/extractor/schema_free_extractor.py). It helps domain-specific questions involving rules, quantities, and exact relationships. **Fit inference:** borrow source-chunk links and typed question plans; defer the full framework until a bounded technical domain justifies its schema and reasoning machinery.

### nano-graphrag

nano-graphrag is a compact GraphRAG implementation with entity extraction, graph storage, communities, and local/global queries. In the inspected classic extractor, each chunk gets **one initial call plus G recovery calls and up to G−1 continuation checks**, followed by applicable summaries. With its default **G = 1**, the extraction portion is **2C calls**; setting **G = 0** gives **C**. These counts exclude its alternative extraction paths, retries, and summaries. [Extractor, revised 2025-07-23](https://github.com/gusye1234/nano-graphrag/blob/c7a6e7af767ba4326915c879213a497b0f2e293a/nano_graphrag/_op.py); [configuration, revised 2025-07-11](https://github.com/gusye1234/nano-graphrag/blob/644b2770be4d8bcd06a1ebbd8529d5d91abe3f2b/nano_graphrag/graphrag.py).

It helps prototyping GraphRAG-style retrieval. **Fit inference:** inspect small components rather than adopt a hard fork. Litgraph's July 2026 note says it was frozen since October 2024, but the pinned source files have July 2025 revisions; that specific inactivity claim is contradicted. This does not establish current maintenance quality. It still lacks Huy's coverage contract without substantial customization.

### RAPTOR-style trees

RAPTOR recursively embeds, clusters, and summarizes text, creating a tree of increasingly broad summaries. Publication: 2024-01-31. [RAPTOR paper](https://arxiv.org/abs/2401.18059). Its pinned tree builder, dated 2024-02-27, makes **one summarizer invocation per cluster at each generated level**. Thus calls equal the sum of generated clusters across levels, excluding retries and any internal summarizer behavior; a constant per document is **not found**. [Tree builder](https://github.com/parthsarthi03/raptor/blob/71d307c826607a4eb2633b49fad2496c4b434b0c/raptor/cluster_tree_builder.py). The comparison below reports indexing tokens for one implementation and corpus.

It helps broad questions over long documents and material at several levels of abstraction. **Fit inference:** existing chapter and course-unit hierarchies are a cheaper starting tree. Add summaries only to selected branches, and preserve original leaf evidence. A summary tree is not a typed knowledge graph and cannot establish a missing Method-to-Problem relationship. It is worth a separate comparison for course or book synthesis; it should not replace literal search over code identifiers or a coverage ledger.

### Newer work: PathRAG

PathRAG retrieves and prunes relational paths rather than sending a broad graph neighborhood to the answer model. Publication: 2025-02-18. [PathRAG paper](https://arxiv.org/abs/2502.14902). It is principally a retrieval improvement over an existing indexing graph. Its **additional extraction calls for the path-pruning step are zero**, but total graph-construction calls per source document are **not found** in the inspected abstract; upstream graph extraction is still required.

It helps questions whose answer depends on a chain of relationships. **Fit inference:** compare bounded paths with simple one-hop graph tools only after trustworthy relations exist. Source passages must accompany each path, especially when books disagree or software versions differ. Path pruning cannot repair an extraction omission or certify corpus completeness.

### Newer work: HyperSU and RAGU

HyperSU builds source-grounded semantic units and hyperedges, which connect several entities together. It uses GLiNER, a named-entity recognition model, and an optimization that chooses compact, coherent sentence groups. Its offline graph construction requires **zero LLM extraction calls and zero LLM indexing tokens**; the recognition model and embeddings still require computation. It targets evidence chains across passages. This read uses cached version 1, dated 2026-06-03; the live abstract records version 2 on 2026-09-27. [Version 1](https://arxiv.org/html/2606.28351v1); [version history](https://arxiv.org/abs/2606.28351). **Fit inference:** consider this extraction-light design for broad concept discovery. Co-mentioned entities still do not establish a typed benchmark claim. Represent the method, dataset, metric, and conditions together in an evidence record; defer the full retrieval algorithm.

RAGU uses two-stage typed extraction, deduplication, consolidation, and communities; its authors evaluate a domain-adapted 7B extractor. Publication: 2026-07-13. Its paper gives approximate tokens per document, but **exact calls per document or tokens per original source token are not found**. Those estimates use different models and tokenizers and cannot supply Huy's budget. “Two-stage” does not mean two calls per entire document. [RAGU paper, including cost Appendix C](https://arxiv.org/html/2607.11683v1). **Fit inference:** compact extractors merit a quality pilot; this paper does not validate either of Huy's Qwen configurations. Do not download or train another model for this research task.

### Newer work: EffiRAG and context-optimization evidence

EffiRAG links graph records to source chunks and bounds extraction to **one model extraction per selected chunk**, omitting community summaries. Thus extraction is **C calls** when every chunk is selected, or the exact selected-chunk count when its non-model salience filter is enabled, excluding retries. Publication: 2026-09-16. It reports combined ingestion/query provider costs on a small multi-domain experiment; these are not local wall-time measurements. [EffiRAG paper](https://arxiv.org/html/2609.18099v1). **Fit inference:** its evidence-pointer design is closer to the proposed add-on than an all-library summary pipeline. A salience filter must mark skipped material as unknown for coverage questions.

The cached 2026-06-24 study *Is GraphRAG Needed?* compares nine scenarios on a semi-structured precision-medicine KB and finds that expanded retrieval does not proportionately improve final answers. Extraction calls per source document are **not found**. [Study](https://arxiv.org/abs/2606.25656). **Fit inference:** measure supported answers and false absence, not just retrieval volume or graph size. This corpus differs from Huy's library, so it is a caution and evaluation design input, not a verdict against graphs.

### A sourced indexing-cost comparison

Table 12 reports indexing totals for **11,656 MuSiQue passages**, using Llama-3.3-70B-Instruct on four H100 processors. Values are **reported**, not measured in R3. [Comparison and conditions](https://arxiv.org/html/2502.14802v2).

| Approach | Input tokens_reported | Output tokens_reported | Indexing minutes_reported |
|---|---:|---:|---:|
| RAPTOR | 1,700,000 | 200,000 | 100.5 |
| LightRAG | 68,500,000 | 18,300,000 | 235.0 |
| GraphRAG | 115,500,000 | 36,100,000 | 277.0 |
| HippoRAG 2 | 9,200,000 | 3,000,000 | 99.5 |

These published rounded totals cannot predict Huy's hardware performance or the newly pinned implementations' costs.

## litgraph

**Carry over its separation of raw extraction, mentions, aliases, and canonical nodes.** A canonical node is the chosen identity shared by equivalent mentions. Entity resolution is the process of deciding which names refer to the same thing. Litgraph preserves raw extraction responses and versions prompts and models; derived aliases can be rebuilt. Its DuckDB database is a relational store queryable with Structured Query Language (SQL), and NetworkX builds a disposable graph in memory. Retain DuckDB as the authoritative store initially; construct bounded subgraphs for queries rather than rebuilding the whole graph every time. Source: `src/litgraph/db.py`, `extract.py`, and `graph.py`, read 2026-10-10.

**Carry over typed concepts, claims, assumptions, and evidence.** The actual extracted entity types are Method, Problem, Dataset, Metric, Claim, and Assumption. Contrary to a literal reading of the charter, Paper, BlogPost, and Repo are not canonical node types in the measured database; their source records live in `documents`. The nine edge types include `APPLIED_TO`, `USES`, `ASSUMES`, and `CONTRADICTS`. Keep these for research material. Add Book, Course, Lesson, Repository, File, Symbol, Concept, and EvidenceSpan records, plus `CONTAINS`, `EXPLAINS`, `RECOMMENDS_AGAINST`, `PREREQUISITE_OF`, and source-backed `IMPLEMENTS`. A code symbol is a defined function, class, or similar named program element. This extension is a proposal, not existing code.

**Carry over the closed-world contract, with a stronger completeness boundary.** Closed-world means a query answers only about the explicitly indexed world. An SQL anti-join can exhaustively show that a stored relationship is absent; it cannot show that extraction captured every relationship in every source. The charter correctly distinguishes index absence from a model's unsuccessful search. The implemented `who_tried_this` tool is even more cautious: unresolved names establish no absence, and absent edges mean unknown, not disproven. Preserve that behavior and add a coverage certificate.

**Carry over evidence tools, with changes.** `subgraph_around`, `full_text`, `evidence_for`, and `who_tried_this` can become read-only graph tools beside KB search. The current neighborhood tool is limited to one hop and 40 edges; evidence is capped at 20 items; text is capped at 30,000 characters. These explicit caps are useful, but books and courses need paginated section readers and locator-based quotes. `who_tried_this` currently returns any edge type in either direction between resolved nodes; a coverage question must instead specify the intended predicate and direction. Require exhaustive counts before returning absence and expose omitted-item counts. A standard chat-tool interface remains pending in `wiki/active-work.md`; an internal Python tool is not an already deployed integration.

**Do not carry over the extraction configuration unchanged.** Current `models.py` defaults to a paid DeepSeek extractor and a mixed local/API critic configuration. These are incompatible with this task's local-only extraction requirement. Use a separate versioned local extraction profile; do not merge its mentions blindly with the existing DeepSeek graph. Existing facts can be consulted as legacy data with their provenance, but local-only extraction quality remains unmeasured. Keep both model arms isolated during evaluation; publish one chosen profile per comparable extraction cohort. The current schema has immutable extraction responses but does not itself provide a complete persisted edge-validity history.

**Fix document granularity before books.** `extract.py` sends one document call after slicing to **100,000 characters**, with **16,384 maximum output tokens**. The audit found **80 current documents longer than the input cap**. That is a measured exposure to truncation, not proof of 80 erroneous graphs. Entire books would lose later chapters, and a paper-oriented target yield of 5–25 entities is inappropriate for a textbook. Extract by chapter section or lesson segment, track exact source intervals, and distinguish valid-empty extraction from incomplete reading. Verify quotes as actual source substrings; schema-valid JSON alone does not validate the facts.

**Change entity resolution for mixed subjects and scale.** The current implementation auto-merges same-type names at cosine similarity of 0.80 and adjudicates a 0.70–0.80 band. Cosine similarity compares the direction of two vectors; it is not proof of identical meaning. The code creates a full pairwise similarity matrix within each type. Inference: this becomes expensive as names grow and can merge related but distinct concepts across disciplines. Use blocked candidate search, meaning a limited set of plausible matches, plus subject-specific namespaces, context, identifiers, explicit version rules, and human checks of ambiguous merges. Preserve distinct Claim nodes when their conditions or numbers differ. The existing aliases key `(alias_name, node_type)` cannot represent the same ambiguous name in different domains. Cluster-membership changes also change node identifiers; add stable identity redirects before external tools depend on them. Mentions per canonical node is a diagnostic, not proof that merges are correct.

**Carry over templates as leads, not truth.** Transfer gaps, structural holes, unexamined assumptions, and contradictions provide useful review prompts. But the dated decisions supersede the charter's unqualified “structure proposes” rule. On 2026-07-19 the project adopted model proposals plus graph tools and an adversarial evidence check. The corrected active-work scoreboard reports the graph-template arm at **1 hit in 24**, the Qwen model arm without tools at **1 in 23**, and Qwen with graph tools at **10 in 44**. These are internally reported backtest outcomes, not a controlled proof of improvement on a general library. The 2026-07-18 CREEM case explicitly records an extraction-missed edge producing a false gap. Use topology to suggest where to inspect; never describe every missing edge as missing human knowledge.

For books, preserve edition, heading, page or section, negation, and recommendation conditions. For courses, preserve lesson and timestamp, transcript language, slide linkage, prerequisites, exercises, and the status of unprocessed visual material. For code, derive file containment, imports, symbol definitions, and resolvable references from parsers before asking a model for explanatory links. Store commit/version, file, and line locators; do not infer runtime behavior merely from a name or comment. For every medium, distinguish a source's statement from the system's inference and from Huy's own demonstrated knowledge.

## Knowing what it knows

Build a **coverage ledger** alongside the graph: an explicit table describing what processing was completed. For each versioned source unit, record its content hash, a fingerprint of its contents, plus expected units, extracted units, parser outcome, extraction profile, token counts, truncation, errors, quote-verification outcome, and whether visual or code material is excluded. Link every asserted relationship to an EvidenceSpan, a record locating its supporting text, and original KB chunk identifiers. Preserve acquisition time, publication/version time, and extraction time separately. This is proposed infrastructure; these records do not all exist in litgraph today.

Add `coverage(topic, scope, as_of)` and `coverage_gaps(requirement_set, scope)` tools. A requirement set is Huy's chosen list of concepts and relationships needed for a task, learning path, or research agenda. It defines what “enough coverage” means. A library cannot be complete in an unspecified subject.

For “Does my library cover X?”, use this sequence:

1. Resolve X to a concept and disclose ambiguous aliases. Use existing hybrid search as a fallback when graph identity is unresolved.
2. Retrieve source-backed teaching, application, implementation, and evaluation relationships. Return counts by distinct work as well as by evidence span, so repeated editions and transcript duplication do not look like independent coverage.
3. Check completeness of the declared source scope. If any required unit is missing, truncated, failed, skipped, or unprocessed, return **unknown** for absence rather than “not covered.”
4. For a complete scope with no extracted evidence, report **no indexed evidence in this scope**. Search original text and review likely sections before promoting it to a human-reviewed library gap. Even complete processing is not complete extraction recall.

Example query: `coverage("LightRAG ingestion cost compared with HippoRAG 2", scope="R3 inspected sources", as_of="2026-10-10")`. The expected answer shape below is a **design example**, not an executed graph-tool response:

```json
{
  "topic": "LightRAG ingestion cost compared with HippoRAG 2",
  "scope": "R3 inspected sources, not the entire library",
  "status": "covered_in_inspected_sources",
  "support": [
    {"source": "arxiv:2502.14802v2", "locator": "Appendix F, Table 12", "kind": "comparative indexing evidence"},
    {"source": "LightRAG operate.py at 770a2197", "locator": "extract_entities", "kind": "implementation call structure"}
  ],
  "limits": ["Different implementation dates", "No local Qwen throughput measurement"],
  "library_wide_coverage": "unknown"
}
```

For “Where are my gaps?”, use a SQL anti-join between the explicit requirement list and supported coverage relationships, filtered to a source snapshot. The anti-join returns required items with no matching evidence. Then join processing states: **not acquired**, **acquired but not indexed**, **indexed but extraction incomplete**, **complete processing with no extracted support**, or **support present but insufficient for the requirement**. These states demand different actions. “No evaluation of a technique on a required workload” is different from “no introduction to the technique.”

Example requirement: “I need introductions, implementation examples, and evaluation evidence for graph retrieval over course transcripts.” An expected answer reports each missing requirement, the exact reviewed scope, available nearby evidence, skipped units, the latest source date, and the proposed next action. Counts must come from the snapshot query; fabricated zeroes and confidence percentages are prohibited. Method-transfer gaps remain suggestions until source review has ruled out missed relations. Conflicting claims should retain their datasets, metrics, versions, and conditions before being labeled contradictions.

This implements the owner's goal as **the model can inspect the library's evidence and omissions**. It does not claim to know everything in the model's pretrained memory, everything Huy has learned, or everything the outside world knows.

## Recommendation

**Build first:** retain KB hybrid search; create a shared versioned source catalog and processing ledger; add explicit source containment and identifiers without model inference; connect litgraph's evidence and alias concepts to KB section/chunk identifiers. Start typed extraction in one bounded technical domain, with a local-only profile and quote verification. Add coverage and typed-relationship tools as optional tools. Do not make a small agent choose a narrow book subset before seeing search evidence: the KB's September interface evaluations already rejected that pattern. Graph failures should leave normal search available.

**Defer:** full Microsoft community reports, wholesale LightRAG replacement, HippoRAG traversal as the default retriever, conversational-memory infrastructure, all-pairs synonym merging, full KAG deployment, and automated declarations of research novelty. Use chapter/unit trees without generated summaries first. Revisit each deferred choice only when a labeled query class shows a benefit that pays for it.

**Extraction pilot proposal, not an executed experiment:** sample **48 source units**, with **12 each from books, course transcripts, papers, and code**, drawn from **2 books, 2 courses, 8 papers, and 2 repositories**. Keep related sections together for labeling and partition evaluation by source, avoiding answer leakage through neighboring units. Run the same frozen inputs through the specified 27B and 35B-A3B local models in separate arms. In this R3 run neither model is called; scheduling any later pilot requires an authorized compute window, especially on the Mac. The current CPU-only workstation restriction is not permission to run GPU extraction.

Have Huy or a designated knowledgeable reviewer label explicit entities, aliases, required relationships, quotes, and truly absent requirements in this bounded pilot. Create **96 questions: 24 lookups, 24 relational questions, 24 coverage questions, and 24 gap-review questions**. Include **12 known-present and 12 manually checked no-support cases** within the coverage questions. Compare existing search alone, search plus a cheap catalog/concept index, and search plus typed evidence graph. Keep answer model, source snapshot, final context budget, and question wording identical. A blind reviewer grades evidence support, answer correctness, and absence wording. This set is a pilot for finding failures, not a proof of rare-error safety or statistical superiority.

Measure these exact quantities separately by source type and model:

| Number to collect | Operational definition |
|---|---|
| Source units and source tokens | Expected units, attempted units, completed units, skipped units; actual model-tokenizer input length before any truncation. |
| Requests and token amplification | Initial extraction, retries, recovery, consolidation, and entity-resolution calls; prompt and output tokens; total prompt tokens divided by unique original source tokens. |
| Throughput and time | Total wall seconds, seconds per completed unit, input and output tokens per second, median and 95th-percentile unit latency. Report cache hits separately. |
| Resource use | Peak process memory and, only in an authorized GPU run, peak GPU memory; no estimate from parameter count. |
| Completion integrity | Number of input-truncated units, output-truncated responses, invalid schemas, transport failures, and valid-empty outputs. |
| Extraction precision and recall | Supported extracted relations divided by extracted relations; recovered gold relations divided by manually labeled gold relations, stratified by predicate and medium. |
| Resolution errors | Correct merges divided by proposed merges; recovered true-equivalent pairs divided by labeled equivalent pairs; false merges and missed aliases. |
| Provenance validity | Verified source quotes divided by asserted quotes; exact locator validity; unresolved endpoints; dropped relationships during graph construction. |
| Answer quality | Correct supported answers divided by questions for each class; retrieval recall at 10 and normalized discounted cumulative gain at 10 on labeled lookups. The latter rewards placing relevant evidence higher. |
| Absence quality | False-absence count: known-present cases called absent. Correct unknown-state count when processing is incomplete. Human-confirmed gaps divided by graph-proposed gaps. |
| Maintenance cost | Changed-source units reprocessed, unchanged units unnecessarily reprocessed, stale assertions remaining, and incremental update wall seconds. |

Proposed readiness rules are **zero unmarked truncations, zero invalid evidence locators, and zero false absences among the 12 pilot known-present coverage cases**. These are engineering stop rules, not estimated population error rates. Report fractions and numerators/denominators, including when the pilot is too small to resolve a difference. Publish paired answer differences with uncertainty intervals before recommending a retrieval change. Require no resolved lookup regression and a resolved improvement on the target relational/coverage class; if the interval cannot distinguish a gain, the retrieval verdict is **inconclusive** and search remains the default. Do not move a threshold after viewing results.

Forecast full extraction only after measuring source-token inventory and stratified pilot rates. Compute total prompt/output tokens from actual extraction units and their measured amplification, plus separately measured resolution and update work. Report hours only from observed throughput under the chosen local configuration. Local cost is elapsed time and occupied hardware, even when paid API expenditure is zero. If the pilot fails, the catalog and coverage ledger can still ship as useful deterministic infrastructure; typed extraction and graph retrieval remain deferred.

## Output sample

Real output produced by `audit_litgraph_readonly.py` against the existing litgraph database on 2026-10-10; the connection was opened read-only, limited to one thread and 256 MB. This is a storage audit, not a model benchmark. Full output: `cached_sources/litgraph_audit_2026-10-10.txt`.

```text
database_open_mode=read_only
documents_rows=1285
extractions_rows=1873
mentions_rows=68110
canonical_nodes_rows=24782
aliases_rows=31428
document_types=[["blog", 27], ["paper", 1246], ["repo", 12]]
documents_over_input_cap=[[80]]
unresolved_relation_endpoints=[[0]]
```

Existing-helper output also distinguishes local evidence availability from an internet search result: title search found no stored LazyGraphRAG, LightRAG, KAG, or RAPTOR paper titles. That is a statement about these exact title predicates, not proof the terms are absent from full text. `cached_sources/inspection_2026-10-10.txt` preserves the actual rows.

## Sources

All web sources accessed 2026-10-10. Papers provide author-reported experimental evidence; project documentation and source code establish implementation behavior, not local performance. Cached July paper texts were reused and their live identities checked. Where publication/update dates were not found, that is stated explicitly.

| Source | Source date and evidence role |
|---|---|
| [Microsoft GraphRAG dataflow](https://github.com/microsoft/graphrag/blob/main/docs/index/default_dataflow.md) | Publication/update date not found; official implementation documentation. |
| [Microsoft indexing methods](https://microsoft.github.io/graphrag/index/methods/) | Publication/update date not found; standard versus fast indexing. |
| [LazyGraphRAG](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/) | Published 2024-11-25; editor note 2025-06-06; author-reported cost experiment and availability. |
| [LightRAG paper](https://arxiv.org/abs/2410.05779) | First submission 2024-10-08; architecture. |
| [LightRAG project](https://github.com/HKUDS/LightRAG) | README update date not found; identifies EMNLP 2025 publication. |
| [LightRAG pinned extractor](https://github.com/HKUDS/LightRAG/blob/770a21972425a72433b24e1a526204322f9271da/lightrag/operate.py) | File commit 2026-09-13; actual extraction-call structure. |
| [HippoRAG 2](https://arxiv.org/abs/2502.14802) and [version 2 full text](https://arxiv.org/html/2502.14802v2) | Submitted 2025-02-20; revised 2025-06-19; retrieval design and Table 12 comparison. |
| [HippoRAG pinned OpenIE](https://github.com/OSU-NLP-Group/HippoRAG/blob/94bd935fd236950d51ec822d94f7d0d357eefe15/src/hipporag/information_extraction/openie_openai.py) | File commit 2026-09-29; two-stage passage extraction. |
| [Zep](https://arxiv.org/abs/2501.13956) | Submitted 2025-01-20; temporal memory architecture. |
| [Graphiti node code](https://github.com/getzep/graphiti/blob/6ba19a1b4d860c1b72aec8f099f458d424bac90f/graphiti_core/utils/maintenance/node_operations.py) and [edge code](https://github.com/getzep/graphiti/blob/6ba19a1b4d860c1b72aec8f099f458d424bac90f/graphiti_core/utils/maintenance/edge_operations.py) | File commits 2026-10-09; extraction and resolution stages. |
| [KAG](https://arxiv.org/abs/2409.13731) and [official project](https://github.com/OpenSPG/KAG) | Paper submitted 2024-09-10; project README update date not found; domain reasoning and source links. |
| [KAG pinned schema-free extractor](https://github.com/OpenSPG/KAG/blob/fc98ad136e1bc4a3379b789152d1618707e1b197/kag/builder/component/extractor/schema_free_extractor.py) | File commit 2025-06-19; three model-client invocations per ordinary text chunk. |
| [Unrelated cached-helper lookup](https://arxiv.org/abs/2410.05904) | Submitted 2024-10-08; astronomy source, used only to identify the incorrect KAG lookup. |
| [nano-graphrag extraction](https://github.com/gusye1234/nano-graphrag/blob/c7a6e7af767ba4326915c879213a497b0f2e293a/nano_graphrag/_op.py) and [configuration](https://github.com/gusye1234/nano-graphrag/blob/644b2770be4d8bcd06a1ebbd8529d5d91abe3f2b/nano_graphrag/graphrag.py) | File commits 2025-07-23 and 2025-07-11; default recovery count and call formula. |
| [RAPTOR](https://arxiv.org/abs/2401.18059) | Submitted 2024-01-31; recursive summary tree. |
| [RAPTOR pinned cluster tree builder](https://github.com/parthsarthi03/raptor/blob/71d307c826607a4eb2633b49fad2496c4b434b0c/raptor/cluster_tree_builder.py) | File commit 2024-02-27; one summarizer invocation per generated cluster. |
| [PathRAG](https://arxiv.org/abs/2502.14902) | First submission 2025-02-18; relational-path retrieval. |
| [HyperSU version 1](https://arxiv.org/html/2606.28351v1) and [live history](https://arxiv.org/abs/2606.28351) | Version 1 dated 2026-06-03; version 2 dated 2026-09-27; cached technical read uses version 1. |
| [RAGU](https://arxiv.org/html/2607.11683v1) | Submitted 2026-07-13; staged extraction and compact-model evidence. |
| [EffiRAG](https://arxiv.org/html/2609.18099v1) | Submitted 2026-09-16; bounded extraction and source-grounded retrieval. |
| [Is GraphRAG Needed?](https://arxiv.org/abs/2606.25656) | Submitted 2026-06-24; scenario evaluation and retrieval/answer-quality distinction. |

Local source paths are relative to the named project roots, read 2026-10-10:

- **KB root:** `/Users/GaryT/Documents/Work/tools/knowledge-base`. `CLAUDE.md` current status records promotion on 2026-09-30; `wiki/architecture.md` last synced 2026-05-30; `wiki/decisions.md` GraphRAG rejection is undated, and September 2026 interface decisions and enrichment re-tests provide qualifications. Current counts are documented, not queried from the vector service.
- **Litgraph root:** `/Users/GaryT/Documents/Work/products/litgraph`. `AGENTS.md` charter; `wiki/decisions.md` entries 2026-07-15 through 2026-07-25; `wiki/active-work.md` includes 2026-09-18 integration assessment; `wiki/phase1-design.md`, `phase2-design.md`, and `phase4-design.md` describe storage and evaluation contracts. The actual schema/extraction/resolution/tool files were read directly; file publication dates not found. Dated notes are historical reports, not fresh benchmark reruns.
- **R3 evidence:** existing `cached_sources/*.txt` metadata records retrieval on 2026-07-15 through 2026-07-17. `inspect_corpus.py` was reused; `audit_litgraph_readonly.py` produced the quoted live storage output; `fetch_primary_sources.py` preserved pinned code with source dates and checksums in `cached_sources/primary_code_2026-10-10/sources.json`. Failed helper lookups remain visible rather than being silently treated as sources.

The artifact is an internal reversible research decision. Independent model review and local extraction/performance testing were deferred; neither is claimed. The supplied `bash verify.sh` returned **VERDICT: PASS**. Its result validates required structure, length, terms, and source count, not the scientific recommendation. The final check output is preserved in `verification.txt`.
