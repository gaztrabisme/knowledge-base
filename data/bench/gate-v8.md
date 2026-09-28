# Gate v8: technical shelf candidate

Reader: Gary. This report decides whether `developer_knowledge_v8` becomes the live search collection. The candidate is the live collection (126 books, 132,623 vectors) plus 165 new technical books (134,024 vectors).

## Verdict: not promoted

The plan fixed three promotion conditions before the run. Two pass. The third fails by 2 queries out of 40:

| Condition | Threshold | Result | Pass |
|---|---|---|---|
| Hard-set recall@10 drop | at most 0.02 | 0.9680 → 0.9521 (−0.016) | yes |
| Sanity-set recall@10 (new books findable) | at least 0.85 | 0.867 | yes |
| Share of sampled regressions that are real dilution | at most 20 of 40 | 22 of 40 | **no** |

Under the plan's rule the candidate stays unpromoted and the decision goes to Gary. The live collection is unchanged.

## Terms

- **Hard set**: the 438-query benchmark. **Easy set**: 199 queries. All 637 were written from the original 46 books, so no query has a new book as its answer. The gate can only lose score from new books, never gain it.
- **Sanity set**: 60 new queries, each written from a passage in a different new book and paraphrased. It is the only part of the gate that can see the new books.
- **NDCG@10**: how high the labelled answer ranks in the top 10 (1.0 = first). **Recall@10**: whether it is in the top 10 at all. **Ceiling**: whether it is in the 50 candidates before reranking.
- **Real dilution**: a query regressed, and the passage that pushed the labelled answer down answers the question worse than the labelled answer does.

## Numbers

All runs are on the bppc RTX 5080 against a Qdrant copy of the live collection. The v7.1 baseline re-run matches the published MPS numbers (hard NDCG 0.7703 vs 0.7704), so the device does not affect the comparison.

| Set | Metric | v7.1 (live) | v8 candidate | Change |
|---|---|---|---|---|
| Hard (438) | NDCG@10 | 0.7703 | 0.7429 | −0.0274 |
| | Recall@10 | 0.9680 | 0.9521 | −0.0159 |
| | MRR | 0.8573 | 0.8324 | −0.0249 |
| | Ceiling (recall@50) | 0.9886 | 0.9749 | −0.0137 |
| Easy (199) | NDCG@10 | 0.9108 | 0.9042 | −0.0066 |
| | Recall@10 | 1.0000 | 1.0000 | 0 |
| Sanity (60) | Recall@10 | n/a | 0.8667 | |
| | NDCG@10 | n/a | 0.7401 | |

On the hard set, 88 queries regressed, 16 improved and 334 did not move.

## Dilution sample

Method:
- 40 of the 88 regressed queries, drawn with seed 42.
- For each, the labelled answer and the highest-ranked passage above it (the "displacer") were shown in random A/B order, with no labels.
- A DeepSeek-v4-pro judge graded each passage 0/1/2:
  - 2: answers;
  - 1: partial;
  - 0: does not answer.
- Files: `gate-v8/dilution-sheet.jsonl` (what the judge saw), `gate-v8/dilution-key.jsonl` (the key), `gate-v8/dilution-grades.jsonl`.

| Displacer | Samples | Dilution (displacer graded lower) | Tie | Displacer better |
|---|---|---|---|---|
| All | 40 | 22 | 9 | 9 |
| From a new book | 22 | 14 | 2 | 6 |
| From an old book | 18 | 8 | 7 | 3 |

Grade pairs (labelled, displacer):

| Pair | Count |
|---|---|
| (2,1) | 14 |
| (2,2) | 6 |
| (2,0) | 3 |
| (1,2) | 8 |
| (1,0) | 5 |
| (1,1) | 2 |
| (0,2) | 1 |
| (0,0) | 1 |

What the grades show:
- **Label quality.** The labelled answer was a full answer (grade 2) in only 23 of 40 cases.
- **The clear harm.** In 17 cases a full answer was pushed down by a passage that is not one. That is the dilution that matters.
- **New-book wins.** In 9 cases the displacer answers better than the label.

**Which new books displace most:** broad ones overlapping the old shelf. Across the 88 regressed top-10 lists they appear this often:

| Book | Appearances |
|---|---|
| `designing-data-intensive-applications` | 9 |
| `essential-math-ai` | 9 |
| `foundations-scalable-systems` | 9 |
| `generative-deep-learning` | 8 |
| `data-science-from-scratch` | 8 |
| `qt6cplusplusguiprogrammingcookbook` | 8 |

**Not only the new books.** 18 of the 40 displacers are old books. Adding 134,000 candidates changes which 50 passages reach the reranker, and the reranker then reorders old passages too. The same pattern appeared at v7.0 (ceiling steady, reranker demoting known-good hits).

## Reading the failure

- **Margin.** 22 of 40 against a limit of 20. With 40 samples, the 95% interval on the dilution share is roughly 39–70%, so this sample cannot tell 55% from 50%.
- **Where the harm lands.** Recall@10 barely moves (−0.016). The labelled answers mostly stay in the top 10 but rank lower. An agent reading the top results still sees them, lower down.
- **What promotion gains.** The 165 new books add coverage the benchmark cannot measure: design, frontend, C++, data engineering, reverse engineering, management. The sanity set shows they are findable (0.867).

## Candidate status

Both candidate copies are built and verified. `scripts/merge_collection.py verify` compares point counts and 200 sampled points (100 old, 100 new) against their origins.

| Server | Collection | Points |
|---|---|---|
| bppc Qdrant | `developer_knowledge_v8` | 266,647 |
| Mac Qdrant | `developer_knowledge_v8` | 266,647 |

Promotion is one alias switch (`merge_collection.py promote`) plus `KB_COLLECTION=developer_knowledge_live` in `.mcp.json`.
