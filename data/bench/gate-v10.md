# Verdict: PASS

The v10 candidate passes all fixed gate conditions. Comparisons used the RTX 5080 on bppc, the same 50-candidate hybrid retrieval and reranking pipeline, and the same v9 hard and easy query files. The gate mirror held 286,723 v9 points and 330,778 v10 points; both collections were green.

| Condition | Threshold | v9 | v10 | Result | Status |
|---|---:|---:|---:|---:|---|
| Hard NDCG@10 drop | ≤ 0.010 | 0.7409 | 0.7393 | drop 0.0016 | **PASS** |
| Hard recall@10 drop | ≤ 0.005 | 0.9521 | 0.9521 | drop 0.0000 | **PASS** |
| New-doc sanity recall@10 | ≥ 0.80 | — | 28/30 = 0.9333 | 2 misses | **PASS** |

The paired easy-set comparison is informational: NDCG@10 0.9041 → 0.9044 (+0.0003); recall@10 1.0000 → 1.0000.

## Sanity misses

The 30-query plan, with each expected book and section, was written before retrieval results were viewed. Both misses appeared in fusion’s top 50 but fell outside the reranked top 10.

| Book | Expected section | Query |
|---|---|---|
| `web-dev-baseline` | Optimize Interaction to Next Paint | When optimizing INP, how can developers reduce the delay before an event handler begins running? |
| `whatwg-html` | The popover target attributes | How can a button declare which popover it controls in HTML, including the relationship used to invoke it? |

## Paired significance

`scripts/significance.py` paired all 438 hard queries and 199 easy queries. Hard NDCG@10 delta (v10 − v9) was −0.0017 from rounded per-query scores (95% paired bootstrap CI [−0.0035, −0.0002], sign-test p=0.8238, Wilcoxon p=0.1044); the script classifies it as noise under its CI-plus-test rule. Hard recall had zero paired changes. Easy NDCG delta was +0.0004 (95% CI [0.0000, +0.0011], sign-test and Wilcoxon p=1.0000); easy recall had zero changes.

## Files

- Blind query and section plan: `data/bench/gate-v10/sanity-plan.jsonl`
- Labeled sanity inputs: `data/bench/gate-v10/sanity.jsonl`
- Aggregate JSON: `data/bench/gate-v10/aggregate/`
- Paired per-query output and retrieved candidates: `data/bench/gate-v10/per-query/`
- Logs: `data/bench/gate-v10/logs/`
- Parent-map preparation record: `data/intake/v10-gate-parent-map.json`
