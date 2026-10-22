# PARTIAL — M3 graph-extraction pilot

Run: kbu-2026-10-07. Owner: Huy. Analysis date: 2026-10-10, Asia/Ho_Chi_Minh.
**Run status: PARTIAL. Extraction-integrity verdict: FAIL.** The coordinator stopped the run after 30 of 48 planned units when the graphics processing unit (GPU) was recalled. Concurrency, the number of requests in flight at once, was 1 throughout. The concurrency 2/4 slice did not run; concurrency scaling was not measured. This analysis made no model-endpoint or workstation calls, loaded no model, and changed no source repository. All new outputs are in M3.

A knowledge graph stores named things as nodes and typed relationships as edges. This pilot asks a language model to extract those records with supporting source quotes. JSON is the machine-readable format used for the results; a schema defines their permitted fields and types. A token is a piece of text in the model's vocabulary. The report measures extraction workload and checks textual support; it does not demonstrate better answers, complete library coverage, or safe conclusions that a subject is absent.

## Sample

The frozen plan in `extractions/sample.json` contains 48 units: 12 book sections from 2 books, 12 course transcript segments covering 8 lectures in 1 course, 12 paper sections from 6 papers, and 12 complete code files from 2 repositories. A repository, abbreviated repo, is a collection of version-controlled source files. The books are Essential GraphRAG and AI Engineering. The course is Using Generative AI as Your Thought Partner. This differs from R3's proposed 2 courses and 8 papers; the actual frozen inputs govern this report.

There are 30 terminal records in `extractions/units.jsonl`: book 12, course 12, paper 6, repo/code 0. **Only 26 records contain returned extraction objects**, because 4 requests failed. Here, a recorded unit is an attempted request with a final log record; a completed response is a returned parseable extraction, including outputs with invalid quotes. A strict-valid unit passes both the stored schema and exact-quote checks. Those distinctions prevent failed requests from being counted as usable extractions.

Exactly **18 planned sample units are missing**: 6 paper and 12 repo/code; book and course each have 0 missing terminal records. The missing identifiers are:

- Paper: paper-07, paper-08, paper-09, paper-10, paper-11, paper-12.
- Repo/code: code-01, code-02, code-03, code-04, code-05, code-06, code-07, code-08, code-09, code-10, code-11, code-12.

The missing papers are the two planned sections each of arXiv:2606.10694, arXiv:2606.25656, and arXiv:2606.28351. The missing code includes 6 knowledge-base files and 6 litgraph files. Missing units are unknown, rather than valid-empty outputs or failed requests. Source text, locators, and content fingerprints are preserved in the frozen sample. Lecture segments retain cue metadata; images, audio, slides, and interactive exercises were excluded. This is a stopped convenience sample, not a randomly drawn representation of the library.

## Throughput

All figures in this section are recomputed from `units.jsonl` only. Source tokens include every recorded attempt, including the failed inputs. The recorded source-count instrument is the saved Qwen3.8 tokenizer, without added special tokens; this pass uses those counts without loading a model or rerunning the tokenizer. Prompt tokens are instructions plus input as reported by the server; completion tokens are the server-reported generated total, including its accounting for reasoning. Usage for the 4 failed requests is **not found**, so token sums are reported subtotals rather than complete consumed-token budgets. A zero for repo/code means no requests were recorded, not free extraction.

Seconds are client request durations. The median is the middle duration; p95, the 95th percentile, uses nearest rank: sort durations and take position ceil(0.95 × number of records). Both include failures. At 12 or 6 records, p95 is the maximum observed duration, not a reliable population tail estimate. Rate denominators are the sum of recorded request seconds, including failures. Units per hour means completed responses divided by that time; the attempt rate is shown separately. Completion tokens per second uses reported tokens divided by the same failure-inclusive time.

