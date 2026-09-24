# Failure analysis: Qwen3.6-35B-A3B on A0 vs A1 (150 questions each)

Sources: `data/bench/runs/{A0,A1}-Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B.jsonl` (150 rows each),
`data/bench/calls/*.jsonl`, `data/bench/transcripts/*/`. A1 has 35 `cited=false` rows, A0 has 37.
**No sampling — every cited-false row in both runs was classified**, using `found`, `n_calls`,
`gave_up`, `stop_reason`, `cited_ids`, the full answer text, and every call's `args`/`error`/`n_results`.
Full transcripts were read for 8 qids (n024, n025, h0119, h0052; A0 h0129, h0165, h0367, n018) and
positive-parent texts for 8 qids, to confirm causes. Scoring rule (from `scripts/agent_bench.py:97-102`):
credit requires a line *starting* with `cited:` containing ids matching `-pN-cM`.

**Class rules (first match wins):** (c) `n_calls=0`; (f) `gave_up`; (d) run completed with tool calls
but the harness extracted no parseable CITED ids; (e) hard tool error; (a) `found=false`; (b) `found=true`
with a parseable CITED line naming no positive parent; (g) other. (e) is empty for both arms: the two
empty-result cases (A1 h0246, A0 n005) are counted under (a) because the binding failure was retrieval,
not the empty output; A0 h0367's `read_chunk` error ("Book not found: rustwebprogramming-14927") is
noted under (d), which is what actually cost it credit.

## 1. A1 cited-false questions (35)

| qid | arch | cls | cause |
|---|---|---|---|
| h0003 | baseline | (a) | `'reinforcement learning agent update rule log probability reward sum'` — policy-gradient content returned from probml/UDL/AIMA, never the DRL book; missing "policy gradient"/"return". |
| h0027 | baseline | (a) | `'latest GPT model parameters rumored at launch'`, `'GPT-4 parameters number of parameters rumored'` — MLE-2e p145 says "**reported** one trillion parameters"; "rumored" misses it. |
| h0052 | baseline | (d) | Read the right parent (redis-for-dummies-p7), named `p7-c0` first — as `**CITED:**`. |
| h0060 | baseline | (f) | Cap (8 calls): 5 searches + grep + read; positive p113 had surfaced but it cited p137/p112/use-the-index-luke. |
| h0071 | baseline | (d) | Search hit the right parent (p166), cited `p166-c2` — inside `` **CITED:** `…` ``. |
| h0073 | baseline | (d) | Read the right parent (azure p72), cited `p72-c1` — `**CITED: …**`. |
| h0105 | baseline | (b) | Positive graphml-p32 surfaced in search 2; read/cited d2l + 3 Huyen ids instead. |
| h0116 | baseline | (a) | `'DQN Atari image processing layers value prediction action selection same network'` — the book's A2C-on-Pong section (p187) never uses these terms; "actor-critic"/"A2C" never tried. |
| h0119 | baseline | (c) | 0 calls; HSET semantics from memory; placeholder `CITED: search_result_HSET_return_value`. |
| h0129 | baseline | (d) | Right parent crypto-101-p11 read and cited — `**CITED:`. |
| h0152 | baseline | (b) | Search returned the 1st-ed positive (designing-distributed-systems-p8); read/cited the 2nd-edition book (…-2e-p21-c2) instead. |
| h0167 | navig. | (a) | Right book, wrong vocabulary: `book='boneh-shoup-applied-cryptography'`, `'zero-knowledge simulation fake transcript ideal world security definition'` (n=10) — book's "Masked VESS"/hybrid-argument terms never tried. |
| h0180 | baseline | (a) | `'reinforcement learning agent tries all possible actions estimating value from a state exhaustive evaluation'`, `'value iteration exhaustive all possible actions Bellman equation reinforcement learning'` — book's MC section (p343) says "exploring starts"/"simulated experience". |
| h0201 | keyword | (b) | Positives rustwebprogramming-p287/masteringpytorch-p196 surfaced; read/cited masteringlinuxadministration p342/p349 (cited line also `**CITED:`). |
| h0242 | keyword | (b) | masteringpytorch-p116 surfaced; cited d2l-en p792/793/795. |
| h0246 | keyword | (a) | `grep_books "mac not prf"` → 0 (literal match; text reads "Not every MAC is a PRF"); search ranked the adjacent parent p112-c2; positive p113 never surfaced. |
| h0264 | keyword | (f) | Cap (8): same query `'tokio move keyword await tasks'` 5× across 5 `book=` guesses + `list_books` (126 rows); never tried rust_ebook/rustwebprogramming. |
| h0330 | navig. | (d) | Right parent p209 read and cited — `**CITED:`. |
| h0335 | navig. | (d) | Three right-book ids cited — `**CITED:`. |
| h0352 | err_sym | (c) | `pd.read_parquet` — 0 calls, no CITED line. |
| h0358 | err_sym | (c) | `` `memory usage: 6.1+ GB` `` — 0 calls. |
| h0396 | err_sym | (c) | `sized_iter! macro` — 0 calls; `CITED: search result`. |
| h0397 | err_sym | (c) | `agent.replay(batch_size)` — 0 calls. |
| h0398 | err_sym | (d) | Right parents read and cited — `**CITED:**`. |
| h0406 | err_sym | (c) | `Embedding(weights=…)` — 0 calls. |
| h0407 | err_sym | (c) | `nn.Softmax(dim=1)` — 0 calls. |
| h0412 | err_sym | (c) | `plt.barh([], [])` — 0 calls; answer admits it is general knowledge. |
| n005 | baseline | (a) | `'cosine similarity score ranking vector search'`; 3rd query scoped `book='ai-powered-search'` — resolution worked (n=3) but wrong book; positive building-reliable-ai-systems-p70 ("employee chatbot") never surfaced; "HR policy" ≠ book's "employee" vocabulary. |
| n007 | baseline | (d) | coding-with-ai-p92 surfaced twice, cited `p92-c2` — `**CITED:`. |
| n014 | baseline | (b) | Positive p172 ("8.3 Aggregating multiple annotations…") surfaced; cited adjacent p175 + p221. |
| n019 | baseline | (d) | llms-in-production-p107 surfaced, cited `p107-c1` — `**CITED:`. |
| n022 | baseline | (d) | Right parents p29/p30 read and cited — `**CITED:`. |
| n024 | baseline | (d) | Read the right parent (optimization-algorithms-p181-c6) and reported its numbers; emitted **no CITED line at all**. |
| n025 | baseline | (b) | Positive p260 surfaced; cited p136-c2 (a different PSO section). |

