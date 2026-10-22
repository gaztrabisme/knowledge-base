# R1 — EmbeddingGemma 2 facts and CPU timing

Owner: Huy. Run: kbu-2026-10-07. Research date: 2026-10-10. Verdict: PASS for the requested fact sheet and CPU measurements. A migration of the knowledge base (KB) remains unvalidated until retrieval quality and Mac query latency are checked. An embedding is an ordered list of numbers representing an input for similarity search. The question is whether the proposed model is compatible with the KB, and how its central processing unit (CPU) cost compares with the current Jina model. This report does not establish retrieval quality or the Mac's runtime performance.

## Fact sheet

Parameters are learned model values. Dimensions count the entries in an output vector. A task prompt here is a fixed text prefix that guides how an input is embedded. API means application programming interface; the Hugging Face API returns repository metadata.

| Property | Value | Source |
|---|---|---|
| Release | Launch: 2026-10-06; repository created 2026-09-14, updated 2026-10-06. | [Google launch](https://blog.google/innovation-and-ai/technology/developers-tools/embeddinggemma-2/), [metadata](https://huggingface.co/api/models/google/embeddinggemma-2) |
| parameters | Full model: 744,371,488 in Google's tutorial; API count: 744,371,512. Loaded text-only: 271,002,624; text + vision: 438,760,448. Google uses rounded labels 740M, 270M and 440M. | [API](https://huggingface.co/api/models/google/embeddinggemma-2), [Google count](https://ai.google.dev/gemma/docs/embeddinggemma/inference-embeddinggemma-with-sentence-transformers), [measured text](results/result_text_fp32.json), [measured image](results/result_image_fp32.json) |
| dimensions | Native output: 768 numbers. Masked mean pooling averages valid token outputs; normalization rescales the vector to length one. | [Configuration](https://huggingface.co/google/embeddinggemma-2/blob/main/config.json), [pooling](https://huggingface.co/google/embeddinggemma-2/blob/main/1_Pooling/config.json), [modules](https://huggingface.co/google/embeddinggemma-2/blob/main/modules.json) |
| Matryoshka | Trained to retain information in leading vector coordinates; recommended sizes: 768, 512, 256, 128. Keep leading coordinates, then normalize to unit length. Google also documents arbitrary sizes from 128 through 768, with those four recommended. | [Model card](https://huggingface.co/google/embeddinggemma-2), [truncation guide](https://ai.google.dev/gemma/docs/embeddinggemma/inference-embeddinggemma-with-sentence-transformers) |
| context length | Published shared input budget: 8,192 tokens, where a token is a text subword or encoded media unit. Config positional capacity is 262,144; that is not the documented supported input budget. | [Overview](https://ai.google.dev/gemma/docs/embeddinggemma), [configuration](https://huggingface.co/google/embeddinggemma-2/blob/main/config.json) |
| modalities | Text, including code; images; audio; video; and interleaved combinations. Modalities are the different kinds of input. | [Overview](https://ai.google.dev/gemma/docs/embeddinggemma) |
| Image call | `model.encode({"image": source})`, with a file path, URL, or Pillow image object. Media receives no text task prefix. | [Multimodal guide](https://ai.google.dev/gemma/docs/embeddinggemma/multimodal-embeddinggemma-with-sentence-transformers) |
| Query prompt | `SearchQuery`: `task: search result \| query: {query}`. `CodeRetrieval`: `task: code retrieval \| query: {query}`. | [Prompt configuration](https://huggingface.co/google/embeddinggemma-2/blob/main/config_sentence_transformers.json) |
| Document prompt | `Document`: `title: none \| text: {content}`. Use `title: {title} \| text: {content}` for real titles, formatted manually. | [Prompt configuration](https://huggingface.co/google/embeddinggemma-2/blob/main/config_sentence_transformers.json), [inference guide](https://ai.google.dev/gemma/docs/embeddinggemma/inference-embeddinggemma-with-sentence-transformers) |
| Libraries | Card requests updated sentence-transformers and transformers. Repository requires sentence-transformers >=6.1.0 for ordered multimodal inputs; saved config names transformers 5.18.0.dev0. A precise minimum stable transformers version is not found. | [Card](https://huggingface.co/google/embeddinggemma-2), [requirements](https://huggingface.co/google/embeddinggemma-2/blob/main/config_sentence_transformers.json), [config](https://huggingface.co/google/embeddinggemma-2/blob/main/config.json) |
| Precision | Use fp32 (32-bit floating point) or BF16 (16-bit bfloat floating point). Card warns against conventional 16-bit floating point (fp16). The measured int8 variant converts Linear layers to 8-bit integers; token-embedding weights remain fp32. | [Card](https://huggingface.co/google/embeddinggemma-2) |
| Quantized / ONNX | Community Open Neural Network Exchange (ONNX) conversion: q8 (8-bit) and q4 (4-bit). Google-linked LiteRT-LM variants quantize text to int4, with int8 vision in the image variant. Quantization-aware training (QAT) incorporates reduced precision during training. These exported variants were not timed. | [ONNX conversion](https://huggingface.co/onnx-community/embeddinggemma-2-ONNX), [LiteRT specification](https://huggingface.co/litert-community/embeddinggemma-2-text-270m-litert-lm) |
| license | Apache-2.0 in metadata and Google's documentation; repository is ungated. The card also references Google's prohibited-use policy. | [Metadata](https://huggingface.co/api/models/google/embeddinggemma-2), [license text](https://ai.google.dev/gemma/apache_2), [card](https://huggingface.co/google/embeddinggemma-2) |
| Linked research | Read the linked launch and developer blogs. A dedicated EmbeddingGemma 2 paper is not found in the card or those links; predecessor papers are not evidence for this checkpoint. | [Card](https://huggingface.co/google/embeddinggemma-2), [developer blog](https://developers.googleblog.com/en/embeddinggemma-2-the-developer-guide/) |

## CPU timing

All requested input/precision combinations produced finite vectors. Remote host: bppc at 192.168.1.17. CPU: AMD Ryzen 9 9950X 16-Core Processor, with 16 physical cores and 32 logical CPUs. `OMP_NUM_THREADS=16`, `MKL_NUM_THREADS=16` and `torch.set_num_threads(16)` were applied. PyTorch used 1 thread for scheduling across operations. All models were explicitly on CPU, with graphics processing unit (GPU) visibility disabled. Linux and package versions are saved in [platform.txt](logs/platform.txt) and [requirements.lock](logs/requirements.lock).

| Input / model | Precision | Median single call, ms | Text batch, passages/s |
|---|---|---:|---:|
| Target text query | fp32 | 34.921429 | 8.720811806025287 |
| Target text query | int8 (Linear only) | 15.1690745 | 11.927754653127142 |
| Target Python function | fp32 | 118.79585850000001 | not requested |
| Target Python function | int8 (Linear only) | 78.3223285 | not requested |
| Target diagram | fp32 | 1080.7977215 | not requested |
| Target diagram | int8, one Linear exempt | 697.885907 | not requested |
| Current Jina text query | fp32 | 92.1462285 | 3.415765464004716 |

The query is the original 12-word string; with the target prompt it uses 22 tokens. The original 30-line Python function uses 311 tokens with the document prompt. The earlier 1000 × 600 pixel diagram was reused; it is a synthetic flow chart, not a rendered PDF page. Image timing starts from an already decoded Pillow image, includes processor resizing and inference, and uses the default 280-token vision budget. It excludes disk reads and PDF rendering. That budget comes from the [processor configuration](https://huggingface.co/google/embeddinggemma-2/blob/main/processor_config.json).

Batch size is 32, using exactly 32 unique passages selected from the existing 64. All selected strings remain unchanged. Target passage lengths with the document prompt have minimum 230, median 249, maximum 281 and mean 252.15625 tokens. Jina receives identical strings; its lengths are minimum 214, median 236.5, maximum 273 and mean 238.78125 tokens. The two tokenizers divide text differently. The fixture identities and counts are preserved in [input_manifest.json](input_manifest.json).

Each single-call test discards 3 warm-ups and reports the median of 20 elapsed times measured with a monotonic nanosecond clock. Throughput is 32 divided by median batch seconds, after 3 warm-ups and 5 measured batches. Calls include tokenization or image processing, inference, normalization, and NumPy output conversion. fp32 is 32-bit floating point. Dynamic int8 quantization converts Linear layers, the learned matrix projections, to 8-bit integer weights; it leaves token-embedding lookup tables in fp32. Attention combines information from other token positions; the runs use PyTorch scaled dot-product attention (SDPA). Query and document prompts follow each model's card: target SearchQuery/Document; Jina query/document. This is a model comparison, not a replay of the KB's entire search request. [Jina usage](https://huggingface.co/jinaai/jina-embeddings-v5-text-small-retrieval).

Text int8 converts 218 Linear layers. Applying quantization to every image Linear layer failed on the first warm-up: the patch projection reads `self.input_proj.weight.dtype`, while a dynamic quantized Linear exposes `weight` as a function. The saved failure is [result_image_int8_all_linear_failed.json](results/result_image_int8_all_linear_failed.json). Keeping exactly `0.model.vision_tower.patch_embedder.input_proj` in fp32 resolves the mismatch: the final image variant quantizes 331 Linear layers and completes all 23 calls. No library source was patched. The image int8 label therefore describes a mixed-precision model, with that exception and fp32 embedding lookup weights stated explicitly.

Memory below is process resident set size (RSS): physical memory occupied by the worker, including Python, libraries and allocator caches. Each row used a fresh process. Ready RSS is measured after loading and any quantization. Inference peak is sampled every 10 ms, so a briefer spike may be missed. Lifetime peak is the operating system's high-water mark and includes loading and quantization. Text/code rows include the subsequent batch workload; they are not memory peaks of the query alone.

| Worker | Ready RSS, bytes | Inference peak RSS, bytes | Lifetime peak RSS, bytes |
|---|---:|---:|---:|
| Target text/code fp32 | 1,872,822,272 | 3,400,384,512 | 3,444,326,400 |
| Target text/code int8 | 1,543,004,160 | 3,117,510,656 | 3,151,134,720 |
| Target image fp32 | 2,546,765,824 | 2,732,675,072 | 3,098,959,872 |
| Target image int8 | 1,792,729,088 | 2,014,511,104 | 3,099,025,408 |
| Jina text fp32 | 2,976,788,480 | 5,486,620,672 | 5,494,755,328 |

Installed versions: torch 2.14.1+cpu, torchvision 0.29.1+cpu, transformers 5.19.0, sentence-transformers 6.1.0, NumPy 2.5.3, Pillow 12.3.0 and psutil 7.2.2. The short card install recipe initially omitted torchvision, which the installed image processor imports. The CPU wheel resolved that failure; the import is visible in the [versioned processor source](https://github.com/huggingface/transformers/blob/v5.19.0/src/transformers/models/gemma4/image_processing_gemma4.py). A subsequent Hub lookup stalled after weights loaded. Final runs load the downloaded, revision-pinned checkpoint offline. Those setup attempts supply no accepted latency result.

Reproduction: create an isolated remote Python environment (venv) with CPU-only PyTorch and torchvision, then install the other pinned dependencies; copy inputs and scripts into the remote R1 directory. Run `prepare_remote.py`, followed sequentially by `benchmark.py text_fp32`, `text_int8`, `image_fp32`, `image_int8`, and `jina_fp32`. Copy each result into results/ and run `assemble_results.py` locally. The Mac only assembled these small JSON files and did not load a model. Scripts, raw durations, errors and logs are retained. The graphics processing unit (GPU), containers, and services on ports 6333 and 8000 were not used.

## What this means for the KB

The same-model constraint is explicit in the KB's [Architecture](/Users/GaryT/Documents/Work/tools/knowledge-base/CLAUDE.md:31) and [RAG frontier note](/Users/GaryT/Documents/Work/tools/knowledge-base/wiki/rag-frontier-2026.md:135): indexing and query embedding must share a model and vector space. The note targets about 300 ms for query embedding on the Mac, whose Apple Silicon processor differs from bppc's x86 CPU. **Inference:** even a workstation result below that budget cannot establish Mac compliance because bppc's CPU and software differ. Full search also adds index retrieval and reranking, the reordering of candidate results; this experiment only times the embedding component.

Read-only inspection confirms the earlier integration finding. [knowledge_base/embedder.py](/Users/GaryT/Documents/Work/tools/knowledge-base/knowledge_base/embedder.py:28) has no EmbeddingGemma 2 registration. [model_dim() and model_idiom()](/Users/GaryT/Documents/Work/tools/knowledge-base/knowledge_base/embedder.py:45) default to 1024 and `jina-task`; the encoding branch sends `task="retrieval.query"` or `task="retrieval.passage"`. `config.py` obtains the dimension from this registry unless overridden, `index.py` uses it when creating a collection, and `search.py` routes queries through the shared encoder. Changing only the model environment variable would therefore use the wrong dimension and encoding convention.

A swap needs explicit model registration at 768 dimensions, an encode-query/document convention using the repository's query/document prompt aliases, consistent normalization and truncation, and selective encoder loading. The query process should disable unused image and audio encoders; image ingestion needs the vision encoder. The observed default SentenceTransformer maximum-length value is a tokenizer placeholder for no meaningful limit, rather than an enforced 8,192-token cap. Set that supported budget explicitly and keep the existing character truncation rule under review. Image ingestion also needs an input path accepting image dictionaries, figure identifiers and recoverable source-page metadata; the current shared encoder accepts strings. 

The standalone remote indexer imports the same adapter, so both locations must receive identical behavior. A new collection must be built at the chosen dimension and populated by re-embedding every document. Overriding the vector length alone cannot align Jina and Gemma coordinates. 

**Inference:** shorter vectors reduce vector storage and comparison cost, but do not eliminate the model's input-processing cost. For fp32 vector values alone, the current 1024 dimensions require 4,096 bytes per vector; 768, 512, 256 and 128 dimensions require 3,072, 2,048, 1,024 and 512 bytes respectively. These are arithmetic storage figures excluding index overhead. The card's reduced-dimension quality results belong to the publisher, not a KB retrieval evaluation. [Truncation evidence](https://huggingface.co/google/embeddinggemma-2).

The measured target query is below the 300 ms reference on bppc at both precisions, and faster than this measured Jina baseline. Image calls take longer than that query budget even for the simple diagram. **Inference:** this favors testing a text-only Mac query process with image embedding performed during indexing, using the same checkpoint and vector settings. It does not justify a migration yet. A quality gate must compare retrieval on the KB, including any shortened or quantized vectors; no such test was requested here. Mac inference was deliberately not run under the standing compute restriction. No repository was changed. The supplied `bash verify.sh` returned `VERDICT: PASS`. Additional checks verified fixture identity, sample counts, medians, thread settings, dimensions, unit-length vectors and throughput arithmetic. These checks validate the unit artifacts and measurements, not a decision to promote the model.

## Output sample

These lines are real output from [assemble_results.py](assemble_results.py), assembled from the saved measured worker results:

```text
target_fp32_query_ms: 34.921429
target_int8_query_ms: 15.1690745
target_fp32_code_ms: 118.79585850000001
target_int8_code_ms: 78.3223285
target_fp32_image_ms: 1080.7977215
target_int8_image_ms: 697.885907
jina_fp32_query_ms: 92.1462285
target_fp32_passages_per_second: 8.720811806025287
target_int8_passages_per_second: 11.927754653127142
jina_fp32_passages_per_second: 3.415765464004716
```

## Sources

All external sources were accessed on 2026-10-10. Source dates are distinguished from access dates.

- [Hugging Face metadata](https://huggingface.co/api/models/google/embeddinggemma-2): created 2026-09-14; updated 2026-10-06; revision `914f7f89142e33e77833254d9c9b90c3cef7303b`. Repository files cited above share this retrieved revision.
- [Google model card](https://huggingface.co/google/embeddinggemma-2): repository modification date 2026-10-06; card-specific publication timestamp not found.
- [Google launch blog](https://blog.google/innovation-and-ai/technology/developers-tools/embeddinggemma-2/): published 2026-10-06.
- [Google developer blog](https://developers.googleblog.com/en/embeddinggemma-2-the-developer-guide/): published 2026-10-06.
- [Google overview](https://ai.google.dev/gemma/docs/embeddinggemma): updated 2026-10-06.
- [Google inference guide](https://ai.google.dev/gemma/docs/embeddinggemma/inference-embeddinggemma-with-sentence-transformers): updated 2026-10-07.
- [Google multimodal guide](https://ai.google.dev/gemma/docs/embeddinggemma/multimodal-embeddinggemma-with-sentence-transformers): updated 2026-10-07.
- [Apache license text](https://ai.google.dev/gemma/apache_2): updated 2026-04-01.
- [ONNX conversion](https://huggingface.co/onnx-community/embeddinggemma-2-ONNX): repository created 2026-10-04, updated 2026-10-06, revision `daa72c51243991dfcaf9f9137d2c573d8f7790c0`; [metadata](https://huggingface.co/api/models/onnx-community/embeddinggemma-2-ONNX).
- [LiteRT specification](https://huggingface.co/litert-community/embeddinggemma-2-text-270m-litert-lm): repository created 2026-09-29, updated 2026-10-06; [metadata](https://huggingface.co/api/models/litert-community/embeddinggemma-2-text-270m-litert-lm).
- [Versioned processor source](https://github.com/huggingface/transformers/blob/v5.19.0/src/transformers/models/gemma4/image_processing_gemma4.py): tag v5.19.0; source publication date not found in the retrieved file.
- [Jina baseline card](https://huggingface.co/jinaai/jina-embeddings-v5-text-small-retrieval): repository updated 2026-04-15; revision `6856e76bb72982e58de0620458a4e8b3614da340`.
- Local KB: `CLAUDE.md`, `wiki/rag-frontier-2026.md`, `knowledge_base/embedder.py`, `config.py`, `index.py`, `search.py`, and `scripts/remote_index.py`, read 2026-10-10. The frontier note is dated 2026-05-30. Local fixture source is recorded in input_manifest.json; the source book's publication date was not checked and is not found in this run.
