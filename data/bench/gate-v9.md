# Verdict: FAIL

Reader: Gary. `developer_knowledge_v9` fails the fixed gate because sanity recall@10 is below its threshold. The two hard-set conditions pass.

| Condition | Threshold | Result | Status |
|---|---:|---:|---|
| Hard NDCG@10 drop vs v8 | ≤ 0.010 | 0.742890 → 0.740932 (drop 0.001958) | **PASS** |
| Hard recall@10 drop vs v8 | ≤ 0.005 | 0.952055 → 0.952055 (drop 0.000000) | **PASS** |
| Sanity recall@10 on new books | ≥ 0.80 | 0.793103 (23/29; 24 hits required) | **FAIL** |

## Run and numbers

The 438-query hard set and 199-query easy set were run against both collections on bppc’s NVIDIA RTX 5080. The 29-query sanity set covers all 29 manifest ingest books and was run against v9. `KB_COLLECTION` selected each collection explicitly; Qdrant was queried read-only. The verified point counts were 266,647 for v8 and 286,723 for v9.

| Set | Metric | v8 | v9 | v9 − v8 |
|---|---|---:|---:|---:|
| Hard (438) | NDCG@10 | 0.7429 | 0.7409 | −0.0020 |
|  | Recall@10 | 0.9521 | 0.9521 | 0.0000 |
|  | MRR | 0.8324 | 0.8307 | −0.0017 |
|  | Ceiling (recall@50) | 0.9749 | 0.9749 | 0.0000 |
| Easy (199) | NDCG@10 | 0.9043 | 0.9044 | +0.0001 |
|  | Recall@10 | 1.0000 | 1.0000 | 0.0000 |
|  | MRR | 0.9639 | 0.9664 | +0.0025 |
|  | Ceiling (recall@50) | 1.0000 | 1.0000 | 0.0000 |
| Sanity (29) | Recall@10 | n/a | 0.7931 (23/29) | n/a |
|  | NDCG@10 | n/a | 0.6000 | n/a |

The v8 hard rerun reproduces the gate-v8 values. Its easy NDCG@10 rerun is 0.9043, compared with 0.9042 in gate-v8; the paired comparison uses this same-session v8 result.

## Paired significance

`scripts/significance.py` paired all 438 hard queries. For NDCG@10, v9 − v8 is −0.00196 with paired bootstrap 95% CI [−0.0043, −0.0002], sign-test p=0.0923, and Wilcoxon p=0.0360. The script classifies this delta as **significant** under its CI-plus-test rule. Hard recall has zero paired changes. On the easy set, the NDCG@10 delta is +0.00009 with 95% CI [−0.0006, +0.0009], sign-test p=0.6250 and Wilcoxon p=0.8551; the script classifies it as not significant.

## Hard-set regression breakdown

Counts use per-query NDCG@10: **10 regressed, 3 improved, 425 unchanged**. The table lists the ten largest NDCG drops. A displacer is the highest-ranked v9 non-positive top-10 result that moved from below or outside the v8 ranking to above a labeled parent. “New v9 book?” checks the displacer slug against the 29 manifest ingest slugs. Ranks shown are first-hit ranks; NDCG includes every labeled parent.

| Hard query | NDCG@10 v8 → v9 | First-hit rank v8 → v9 | Displacing passage book (parent) | New v9 book? |
|---|---:|---:|---|---|
| Why does my Docker image metadata show the wrong CPU architecture and missing environment variables when I inspect it? | 1.000000 → 0.630930 | 1 → 2 | `container-security` (`container-security-p42`) | Yes |
| What are the current minimum recommended settings for hashing passwords with different algorithms, specifically how many iterations for older methods and how much memory for newer ones? | 0.243360 → 0.073277 | 3 → 3 | `practical-cloud-security` (`practical-cloud-security-p32`) | Yes |
| Why do older machine learning models like logistic regression and SVMs still get used in production even though deep learning is more powerful? | 0.630930 → 0.500000 | 2 → 3 | `python-for-devops` (`python-for-devops-p211`) | Yes |
| `string.punctuation` | 0.639909 → 0.521296 | 2 → 2 | `hands-on-large-language-models` (`hands-on-large-language-models-p146`) | No |
| Why are my error messages not showing up in my application log file even though I'm using the standard logging setup? | 0.430677 → 0.356207 | 4 → 6 | `python-for-devops` (`python-for-devops-p103`) | Yes |
| gram-schmidt process discord | 0.866307 → 0.794323 | 1 → 1 | None; the adaptive cutoff omitted a labeled parent without a replacement moving ahead | n/a |
| where is the References section | 0.342222 → 0.321245 | 2 → 2 | `research-methods-psychology` (`research-methods-psychology-p220`) | Yes |
| How do I check that my application is actually encrypting data while it's being processed in RAM, not just at rest or in transit, so that other processes or users on the same machine can't read it? | 0.963940 → 0.944848 | 1 → 1 | `practical-cloud-security` (`practical-cloud-security-p11`) | Yes |
| Why does my document processing tool have ready-made templates for pulling data from things like bills, payment slips, and driver's licenses? | 0.944848 → 0.932778 | 1 → 1 | `training-data-for-machine-learning` (`training-data-for-machine-learning-p103`) | No |
| risk mitigation strategies | 0.536404 → 0.528572 | 1 → 1 | `pmbok-guide-7e` (`pmbok-guide-7e-p112`) | Yes |

## Files

