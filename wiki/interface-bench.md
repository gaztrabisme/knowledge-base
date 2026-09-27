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

## Two conditions: thinking off (part 1) and reasoning on (part 2)

Stages 1 to 4 below ran with the harness forcing `enable_thinking=false` and `max_tokens=2048`,
an 8-call cap, and the original 150 questions. Their verdicts hold for that condition only.
Part 2 reruns the arms with no generation parameters in the request (oMLX's per-model settings
apply: thinking on, `max_tokens` 32768), a 25-call cap, and `data/bench/questions_v2.jsonl`:
128 questions whose labels were independently verified (`data/bench/analysis/golden-verify.md`).
Part-2 results are in the section of that name at the end.

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

## Part 2: reasoning on, verified questions

### A5 against A1 — A5 REJECTED, A1 kept

A5 is A1 plus an optional `find_books(query)` that returns each book's top passage, and a
`search(books=[...])` that merges scoped and unscoped results by reranker score instead of
restricting to the chosen books.

| Model | found A1 → A5 | cited A1 → A5 | prompt tokens per question | calls per question |
|---|---|---|---|---|
| Gemma-4-12B | 0.938 → 0.922, n.s. | 0.938 → 0.922, n.s. | 6,257 → 4,949, better | 1.2 → 1.0, better |
| Qwen3.6-35B-A3B | 0.992 → 0.992, n.s. | 0.953 → 0.930, n.s. | 30,780 → 33,294, n.s. | 4.0 → 4.5, n.s. |
| Pooled (256 pairs) | 0.965 → 0.957, n.s. | 0.945 → 0.926, n.s. | n.s. | n.s. |

No pooled metric moved significantly, so A5 fails the rule's "at least one improves". The token
and call savings are Gemma's alone. With reasoning on, A1 finds a correct passage for 94% (Gemma)
and 99% (Qwen3.6) of the verified questions, against 88% pooled under thinking off; the remaining
headroom is small, which limits what any later arm can show on this set.

Table: `data/bench/compare-A5r-vs-A1r-v2.md`.

### A1 against A0 — A1 kept

A0 is the interface before any refinement: full-section search results, a 103k-token
`list_books`, exact book names only.

| Model | found A0 → A1 | cited A0 → A1 | prompt tokens per question | tool-output tokens | calls per question | invalid calls |
|---|---|---|---|---|---|---|
| Gemma-4-12B | 0.930 → 0.938, n.s. | 0.922 → 0.938, n.s. | 13,043 → 6,257, better | 51,027 → 2,874, better | 1.4 → 1.2, better | 0.4 → 0.0, better |
| Qwen3.6-35B-A3B | 0.984 → 0.992, n.s. | 0.938 → 0.953, n.s. | 43,140 → 30,780, n.s. | 34,838 → 9,030, better | 2.6 → 4.0, worse | 0.2 → 0.0, better |
| Pooled (256 pairs) | 0.957 → 0.965, n.s. | 0.930 → 0.945, n.s. | 28,092 → 18,519, better | 42,933 → 5,952, better | 2.0 → 2.6, worse | 0.3 → 0.0, better |

With reasoning on, both models answer as well from A0's long results as from A1's short ones;
A1's gain is cost: a third less prompt, a seventh of the tool output, no invalid calls.

The pooled call count is worse, which the decision rule forbids read literally. It is kept on the
same reading as Stage 1: every extra call comes after the first correct passage. Calls up to and
including the first hit fall on both models (Gemma 1.39 → 1.17, Qwen3.6 1.21 → 1.15); after it,
Qwen3.6 goes from 1.42 to 2.88 calls a question, and 226 of its 284 post-hit A1 calls are
`read_chunk`, reading around a short hit that A0 would have returned in full. Those calls are
the price of the smaller results and are counted inside the prompt-token saving.

Table: `data/bench/compare-A1r-vs-A0r-v2.md`.

### A3hb (catalog, corpus vocabulary, HyDE advice) against A1 — REJECTED

A3hb is the Stage 3 arm with HyDE advice: A1 plus `find_books`, `related_headings` in results, and
tool descriptions that tell the agent to write a `hyde_passage` for conceptual questions. It tests
that package, not HyDE alone.

| Model | found A1 → A3hb | cited A1 → A3hb | calls per question | tool-output tokens |
|---|---|---|---|---|
| Gemma-4-12B | 0.938 → 0.875, n.s. (p=0.057) | 0.938 → 0.875, n.s. (p=0.057) | 1.2 → 1.6, worse | n.s. |
| Qwen3.6-35B-A3B | 0.992 → 0.953, n.s. (p=0.063) | 0.953 → 0.914, n.s. | n.s. | 9,030 → 7,310, better |
| Pooled (256 pairs) | 0.965 → 0.914, **worse (p=0.004)** | 0.945 → 0.895, **worse (p=0.019)** | n.s. | n.s. |

Of the 19 questions where exactly one arm found a correct passage, A1 found it in 16. Reasoning
did not rescue the part-1 finding: asking a small model to narrow by book and to write a
hypothetical passage loses answers. HyDE stays an optional `search` parameter; tool descriptions
should not push small agents toward it.

Table: `data/bench/compare-A3hbr-vs-A1r-v2.md`.

### Real-harness check through `claude -p` — A1 holds (2026-09-27)

`scripts/claude_bench.py` runs each question through the Claude Code CLI (2.1.283) with the
knowledge base as its only MCP server, Qwen3.6-35B-A3B on oMLX as the model, and the tool-call
cap raised to 25 turns. First 20 questions of `questions_v2.jsonl`, one at a time, A1 then A0.

oMLX's own Anthropic endpoint (`/v1/messages`) cannot serve this: with a tool defined, Qwen3.6
and Gemma-4-12B both return the call as plain text in a `text` block, the stream ends with
`end_turn`, and `usage` reads 0 tokens, so the CLI never calls a tool. The run therefore goes
through a LiteLLM proxy (Anthropic in, `/v1/chat/completions` out, provider `hosted_vllm`) that
drops every generation parameter the CLI sends (`max_tokens`, `temperature`, `thinking`, …), so
oMLX's per-model settings apply as in the in-process benchmark. The LiteLLM `openai` provider is
unusable here: it routes to oMLX's `/v1/responses`. Point the script at the proxy with
`KB_CLAUDE_BENCH_BASE_URL`.

| Metric, 20 paired questions | A0 | A1 | Verdict |
|---|---:|---:|---|
| found | 19 | 18 | n.s. (one discordant pair) |
| cited | 19 | 18 | n.s. |
| prompt tokens per question | 37,491 | 29,499 | n.s. (p=0.089) |
| tool-output tokens per question | 12,922 | 12,195 | n.s. |
| calls per question | 5.7 | 5.0 | n.s. |
| invalid calls per question | 0.10 | 0.00 | n.s. |
| wall time per question | 118 s | 97 s | not tested |

Twenty questions cannot show a difference of the size the in-process benchmark found, and none
is significant. What the check shows is that A1 works in a real client: no invalid calls, no
give-ups, the same tool mix (search, then `read_chunk` on hits). Its token saving is smaller
than in-process because Claude Code already truncates oversized MCP output, which caps A0's
long results (A0 tool output here is 12.9k tokens a question against 34.8k in-process).
The one discordant question, h0088, A0 found after 13 calls and A1 missed after 6.

Table: `data/bench/compare-claude-A1-vs-A0-v2.md`. Rows: `data/bench/runs/claude-CA{0,1}-*.jsonl`.
