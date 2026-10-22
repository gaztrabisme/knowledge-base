# M4 — graph extraction with LFM2.5-24B-A2B

Owner: Huy. Run: kbu-2026-10-07. Updated: 2026-10-15T12:59:32.107156+00:00.

**Collection: COMPLETE; 192/192 planned request records saved.** The 192 records are four runs of the same 48 units, not 192 distinct sources.

**Replacement verdict: FAIL.** Chosen configuration: q4-c1; returned 3/48 and strict-valid 3/48. Qwen M3 returned 40/48 and strict-valid 35/48. Strict-valid checks structure and exact evidence strings; it does not prove relation meaning or completeness.

## Setup

A knowledge graph stores named things as nodes and typed relationships as edges. This experiment asks a language model to extract those records with exact source quotes. JSON (JavaScript Object Notation) is the structured text format for these records. A token is a piece of text in a model vocabulary; a tokenizer divides text into those pieces. A quantized model stores weights with fewer bits. LFM2.5 has 24.0 billion total parameters and 2.45 billion active parameters per token, as reported by its [model card](https://huggingface.co/LiquidAI/LFM2.5-24B-A2B). These are vendor specifications, not measurements in this experiment. M3 refers to the previous Qwen3.8-27b pilot; q4 and q3 below name the supplied quantization files, and c1, c2 and c4 mean concurrency 1, 2 and 4.

The supplied files are `LFM2.5-24B-A2B-QAD-Q4_0.gguf` (13,578,190,880 bytes) and `LFM2.5-24B-A2B-UD-Q3_K_XL.gguf` (10,947,100,928 bytes). GGUF is the model-file format used by llama.cpp. Liquid describes QAD Q4_0 as quantization-aware distillation intended to recover accuracy after four-bit quantization; [Liquid quantization card](https://huggingface.co/LiquidAI/LFM2.5-24B-A2B-GGUF). Q3 is the supplied Unsloth dynamic three-bit candidate; [Unsloth card](https://huggingface.co/unsloth/LFM2.5-24B-A2B-GGUF).

The installed `~/.unsloth/llama.cpp/build/bin/llama-server` loaded both models. No build was needed. It reports build 10639, commit `2a36554fc`; installed metadata and the [published build manifest](https://github.com/unslothai/llama.cpp/releases/download/b10639-mix-f6f92fe/llama-prebuilt-manifest.json) identify full source commit `2a36554fc89e1fdbbd0de8cb382afbc1677b1b65`. This is the Unsloth CUDA build (CUDA is NVIDIA’s GPU computing system), release `b10639-mix-f6f92fe`, published 2026-08-27.

Graphics processing unit (GPU) memory was measured with `nvidia-smi` on the RTX 5080, which reports 16,303 MiB total. MiB means 1,048,576 bytes. A slot holds one active request; concurrency is the number of requests in flight. Each primary-test slot has 8,192 context tokens, including the prompt, reasoning and final answer. Four slots and 32,768 total context tokens are the largest requested configuration tested; a hardware maximum beyond those settings was not measured.

| Quant | Slots | Total context | Ready GPU memory | Sampled run peak MiB | Layer placement |
| --- | --- | --- | --- | --- | --- |
| q4 | 1 | 8,192 | 13616 MiB | 13,668 | 41/41 GPU; 0/41 CPU |
| q4 | 2 | 16,384 | 13776 MiB | 13,828 | 41/41 GPU; 0/41 CPU |
| q4 | 4 | 32,768 | 14096 MiB | 14,150 | 41/41 GPU; 0/41 CPU |
| q3 | 1 | 8,192 | 11108 MiB | 11,162 | 41/41 GPU; 0/41 CPU |
| q3 | 2 | 16,384 | 11268 MiB | not found | 41/41 GPU; 0/41 CPU |
| q3 | 4 | 32,768 | 11588 MiB | not found | 41/41 GPU; 0/41 CPU |

Every capacity log reports `offloaded 41/41 layers to GPU`; zero non-GPU layers is the subtraction 41 − 41. Automatic fitting was disabled, so the server could not silently reduce layer placement or context. Logs also report a CPU_Mapped model buffer of 205.08 MiB for Q4 and 265.62 MiB for Q3, plus host compute buffers. These CPU-memory allocations are disclosed separately from the layer-placement check; this experiment does not claim zero host memory use. Run peaks are sampled once per second and can miss shorter spikes. Raw evidence is in `capacity.json` and `logs/`.

Launch flags, with the appropriate model file and slot count substituted:

```sh
taskset -c 8-31 ~/.unsloth/llama.cpp/build/bin/llama-server \
  -m MODEL_FILE --alias lfm2.5-24b-a2b --host 127.0.0.1 --port 18084 \
  -ngl 999 --fit off -c TOTAL_CONTEXT -np SLOTS -fa on \
  --temp 0.1 --top-k 50 --repeat-penalty 1.05 -t 24 -tb 24 \
  --cache-ram 0 --no-context-shift --jinja --reasoning-format deepseek -lv 4
```

Temperature 0.1, top-k 50 and repetition penalty 1.05 follow the [Liquid model card](https://huggingface.co/LiquidAI/LFM2.5-24B-A2B-GGUF). Sampling controls and token limits are absent from requests: every request contains only `model` and `messages`. Server properties confirm these sampling defaults and unlimited generation (`n_predict = -1`), bounded by context. The `deepseek` format separates generated reasoning from final content; it does not disable or cap reasoning. The model card says this model always reasons before answering; [model card](https://huggingface.co/LiquidAI/LFM2.5-24B-A2B). Other sampling defaults were retained and are saved in the server-property files.

The server, benchmark client, telemetry and remote control scripts run under `taskset -c 8-31`; capacity snapshots confirm server affinity 8–31. No model or tokenizer was loaded on the Mac. The server binds only to 127.0.0.1:18084. No Strata, proxy, container or unrelated service was changed. A local watcher forwards a local `GPU_RECALL` marker; the remote guard checks the remote marker every 0.25 seconds. Requests check recall before submission. A deadline guard stops at 2026-10-16 09:30 ICT.

Cleanup evidence: M4 model server stopped; port 18084 has no listener; GPU memory 120 MiB, versus 120 MiB before the run; compute process list is empty. See `cleanup.json`.

## Results

A repository, shortened to repo, is a collection of version-controlled files. The unchanged M3 sample has 12 book units, 12 course-transcript units, 12 paper units and 12 complete code files. Source text, source token counts, prompt and validator are copied unchanged into `baseline/`. Inputs were not shortened. No retries, output repairs, name merging or graph insertion were performed. The two sequential runs test each quant; the chosen quant then runs all 48 inputs at concurrency 2 and 4. Selection was recorded before results in `EXPERIMENT.md`: most strict-valid sequential outputs, then returned count, then returned source throughput; select the fastest concurrency with no reduction in strict-valid count against its sequential run.

A returned extraction means final content parsed as JSON. Strict-valid means the unchanged M3 schema and exact-contiguous-quote validator passed, including valid empty arrays. A schema defines permitted fields and values. Invalid JSON, schema errors, quotation errors and transport errors remain failures. Semantic support separately asks whether the source establishes both endpoints, relation meaning, direction, negation and conditions.

Median is the middle request duration; the 95th percentile (p95) is sorted position ceil(0.95 × n), with ceil rounding up. Durations include failed attempts. For sequential runs the rate denominator is the sum of request seconds, matching M3. For concurrent runs it is the union of in-flight request intervals; deliberate pauses are excluded. Per-type concurrent rates include contention with other active types, and must not be added. Completion tokens/second includes generated reasoning. Token totals use reported usage only; missing usage is unknown, not evidence of zero consumption. Counts are exact integers; displayed times and rates are rounded to three decimal places, with full precision retained in JSON artifacts. Model tokenizers differ, so it is not a matched-work speed measure. Returned source tokens/hour counts the frozen M3 source tokens only for parseable extractions, divided by all request time. Attempted source tokens/hour also counts inputs whose extraction failed. The common source-token instrument is the stored Qwen tokenizer count; no retokenization was performed. Returned source-token throughput measures inputs for answered requests, not recovered knowledge: a valid empty graph can count source tokens while missing explicit relations.

| Type | Model/configuration | Attempts | Returned | Strict-valid | Median s | p95 s | Completion tokens/s | Returned source tokens/h | Attempted source tokens/h |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | qwen-c1 | 48 | 40 | 35 | 181.765 | 300.071 | 63.931 | 18,727.350 | 28,169.514 |
| all | q4-c1 | 48 | 3 | 3 | 19.624 | 23.417 | 322.733 | 15,250.941 | 289,348.958 |
| all | q3-c1 | 48 | 2 | 1 | 23.378 | 25.984 | 280.146 | 650.039 | 250,487.546 |
| all | q4-c2 | 48 | 2 | 2 | 30.460 | 34.572 | 427.749 | 5,555.913 | 383,751.101 |
| all | q4-c4 | 48 | 3 | 2 | 49.181 | 55.878 | 524.259 | 4,139.472 | 468,425.779 |
| book | qwen-c1 | 12 | 9 | 8 | 174.239 | 300.085 | 45.114 | 11,942.864 | 18,407.689 |
| book | q4-c1 | 12 | 0 | 0 | 20.411 | 24.233 | 316.946 | 0.000 | 173,187.593 |
| book | q3-c1 | 12 | 2 | 1 | 22.018 | 26.078 | 276.745 | 2,456.129 | 154,813.663 |
| book | q4-c2 | 12 | 1 | 1 | 30.461 | 36.950 | 422.896 | 2,609.577 | 231,498.446 |
| book | q4-c4 | 12 | 3 | 2 | 48.270 | 58.481 | 490.741 | 14,791.194 | 273,785.689 |
| course | qwen-c1 | 12 | 11 | 8 | 184.042 | 300.071 | 76.355 | 17,708.697 | 19,486.607 |
| course | q4-c1 | 12 | 0 | 0 | 19.863 | 23.417 | 330.873 | 0.000 | 178,949.635 |
| course | q3-c1 | 12 | 0 | 0 | 23.741 | 25.478 | 278.953 | 0.000 | 150,869.035 |
| course | q4-c2 | 12 | 0 | 0 | 30.090 | 32.368 | 431.747 | 0.000 | 233,506.497 |
| course | q4-c4 | 12 | 0 | 0 | 48.894 | 54.608 | 456.503 | 0.000 | 246,895.281 |
| paper | qwen-c1 | 12 | 11 | 11 | 176.486 | 300.043 | 78.316 | 11,707.912 | 13,438.588 |
| paper | q4-c1 | 12 | 1 | 1 | 21.409 | 23.410 | 323.663 | 7,848.189 | 111,907.276 |
| paper | q3-c1 | 12 | 0 | 0 | 23.825 | 25.312 | 289.334 | 0.000 | 100,004.061 |
| paper | q4-c2 | 12 | 0 | 0 | 32.319 | 34.643 | 419.780 | 0.000 | 145,090.511 |
| paper | q4-c4 | 12 | 0 | 0 | 52.252 | 54.033 | 470.832 | 0.000 | 162,735.970 |
| code | qwen-c1 | 12 | 9 | 8 | 208.543 | 300.117 | 58.806 | 31,001.076 | 55,379.317 |
| code | q4-c1 | 12 | 2 | 2 | 17.541 | 22.265 | 318.279 | 70,997.396 | 890,057.578 |
| code | q3-c1 | 12 | 0 | 0 | 20.771 | 26.294 | 273.606 | 0.000 | 729,534.989 |
| code | q4-c2 | 12 | 1 | 1 | 25.173 | 32.670 | 411.766 | 25,760.045 | 1,153,158.863 |
| code | q4-c4 | 12 | 0 | 0 | 45.950 | 51.952 | 478.272 | 0.000 | 1,275,251.707 |

| Run | Invalid JSON | Schema error | Quote error | Transport error | Length stop | Empty final content | Bad/checked quotes | Valid empty graphs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| qwen-c1 | 0 | 1 | 4 | 8 | 0 | 0 | 8/238 | 1 |
| q3-c1 | 44 | 0 | 1 | 2 | 44 | 44 | 1/3 | 0 |
| q4-c1 | 43 | 0 | 0 | 2 | 43 | 43 | 0/4 | 1 |
| q4-c2 | 44 | 0 | 0 | 2 | 44 | 44 | 0/4 | 0 |
| q4-c4 | 43 | 0 | 1 | 2 | 43 | 43 | 2/5 | 0 |

| Run | Usage missing | Cache reported | Positive cache | Cached prompt tokens |
| --- | --- | --- | --- | --- |
| qwen-c1 | 8 | 40 | 0 | 0 |
| q3-c1 | 2 | 46 | 43 | 10579 |
| q4-c1 | 2 | 46 | 43 | 10579 |
| q4-c2 | 2 | 46 | 39 | 11441 |
| q4-c4 | 2 | 46 | 29 | 11278 |

Cache reuse means reusing previously processed prompt text. Disabling the saved prompt cache does not eliminate live-slot prefix reuse; the table reports actual returned usage. M3 reported zero positive reuse on its 40 requests with usage; the other 8 are unknown. The comparison also changes the serving path: M3 used Strata through an intermediary network service called a proxy, while M4 calls llama.cpp directly. M3 server context and peak GPU memory are not found. Rates describe these complete configurations, not an isolated causal effect of model size. Configuration order was fixed, each configuration ran once, and random sampling was not seeded; output-length and quality differences cannot be attributed to concurrency alone. No GPU-time projection is a calendar promise.

| Run | HTTP 400 units | Saved server rejection |
| --- | --- | --- |
| q3-c1 | code-01, code-03 | {"error":{"code":400,"message":"request (9509 tokens) exceeds the available context size (8192 tokens), try increasing it","type":"exceed_context_size_error","n_prompt_tokens":9509,"n_ctx":8192}}; {"error":{"code":400,"message":"request (13658 tokens) exceeds the available context size (8192 tokens), try increasing it","type":"exceed_context_size_error","n_prompt_tokens":13658,"n_ctx":8192}} |
| q4-c1 | code-01, code-03 | {"error":{"code":400,"message":"request (9509 tokens) exceeds the available context size (8192 tokens), try increasing it","type":"exceed_context_size_error","n_prompt_tokens":9509,"n_ctx":8192}}; {"error":{"code":400,"message":"request (13658 tokens) exceeds the available context size (8192 tokens), try increasing it","type":"exceed_context_size_error","n_prompt_tokens":13658,"n_ctx":8192}} |
| q4-c2 | code-01, code-03 | {"error":{"code":400,"message":"request (9509 tokens) exceeds the available context size (8192 tokens), try increasing it","type":"exceed_context_size_error","n_prompt_tokens":9509,"n_ctx":8192}}; {"error":{"code":400,"message":"request (13658 tokens) exceeds the available context size (8192 tokens), try increasing it","type":"exceed_context_size_error","n_prompt_tokens":13658,"n_ctx":8192}} |
| q4-c4 | code-01, code-03 | {"error":{"code":400,"message":"request (9509 tokens) exceeds the available context size (8192 tokens), try increasing it","type":"exceed_context_size_error","n_prompt_tokens":9509,"n_ctx":8192}}; {"error":{"code":400,"message":"request (13658 tokens) exceeds the available context size (8192 tokens), try increasing it","type":"exceed_context_size_error","n_prompt_tokens":13658,"n_ctx":8192}} |

HTTP means the network response protocol. Status 400 identifies a rejected request. Where the response says exceed_context_size_error, the complete prompt is too long for the configured slot: the client did not truncate it and the server rejected it. A length stop instead means the accepted prompt plus generated text filled the context. These are different failures. Empty final content does not count as a valid empty graph; valid empty graphs require an actual parsed object with empty arrays.

Sequential quant selection: `q4`; saved scores (strict-valid, returned, returned source tokens/hour): `{"q4": [3, 3, 15250.940751436923], "q3": [1, 2, 650.0393875448345]}`.

Best measured eligible configuration: **q4-c1**. Eligibility preserves the chosen quant’s sequential strict-valid count; it does not by itself establish acceptable quality.

M3 inspected 17 available outputs: semantic support 83/97 relations, exact quotes 93/97, and support with exact quotes 80/97. Those annotations are an unblinded same-agent spot-check, not a complete human reference graph or a population-accuracy estimate. Recall—the fraction of required relations recovered—is not found. M4 follows the same source-only semantic method and prioritizes those same 17 unit identifiers. Semantic judgments are analyst inferences from the frozen text; they are unblinded and conditioned on available output.

M4 inspected 10 available outputs, with 2/16 semantically supported relations. No semantic fraction is assigned to missing output. The counts describe only inspected outputs and are not population precision.

| Spot-check pool | Reviewed outputs | Supported/extracted relations | Exact/extracted quotes | Scope |
| --- | --- | --- | --- | --- |
| Qwen M3 | 17 | 83/97 | 93/97 | historical 17-output pool |
| q3-c1 | 2 | 1/3 | 2/3 | available outputs only; 0/0 means accuracy not found |
| q4-c1 | 3 | 1/4 | 4/4 | available outputs only; 0/0 means accuracy not found |
| q4-c2 | 2 | 0/4 | 4/4 | available outputs only; 0/0 means accuracy not found |
| q4-c4 | 3 | 0/5 | 3/5 | available outputs only; 0/0 means accuracy not found |

| Available matched-unit pool | Units | Qwen supported/extracted | LFM supported/extracted |
| --- | --- | --- | --- |
| q3-c1 | book-03 | 0/0 | 0/1 |
| q4-c4 | book-03, book-06 | 3/5 | 0/3 |

These relation fractions use different available-output pools and are not a paired population-accuracy comparison. The 17 historical unit identifiers are tracked individually in spotcheck.json, including unavailable outputs; no relation score is imputed for a missing graph.

| Run | Unit | Supported/extracted | Exact/extracted | Notes |
| --- | --- | --- | --- | --- |
| q4-c1 | paper-04 | 1/2 | 2/2 | The Segment Tree dependency is explicit in the paragraph introducing SegTreeMem; the short we-use quote relies on that paragraph for source attribution. The second edge turns the generic phrase a transition matrix into a capitalized named Method, Transition Matrix, which the source does not establish. Both quotes are exact. This demonstrates a semantic/type error despite strict validity. |
| q4-c1 | code-06 | 0/2 | 2/2 | Both quoted call sites exist and the caller dependencies are explicit in source context, but all three defined Python functions are mislabeled Method rather than Function. The source does not establish them as named techniques or algorithms. Both typed edges are therefore unsupported under the unchanged type definitions. Quotes are exact; no code was executed. |
| q4-c1 | code-11 | 0/0 | 0/0 | Valid empty arrays contain no relations to grade, so semantic precision is not found. The source contains explicit local function dependencies; an empty graph misses them. No source code was executed. |
| q3-c1 | book-03 | 0/1 | 0/1 | The output turns a section heading into a named Method and invents a USES dependency on the figure-caption Claim. The source only states a discussion boundary and a caption; neither establishes that method or dependency. The evidence also collapses double spaces in the source and is not an exact substring. No additional explicit permitted relation was identified. |
| q3-c1 | book-09 | 1/2 | 2/2 | The self-supervision dependency is supported in the specific context of language models growing to their current scale; that qualification must stay with the evidence. The EXPLAINS edge assigns AI Engineering to the new subsection, but the new subsection explicitly promises an overview of language models and self-supervision. The AI-engineering sentence belongs to the preceding introduction and does not establish the stated Lesson edge. Both evidence strings are exact. Output naming also changes source capitalization and number. |
| q4-c2 | code-06 | 0/2 | 2/2 | Both quoted call sites exist and the caller dependencies are explicit in source context, but all three defined Python functions are mislabeled Method rather than Function. The source does not establish them as named techniques or algorithms. Both typed edges are therefore unsupported under the unchanged type definitions. Quotes are exact; no code was executed. |
| q4-c2 | book-09 | 0/2 | 2/2 | Both IMPROVES_ON edges misuse an enabling statement as a comparative improvement. Self-supervision enables language-model scale; the text does not compare it against Language Models as an alternative method. Likewise, breakthroughs enable an evolution; they are not stated to outperform that evolution. The predicate and direction are unsupported although both evidence strings are exact. |
| q4-c4 | book-03 | 0/1 | 1/1 | The sole relation turns a book-section heading into a Module, whose allowed meaning is a source file, module or class. The EXPLAINS meaning allows Book/Course/Lesson/Concept as the explaining source, not a code Module. The heading alone also does not establish a completed explanatory relation in this fragment. The quote is exact. Unused entities additionally broaden the source caption by dropping some, but no relation uses them. |
| q4-c4 | book-06 | 0/2 | 0/2 | The first edge treats a section heading as the name of a Book, which this source does not establish. The second uses IMPROVES_ON for a suitability statement: knowledge graphs being suited to RAG is not an improvement over RAG. Both evidence strings repair source line breaks or hyphenation and are not exact substrings. |
| q4-c4 | book-08 | 0/2 | 2/2 | Both edges turn historical origin into a different relation: emerged from does not establish a USES dependency, and originated as does not state an explicit prerequisite. Generic foundation/language-model families are also typed as Method despite the prompt excluding generic AI/LLM from that type. Both quotes are exact. No additional explicit permitted relation was identified. |

Additional diagnostic, kept outside all primary counts and projections: q4, one slot with 32,768 context tokens. It uses one short artificial format-control input and four unchanged frozen units. This is a selected diagnostic, not a full-library or 48-unit result. Same sampling, prompt, parser and validator; no request controls or retries. GPU memory at readiness: 2026/10/15 19:52:31.488, 14120 MiB, 16303 MiB.

| Diagnostic unit | Status | Prompt tokens | Completion tokens | Seconds | Stop reason |
| --- | --- | --- | --- | --- | --- |
| format-control | ok_empty | 662 | 451 | 1.439 | stop |
| book-01 | quote_error | 2318 | 9169 | 27.248 | stop |
| paper-01 | ok | 947 | 12885 | 38.323 | stop |
| code-01 | schema_error | 9509 | 6450 | 20.881 | stop |
| code-03 | ok | 13658 | 13329 | 45.091 | stop |

| Diagnostic unit | Supported/extracted | Exact/extracted | Notes |
| --- | --- | --- | --- |
| book-01 | 3/6 | 4/6 | The LLM component, graph-augmented RAG component, and motivation by LLM limitations have source support, with the graph dependency limited to the source's graph-augmented setting. IMPROVES_ON incorrectly targets accuracy rather than a compared approach; optional graph integration is not a prerequisite; healthcare is a domain typed Concept, not the addressed Problem required by APPLIED_TO. Two quotes repair source hyphenation or line breaks. |
| paper-01 | 2/5 | 5/5 | PageRank use is explicit. Knowledge-graph use is supported only for the recent structured RAG approaches described in the source, not every RAG implementation. Three IMPROVES_ON edges target tasks rather than the compared method or baseline; the source's improvement does not mean the system outperforms a task. All five quotes are exact. |
| code-01 | 0/1 | 1/1 | The relation types model_dim as Method while the entity types it Function, causing an unresolved endpoint. The import does not establish that model_dim USES its parent embedder module in this direction. The import quote is exact; source was read, not executed. |
| code-03 | 0/10 | 10/10 | Every relation endpoint is an explicitly defined Python function in the frozen file, but all are labeled Method rather than Function. The ten typed edges therefore fail semantic support despite exact call-site quotes. Definitions were checked by source text and Python abstract-syntax-tree parsing; no source code was executed. |

Separate diagnostic semantic review: 5/22 supported relations; 20/22 exact quotes; 3/22 supported relations with exact quotes. The artificial control returned a valid empty object and is excluded from these relation counts. This supports context exhaustion as one failure mechanism (inference), while showing remaining type, predicate and quotation errors. Raw evidence and annotations are in diagnostic/.

## Projection

**Every number in this section is an inference input or inference output, not a measured current library run.** The measured rate is the selected configuration’s returned source tokens/hour for the corresponding source type. Inferred hours = M3 population source tokens ÷ measured returned source tokens/hour. The unit-based alternative uses returned units/hour. A zero returned-output rate cannot support a finite completion-time projection; its hours are written as not found. Invalid returned graphs still count in returned throughput, matching M3, so finite estimates do not purchase a verified graph. Strict-output hours use only schema-and-quote-valid output throughput; semantic correctness and coverage remain unproven.

| Population (all values are inferences) | Source tokens (inference) | Qwen hours (inference) | q4-c1 returned-output h (inference) | LFM strict-output h (inference) | Qwen unit-based h (inference) | LFM unit-based h (inference) | Speedup (inference) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| registered_book | 64,844,679.000 | 5,429.575 | not found | not found | 5,232.830 | not found | not found |
| reference_documentation | 9,545,958.000 | 799.302 | not found | not found | 899.560 | not found | not found |
| philosophy | 7,194,460.000 | 602.407 | not found | not found | 679.441 | not found | not found |
| paper records | 12,379,394.808 | 1,057.353 | 1,577.357 | 1,577.357 | not found | not found | 0.670 |
| one supplied course | 11,903.000 | 0.672 | not found | not found | 0.666 | not found | not found |
| stored repo README records; code proxy | 59,051.000 | 1.905 | 0.832 | 0.832 | not found | not found | 2.290 |
| two accessible Python source trees | 112,811.000 | 3.639 | 1.589 | 1.589 | 3.323 | 0.930 | 2.290 |
| 12-repo Python-code scenario; 20 files per repo | 676,866.000 | 21.834 | 9.534 | 9.534 | 19.939 | 5.583 | 2.290 |

M3’s stored census covers 320 registered books (64,844,679 source tokens), 8 reference-documentation corpora (9,545,958), 359 philosophy language/edition files (7,194,460), 1,246 paper records (12,379,394.808 estimated source tokens), and 40 Python source files across two accessible source trees (112,811 tokens). These population counts were read from saved M3 inventories; no fresh census was run. Reference documentation and philosophy use the unmeasured book-format proxy. Paper tokens retain M3’s character-to-token estimate. Applying code throughput to 12 introductory repository documents (59,051 tokens) is an unmeasured format proxy; the 12-repository code scenario (676,866 tokens) multiplies the two-tree inventory by 6. These assumptions are inferences. Full source for all 12 repositories and the complete course-library inventory are not found. Retries, repairs, merging names that refer to the same thing, numeric text representations, graph insertion, human review and future updates are excluded.

## Recommendation

**Recommendation (inference): do not replace Qwen with this LFM configuration for graph extraction.** It produced 3/48 strict-valid outputs versus Qwen’s 35/48. Faster token generation does not compensate for missing or invalid graphs. This conclusion applies to the measured 8,192-token context, unchanged M3 prompt and recorded server settings; it does not establish that every larger-context or differently configured LFM run would fail. Missing relations must not be treated as evidence that knowledge is absent from the library. Qwen also failed M3’s extraction-integrity gate; retaining Qwen as the comparison does not make its unvalidated outputs safe to insert directly.

The selected run had 43/48 length stops with empty final content, 2 oversized-prompt rejections, and 3 parseable outputs, including 1 empty graph. Its reviewed relations have semantic support 1/4 and exact quotes 4/4; Qwen’s historical inspected pool is 83/97 supported and 93/97 exact. The pools differ, so this is a descriptive comparison, not a population-accuracy test. Both selected-run nonempty graphs contain type or predicate errors, and the empty code graph omits explicit dependencies.

The longer-context diagnostic does not change selection or the projection: 2/4 selected corpus units passed schema and quote checks, but only 5/22 reviewed relations were supported. More context is a necessary candidate change for a further trial, not evidence that LFM is good enough. Any new full comparison should be separately versioned and retain source-only type, predicate and exact-quote requirements.

## Output sample

Real saved command output from this run (see `logs/experiment.log` and `logs/analysis-progress.txt`):

```text
q4-c1 book-01 invalid_json seconds=19.204 prompt=2318 completion=5874 quotes_bad=None finish=length
q4-c1 book-02 invalid_json seconds=18.829 prompt=2424 completion=5768 quotes_bad=None finish=length
q4-c1 book-03 invalid_json seconds=24.161 prompt=702 completion=7490 quotes_bad=None finish=length
q4-c4 code-12 invalid_json seconds=15.299 prompt=5914 completion=2278 quotes_bad=None finish=length
q4-c4 code-10 invalid_json seconds=51.952 prompt=1196 completion=6996 quotes_bad=None finish=length
q4-c4 code-11 invalid_json seconds=37.303 prompt=2986 completion=5206 quotes_bad=None finish=length
```

## Sources

All external sources were read on 2026-10-15. Repository creation and last-modified timestamps below come from the host API; they are not asserted as model publication dates. Snapshots and retrieval records are in `sources/`.

- [Liquid model card](https://huggingface.co/LiquidAI/LFM2.5-24B-A2B): model architecture, active/total parameters, sampling and reasoning behavior. Repository created 2026-10-12T05:35:46Z; last modified 2026-10-13T16:59:33Z. Publication date not found. Saved revision `1769516ac588c4c558089c94f27d96b0dc67b183`.

- [Liquid GGUF card](https://huggingface.co/LiquidAI/LFM2.5-24B-A2B-GGUF): QAD Q4_0 and sampling. Repository created 2026-10-09T18:03:23Z; last modified 2026-10-13T21:33:53Z. Publication date not found. Saved revision `0912d33141f77e10705345a6732bfd83f0252fdc`.

- [Unsloth GGUF card](https://huggingface.co/unsloth/LFM2.5-24B-A2B-GGUF): Q3 candidate. Repository created 2026-10-13T14:19:48Z; last modified 2026-10-13T21:55:20Z. Publication date not found. Saved revision `faa77113e93335b63423e9e8d33395f86eaf8946`.

- [llama.cpp build release](https://github.com/unslothai/llama.cpp/releases/tag/b10639-mix-f6f92fe) and [source manifest](https://github.com/unslothai/llama.cpp/releases/download/b10639-mix-f6f92fe/llama-prebuilt-manifest.json): published 2026-08-27T04:40:42Z; source commit `2a36554fc89e1fdbbd0de8cb382afbc1677b1b65`. The installed `UNSLOTH_PREBUILT_INFO.json` agrees. Commit-specific web page/date not found; no replacement commit is inferred. `logs/server-help.txt` records the actual binary’s flag definitions.

- M3 `REPORT.md` (2026-10-10), `extract.py`, `extractions/sample.json`, `units.jsonl`, `summary.json`, `spotcheck.json`, `projection.json`, `profile.json` and `source_dates.json`: frozen comparison and population inventories, copied to `baseline/`. The frozen sample—not live source pages—is the evidence authority for relation review. Input publication dates are retained from M3 where present; not independently reverified.

- M4 `capacity.json`, `results/*/units.jsonl`, raw response files, `run.json`, `gpu.csv`, `logs/`, `summary.json` and `audit.json`: measurements dated individually. `EXPERIMENT.md` records the comparison rule before measurement. `benchmark.py` preserves the prompt and validator; `analyze.py` checks source hashes, request fields, exact validation and arithmetic. This report is generated by `make_report.py`.

Artifact verification: **PASS**; 148 checks passed. See `verification.json` and `logs/verification.log`. These checks cover artifact integrity and shutdown, not independent semantic truth; the replacement verdict remains FAIL.
