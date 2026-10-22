# M3 — graph-extraction pilot

**Final status: 48 of 48 units at concurrency 1; concurrency scaling not measured.**

Run: kbu-2026-10-07. Owner: Huy. Analysis date: 2026-10-10, Asia/Ho_Chi_Minh. Snapshot timestamp: 2026-10-09T21:57:42.801867+00:00.
**Collection status: COMPLETE. Extraction-integrity verdict: FAIL.** All 48 planned concurrency-1 attempts have a terminal record; 40 returned parseable extractions and 35 passed the stored schema and quote checks, including 1 valid empty output. The concurrency 2 and 4 slices did not run after the GPU was recalled. Their missing measurements do not change completion of the final 48-unit scope. Collection completion means every requested attempt has a durable record; it does not mean every extraction succeeded. The earlier report `REPORT-partial-30.md` is preserved unchanged.

A knowledge graph stores named things as nodes and typed relationships as edges. This pilot asked a language model to produce those records with source quotes. JSON (JavaScript Object Notation) is the machine-readable text format; a schema defines its permitted fields and types. A token is a piece of text in the model's vocabulary. Concurrency means requests in flight at once; c1, c2 and c4 denote concurrency 1, 2 and 4. Truncation means text was cut off. The saved rows identify the model as qwen3.8-27b. This final pass performs only lightweight, standard-library analysis of saved files. It made no model-endpoint or workstation calls, loaded no model or tokenizer, and changed no source repository.

## Sample

The frozen `extractions/sample.json` has 48 inputs: 12 book sections from 2 books, 12 course transcript segments covering 8 lectures in 1 course, 12 paper sections or contiguous opening spans from 6 papers, and 12 whole code files from 2 repositories. A repository, abbreviated repo, is a collection of version-controlled source files. The book snapshots are Essential GraphRAG and AI Engineering; the course input is Using Generative AI as Your Thought Partner. These are convenience inputs, not a random library sample. The frozen text, locators and content fingerprints define this experiment. A locator identifies a source position, such as a line or cue range; a fingerprint is a SHA-256 digest, a fixed identifier calculated from the exact saved text. Source images, audio, slides, exercises and code execution are outside it. Where heading detection failed, the frozen preparation used bounded opening spans that can cut across section or sentence boundaries. Sending each whole frozen input is not the same as sending each whole paper; the client input-truncation flag describes the frozen unit only.

The earlier collection extended 30 terminal records with paper-07 through paper-12 and code-01 through code-12 at concurrency 1. This final analysis sent no requests. All original 30 rows remain byte for byte, including failed requests; the complete 48-row file was also preserved unchanged during analysis. Missing c1 inputs: none. Stored request metadata contains only `model` and `messages`; no generation parameters were sent. The saved runner configures a 600-second network timeout. Its failed durations are listed exactly in `units.jsonl`; their underlying server cause is not found.

The canceled concurrency slices were planned to reuse book-01/02, course-01/02, paper-01/02 and code-01/02, with 2 inputs per source type. No repeated slice rows exist. An attempted unit has a terminal record, a returned response has a parseable extraction, and a strict-valid response passes the stored schema and exact-quote checks. These meanings are kept separate throughout.

## Throughput

All measurements below are recomputed from `units.jsonl`. Source tokens use stored counts from the saved Qwen3.8 tokenizer, without added special tokens; this pass does not rerun tokenization. Prompt tokens are instructions plus input as reported by the server. Completion tokens include the server's accounting for generated reasoning. Usage missing on failures is **not found**, so token sums are reported subtotals, not complete consumed-token budgets.

The sequential denominator sums client request durations, including failures and waiting within requests. Completed units per hour counts returned parseable extractions; attempts per hour counts all terminal records. Median is the middle sorted request duration, or the average of the 2 middle durations when the count is even. The 95th percentile, p95, sorts durations and selects position ceil(0.95 × count), where ceil means round up to the next integer. These small groups do not establish population tail latency. Deliberate gaps between runs are excluded.