| Source type | Recorded units | Completed responses | Source tokens, all attempts | Prompt tokens, reported | Completion tokens, reported | Request seconds | Median seconds/unit | p95 seconds/unit | Completed units per hour | Recorded attempts per hour | Completion tokens/second |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| book | 12 | 9 | 11,976 | 13,890 | 105,663 | 2,342.152 | 174.239 | 300.085 | 13.833 | 18.445 | 45.114 |
| course | 12 | 11 | 11,903 | 18,297 | 167,903 | 2,198.987 | 184.042 | 300.071 | 18.008 | 19.645 | 76.355 |
| paper | 6 | 6 | 3,316 | 7,387 | 94,618 | 1,031.438 | 176.621 | 256.031 | 20.942 | 20.942 | 91.734 |
| repo/code | 0 | 0 | 0 | 0 | 0 | 0.000 | not found | not found | not found | not found | not found |
| all | 30 | 26 | 27,195 | 39,574 | 368,184 | 5,572.577 | 177.678 | 300.071 | 16.797 | 19.381 | 66.071 |

The measured request intervals run from 2026-10-09 18:13:49.436553 UTC through 19:47:12.464935 UTC. Summed request time is 5,572.577 seconds. That excludes gaps between requests and includes shared-server waiting or contention inside each request. Causes of the 300-second failed book/course requests were not independently diagnosed. No isolated-hardware speed claim follows from these timings.

Token amplification means reported prompt tokens divided by source tokens of responses with reported usage. It is 13,890/7,770 for book, 18,297/10,817 for course, and 7,387/3,316 for paper. The all-type fraction is 39,574/21,903. Dividing these incomplete prompt totals by all attempted inputs would conceal unknown usage on failures. Cache reuse means using previously processed prompt text: 26 responses report 0 cached prompt tokens; cache information for 4 failures is not found. Peak process memory and GPU memory are not found. There were no retry, repair, consolidation, or name-resolution calls recorded in these 30 rows. Name resolution, which merges equivalent entity names, was not performed.

## Quality spot-check

This is a **same-agent spot-check, not a blind human label**. It rereads the frozen source text and every extracted relation in the first 3 returned parseable units per available source type: book-01/03/06, course-01/02/03, and paper-01/02/03. There are 0 repo/code outputs to inspect. Failed book requests are skipped for semantic grading and remain counted in Integrity. Selection therefore depends on output availability and covers only the first sampled book, rather than both books.

Supported relations / extracted relations checks whether the source supports both endpoints, the relationship meaning, its direction, and its conditions. Exact quotes are checked separately: a textually true assertion can still have an invalid quote, and an exact quote can still be attached to the wrong relationship. Obvious misses are examples found during reading, not a count of all required relations. Without a fully labeled reference set, recall—the fraction of required relations recovered—is not found. A 0/0 empty output has no precision value.

| Unit | Type | Supported / extracted relations | Exact quotes / extracted | Invalid quotes | Obvious misses |
|---|---|---:|---:|---:|---|
| book-01 | book | 6/7 | 5/7 | 2 | transformer used for next-word prediction; ChatGPT used to generate a haiku |
| book-03 | book | 0/0 | 0/0 | 0 | none identified in this spot-check |
| book-06 | book | 3/5 | 5/5 | 0 | knowledge graph uses nodes to represent concepts and entities |
| course-01 | course | 1/1 | 0/1 | 1 | course explains AI's impact on jobs and setting up a generative AI playground |
| course-02 | course | 5/6 | 6/6 | 0 | ChatGPT and Gemini used for coding |
| course-03 | course | 5/6 | 6/6 | 0 | course explains prompts and context |
| paper-01 | paper | 6/6 | 6/6 | 0 | HippoRAG 2 used for associative and factual memory tasks |
| paper-02 | paper | 8/8 | 8/8 | 0 | PageRank citation to Haveliwala, 2002; HippoRAG 2 used for associativity tasks |
| paper-03 | paper | 5/5 | 5/5 | 0 | SegTreeMem used for long-horizon conversational agents |
| repo/code | repo/code | not found | not found | not found | zero completed outputs |