For every (a) row the queries were reasonable in specificity; the failures are **wrong vocabulary**
(h0003, h0116, h0167, h0180, h0027, n005) or an adjacent-parent near-miss (h0246). Only n005 and h0167
scoped books, and n005's scope was the wrong book; no (a) row was hurt by vagueness.

## 2. Class counts

| Class | A1 (n=35) | A0 (n=37) |
|---|---|---|
| (a) never retrieved | 7 | 5 |
| (b) retrieved, not cited | 6 | 8 |
| (c) no tool use | 8 | 13 |
| (d) bad citation format | 12 | 11 |
| (e) tool error / empty | 0 | 0 |
| (f) stopped early | 2 | 0 |
| (g) other | 0 | 0 |

**Check:** A1 7+6+8+12+0+2+0 = 35 = the 35 cited-false rows; A0 5+8+13+11+0+0+0 = 37 = the 37
cited-false rows. Verified programmatically (`classify_failures.py`): declared sets equal the
cited-false sets exactly, no duplicates.

## 3. Where A1 fixed or broke things (40 questions; all 40 verified present in both run files)

A1 fixed 21, broke 19, net +2 (115 vs 113 cited).

**A1 fixed (A0 failed → A1 cited), class of the A0 failure:**

| qid | A0 class | one-line cause |
|---|---|---|
| h0032, h0038, h0095, h0096, h0133, h0140, n021 | (d) | A0 wrote `**CITED:`/`CITED:**`; A1's run emitted a parseable line. |
| h0165 | (d) | A0 answer degenerated into endless "https --proto" repetition, no CITED line. |
| h0367 | (d) | A0 called `read_chunk` with mangled id `rustwebprogramming-14927` ("Book not found") and wrote `CACHED:`; A1 clean. |
| n018 | (d) | A0 produced no CITED line. |
| h0090, h0158, h0202, h0356, n011 | (c) | A0 answered from memory; A1 searched and cited. |
| h0114, h0127, h0231, h0408 | (b) | A0 retrieved the positive but cited other ids; A1 cited the positive. |
| h0088, h0326 | (a) | A0 never retrieved; A1 did. |

