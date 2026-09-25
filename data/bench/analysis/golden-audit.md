# Agent benchmark question-set reliability audit

All 150 questions were reviewed against their labeled full parent passages, the prescribed production candidate pool (top 10 plus every non-positive above the lowest positive), prior hard-set human judgments, and available agent citations. Candidate snippets were checked against full parent text when needed. No model was loaded or called.

## Verdict counts

Total: **150**. **sound: 28**, **missing_positives: 95**, **wrong_positive: 7**, **ambiguous: 16**, **unanswerable: 2**, **leaky: 2**. The audit records **258 additional answer-bearing parent labels** and **15 wrong-positive labels across 10 questions.

| Stratum | sound | missing_positives | wrong_positive | ambiguous | unanswerable | leaky | Total |
|---|---:|---:|---:|---:|---:|---:|---:|
| golden | 27 | 68 | 6 | 16 | 1 | 2 | 120 |
| new-books | 1 | 27 | 1 | 0 | 1 | 0 | 30 |

## Verdicts by domain

| Domain | sound | missing_positives | wrong_positive | ambiguous | unanswerable | leaky | Total |
|---|---:|---:|---:|---:|---:|---:|---:|
| ai-engineering | 1 | 23 | 0 | 0 | 1 | 0 | 25 |
| databases | 2 | 6 | 2 | 2 | 0 | 0 | 12 |
| distributed | 1 | 4 | 0 | 2 | 0 | 0 | 7 |
| ml | 9 | 35 | 2 | 7 | 0 | 0 | 53 |
| rust | 9 | 19 | 2 | 1 | 1 | 1 | 33 |
| security | 6 | 5 | 1 | 4 | 0 | 1 | 17 |
| software-engineering | 0 | 3 | 0 | 0 | 0 | 0 | 3 |

## Effect on the benchmark runs

“Found misses recovered” counts original `found=false` rows where an audited extra parent appears in a captured tool output. “Cited misses recovered” counts original `cited=false` rows whose `cited_ids` resolve to an audited extra parent. These count miss rows, not chunks. Qwen parent-level call logs make its found recoveries exact. Gemma’s run records have empty `calls` arrays and no corresponding call-log files, so only extra-parent citations prove a found recovery; additional found recoveries are unknown. Cited counts are exact. This is the add-only effect; correcting false positives, rewriting, or dropping questions is not included.

| Arm | Model | Found misses recovered | Cited misses recovered | Original found | Revised found | Original cited | Revised cited |
|---|---|---:|---:|---:|---:|---:|---:|
| A0 | Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B | 2 (exact) | 7 | 132/150 | 134/150 | 120/150 | 127/150 |
| A0 | gemma-4-12B-it-qat-OptiQ-4bit | 2 confirmed; +0–18 unobserved | 5 | 118/150 | 120–138/150 | 114/150 | 119/150 |
| A1 | Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B | 5 (exact) | 10 | 134/150 | 139/150 | 126/150 | 136/150 |
| A1 | gemma-4-12B-it-qat-OptiQ-4bit | 2 confirmed; +0–11 unobserved | 3 | 130/150 | 132–143/150 | 126/150 | 129/150 |

Across Qwen, relabeling raises A0 found/cited from 132/120 to 134/127 and A1 from 134/126 to 139/136. Across Gemma, cited rises from 114/126 to 119/129; found is at least 120/132 and could be as high as 138/143 if every unobserved extra parent was in a tool output.

## New-books specificity

Each n000–n029 JSONL note states whether its question is specific to the source example/method or broadly answerable across books. General RAG, embeddings, annotation, interpretability, PSO, DevOps, and floating-point questions have direct alternatives. Named API calls, niche methods, exact benchmark results, and particular source scenarios are more distinctive. n015 is unanswerable as written because the source explicitly declines to resolve responsibility; n025’s selected passage is a multiple-choice prompt with no answer, so its positive label is wrong.

## Could mislabelling favor one arm?

Yes. For Qwen, adding positives recovers 2 A0 versus 5 A1 found misses, and 7 versus 10 cited misses. The old labels therefore penalize A1 by 3 more misses on both measures and make A0 look better by that amount. For Gemma, cited recoveries are 5 for A0 versus 3 for A1, so the old labels make A1 look better by 2 cited misses on these rows. Gemma found asymmetry cannot be determined: both arms have 2 citation-confirmed recoveries, with 18 additional A0 and 11 additional A1 found misses whose tool outputs were not captured. The label changes are arm-neutral; the differential comes from the arms retrieving different parents.

## Ranked fixes

1. **Add answer-bearing parents where runs already show a measurable cost.** The changes recover **25 cited misses across four model/arm runs**. Prioritize h0180 (3 cited recoveries), then h0003, h0060, h0201, h0246, and n005 (2 each), followed by the 12 one-recovery qids. Among Qwen runs this also recovers 2 found misses in A0 and 5 in A1; Gemma has 4 citation-confirmed found recoveries and 29 additional unobserved cases.

2. **Correct wrong positives.** Remove or replace the **15 wrong-positive labels across 10 questions**, especially h0060, h0159, h0290, h0312, h0316, h0318, h0367, h0396, and n025. Rewrite h0396 to ask for `unsized_iter!` or drop it; the corpus documents that macro, not the asked `sized_iter!` symbol.

3. **Rewrite or drop under-specified questions.** Resolve product/version/workload or requested-target context for the 16 ambiguous and 2 unanswerable rows, including h0027, h0052, h0073, h0090, h0116, h0129, h0153, h0158, h0259, h0305, h0326, and n015. Rewrite h0031 so it does not include the vulnerable origin-check pattern and exploit clue in the question itself.

4. **Handle new-books labels according to specificity.** Use each row’s specificity note: retain exact API, benchmark-result, or source-example questions with their source; accept equivalent cross-book parents for generic concepts or rewrite them to ask for a source-unique detail.

## Row-level decisions

See `golden-audit.jsonl` for every qid, extra/wrong parent IDs, confidence, and passage-level evidence.

## Stage 1 verdict under the audited labels

The Gemma call logs are in the arm worktrees (`kb-bench-A0/`, `kb-bench-A1/` under `data/bench/calls/`), so found can be recomputed for both models. `scripts/bench_relabel.py` scores A0 and A1 three ways: the original labels, the audited labels (wrong positives removed, extra positives added), and the audited labels with the 20 ambiguous, unanswerable and leaky questions dropped. Found uses every parent id in the arm's call log, which includes retried attempts, so it can overcount by a row or two; cited uses the stored answer and is exact.

| Labels | n per model | Pooled found, A0-only / A1-only | p | Pooled cited, A0-only / A1-only | p |
|---|---:|---:|---:|---:|---:|
| original | 150 | 14 / 26 | 0.081 | 20 / 38 | 0.025 |
| audited | 150 | 12 / 25 | 0.047 | 15 / 33 | 0.013 |
| audited, 20 bad questions dropped | 130 | 9 / 21 | 0.043 | 11 / 28 | 0.009 |

The Stage 1 decision does not change: cited improves significantly under every label set, and nothing gets worse. (The original-label found p here is 0.081 rather than the recorded 0.044 because this script ORs the stored flag with call-log parents, which adds retried attempts.)

A spot check of three missing-positive verdicts found the extra parents correct in two and one borderline: for h0133, `moderntimeseriesforecastingwithpython_secondedition-p329` describes intervals adapting over time, not per data group. The extra labels lean generous.