| Source type | Records | Returned | Strict-valid | Source tokens | Prompt tokens reported | Completion tokens reported | Request seconds | Median seconds | p95 seconds | Completed units per hour | Strict-valid units per hour | Attempts per hour | Completion tokens/second |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| book | 12 | 9 | 8 | 11,976 | 13,890 | 105,663 | 2,342.152 | 174.239 | 300.085 | 13.833 | 12.296 | 18.445 | 45.114 |
| course | 12 | 11 | 8 | 11,903 | 18,297 | 167,903 | 2,198.987 | 184.042 | 300.071 | 18.008 | 13.097 | 19.645 | 76.355 |
| paper | 12 | 11 | 11 | 7,928 | 14,371 | 166,327 | 2,123.794 | 176.486 | 300.043 | 18.646 | 18.646 | 20.341 | 78.316 |
| repo/code | 12 | 9 | 8 | 41,408 | 29,291 | 158,293 | 2,691.778 | 208.543 | 300.117 | 12.037 | 10.699 | 16.049 | 58.806 |
| all | 48 | 40 | 35 | 73,215 | 75,849 | 598,186 | 9,356.711 | 181.765 | 300.071 | 15.390 | 13.466 | 18.468 | 63.931 |

Concurrency scaling is **not measured**. The table below contains only the sequential baseline for the 8 inputs that had been chosen for the canceled slices. Its 1.000 ratio compares the baseline to itself and is not a measured scaling gain. No concurrency 2 or 4 speedup, efficiency, or parallel completion rate can be calculated from these rows. Book-02 failed in this baseline, so even a future comparison would need to retain that failure and account for output length, server load, cache reuse, and run order.

| Matched slice | Records | Returned | Strict-valid | Active seconds | Attempts per hour | Completed units per hour | Completion tokens reported | Speedup vs c1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| c1 | 8 | 7 | 5 | 1,517.149 | 18.983 | 16.610 | 98,310 | 1.000 |

Cache reuse means reusing previously processed prompt text. Of 48 requests, 40 report cache counts, 0 report positive reuse, and the reported sum is 0 cached prompt tokens. Missing cache data is unknown. Peak process and graphics processing unit (GPU) memory are not found. No resource telemetry was inspected. Reported prompt amplification, prompt tokens divided by source tokens of requests with usage, is book: 1.787645; course: 1.691504; paper: 2.080643; code: 1.263632.

## Quality spot-check

This is a **same-agent, unblinded spot-check**, not independent human labeling. The analyst also performs the output review and sees output identities and prior annotations before grading. The earlier book-01/03/06, course-01/02/03 and paper-01/02/03 annotation rows are retained unchanged and checked against the recorded relations. This final pass re-read every returned new paper unit and 3 returned code units against the frozen inputs: paper-07 through paper-11, plus code-01, code-02 and code-05. Paper-12 has a terminal failure record; its source was read but there is no output to grade. Code selection follows frozen sample order, skipping failed code-03 and code-04. Failed or non-JSON requests are counted in integrity but cannot receive semantic relation grading. The selection is conditioned on output availability.

Semantic support checks both endpoints, relationship meaning, direction, negation and stated conditions against the frozen input. An exact quote is a contiguous source substring with unchanged whitespace and punctuation. Exact quotes and supported meanings are separate tests. Obvious misses are illustrative omissions found while reading, not a full reference set. Recall, the fraction of required relations recovered, is not found because complete human labels were not created. Empty output has no precision fraction. Relation-level verdicts, review notes and source locators are in `extractions/spotcheck.json`. Sample order biases the code selection toward knowledge-base; neither repo has complete human labels. The retained book checks cover only the first sampled book.


