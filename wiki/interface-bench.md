# Interface benchmark: tool design measured on small agents

Reader: whoever changes the knowledge-base MCP tools next. This page records how each interface
change was measured and whether it was kept.

## Method

- **Agents.** The main arms are run by two local models on oMLX:
  - `gemma-4-12B-it-qat-OptiQ-4bit`, a 12B dense model;
  - `Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B`, a mixture-of-experts model with about 3B active parameters.

  `Qwen3.8-Flash-Next-REAP-384-oQ4e-BF16-MTP-PLE` is a larger reference model, run on the baseline and on the final arm only.
- **Harness.** `scripts/agent_bench.py` runs an OpenAI-style tool-calling loop against oMLX:
  - the tool functions are called in-process, with the same schemas an MCP client sees;
  - the system prompt is short;
  - the cap is 8 tool calls, thinking is off, and there are 4 concurrent requests.

  Each arm runs from a git worktree pinned at that arm's commit.
- **Questions.** `data/bench/questions.jsonl` has 150 questions with known correct parent passages:
  - 120 drawn from the hard retrieval benchmark, stratified by domain and question type;
  - 30 generated on Qwen3.8 from the 17 books added in v7.1, at least one per book.
- **Metrics per run:**
  - **Goal achievement.** `found`: a correct passage appeared in some tool output. `cited`: the final `CITED:` line names one.
  - **Token efficiency.** Prompt tokens summed over turns, tokens returned by tools, and peak context.
  - **Ergonomics.** Invalid calls, empty results, calls before the first correct passage, and runs that gave up.
- **Decision rule, fixed before any run.** Pooled across both small models and paired per question, against the current best arm:
  - no metric gets significantly worse;
  - at least one improves significantly;
  - the retrieval gate is unchanged, unless the stage is meant to change ranking.

  Binary metrics use exact McNemar tests. Counts use a paired bootstrap 95% CI plus a Wilcoxon test. Both are applied at α=0.05, in `scripts/bench_compare.py`.
- **Citation scoring.** The first `CITED:` parser missed markdown-formatted lines such as `**CITED:**`. Every run file has been rescored with the fixed parser, using `scripts/rescore_citations.py` on the stored answers, so all arms are scored the same way.

## Stage 1 (A1): short search results, slim catalog, clean chapters, book-name resolution — KEPT

What changed:
- `search` returns the matched child passage by default (`detail="brief"`). A single search result fell from about 23k to about 2.7k tokens.
- `list_books()` became a 4.9k-token catalog. Before, it was 103k tokens and every MCP client rejected it for size.
- Chapter lists skip headings inside code blocks and headings that are only links.
- `book` accepts a title or a near miss, and returns suggestions when nothing matches.

Results, pooled across both small models, 300 paired runs (A0 → A1):

| Metric | A0 | A1 | Change | Verdict |
|---|---:|---:|---:|---|
| found | 0.833 | 0.880 | discordant 14 / 28 | better (p=0.044) |
| cited | 0.780 | 0.840 | discordant 20 / 38 | better (p=0.025) |
| gave up | 0.020 | 0.023 | 5 / 6 | n.s. |
| prompt tokens per question | 26,144 | 15,350 | −10,794 [−14,523, −7,332] | better |
| tool-output tokens per question | 48,510 | 5,447 | −43,062 [−49,208, −36,984] | better |
| peak context per question | 14,324 | 7,175 | −7,149 [−8,080, −6,234] | better |
| invalid calls per question | 0.35 | 0.00 | −0.33 [−0.4, −0.3] | better |
| calls before first correct passage | — | — | −0.12 [−0.21, −0.03], n=236 | better (p<0.001) |
| total calls per question | 1.9 | 2.3 | +0.3 [+0.2, +0.5] | more; the extra calls are `read_chunk` after a hit |

Per model:
- **Gemma-4-12B** gains most. In A0 it called `list_books`, got the oversized-output error (0.7 invalid calls per question), and often searched less as a result. In A1, `found` rose from 0.787 to 0.867 and `cited` from 0.760 to 0.840, both significant.
- **Qwen3.6-35B-A3B** held its answer quality: `found` 0.880 → 0.893 and `cited` 0.800 → 0.840, both n.s. It halved its prompt tokens, and its wall time per question fell from 404 s to 235 s.

Retrieval gate: NDCG@10 0.7704, unchanged.

Full tables are in `data/bench/compare-A1-vs-A0.md` and `data/bench/compare-A1-vs-A0-firsthit.txt`. The failure analysis is in `data/bench/analysis/failures-qwen36-A0-A1.md`.

## Stage 2 (A2): catalog, `find_books`, book and domain filters — REJECTED

What changed:
- `data/catalog.json` gives every book a domain, 6–10 tags from a fixed vocabulary and a one-line summary; Qdrant points carry `domain` and `tags`.
- `find_books(query, domain, tags)` ranks books for a query by their search hits and returns the matching section headings.
- `search` gained `books=[...]` and `domain=` filters.

Results, pooled across both small models, 300 paired runs (A1 → A2):

| Metric | A1 | A2 | Change | Verdict |
|---|---:|---:|---:|---|
| found | 0.880 | 0.723 | discordant 62 / 15 | worse (p<0.0001) |
| cited | 0.840 | 0.670 | discordant 70 / 19 | worse (p<0.0001) |
| gave up | 0.023 | 0.070 | 4 / 18 | worse (p=0.004) |
| prompt tokens per question | 15,350 | 17,989 | +2,640 [+156, +4,887] | worse |
| tool-output tokens per question | 5,447 | 4,628 | −820 [−1,343, −315] | better |
| total calls per question | 2.3 | 3.0 | +0.8 [+0.6, +1.0] | worse |
| invalid calls per question | 0.0 | 0.3 | +0.3 [+0.2, +0.3] | worse |