- Sanity queries and labels: `data/bench/gate-v9/sanity.jsonl`
- Paired per-query results: `data/bench/gate-v9/gate-v9-v8-hard-per-query.jsonl`, `gate-v9-v9-hard-per-query.jsonl`, `gate-v9-v8-easy-per-query.jsonl`, and `gate-v9-v9-easy-per-query.jsonl`; v9 sanity: `data/bench/gate-v9/gate-v9-v9-sanity-per-query.jsonl`
- Aggregate run JSON and console logs: `data/bench/gate-v9/aggregate/` and `data/bench/gate-v9/logs/`
- Paired significance output: `data/bench/gate-v9/significance-hard.txt` and `data/bench/gate-v9/significance-easy.txt`
- Regression calculations: `data/bench/gate-v9/analyze.py` and `data/bench/gate-v9/analysis-summary.json`
- Inputs: hard set `data/golden/golden_queries_hard.jsonl`; easy set `data/golden/golden_queries.jsonl`; retrieval harness `scripts/eval_retrieval.py`; significance harness `scripts/significance.py`


## Reviewed sanity set

The pre-set verdict stands: v9 failed the gate under the conditions set before that run. The reviewed-set result is reported beside the original and does not replace it, because the queries were reviewed after the original result was known, although the reviewer was not told which queries missed.

The review ran on the Gemini lane (`gemini-3.8-flash-high`), a different model family from the Codex session that wrote the queries, and was blind to retrieval outcomes: its workspace held only the queries and the 29 books' chunk files, and its brief did not say which queries missed. The reviewer applied four rules: (1) on-topic — the query asks about a core subject of the book; (2) self-contained — it makes sense without an unstated scenario or passage-specific anecdote; (3) label answers — the labeled text contains the substantive answer, not just related material or headers; and (4) label complete — the positive IDs include all passages in the book that answer as well or better.
Both Mac evaluations used v9 with 50 candidates and reranking enabled.

| Set | Queries | Recall@10 | NDCG@10 |
|---|---:|---:|---:|
| Original on bppc (preset gate) | 29 | 0.793 (23/29) | 0.600 |
| Original on the Mac | 29 | 0.793 (23/29) | 0.605 |
| Reviewed on the Mac (drop removed) | 28 | 0.821 (23/28) | 0.639 |

The reviewed set has Recall@10 of 0.821 (23/28) and NDCG@10 of 0.639.

The table below shows each review change. Hit@10 is for the original and reviewed row on the Mac; a dropped row has no reviewed result.

| Book | Verdict | Old → new query or label (short) | Hit@10 before → after |
|---|---|---|---:|
| `pmbok-guide-7e` | fix-query | Airport retail-demand example → simulation for project complexity | 0 → 1 |
| `designing-ai-interfaces` | fix-label | `p47-c2` → `p47-c0` + `p47-c2` | 1 → 1 |
| `hbr-guide-business-writing` | drop | HR work-habits table fragment → dropped | 1 → dropped |
| `value-based-fees` | fix-label | `p76-c0` introduction → `p76-c1` substantive advice | 1 → 1 |

Of the six original bppc misses, the reviewer changed `pmbok-guide-7e` and kept `agentic-mesh`, `head-first-pmp`, `python-for-devops`, `selling-to-big-companies`, and `flawless-consulting-fieldbook-companion-2e` as fair queries. All five kept queries still miss on the reviewed Mac run; each is a retrieval miss.

The next table lists the per-query hit@10 results from both Mac runs. `1` means a positive parent appeared in the top 10; `0` means none did. The HBR row was dropped from the reviewed set.

| Book | Hit@10 original Mac | Hit@10 reviewed Mac |
|---|---:|---:|
| `pmbok-guide-7e` | 0 | 1 |
| `agentic-mesh` | 0 | 0 |
| `bargaining-for-advantage` | 1 | 1 |
| `container-security` | 1 | 1 |
| `critical-thinking-about-research` | 1 | 1 |
| `designing-ai-interfaces` | 1 | 1 |
| `flawless-consulting` | 1 | 1 |
| `getting-to-yes` | 1 | 1 |
| `hbr-guide-business-writing` | 1 | dropped |
| `hands-on-site-reliability-engineering` | 1 | 1 |
| `head-first-pmp` | 0 | 0 |
| `high-performance-browser-networking` | 1 | 1 |
| `how-to-read-a-paper` | 1 | 1 |
| `key-account-management` | 1 | 1 |
| `meddicc` | 1 | 1 |
| `practical-cloud-security` | 1 | 1 |
| `privacy-in-context` | 1 | 1 |
| `project-planning-scheduling-control` | 1 | 1 |
| `python-for-devops` | 0 | 0 |
| `real-world-software-development` | 1 | 1 |
| `research-ethics-integrity-social-scientists` | 1 | 1 |
| `research-methods-psychology` | 1 | 1 |
| `selling-to-big-companies` | 0 | 0 |
| `software-engineering-at-google` | 1 | 1 |
| `art-of-assembly-language` | 1 | 1 |
| `challenger-sale` | 1 | 1 |
| `flawless-consulting-fieldbook-companion-2e` | 0 | 0 |
| `new-ethics-of-journalism` | 1 | 1 |
| `value-based-fees` | 1 | 1 |

PMBOK diagnosis: [data/bench/gate-v9/pmbok-diagnosis.md](data/bench/gate-v9/pmbok-diagnosis.md).

A defect noted during diagnosis is that chunk heading paths repeat the `(part 1) (part 1)` suffix, generated by `knowledge_base/chunk.py`; it is not fixed here.