| Unit | Type | Supported / extracted | Exact quotes / extracted | Obvious misses |
| --- | --- | --- | --- | --- |
| book-01 | book | 6/7 | 5/7 | transformer APPLIED_TO next-word prediction; ChatGPT APPLIED_TO generating haiku |
| book-03 | book | 0/0 | 0/0 | none identified |
| book-06 | book | 3/5 | 5/5 | knowledge graph USES nodes to represent concepts and entities |
| code-01 | code | 1/2 | 2/2 | source unit USES os through os.environ.get; imported module and access omitted |
| code-02 | code | 7/7 | 7/7 | _chapter_title USES re |
| code-05 | code | 0/7 | 6/7 | _append USES datetime.now |
| course-01 | course | 1/1 | 0/1 | Using Generative AI as Your Thought Partner EXPLAINS impact of AI on your job; Using Generative AI as Your Thought Partner EXPLAINS setting up a generative AI playground |
| course-02 | course | 5/6 | 6/6 | ChatGPT APPLIED_TO coding; Google's Gemini APPLIED_TO coding |
| course-03 | course | 5/6 | 6/6 | this course EXPLAINS prompt; this course EXPLAINS context |
| paper-01 | paper | 6/6 | 6/6 | HippoRAG 2 APPLIED_TO associative memory tasks; HippoRAG 2 APPLIED_TO factual memory tasks |
| paper-02 | paper | 8/8 | 8/8 | Personalized PageRank algorithm CITES Haveliwala, 2002; HippoRAG 2 APPLIED_TO associativity tasks |
| paper-03 | paper | 5/5 | 5/5 | SegTreeMem APPLIED_TO long-horizon conversational agents |
| paper-07 | paper | 5/5 | 5/5 | REAL USES temporal and confidence-aware directed property graph |
| paper-08 | paper | 11/11 | 11/11 | REAL USES non-destructive incremental graph updates |
| paper-09 | paper | 4/5 | 5/5 | none identified |
| paper-10 | paper | 8/8 | 8/8 | Retrieval-Augmented Generation (RAG) CITES Lewis et al. (2020); context engineering method USES new agentic loop design pattern |
| paper-11 | paper | 8/8 | 8/8 | HyperSU USES semantic-unit hyperedges |

**paper-12 unavailable for output grading:** HTTP status 500; no returned extraction object. Frozen source read; semantic grading of output is not found.

**code-03 unavailable for output grading:** HTTP status 500; no returned extraction object. Output grading is not found; selection proceeds to the next returned code unit.

**code-04 unavailable for output grading:** HTTP status 500; no returned extraction object. Output grading is not found; selection proceeds to the next returned code unit.

Pooled semantic support is 83/97; support with exact quotes is 80/97; exact quotes alone are 93/97. These describe only inspected outputs. Schema validity and correct quotation do not establish correct relationship meaning or complete coverage. A relation predicate is its relationship label, such as USES or ASSUMES; a missing or inappropriate predicate can invalidate an edge even when its quote is exact.

**code-01:** The .embedder/model_dim membership is supported by its import and callable use. The pathlib/Path import association is explicit, but assigning Path the Module type (which includes classes) is not established by this unit: it imports and calls Path without declaring whether that external symbol is a class or a function. Under the source-only rule that typed endpoint is unconfirmed and is scored unsupported. Both quotes are exact. Only imports are extracted; many configuration dependencies are omitted. No runtime behavior was tested.

**code-02:** All 7 dependencies are supported by imports or direct calls, and every quote is exact. The function-call quotes include their caller definitions rather than detached call lines. The source module is labeled with its docstring sentence instead of a stable file identifier; its dependency meaning is supported, but identity resolution must bind that description to this source path. The regular-expression dependency of _chapter_title is omitted. This is static source support, not an execution test.

**code-05:** Every one of the 7 relation records omits edge_type, so its predicate is not found and no complete typed relationship can be confirmed; fields are not repaired or inferred. Only 6/7 evidence strings match the frozen source exactly. Relation index 4 changes the source expression "n_results": n_results into "n_results": _result_count(result), so that quotation is altered. This corrects the earlier code annotation, which reported 7/7 exact quotes. The stored validator skips quote checks for all 7 malformed records; the final scan checks them separately. Additional datetime usage is omitted. No source code was executed.

**paper-07:** All 5 relations are supported by the frozen text and use exact quotes. The average-improvement metric is broad and its underlying evaluation measure is not defined in this unit; the source comparison scope is retained in the evidence. This review checks the authors' statements, not their experimental results. Source: [arxiv:2606.10694](https://arxiv.org/abs/2606.10694); publication date as stored in the frozen metadata: 2026-06-09.