Per model:
- **Gemma-4-12B:** found 0.867 → 0.580, cited 0.840 → 0.553. It called `find_books` on 136 of 150 questions, and passed a guessed `domain` in 87 of its 138 calls, then restricted `search` to the books that came back. When the guess was wrong the right book never appeared (45 questions lost).
- **Qwen3.6-35B-A3B:** found and cited n.s., but gave up on 13% of questions (A1: 5%), made 0.6 invalid calls a question, and used 36% more prompt tokens. 61 of its calls passed `books` as a JSON string, which the server read character by character.

Full tables: `data/bench/compare-A2-vs-A1.md`.

## Stage 2b (A2b): the Stage 2 defects fixed — REJECTED

What changed from A2:
- `find_books(query)` ranks the whole library; `domain` and `tags` only filter the browse listing.
- `search` lost its `domain` parameter.
- List arguments accept a JSON-encoded or comma-separated string.
- A book-scoped search whose results all score below the reranker floor also returns up to 3 results from other books, marked `outside_filter`.

Retrieval gate: NDCG@10 0.7700, unchanged.

Results, pooled across both small models, 300 paired runs (A1 → A2b):

| Metric | A1 | A2b | Change | Verdict |
|---|---:|---:|---:|---|
| found | 0.880 | 0.753 | discordant 53 / 15 | worse (p<0.0001) |
| cited | 0.840 | 0.720 | discordant 53 / 17 | worse (p<0.0001) |
| gave up | 0.023 | 0.033 | 6 / 9 | n.s. |
| prompt tokens per question | 15,350 | 16,486 | +1,137 [−1,101, +3,224] | n.s. |
| tool-output tokens per question | 5,447 | 4,443 | −1,004 [−1,488, −559] | better |
| total calls per question | 2.3 | 2.8 | +0.5 [+0.3, +0.7] | worse |
| invalid calls per question | 0.0 | 0.1 | n.s. | n.s. |

The fix removed the invalid calls and the extra give-ups, but found and cited stayed down. Gemma lost 40 questions that A1 found. In 37 of them it called `find_books`, and in 30 of those the right book was in the top 5 that `find_books` returned. Gemma then scoped `search` to one or two of the five and left the right one out. The safety net did not fire, because the wrong books still returned passages above the reranker floor. The failure is the narrowing step itself: a small model picks the wrong books even from a correct shortlist.

## Stage 3 (A3b, A3hb): corpus vocabulary instead of HyDE — REJECTED

What changed from A2b:
- `search` returns `related_headings`: headings of the next-ranked passages, as vocabulary for a follow-up query.
- Tool descriptions steer agents to `find_books` → scoped `search` → `read_chunk`, and demote `hyde_passage`.
- A3hb is the same code with descriptions that encourage `hyde_passage` (`KB_TOOL_DOCS=hyde`).

Pooled, 300 paired runs each:

| Comparison | found | cited | gave up | prompt tokens per question | calls per question |
|---|---|---|---|---|---|
| A1 → A3b | 0.880 → 0.760, worse (p<0.0001) | 0.840 → 0.713, worse (p<0.0001) | 0.023 → 0.053, worse (p=0.049) | +4,008, worse | +0.9, worse |
| A2b → A3b | 0.753 → 0.760, n.s. | 0.720 → 0.713, n.s. | n.s. | n.s. | +0.4, worse |
| A3b → A3hb (HyDE) | 0.760 → 0.687, worse (p=0.007) | 0.713 → 0.640, worse (p=0.013) | n.s. | −6,422, better | −0.7, better |

- `related_headings` and the workflow descriptions added nothing over A2b and cost 1,089 more tool-output tokens a question.
- Encouraging HyDE cut tokens but lost answers. The loss is Qwen3.6's: found 0.840 → 0.673 against A3b (Gemma n.s.). This is the direct test of whether a small model can write a useful hypothetical passage: it cannot do so reliably, and relying on it costs about one question in six for Qwen3.6.

## Stage 4 (A4b): fewer tools — REJECTED

What changed from A3b: `search_book` removed (`search(books=[...])` covers it); `read_chunk` and `get_chapter` merged into `read(chunk_id | book + chapter)`.

Pooled, 300 paired runs each:

| Comparison | found | cited | gave up | prompt tokens per question | invalid calls per question |
|---|---|---|---|---|---|
| A1 → A4b | 0.880 → 0.743, worse (p<0.0001) | 0.840 → 0.703, worse (p<0.0001) | 0.023 → 0.067, worse (p=0.007) | +1,718, n.s. | 0.0 → 0.3, worse |
| A3b → A4b | 0.760 → 0.743, n.s. | 0.713 → 0.703, n.s. | n.s. | −2,291, better | 0.2 → 0.3, worse |

Merging the tools saved prompt tokens against A3b but raised invalid calls, and it sits on top of the `find_books` workflow that lost to A1.

## Where this leaves the interface

A1 remains the best arm on both small models. Every arm that adds a narrowing step the agent must choose (a domain, a book list, a hypothetical passage) lowers found and cited for small agents, and the losses are larger than any token saving. The catalog and Qdrant payload are sound: `find_books` ranks the right book in its top 5 for most questions. What fails is handing the narrowing decision to the small model.

Full tables: `data/bench/compare-A2b-vs-A1.md`, `compare-A3b-vs-A1.md`, `compare-A3b-vs-A2b.md`, `compare-A3hb-vs-A3b.md`, `compare-A3hb-vs-A1.md`, `compare-A4b-vs-A1.md`, `compare-A4b-vs-A3b.md`.
