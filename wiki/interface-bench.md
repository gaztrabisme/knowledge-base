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