**paper-08:** All 11 relations have source support and exact quotes. C1/C2/C3 are local challenge identifiers and require source-scoped names. The conditional trigger for counterfactual inference remains in its evidence; the edge alone does not encode that condition. The source's empirical performance claims were not reproduced. Source: [arxiv:2606.10694](https://arxiv.org/abs/2606.10694); publication date as stored in the frozen metadata: 2026-06-09.

**paper-09:** The first 4 relations describe the context engineering method with exact support. Relation 4 misclassifies a reported analytical finding as an explicitly assumed premise: the text says the retrieval-generation gap was identified by analysis. All 5 quotes are exact, demonstrating that quote matching alone misses predicate/type errors. No additional clear edge was identified under the frozen allowed relation meanings. Source: [arxiv:2606.25656](https://arxiv.org/abs/2606.25656); publication date as stored in the frozen metadata: 2026-06-24.

**paper-10:** All 8 relations have explicit support and exact quotes. The illustrative precision-medicine question was not turned into factual gene relations. The output omits explicit citation credit and a stated agentic loop dependency. Names such as Traditional RAG approaches remain broad source-specific labels. Source: [arxiv:2606.25656](https://arxiv.org/abs/2606.25656); publication date as stored in the frozen metadata: 2026-06-24.

**paper-11:** All 8 relations are supported by exact source quotes. The often qualifier on existing HyperRAG methods and the comparison scope on the improvement must travel with the evidence; these family labels should not become universal claims about every implementation. The quoted up-to improvement is an author claim, not a reproduced benchmark. Semantic-unit hyperedges are explicitly described but lack their own uses edge. Source: [arxiv:2606.28351](https://arxiv.org/abs/2606.28351); publication date as stored in the frozen metadata: 2026-06-03.

## Integrity

The following counts keep sequential inputs separate from repeated concurrency trials. A network failure remains an unknown extraction; an altered quote is unusable evidence even if its statement is plausible.

| Run | Records | Invalid JSON | Schema-invalid | Transport failures | Quote-invalid units | Unverifiable / validator-checked quotes | Strict-valid units | Output truncation reported |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| c1 | 48 | 0 | 1 | 8 | 4 | 8/238 | 35 | 0 |
| c2 | 0 | 0 | 0 | 0 | 0 | 0/0 | 0 | 0 |
| c4 | 0 | 0 | 0 | 0 | 0 | 0/0 | 0 | 0 |

Across all 48 rows, the stored validator finds 230/238 exact quotes; it skips 7 evidence fields in malformed relation records. An independent string scan of every returned evidence field finds 236/245 exact matches, including those skipped fields; locators are saved in `extractions/completion-quote-audit.json`. Exact evidence does not repair a missing predicate. Output truncation is unknown for 8 rows without a finish reason. The client input-truncation flag is false in 48 rows; server-side input truncation was not independently inspected. All source fingerprints, quote locators, request fields, prompt fingerprints and run/unit uniqueness were rechecked against the frozen sample. The original-byte check proves existing rows were not rewritten.

The separate scan finds altered quotes in 5 units: book-01, code-05, course-01, course-05, course-09. The stored validator's quote-invalid count excludes malformed code-05; its schema failure and altered quote overlap and must not be added as different failed units. All 7 code-05 predicates are missing; 1 of those 7 quotes is altered. Invalid JSON means text cannot be parsed as JSON; schema-invalid means parsed fields violate the permitted structure; truncation means text was cut off. A reported stop reason does not prove extraction coverage.

Transport failures by run: c1: book-02, book-04, book-05, course-10, paper-12, code-03, code-04, code-09; c2: none; c4: none. Their underlying server cause is not found; no diagnosis is inferred from HTTP status 500 alone. HTTP is the network response protocol, and status 500 reports a server error.

The extraction-integrity verdict remains FAIL when any transport, schema, quotation or truncation check fails. A passing report acceptance script verifies structure, not extraction truth. No names were merged into shared identities, no graph was inserted, and no blind answer-quality or known-present coverage study was run. An absent edge must not be used to claim a topic is absent from the library. The next decision requires validated quote handling and independent semantic labels before trusting graph retrieval. This internal pilot uses the requested same-agent review; independent review and a literature benchmark were outside this completion pass.

## Projection

Every duration in this section is an **inference**, not observed full-library processing. Token-scaled hours equal population source tokens divided by source tokens in returned c1 extractions per hour, including failed-request time. Unit-scaled hours divide population input count by returned c1 units per hour. Returned outputs with quote or schema errors remain in the rate; these estimates do not purchase a verified graph. Different unit sizes and generated reasoning lengths can cause the two estimates to diverge.

The prior on-disk census contains 320 registered book files, 8 reference-documentation corpora and 359 philosophy language/edition files. It counts parent text once rather than duplicate search chunks. The existing direct token census has matching file, parent and character totals: 64,844,679 registered-book tokens, 9,545,958 reference-documentation tokens and 7,194,460 philosophy tokens. This final projection uses those stored counts; the partial report used character-derived estimates. No new tokenization was run. The stored litgraph inventory has 1,246 papers, 12 repo introductory documents called READMEs and 27 blogs. The 63,331,972 paper characters are recalibrated with all currently recorded paper inputs. The complete course-library inventory and complete source of those 12 repos are not found. Blogs have no extraction arm and are excluded.

Stored code inventory covers 20 Python files in each of the 2 accessible production-code folders: 40 files and 112,811 tokens. It excludes tests, dependencies, documentation and other languages. Code projection now uses measured code throughput. Applying that rate to 59,051 stored README tokens is an explicit unmeasured format proxy. The 12-repo scenario multiplies the 2 accessible trees by 6, assuming 20 Python files per repo; it is not a measured inventory of all 12 repos.


| Population | Source tokens | Returned source tokens per hour | Sequential hours | Unit-scaled hours | c2 scenario hours | c4 scenario hours |
| --- | --- | --- | --- | --- | --- | --- |
| registered_book | 64,844,679.000 | 11,942.864 | 5,429.575 | 5,232.830 | not found | not found |
| reference_documentation | 9,545,958.000 | 11,942.864 | 799.302 | 899.560 | not found | not found |
| philosophy | 7,194,460.000 | 11,942.864 | 602.407 | 679.441 | not found | not found |
| paper records | 12,379,394.808 | 11,707.912 | 1,057.353 | not found | not found | not found |
| one supplied course | 11,903.000 | 17,708.697 | 0.672 | 0.666 | not found | not found |
| stored repo README records; code proxy | 59,051.000 | 31,001.076 | 1.905 | not found | not found | not found |
| two accessible Python source trees | 112,811.000 | 31,001.076 | 3.639 | 3.323 | not found | not found |
| 12-repo Python-code scenario; 20 files per repo | 676,866.000 | 31,001.076 | 21.834 | 19.939 | not found | not found |

Concurrency 2 and 4 scenario hours are **not found** because those slices did not run; their speedups are not assumed. Reference-documentation and philosophy timings use an unmeasured book-format proxy. All estimates exclude retries, repairs, name resolution, embeddings (numeric text representations), graph insertion, human labels and future updates. These are processing-time inferences under the measured sequential rate, not calendar promises or verified-graph costs.

## Output sample

Real output produced by `python3 completion_report.py` from the saved request rows:

```text
book: records=12 completed=9 source_tokens=11976 prompt_tokens_reported=13890 completion_tokens_reported=105663
course: records=12 completed=11 source_tokens=11903 prompt_tokens_reported=18297 completion_tokens_reported=167903
paper: records=12 completed=11 source_tokens=7928 prompt_tokens_reported=14371 completion_tokens_reported=166327
repo/code: records=12 completed=9 source_tokens=41408 prompt_tokens_reported=29291 completion_tokens_reported=158293
integrity: c1_strict_valid=35 c1_records=48 all_transport_failures=8 validator_unverifiable_quotes=8 validator_checked_quotes=238
runs: c1=48/48 c2=NOT_RUN c4=NOT_RUN scaling_measured=False original_30_preserved=True
spotcheck: units=17 supported=83/97 supported_exact=80/97
```

## Sources

Local artifacts were read during this final analysis; the summary timestamp above dates the read. Modification dates identify snapshots, not publication dates. No external pages were fetched: paper statements are assessed only as claims in supplied cached excerpts. The URLs below identify those source works, and dates are explicitly stored metadata rather than fresh publication verification.

- `extractions/units.jsonl`, request timestamps recorded per row: sole timing, usage and integrity measurement input. `sample.json`, `profile.json` and `prompt.txt`: frozen text, locators, fingerprints and prompt. The model is qwen3.8-27b; the prompt version is m3_mixed_v1. Profile publication date: not found.
- `extractions/completion_manifest.json`, started 2026-10-09T20:49:29.789478+00:00: original 30-row byte fingerprint and earlier completion plan. Its concurrency slice plan is historical; c2/c4 did not run. `final-analysis-baseline.json` records input fingerprints and the earlier 9 spot-check rows before this rewrite.
- `extractions/analysis_chunk_inventory.json`, recorded read date 2026-10-10: prior character census. Book snapshots in `source_dates.json` were modified 2026-09-28 and 2026-06-13. Book publication dates: not found in supplied artifacts.
- `extractions/exact_token_inventory.json`: stored direct token counts, using the Qwen3.8 tokenizer and tokenizers 0.22.1 on CPU with no special tokens; file/parent/character totals match the prior census. Its counts replace the partial report's character-derived book estimates. Inventory publication date: not found; read during this pass.
- `inputs/coursera-genai-transcripts.json`, modified 2026-10-09: course transcript with frozen cue locators. Course publication date and actual lecture URLs: not found.
- `extractions/litgraph_inventory.json`, `repo_inventory.json` and `code_inventory.json`: stored inventories from the previous pilot; reused without a fresh repository scan. `source_dates.json` supplies source modification dates. Full source of the 12 stored repos: not found.
- `extractions/spotcheck.json`, reviewed 2026-10-10: same-agent annotations. The code-05 quote correction retains the prior annotation. `completion_report.py` reproduces the arithmetic, validates invariants and writes `summary.json`, `projection.json` and this report without model or network calls. `completion-audit.json` independently checks arithmetic and preserved inputs.


- [arxiv:2502.14802](https://arxiv.org/abs/2502.14802): Published (stored metadata): 2025-02-20; Fetched (stored metadata): 2026-07-16 13:25:40.127998. Frozen cached text is the support-check authority.

- [arxiv:2606.04555](https://arxiv.org/abs/2606.04555): Published (stored metadata): 2026-06-03; Fetched (stored metadata): 2026-07-15 09:55:04.148707. Frozen cached text is the support-check authority.

- [arxiv:2606.09900](https://arxiv.org/abs/2606.09900): Published (stored metadata): 2026-06-05; Fetched (stored metadata): 2026-07-15 09:54:41.924313. Frozen cached text is the support-check authority.

- [arxiv:2606.10694](https://arxiv.org/abs/2606.10694): Published (stored metadata): 2026-06-09; Fetched (stored metadata): 2026-07-15 09:54:29.795916. Frozen cached text is the support-check authority.

- [arxiv:2606.25656](https://arxiv.org/abs/2606.25656): Published (stored metadata): 2026-06-24; Fetched (stored metadata): 2026-07-17 13:33:46.783832. Frozen cached text is the support-check authority.

- [arxiv:2606.28351](https://arxiv.org/abs/2606.28351): Published (stored metadata): 2026-06-03; Fetched (stored metadata): 2026-07-17 13:37:31.513238. Frozen cached text is the support-check authority.

Acceptance: `bash verify.sh` returned **VERDICT: PASS** for this rewritten report; see `extractions/completion-verify.log`. The final artifact audit also returned **PASS** with no issues; see `extractions/completion-audit.json`. These checks confirm report structure, arithmetic and preserved inputs; the extraction-integrity verdict remains **FAIL**. The limited same-agent status audit and source-quote checks are in `extractions/claim-audit.md` and `extractions/final-claim-quote-check.json`.
