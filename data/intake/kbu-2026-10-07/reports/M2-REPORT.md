# M2 — PDF image and code retrieval pilot

Owner: Huy. Run: kbu-2026-10-07. Date: 2026-10-10. **Verdict: PASS for completing the pilot; additional page-hit gain not observed.** These measurements cover this pilot; a knowledge-base migration remains unvalidated. The paired image runs retrieved 24 of 24 answer pages with text-only and 23 of 24 with multimodal search. Adding figures produced 0 new page hits and 1 lost page hit. Multimodal search returned the exact figure for 8 of the 9 queries whose specific visual detail is absent from surrounding text, all eight at rank 1. Text-only had already located all nine source pages, so 0 text-only page misses became exact figure hits. The generic and code-specific Gemma query prompts found 12 and 12 of 12 answer files; Jina found 12.

## Pilot set

The books are Portable Document Format (PDF) files. An embedding is a vector, an ordered list of numbers, that represents an input for similarity search. Text-only means indexing book passages. Multimodal means adding image vectors to those same passage vectors and ranking them together. A token is a text fragment identified by the model's tokenizer, the software that divides input text. JavaScript Object Notation (JSON) is the structured text format used for saved measurements; a JSON-lines file stores one record per line.

The four books were selected for technical diagrams, not sampled randomly. Page numbers below and in queries.jsonl are one-based physical PDF pages, including front matter, rather than printed page labels. The pool contains 280 caption-linked figures, exactly 70 per book. It includes 212 extracted raster images, pictures stored as pixels, 49 rendered vector regions, and 19 combined regions. Vector drawings store shapes and strokes; rendering turns them into pixels. All figure identifiers, captions, page text, crop coordinates and component identifiers are saved in [figures.jsonl](artifacts/figures.jsonl); the Portable Network Graphics (PNG) images are in [figures/](figures/).

| Book | PDF pages | Raw regions | Retained consolidated regions | Caption-linked regions | Pilot figures | Pilot raster / rendered |
|---|---:|---:|---:|---:|---:|---:|
| Understanding Deep Learning (udl) | 541 | 670 | 363 | 232 | 70 | 2 / 68 |
| Designing Data-Intensive Applications (ddia) | 613 | 102 | 102 | 89 | 70 | 70 / 0 |
| Fundamentals of Data Engineering (fde) | 544 | 99 | 93 | 92 | 70 | 70 / 0 |
| Clean Architecture (ca) | 444 | 169 | 168 | 83 | 70 | 70 / 0 |