By type, semantic support is book 9/12, course 11/13, paper 19/19. Pooled support is **39/44**; **36/44** relations have both semantic support and exact quotes. These are reviewed-output fractions, not population accuracy estimates. Full relation annotations, source locators, and missed-relation examples are in `extractions/spotcheck.json`.

The book-01 edge saying RAG improves on hallucinations uses an unsuitable comparison predicate: hallucinations is a problem, rather than a comparison method. Its 2 altered quotes remove internal line breaks. In book-06, 2 application edges turn the authors' storage recommendation into unconditional applications; the quotes themselves are exact. These are reviewer judgments under the supplied prompt. Course-01 joins nonadjacent transcript passages into 1 quote. Course-02's Gemini integration statement does not establish its asserted directional dependency on Google Workspace. Course-03 miscasts a recommendation for where to start as ChatGPT addressing a task called “where to start.”

The reviewed paper relations are supported as statements in the cached abstracts and introduction, with comparison scope retained. This does not reproduce the authors' experiments. Broad labels such as “Recent RAG approaches” and generic problem names still need source-scoped identities. The transcript spelling “Anthropx Cloud” is retained as source text; it was not silently corrected. Course product claims are assessed for support in this transcript, not for current external accuracy.

## Integrity

Counts below come only from the 30 terminal records. Invalid JSON means parsing failed; invalid schema means an extraction violated the permitted fields or types; an unverifiable quote is not an exact contiguous substring of its frozen source. Failures means transport failures, shown separately from quote-invalid units. These categories are not interchangeable.

| Type | Invalid JSON | Invalid schemas | Input truncated, client flag | Output truncated, known | Output truncation unknown | Unverifiable quotes / asserted | Quote-invalid units | Transport failures | Strict-valid units | Valid-empty outputs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| book | 0 | 0 | 0 | 0 | 3 | 2/38 | 1 | 3 | 8 | 1 |
| course | 0 | 0 | 0 | 0 | 1 | 6/44 | 3 | 1 | 8 | 0 |
| paper | 0 | 0 | 0 | 0 | 0 | 0/51 | 0 | 0 | 6 | 0 |
| repo/code | 0 | 0 | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 0 |
| all | 0 | 0 | 0 | 0 | 4 | 8/133 | 4 | 4 | 22 | 1 |

Verified quotes are **125/133**. Quote-invalid units are book-01 and course-01/04/07. Transport failures are book-02/04/05 and course-10, all with HTTP status 500; HTTP is the network response protocol, and this code records a server error. No returned response reports a length-limit finish. Output truncation is unknown for the 4 failed requests. Client-side input truncation is flagged false in all 30 records, but server-side input truncation was not independently inspected for any request; its absence cannot be proven from the client flag.

There are **22/30 strict-valid units**, including book-03's empty output, and 8/30 units fail transport or quote integrity. Source fingerprints match the frozen inputs for all recorded units. The zero invalid-JSON/schema counts apply to the returned outputs; they do not turn failed or missing requests into valid objects. Schema and quote checks also do not prove semantic correctness, as the spot-check shows.

R3's zero-invalid-evidence readiness rule is not met. No entities were merged, no graph-construction drop rate was measured, and no blind answer study or known-present/no-support coverage test was performed. False absences, alias-resolution accuracy, and maintenance cost are not found. The verdict is therefore FAIL for extraction integrity and inconclusive for retrieval benefit. A missing or failed unit must remain “unknown” in coverage answers. The next evidence needed is quote repair validation, the 18 missing units and 4 failed inputs in a separately authorized run, repo/code timing, and blind human review; this analysis does not resume extraction.

## Projection

**Inference:** these are token-scaled planning calculations, not observed whole-library completion times. They use concurrency-1 measurements only. The main rate is source tokens in returned extraction objects **per hour**, divided by all recorded request time including failures. Returned objects with quote errors count toward this rate, so these are not verified-graph production rates. A stable fraction of failures and similar output density are assumptions, rather than forecasts proven by this sample. No concurrency speedup is applied: concurrency scaling was not measured.