**A1 broke (A0 cited → A1 failed), class of the A1 failure:**

| qid | A1 class | one-line cause |
|---|---|---|
| h0052, h0073, h0118, h0330, h0335, n007, n019 | (d) | Right parent read/cited, but `**CITED:` bold broke the line. |
| n024 | (d) | Read the right parent, reported its content, no CITED line. |
| h0027, h0180 | (a) | Queries missed on vocabulary ("rumored" vs "reported"; no "Monte Carlo"/"exploring starts"); A0 had retrieved them. |
| h0105, h0242, n014 | (b) | Positive surfaced but cited other books/adjacent parents. |
| h0152 | (b) | Cited the 2nd-edition book instead of the 1st-ed positive search returned. |
| h0119 | (c) | Answered HSET from memory with a placeholder citation; A0 had searched. |
| h0396, h0406 | (c) | error_symbol questions, 0 tool calls. |
| h0060 | (f) | Hit the 8-call cap after 5 near-duplicate skip-scan searches. |
| h0264 | (f) | Hit the cap after 6 calls re-issuing one query across 5 `book=` guesses. |

Note the symmetry: 10 of A1's 21 gains and 8 of its 19 losses are format luck, not interface effect.

## 4. Tool usage patterns in A1 (all 150 runs)

- **First call:** `search` 136/150 (91%), `grep_books` 5, `list_books` 1, no call 8. A0: search 132, grep_books 5, list_books 0, no call 13.
- **`read_chunk` after search:** 117/140 runs with ≥1 search (84%) issued ≥1 `read_chunk` after a search (A0: 68/135, 50%). `read_chunk` calls: 209 total (A0: 117).
- **Near-identical query repeats** (token-set Jaccard ≥0.75, stopwords removed): 5/150 A1 runs (A0: 6/150). In A1 failures: h0264 re-issued one query 5× (15 identical pairs) and h0060 twice. h0029 (cited=true) repeated one query 5×.
- **`book=`:** 9/150 runs (6%) (A0: 6/150). 3 of those 9 A1 runs failed (h0167, h0264, n005) vs 23% overall failure. A1's single `list_books` call returned all 126 books.
- Every run with 0 tool calls failed: 8/8 in A1, 13/13 in A0.

## 5. Three interface changes the evidence supports

1. **Make the citation channel structured (or strip markdown before parsing).** (d) is A1's largest class: 12/35 failures (A0: 11/37), and in 11 of the 12 the correct chunk id appears verbatim in the answer text. The model writes `**CITED`/`CITED:**` in 21/150 A1 runs (14%); 14 lost all credit while 7 were rescued by a later plain line. Replacing the free-text `CITED:` line with a required final tool call (e.g. `submit_answer(answer, chunk_ids=[…])`), or normalizing `*`/backticks in the parser, addresses 12/35 A1 failures — more than any other class — and is arm-independent noise today, deciding 18 of the 40 A0↔A1 differences.

2. **Refuse a zero-tool-call answer (one reminder, then re-prompt).** All 8 A1 zero-call runs failed (13/13 in A0), and 7 of A1's 8 are `error_symbol` questions the model answered from memory (h0412 even says so). A1 already cut these 13→8; an orchestration rule — if the model produces a final answer with `n_calls=0`, inject one "search before answering" turn — targets the entire remaining (c) class, worth up to 8 questions.

3. **Fail safe on thin scoped searches.** Three A1 failures came from scoping: h0264 burned 6 of 8 calls (5 `book=` re-scopes + `list_books` returning 126 rows) and hit the cap; n005 scoped to the plausible-but-wrong `ai-powered-search`; h0060 hit the cap on 5 near-duplicate unscoped searches. When a `book=`-scoped search returns few results, the server should automatically also run unscoped and label which hits are in-book, and `list_books` should return a compact shortlist (or accept a topic filter) instead of 126 rows — the model cannot use a 126-row dump mid-run and instead guesses book names.

## Unfinished / caveats

- All sections complete. Class boundaries required judgment in two places, stated in the preamble: (e) is unused because empty results never *derailed* a run, and A0 h0367 is counted (d) though it also had the run's only hard tool error.
- Analysis helpers (read-only): `analyze_a0_a1.py`, `classify_failures.py`, `diff_and_checks.py`, `tool_usage_stats.py`, `positive_text.py` in this directory.