PyMuPDF 1.28.2 ran on bppc. The extractor recovered embedded raster objects, reconstructed transparency masks, and rendered a region if direct extraction failed. For practical vector recovery it found caption blocks beginning with a numbered Figure label, collected nearby drawing bounds above each caption, and rendered their union at twice the PDF coordinate resolution. Raster fragments associated with one caption on one page were combined into a rendered region. Small and severely elongated regions were excluded. The pool selected 70 evenly spaced eligible caption-linked regions per book without using retrieval scores. This implements the documented image-object extraction and clipped rendering APIs. [PyMuPDF image recipes](https://pymupdf.readthedocs.io/en/latest/recipes-images.html).

There were 1,040 raw candidate regions; consolidation and size filtering left 726 regions, including 496 caption-linked regions. These are heuristic detection counts, not a manual census of semantic figures. Multiple panels can become one region; uncaptioned vector drawings can be missed; a caption block can stop before the complete caption. Complete extracted page text is retained independently. Forty-eight selected figures were inspected in contact sheets before labels were written; all 24 labelled figures came from those sheets. No figure was selected or relabelled after seeing its rank. The algorithm and intermediate counts are in [extract_pdfs.py](scripts/extract_pdfs.py), [prepare_pool.py](scripts/prepare_pool.py), and [extraction.json](artifacts/extraction.json).

The text index includes all 2,142 pages of the same four PDFs, producing 5,337 passages. Passage boundaries use the pinned Gemma tokenizer with a 250-token target, without cross-page merging or overlap. Retokenized lengths are minimum 1, median 249, maximum 252, and mean 200.631440884; short final passages are retained so no answer page is dropped. Figure labels extractable from a PDF's text layer remain in the text pool. No optical character recognition, software for reading characters from pixels, was applied to raster figures.

The code pool contains exactly 40 Python source files copied read-only from knowledge_base/ and litgraph/src/. Three empty initializer files have no indexable content; the remaining 37 files yield 518 passages under the same chunking procedure. File paths are relevance metadata, not extra text added to embeddings. Original file names, sizes and cryptographic hashes, fingerprints used to detect changes, are saved in [manifest.json](inputs/manifest.json). The source copies were read for labels but never executed or edited in their original repositories.

The agent wrote **24 image queries after seeing the figures**, and 12 code queries after reading the answering functions. This biases the image test toward visible, describable features and known answers; it does not estimate the frequency or difficulty of actual user queries. A second person did not independently annotate relevance. An in_text=true label means the specific queried fact is explicitly recoverable from extracted text on the answer page or the immediately adjacent pages, including captions and diagram labels. An in_text=false label requires visual content or arrangement absent from that text. There are 15 true and 9 false labels. For example, the sliding-window durations and graph-axis orientation are true because the previous page states them. The pictured gateway count and generated-car color order are false. Each label has a visual answer and explanation in [queries.jsonl](queries.jsonl); its three-page context is in [label_contexts.jsonl](artifacts/label_contexts.jsonl). Labels and corpus fingerprints were frozen before any retrieval rankings.

## Results

Recall@10 is the fraction of queries with a relevant result in the first ten candidates. Mean reciprocal rank (MRR) averages one divided by the first relevant rank over the full index. MRR@10 additionally sets ranks beyond ten to zero. Scores below are rounded to six decimal places; exact hit counts and unrounded metrics are saved in [results.json](artifacts/results.json).

| Run and split | Queries | Recall@10 | MRR | MRR@10 |
|---|---:|---:|---:|---:|
| image text-only; overall | 24 | 24/24 = 1.000000 | 0.683102 | 0.683102 |
| image text-only; in_text=true | 15 | 15/15 = 1.000000 | 0.716667 | 0.716667 |
| image text-only; in_text=false | 9 | 9/9 = 1.000000 | 0.627160 | 0.627160 |
| image multimodal; overall | 24 | 23/24 = 0.958333 | 0.819177 | 0.815972 |
| image multimodal; in_text=true | 15 | 15/15 = 1.000000 | 0.772222 | 0.772222 |
| image multimodal; in_text=false | 9 | 8/9 = 0.888889 | 0.897436 | 0.888889 |
| code Gemma SearchQuery + Document; overall | 12 | 12/12 = 1.000000 | 1.000000 | 1.000000 |
| code Gemma CodeRetrieval + Document; overall | 12 | 12/12 = 1.000000 | 1.000000 | 1.000000 |
| code Jina query + document; overall | 12 | 12/12 = 1.000000 | 1.000000 | 1.000000 |

Exact figure retrieval is a separate diagnostic. It counts only the labelled image, ignoring passages on its page; its mean reciprocal rank uses the exact figure's full-index rank. These figures were computed from the same saved rankings, without changing the primary metric.

| Multimodal exact-figure diagnostic | Queries | Recall@10 | Exact-figure MRR | Exact figures at rank 1 |
|---|---:|---:|---:|---:|
| overall | 24 | 20/24 = 0.833333 | 0.588139 | 11 |
| in_text=true | 15 | 12/15 = 0.800000 | 0.404658 | 3 |
| in_text=false | 9 | 8/9 = 0.888889 | 0.893939 | 8 |

For image queries, a text result is relevant only if it is on the labelled book and page. A figure is relevant only if its identifier is the exact labelled figure; another figure on the answer page does not count. For code, a passage is relevant if its file is the labelled file. All passages count toward rank; there is no page or file deduplication, no lexical search, and no second-stage reranking that reorders candidates. This is an exact cosine comparison, the dot product of normalized unit-length vectors. The text-only index has 5,337 items and the multimodal index has 5,617. Each code run has the same 518 passage strings. Saved [rankings.jsonl](artifacts/rankings.jsonl) includes each query's first relevant rank, exact figure rank, first relevant item, and all ten returned candidates with scores.

All embedding computation ran sequentially on bppc's central processing unit (CPU) with 16 numerical threads and one inter-operation scheduling thread, using R1's environment read-only. A graphics processing unit (GPU) accelerates computation, but no GPU, container, or existing service on ports 6333 or 8000 was used. The Mac only copied files, inspected images, and assembled small JSON reports. Gemma used 768 coordinates and 32-bit floating-point weights; Jina used 1,024 coordinates with the same weight precision. Both checkpoints, saved model weights, were loaded offline from R1's pinned cache: Gemma `914f7f89142e33e77833254d9c9b90c3cef7303b`; Jina `6856e76bb72982e58de0620458a4e8b3614da340`. Text workers disabled vision and audio; image workers disabled audio. Every stored vector was checked for finite entries and unit length.

Gemma indexed book and code passages with Document (`title: none | text: `) and used SearchQuery (`task: search result | query: `) for image queries. The code comparison holds Document passages fixed and changes the query prefix from SearchQuery to CodeRetrieval (`task: code retrieval | query: `). Images used `model.encode({"image": decoded_RGB_Pillow_image})` with no attached caption, page text, or query. These prompts come from the [Gemma prompt configuration](https://huggingface.co/google/embeddinggemma-2/blob/main/config_sentence_transformers.json), and the image call follows [Google's multimodal guide](https://ai.google.dev/gemma/docs/embeddinggemma/multimodal-embeddinggemma-with-sentence-transformers). Jina used its documented query and document prompts on the identical code strings. [Jina usage](https://huggingface.co/jinaai/jina-embeddings-v5-text-small-retrieval). This compares the named Jina model, not the knowledge base's complete current search pipeline.

The pinned processor configuration sets a maximum of 280 image processing tokens, internal image units used by the model. No override was passed. The copied configuration is in [processor_config.json](sources/processor_config.json), matching the [published processor configuration](https://huggingface.co/google/embeddinggemma-2/blob/main/processor_config.json).

## What this means

**Paired visual result:** 0 queries changed from a text-only miss to a multimodal hit, and 1 query changed from a hit to a miss. The gain identifiers are none; losses are I08. Among false labels, 0 gains came from retrieving the actual answer figure: none. The evaluation plan declared that incremental visual value would be observed only if at least one false-label text-only miss became an exact figure hit in the top ten. That gate is not met. It is a pilot gate, not a production acceptance threshold.

The text-only page metric is saturated at 24/24, leaving no room for new page hits in this query set. Consequently the declared gate cannot establish added page recall here. It does not establish that images have no value. Multimodal search directly returns 20 of 24 exact figures, including 8 of 9 false-label figures; all eight false-label hits are at rank 1. Successful text-only page retrieval did not require the absent visual fact to be present in its passage.

The table below includes every false-label query and any gain or loss. It distinguishes recovering a page from recovering its visual answer. The primary metric follows the task's exact answer-page rule. Since the text-presence label also checks adjacent pages, text-only can retrieve an explicit explanation on the previous page and still miss the primary page metric. Surrounding-page ranks are therefore saved separately in results.json; such a hit is a location diagnostic, not proof that any arbitrary passage on those pages contains the queried fact.

| Query | in_text | Exact answer | Text-only first rank | Multimodal first rank | Exact figure rank | Hit change |
|---|---|---|---:|---:|---:|---|
| I01 | false | udl-p0024-f02 (PDF page 24) | 2 | 1 | 1 | same hit status |
| I06 | false | udl-p0302-f10 (PDF page 302) | 1 | 1 | 1 | same hit status |
| I08 | false | ddia-p0114-f01 (PDF page 114) | 9 | 13 | 22 | loss |
| I09 | false | ddia-p0142-f01 (PDF page 142) | 1 | 1 | 1 | same hit status |
| I14 | false | fde-p0159-f01 (PDF page 159) | 1 | 1 | 1 | same hit status |
| I18 | false | fde-p0439-f01 (PDF page 439) | 1 | 1 | 1 | same hit status |
| I19 | false | ca-p0033-f01 (PDF page 33) | 2 | 1 | 1 | same hit status |
| I20 | false | ca-p0073-f01 (PDF page 73) | 3 | 1 | 1 | same hit status |
| I24 | false | ca-p0221-f01 (PDF page 221) | 5 | 1 | 1 | same hit status |

The one regression is I08, the three-source warehouse diagram. Four unrelated Fundamentals of Data Engineering figure vectors entered ahead of its answer-page passage, pushing that unchanged passage from rank 9 to rank 13. The exact target figure ranked 22. The saved scores show the answer passage has the same cosine score, 0.7041895985603333, in both runs; candidate competition caused the loss.

Eight false-label queries returned their exact figure at rank 1: I01, I06, I09, I14, I18, I19, I20, and I24. For example, I01 directly retrieves the doughnut-to-coral and painting-to-dog interpolation image; its text-only answer-page passage is rank 2. I24 directly retrieves the game-rules diagram's left/right arrangement; its text-only answer-page passage is rank 5. Overall first-relevant MRR rises from 0.683102 to 0.819177; for false labels it rises from 0.627160 to 0.897436. This is better ordering and direct image access, with no additional page-recall coverage.

**Inference:** A page hit can still return a passage that never states the queried color, count, or spatial relation. Thus even a high text-only recall@10 cannot establish that text-only search answers visual questions. The exact-figure evidence is the stronger indication of added visual access. Conversely, adding figure vectors can consume top-ten slots and push a relevant passage down; losses must be retained. This run evaluates retrieval access, not whether a language model can correctly read or reason over the returned image. Small figure labels and dense diagrams may be harder at the default image-processing budget, which was not increased or tuned in this pilot. There is no independent test set, no statistical claim of a population-wide advantage, and no Mac model timing.

**Code result:** All three conditions returned a passage from the correct file at rank 1 for every query: SearchQuery + Document, CodeRetrieval + Document, and Jina query + document each score 12/12 and MRR 1.000000. CodeRetrieval adds no answer-file hits or rank improvement in this set. This comparison also has no headroom at the observed ceiling. Chunk boundaries use the Gemma tokenizer for all models; no separate Jina-specific chunker was tuned. The labelled functions describe their behavior in comments and names, so these are source-file location questions rather than tests of code execution or deep program reasoning. Twelve queries are insufficient for a migration claim; this easy query set does not separate the three conditions.

**Embedding cost:** R1 measured a median single image call of 1080.797721500 milliseconds on bppc, excluding image decoding and PDF rendering. In M2, 280 measured image calls after one discarded warm-up have median 1641.866948 milliseconds and mean 2172.089788 milliseconds. They use the same CPU, precision and default processor settings but different images and contemporaneous workstation load. The full image loop, including image decoding, took 610.090488 seconds. Raw call durations are in [run_target-image.json](artifacts/run_target-image.json); R1's reference is [timing.json](../R1/timing.json). A cross-unit timing difference is not a controlled isolated model regression.

There are exactly 182 PDF files in the permitted local library inventory, recorded in [library_pdfs.txt](inputs/library_pdfs.txt). **Inference with assumptions:** treat each PDF as one book, give every PDF the four-book mean number of detected regions, and embed every region once in a serial CPU loop. This yields 22,568 caption-linked regions (496 / 4 × 182), or 33,033 regions if all retained regions are included (726 / 4 × 182). Neither is a measured full-library figure count. These four books were chosen for figures, so the mean may overestimate a general library; detection errors and uncaptioned drawings can shift it in either direction.

| Extrapolation | Estimated figure regions | R1 median-based seconds | R1 median-based hours | M2 mean-based seconds | M2 mean-based hours |
|---|---:|---:|---:|---:|---:|
| Caption-linked regions | 22568 | 24391.442979 | 6.775401 | 49019.722337 | 13.616590 |
| All retained regions (sensitivity) | 33033 | 35701.991134 | 9.917220 | 71750.641969 | 19.930734 |

The R1 column is the requested reference-speed estimate; multiplying a median by a count assumes every figure costs that median. The M2 mean column is a sensitivity estimate for total serial work. Both exclude PDF extraction, rendering, storage, retries, and the separate text embedding workload. They cover PDF images only: audio and video are not embedded. The full-library figure count, total end-to-end ingestion duration, and actual user-query benefit remain **not found** in this pilot. **Decision for Huy:** This pilot supports direct retrieval of visual content and better first-relevant ranks, but it supplies no new page-hit coverage and no code-prompt advantage. Full-library deployment remains unvalidated. **Inference:** if the application renders figures after locating their PDF page with text-only search, it may provide the same visual answer without embedding every figure; that alternative was not measured. A next evaluation should use independently written user questions with misses against a larger text pool, compare rendered-page access with figure-vector retrieval, and score whether the returned material actually supports the requested answer. The four-book pool and queries written after inspection are easier than an independently sampled full-library task. Review figure extraction and ensure that figure hits return the image and source page.

Validation: the separate artifact checker confirmed 84 ranking rows, recomputed all nine primary metric rows from the saved first-relevant ranks, verified the frozen label and corpus fingerprints, checked CPU/thread/dimension settings for all four workers, and confirmed that the 40 copied source files and their original source files still match their initial hashes. The supplied `bash verify.sh` returned `VERDICT: PASS`. These checks validate artifacts and metric arithmetic, not production retrieval quality.

Reproduction: transfer the four manifest PDFs and copied sources into the M2 remote workspace; install PyMuPDF under M2/vendor without changing R1's environment; run extract_pdfs.py then prepare_pool.py. Write and freeze the queries before ranking. Run embed_cpu.py sequentially with target-text, target-image, target-queries, and jina, then score_rankings.py. Copy the artifacts back and run assemble_report.py locally. Run configurations, checkpoint revisions, corpus fingerprints, scripts and raw rankings are retained. No source repository was modified.

## Output sample

Real output produced by assemble_report.py from the measured rankings and image calls, also saved in [output_sample.txt](artifacts/output_sample.txt):

```text
image text-only [overall]: queries=24 hits@10=24 recall@10=1.000000000 MRR=0.683101852
image multimodal [overall]: queries=24 hits@10=23 recall@10=0.958333333 MRR=0.819177350
image text-only [in_text=false]: queries=9 hits@10=9 recall@10=1.000000000 MRR=0.627160494
image multimodal [in_text=false]: queries=9 hits@10=8 recall@10=0.888888889 MRR=0.897435897
code Gemma SearchQuery + Document [overall]: queries=12 hits@10=12 recall@10=1.000000000 MRR=1.000000000
code Gemma CodeRetrieval + Document [overall]: queries=12 hits@10=12 recall@10=1.000000000 MRR=1.000000000
code Jina query + document [overall]: queries=12 hits@10=12 recall@10=1.000000000 MRR=1.000000000
paired_gains=[]
paired_losses=['I08']
false_exact_figure_gains=[]
figure_calls=280 image_median_ms=1641.866948 image_mean_ms=2172.089788
exact_figure_access [overall]: queries=24 hits@10=20 rank1=11 MRR=0.588138819
exact_figure_access [in_text=true]: queries=15 hits@10=12 rank1=3 MRR=0.404658474
exact_figure_access [in_text=false]: queries=9 hits@10=8 rank1=8 MRR=0.893939394
```

## Sources

All sources were read or accessed on 2026-10-10. Dates below identify the document or repository date rather than implying that access date is publication date.

- [Understanding Deep Learning source PDF](/Users/GaryT/Documents/Work/tools/knowledge-base/knowledge-base/advanced-ml/understanding-deep-learning.pdf): front page dated 2026-02-08; it identifies the final public release as 2023-12. PDF creation metadata is 2026-02-08. This local draft is the corpus actually measured.
- [Designing Data-Intensive Applications source PDF](/Users/GaryT/Documents/Work/tools/knowledge-base/knowledge-base/distributed-systems/designing-data-intensive-applications.pdf): first release 2017-03-01 in the PDF front matter.
- [Fundamentals of Data Engineering source PDF](/Users/GaryT/Documents/Work/tools/knowledge-base/knowledge-base/data-engineering/fundamentals-data-engineering.pdf): first release 2022-06-22 in the PDF front matter.
- [Clean Architecture source PDF](/Users/GaryT/Documents/Work/tools/knowledge-base/knowledge-base/software-engineering/clean-architecture.pdf): copyright 2018; publication date not found in the inspected front matter. PDF creation metadata is 2017-09-20, which is not a publication date.
- [R1 report](../R1/REPORT.md) and [R1 timing](../R1/timing.json): measured and reported 2026-10-10. CPU timing and environment reference, not independent retrieval evidence.
- [Gemma prompt configuration](https://huggingface.co/google/embeddinggemma-2/blob/main/config_sentence_transformers.json): repository update date 2026-10-06 from R1 metadata; file-specific publication date not found. Pinned revision listed in Results.
- [Google multimodal guide](https://ai.google.dev/gemma/docs/embeddinggemma/multimodal-embeddinggemma-with-sentence-transformers): last updated 2026-10-07. Supports the image dictionary call and selective encoder loading.
- [Gemma processor configuration](https://huggingface.co/google/embeddinggemma-2/blob/main/processor_config.json): repository update date 2026-10-06 from R1 metadata; file-specific publication date not found. The exact pinned local copy is retained under sources/.
- [Jina model card](https://huggingface.co/jinaai/jina-embeddings-v5-text-small-retrieval): repository update date 2026-04-15 from R1 metadata; card-specific publication date not found. Supports query/document usage; pinned revision listed in Results.
- [PyMuPDF image recipes](https://pymupdf.readthedocs.io/en/latest/recipes-images.html): page publication date not found. Supports embedded-object extraction and clipped rendering; installed version 1.28.2 recorded in extraction.json.
- The 40 local source files in [manifest.json](inputs/manifest.json): copied read-only 2026-10-10; source-file publication dates not found. Each code query records the answering function. Evaluation plan and label fingerprints are in [evaluation_plan.json](artifacts/evaluation_plan.json) and [frozen_labels.json](artifacts/frozen_labels.json).