The fresh read-only disk census inspected JSON chunk files one at a time under `knowledge-base/data/chunks/`. A parent section is the larger source unit; child chunks are search subdivisions of the same text. Only parent `text` fields are counted, avoiding duplication with children and their context. The census found 687 source files, 94,231 parents, and 316,546,949 characters. It excluded 1 empty-parent mapping cache, `v10-gate-parent-map.json`. The 320 registered-book, 8 reference-documentation, and 359 philosophy language/edition groups match the existing scope inventory. Language and edition files are separate workload copies, not 359 independent original works. Repeated text among parents is not deduplicated.

No tokenizer was executed over the library in this pass. Estimated source tokens equal measured parent characters divided by the sample's aggregate characters per token. Calibration uses recorded unit source counts; it includes failed inputs whose source text was already counted. Paper calibration uses the 6 completed sample sections, rather than the 6 missing sections.

| Calibration type | Source characters | Source tokens | Characters per token |
|---|---:|---:|---:|
| book | 52,696 | 11,976 | 4.400134 |
| course | 50,613 | 11,903 | 4.252121 |
| paper | 16,368 | 3,316 | 4.936068 |

R3 reports 1,285 litgraph documents. The existing on-disk inventory in M3 partitions this into 1,246 paper, 12 repo README, and 27 blog documents; those counts sum to 1,285. Paper source text is 63,331,972 characters. Repo text is 199,023 characters with 59,051 previously counted tokenizer tokens. These stored inventory measurements are reused, not fresh database or full-repository measurements. A README is a repository's introductory document; it does not represent the entire implementation. Blogs were not an extraction arm and are excluded from the projection. The complete course-library size and full source size of those 12 repos are not found.

| Population | Files / documents | Source tokens | Returned source tokens per hour | Inferred token-scaled hours | Unit-scaled hours |
|---|---:|---:|---:|---:|---:|
| registered technical books; estimated tokens | 320 | 58,874,615.982 | 11,942.864 | 4,929.690 | 5,232.830 |
| reference documentation; book-rate proxy; estimated tokens | 8 | 8,027,693.295 | 11,942.864 | 672.175 | 899.560 |
| philosophy language/edition files; book-rate proxy; estimated tokens | 359 | 5,037,994.755 | 11,942.864 | 421.841 | 679.441 |
| paper records; estimated tokens | 1246 | 12,830,450.828 | 11,573.745 | 1,108.583 | not found |
| one supplied course; stored tokens | 1 | 11,903.000 | 17,708.697 | 0.672 | 0.666 |
| stored repo README records; stored tokens | 12 | 59,051.000 | not found | not found | not found |

Token-scaled hours equal source tokens divided by returned source tokens per hour. Unit-scaled hours equal the parent-section count divided by completed units per hour; this second calculation assumes future units resemble the sample and exposes sensitivity to fixed instruction/reasoning time. The supplied course projection covers only its 8 lectures and 12 segments. Repo/code hours are **not found**, because 0 code units completed. No book or paper timing proxy is substituted for repo timing. A complete mixed-library total is therefore not found.

The sample-derived ratio can misestimate other languages, code, or document formatting. Reference documentation and philosophy use the book rate as an explicit, unmeasured proxy. Paper workload is extrapolated from only 3 completed paper sources and may have different section sizes or relation density elsewhere. The assumptions are unchanged prompt and server settings, comparable segmentation, stable shared-server load, and comparable generated reasoning and relation counts. The estimates exclude retries and repairs, name resolution, embeddings (numeric text representations), graph insertion, human labeling, images/video, and future updates. They do not promise a validated graph in the listed hours. R3's advice to retain ordinary search and defer broad graph retrieval remains appropriate until quality and answer benefits are demonstrated.

## Output sample

Real output produced by `python3 analysis_pass.py` in this workspace; token totals are server-reported subtotals where usage is missing:

```text
book: records=12 completed=9 source_tokens=11976 prompt_tokens_reported=13890 completion_tokens_reported=105663
course: records=12 completed=11 source_tokens=11903 prompt_tokens_reported=18297 completion_tokens_reported=167903
paper: records=6 completed=6 source_tokens=3316 prompt_tokens_reported=7387 completion_tokens_reported=94618
repo/code: records=0 completed=0 source_tokens=0 prompt_tokens_reported=0 completion_tokens_reported=0
integrity: transport_failures=4 unverifiable_quotes=8 asserted_quotes=133 strict_valid_units=22
missing: paper=6 repo/code=12 total=18
chunk_census: files=687 parent_units=94231 parent_chars=316546949
```

## Sources

All local sources were read on 2026-10-10. File modification dates below identify the snapshots; they are not publication dates. No external pages were newly fetched in this analysis. External URLs identify the recorded source works; textual claims in the spot-check describe the supplied cached excerpts, not independently verified current findings.

- `../R3/REPORT.md`, research date 2026-10-10: Recommendation supplies the measurement definitions and readiness rules; its scale statement supplies the 1,285-document context.
- `extractions/units.jsonl`: request timestamps 2026-10-09 18:13:49.436553–19:47:12.464935 UTC; sole measurement input for throughput and integrity. `extractions/sample.json`, `profile.json`, and `prompt.txt`: frozen source text, source fingerprints, tokenizer counts, and extraction rules. The recorded model is qwen3.8-27b and prompt version is m3_mixed_v1. Profile publication date: not found.
- `knowledge-base/data/chunks/`: fresh character census recorded in `extractions/analysis_chunk_inventory.json`, read 2026-10-10. Book calibration snapshots: `essential-graphrag.json`, modified 2026-09-28; `ai-engineering-huyen.json`, modified 2026-06-13. Book publication dates: not found in these artifacts.
- `inputs/coursera-genai-transcripts.json`: course transcript, modified 2026-10-09; publication date not found. The actual lecture URLs are not found in this input. Frozen cue locators and source text are in the sample.
- `extractions/book_scope.json`, `litgraph_inventory.json`, and `repo_inventory.json`: previously produced 2026-10-10 disk inventories. Full repo source sizes are not found. `extractions/source_dates.json` retains source-file modification timestamps and fingerprints. `extractions/spotcheck.json` contains the reread same-agent annotations, dated 2026-10-10.
- [HippoRAG 2 paper](https://arxiv.org/abs/2502.14802): stored publication date 2025-02-20; stored acquisition 2026-07-16 13:25:40.127998. Completed sample sections paper-01/02; cached text assessed for source support only.
- [SegTreeMem paper](https://arxiv.org/abs/2606.04555): stored publication date 2026-06-03; stored acquisition 2026-07-15 09:55:04.148707. Completed sample sections paper-03/04.
- [Paper arXiv:2606.09900](https://arxiv.org/abs/2606.09900): stored publication date 2026-06-05; stored acquisition 2026-07-15 09:54:41.924313. Completed sample sections paper-05/06.
- [Paper arXiv:2606.10694](https://arxiv.org/abs/2606.10694): stored publication date 2026-06-09; acquisition 2026-07-15 09:54:29.795916; both sample outputs missing.
- [Paper arXiv:2606.25656](https://arxiv.org/abs/2606.25656): stored publication date 2026-06-24; acquisition 2026-07-17 13:33:46.783832; both sample outputs missing.
- [Paper arXiv:2606.28351](https://arxiv.org/abs/2606.28351): stored publication date 2026-06-03; acquisition 2026-07-17 13:37:31.513238; both sample outputs missing. All paper dates are supplied metadata, not fresh publication verification.

`analysis_pass.py` and `analysis_report.py` reproduce this analysis without model or network calls. `extractions/summary.json` is the current partial-run summary and `projection.json` contains the calculations. Earlier progress, audit, inventory, and generation scripts are historical artifacts; they are not the authority for the 30-row report. Verification on 2026-10-10: `bash verify.sh` returned **VERDICT: PASS**. The separate offline audit returned **PASS**, rechecked 133 relation quote locators, and reconciled summary totals and projection arithmetic; its output is in `extractions/analysis_checks.log`. Structural acceptance does not establish extraction truth or a finished graph.
