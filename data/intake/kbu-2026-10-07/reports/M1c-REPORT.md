# M1c — carry PostgreSQL labels to the current corpus and re-gate

Owner: Huy. Run: kbu-2026-10-07. Mapping: 2026-10-14. Execution on the central processing unit (CPU) spans 2026-10-14 and 2026-10-15. A parent chunk is the larger document passage returned by retrieval. A label names a parent and assigns a relevance grade. An embedding is a numeric representation of text. The candidate collection, a named embedding index in the Qdrant database, is kbu_m1_gemma768_cur. The control is developer_knowledge_v10.

## Label mapping

Old passage text comes from the frozen v10 payloads, the stored text and metadata for indexed records. Current text comes from the exact PostgreSQL chunk snapshot used for M1b. Its SHA-256 file fingerprint is 0131bd41f39e35bcf890fa01faa00b326cf373de055d5c78e4baac4d4134442c. The frozen payload fingerprint is 465ee1010e58e100ac5dd82316b57c3147b2826d17546e2a4a31f5365c86ea7c. The source repository and its benchmark files were read only. Remapped label files exist in the private M1/m1c copy on bppc and in [labels/](labels/). No collection data was written by this unit.

Matching uses literal tokens, separated by whitespace. Unicode compatibility forms, dash glyphs, dash-only table rules and line-wrap hyphens are normalized; case and other punctuation remain. A collapsed hyphen wrap is joined only when exactly one literal joined form occurs in the current book. Parent-local runs of at least eight identical tokens locate a passage; shorter identical blocks count only between those anchors. The overlap ratio is matched old token positions divided by all normalized old tokens. Overlapping chunk text is counted once. Adjacent current parents may jointly cover a split passage; every final target must add at least eight unique old tokens, and pruning cannot leave gaps. Competing non-subset eligible windows are ambiguous and unmapped. No embedding, heading, query wording, semantic similarity or relevance judgment chooses the mapping.

The 80% requirement is applied to combined coverage for split passages, following the instruction to map a split to all of its current parents. The maximum coverage in a single parent is also shown. p101 and p65 qualify only under combined coverage. Each target receives exactly the old grade; no new grade is judged. There are 0 conflicting-grade collisions. The predetermined collision rule is the maximum old grade.

| old ID | old heading(s) | new IDs and heading(s) | matched / old tokens | combined overlap | maximum single-parent overlap | affected queries |
|---|---|---|---:|---:|---:|---|
| postgresql-14-internals-p42 | 10 Write-Ahead Log (part 4) | p66: Introduction > Vacuum and Autovacuum > Autovacuum in Action (part 16)<br>p67: Introduction > Vacuum and Autovacuum > Autovacuum in Action (part 17) | 1188/1357 | 0.8754605747973471 | 0.8275607958732498 | hard[109], easy[109] |
| postgresql-14-internals-p44 | 11 WAL Modes (part 1) | p68: Introduction > Vacuum and Autovacuum > Autovacuum in Action (part 18)<br>p69: Introduction > Vacuum and Autovacuum > Autovacuum in Action (part 19) | 1233/1326 | 0.9298642533936652 | 0.8107088989441931 | hard[52] |
| postgresql-14-internals-p64 | 16 Query Execution Stages (part 2) | p96: Part IV Query Execution > Query Execution Stages > Transformation<br>p97: Part IV Query Execution > Query Execution Stages > Planning (part 1) | 1177/1304 | 0.9026073619631901 | 0.8611963190184049 | hard[159] |
| postgresql-14-internals-p65 | 16 Query Execution Stages (part 3) | p97: Part IV Query Execution > Query Execution Stages > Planning (part 1)<br>p98: Part IV Query Execution > Query Execution Stages > Planning (part 2)<br>p99: Part IV Query Execution > Query Execution Stages > Execution | 1283/1358 | 0.9447717231222386 | 0.5486008836524301 | hard[159], easy[160] |
| postgresql-14-internals-p81 | 19 Index Access Methods (part 3) | p128: Part IV Query Execution > Table Access Methods > Cost Estimation (part 7)<br>p129: Part IV Query Execution > Table Access Methods > Cost Estimation (part 8)<br>p130: Part IV Query Execution > Table Access Methods > Cost Estimation (part 9) | 974/1038 | 0.9383429672447013 | 0.8921001926782274 | hard[114], easy[114] |
| postgresql-14-internals-p101 | 23 Sorting and Merging (part 2) | p147: Part IV Query Execution > Table Access Methods > Bitmap Scans (part 13)<br>p148: Part IV Query Execution > Table Access Methods > Bitmap Scans (part 14) | 998/1066 | 0.9362101313320825 | 0.7579737335834896 | hard[326] |
| postgresql-14-internals-p113 | 25 B-tree (part 5) | p175: Part V Types of Indexes > B-tree > Multicolumn Indexes and Sorting (part 1)<br>p176: Part V Types of Indexes > B-tree > Multicolumn Indexes and Sorting (part 2) | 790/807 | 0.9789343246592317 | 0.8711276332094176 | hard[60], easy[60] |
| postgresql-14-internals-p139 | 29 BRIN (part 6) | p212: Part V Types of Indexes > B-tree > Indexing JSON (part 7)<br>p213: Part V Types of Indexes > B-tree > Indexing JSON (part 8) | 1260/1315 | 0.9581749049429658 | 0.8813688212927757 | hard[288] |
| postgresql-14-internals-p140 | 29 BRIN (part 7) | **unmapped** | 72/765 | 0.09411764705882353 | 0.09411764705882353 | hard[288] |

All abbreviated new IDs above have the prefix postgresql-14-internals-. Query indices are zero-based positions in the unchanged files. Full block positions, exact-block fingerprints, target text fingerprints, grades and alternative windows are in [mapping.json](mapping.json).

p140 has no qualifying current passage: 72/765 old tokens, ratio 0.09411764705882353. Its label is marked unmapped and omitted from the candidate grade map for hard[288]; that query retains p139’s mapped positives. The CPU control keeps all original labels. Nothing is guessed. 7 hard queries and 4 easy queries change; 0 sanity queries change. Every query retains at least one positive, so no query is silently skipped.

Affected query texts and grades:

| set[index] | query | old parent and grade |
|---|---|---|
| easy[60] | How can I use multiple index scans on distinct values of the first column to simulate an index-only search on a non-leading column in PostgreSQL? | postgresql-14-internals-p113: 2 |
| easy[109] | How can I disable WAL file recycling in PostgreSQL to prevent renaming instead of deleting old WAL segments? | postgresql-14-internals-p42: 2 |
| easy[114] | How do I query which operator classes and operators support the less-than strategy for the integer data type in a B-tree index? | postgresql-14-internals-p81: 2 |
| easy[160] | How does PostgreSQL's query planner estimate the cost of a Sort node with a Nested Loop Left Join when sorting by c.relname? | postgresql-14-internals-p65: 2 |
| hard[52] | What kind of throughput and response times can I expect from a production-grade in-memory data store when running with full transaction safety guarantees? | postgresql-14-internals-p44: 1 |
| hard[60] | How can I make PostgreSQL avoid scanning the entire index when I only query the second column of a multi-column index, by breaking it into separate lookups for each unique value in the first column? | postgresql-14-internals-p113: 2 |
| hard[109] | Why does PostgreSQL keep renaming old WAL files instead of deleting them, and how can I force it to actually remove them to free up disk space? | postgresql-14-internals-p42: 2 |
| hard[114] | How can I find all the comparison operators that PostgreSQL uses internally for B-tree indexes when sorting integers with the less-than operation? | postgresql-14-internals-p81: 2 |
| hard[159] | Why does my query plan show a Sort step costing 21.03 after a Nested Loop Left Join, when I'm just ordering by a table name? | postgresql-14-internals-p64: 2, postgresql-14-internals-p65: 2 |
| hard[288] | which section covers Bloom filters in BRIN | postgresql-14-internals-p139: 2, postgresql-14-internals-p140: 1 |
| hard[326] | where is sorting explained in the documentation | postgresql-14-internals-p101: 2 |

Mapping took 2.81619887900888 seconds. The frozen mapping was settled before the primary gate. Independent review corrected duplicate ambiguity, redundant seed targets and pruning gaps; eleven literal-overlap tests and three pause-accounting tests pass. [REVIEW.md](REVIEW.md) records those checks.

## Gate results

Primary comparison: **developer_knowledge_v10 on CPU with original labels**, versus **kbu_m1_gemma768_cur on CPU with remapped labels**. The hard, easy and sanity query texts and order are unchanged: 438, 199 and 30 queries. Pipeline and evaluator fingerprints match the previous fresh v10 control. Search retains 50 embedding matches, 50 keyword matches, distribution-based score fusion (rescaling each score distribution before combining lists), the Ettin reranker (scoring query and passage together), at most ten distinct parents, score floor 4 and at least three results when available. There is no generated hypothetical passage.

NDCG@10 is normalized discounted cumulative gain at ten: relevant parents rank higher, with gain 2^grade−1, divided by the best possible ordering of all positive parents. Expanding a split label to multiple parents therefore changes its ideal denominator. Recall@10 here is the fraction of queries with at least one labelled positive among the delivered results. Differences are candidate minus control. Full precision is recomputed from saved rankings and the correct arm’s labels; the evaluator’s rounded aggregates do not decide the verdict. Easy results are informational.

| set | metric | developer_knowledge_v10 CPU control | candidate | difference |
|---|---|---:|---:|---:|
| hard | NDCG@10 | 0.7391322287126778 | 0.7356808175821504 | -0.003451411130527382 |
| hard | recall@10 | 0.952054794520548 | 0.952054794520548 | 0.0 |
| easy | NDCG@10 | 0.9044205070280983 | 0.8992209798391756 | -0.005199527188922692 |
| easy | recall@10 | 1.0 | 1.0 | 0.0 |
| sanity | NDCG@10 | 0.6462904117686469 | 0.64736407080551 | 0.0010736590368630727 |
| sanity | recall@10 | 0.9333333333333333 | 0.9333333333333333 | 0.0 |

The five-query CPU pilots measured mean complete-query times of 6.687066082601087 seconds for the candidate and 6.713378677802393 seconds for v10. Inference from those measurements: required-work completion 9272.198747722525 active seconds; all six arm/set runs 10929.562464939272 active seconds. The 10,800-second budget initially selected the user-authorized hard-only CPU-control fallback, with candidate easy and sanity still required. The remaining-time recheck, when present below, records the final optional-control decision.

On 2026-10-15 Huy required every remaining CPU arm and set. The resumed run retained 431 candidate hard and 5 control hard checkpoints. Its initial all-six completion forecast was 10609.853038562764 active seconds, an inference. This instruction supersedes the earlier optional-control fallback. All workers are restricted to logical CPU cores numbered 0–7; the concurrent M4 job on cores 8–31 is untouched. Cached progress is monotonic in the controller forecast; replay never resets the validated finished-query count.


Control easy initially stopped at ten queries because their mean 9.767010099996696 seconds projected 11289.27830151796 active seconds. The first five queries were slower; their cause is not found. A bounded ten-query continuation averaged 7.028965288298787 seconds. At 9234.215573310852 active seconds, the remaining 209 queries plus 60 seconds projected 10763.269318565299 seconds, an inference below the unchanged 10,800-second cap. The resumed controller uses the latest ten measured durations for remaining-work forecasts. The gate, labels, scores, thresholds and resource limits are unchanged.


Secondary information only: M1’s earlier GPU control, developer_knowledge_v10, with original labels. GPU means graphics processing unit. These measurements are not the primary matched-hardware comparison.

| set | metric | developer_knowledge_v10 GPU control | candidate CPU | difference |
|---|---|---:|---:|---:|
| hard | NDCG@10 | 0.7392807563384192 | 0.7356808175821504 | -0.003599938756268739 |
| hard | recall@10 | 0.952054794520548 | 0.952054794520548 | 0.0 |
| easy | NDCG@10 | 0.9044205070280983 | 0.8992209798391756 | -0.005199527188922692 |
| easy | recall@10 | 1.0 | 1.0 | 0.0 |
| sanity | NDCG@10 | 0.6462904117686469 | 0.64736407080551 | 0.0010736590368630727 |
| sanity | recall@10 | 0.9333333333333333 | 0.9333333333333333 | 0.0 |

Hard subgroup split. Touched means a query originally labelled one of the nine transferred parents. Hit counts use each arm’s corresponding labels.

| subgroup | queries | CPU v10 hits | candidate hits | GPU v10 hits | CPU v10 NDCG@10 | candidate NDCG@10 |
|---|---:|---:|---:|---:|---:|---:|
| touched | 7 | 5 | 6 | 5 | 0.5138607587644363 | 0.5434473272911743 |
| untouched | 431 | 412 | 411 | 412 | 0.7427909300807467 | 0.738802939234208 |

CPU is the central processing unit. All model workers use logical CPU cores numbered 0–7 and eight compute threads, with one inter-operation thread, which schedules parallel operations. CUDA, NVIDIA’s GPU interface, is hidden and initialization is forbidden. The loaded Gemma model reports torch.float32, the loaded Jina model reports torch.bfloat16, and both rerankers report torch.float32. These are the number representations reported by the loaded models, not a measurement of the returned vector format. The pinned loaders are unchanged; execution hardware is CPU for both. No Mac model or Mac timing is used.

Highest sampled owned-worker plus entire Qdrant resident memory (memory held in RAM): 8333729792 bytes. The supervisor samples every 0.5 seconds, enforces an 18,000,000,000-byte combined guard and a 12,000,000,000-byte per-worker address-space limit, kills only the owned worker group on a breach or monitoring failure, and enforces 10,800 active seconds. This is a sampled safeguard, not a hard instantaneous cap on database or unrelated-session RAM. Recorded active elapsed time at the last supervised stage: 10636.43337392807 seconds. [gate/](gate/) retains each resource record.
All six CPU runs completed. The final stage finished at 2026-10-15T20:38:57.904551+07:00 (Indochina Time), before the scheduled 2026-10-16 10:00 restart.


Actual PAUSE/resume events: 1. Credited pause seconds: 93805.2487809658. The coordinator cleared the real marker and Huy explicitly resumed this run on 2026-10-15 after the earlier controller had stopped. The controller checks the Mac marker at every new-query boundary, saves completed full/ceiling searches, releases the model process during a pause, persists its start and ID, polls every 60 seconds for at most 12 hours, then resumes from checkpoints. A controlled pilot stopped after two completed queries; restart reused two and computed three. [RUNBOOK.md](RUNBOOK.md) describes resumption and the explicit pilot-cache provenance migration.

## Verdict

**kbu_m1_gemma768_cur: PASS.**

- hard NDCG@10 drop: 0.003451411130527382; required ≤ 0.010; PASS.

- hard recall@10 drop: 0.0; required ≤ 0.005; PASS.

- candidate sanity recall@10: 0.9333333333333333; required ≥ 0.80; PASS.

Read-only final checks confirm unchanged point counts, configurations and payload schemas for both existing collections, and unchanged bppc aliases. No collection or alias was promoted. These checks do not claim an exhaustive database-content fingerprint; the M1b payload/vector audit supplies the current-corpus provenance.

Local `bash verify.sh`: PASS. The Mac’s live developer_knowledge alias remains developer_knowledge_v10. This acceptance checks report structure and the protected alias; the experiment verdict above is separate.

## Output sample

Actual output produced or read during this run, 2026-10-14 through 2026-10-15:

```text
TEXT_MAP {"old_id": "postgresql-14-internals-p101", "status": "mapped", "new_ids": ["postgresql-14-internals-p147", "postgresql-14-internals-p148"], "coverage_ratio": 0.9362101313320825, "max_single_parent_ratio": 0.7579737335834896, "old_tokens": 1066, "matched_old_tokens": 998}
TEXT_MAP {"old_id": "postgresql-14-internals-p113", "status": "mapped", "new_ids": ["postgresql-14-internals-p175", "postgresql-14-internals-p176"], "coverage_ratio": 0.9789343246592317, "max_single_parent_ratio": 0.8711276332094176, "old_tokens": 807, "matched_old_tokens": 790}
TEXT_MAP {"old_id": "postgresql-14-internals-p139", "status": "mapped", "new_ids": ["postgresql-14-internals-p212", "postgresql-14-internals-p213"], "coverage_ratio": 0.9581749049429658, "max_single_parent_ratio": 0.8813688212927757, "old_tokens": 1315, "matched_old_tokens": 1260}
TEXT_MAP {"old_id": "postgresql-14-internals-p140", "status": "unmapped", "new_ids": [], "coverage_ratio": 0.09411764705882353, "max_single_parent_ratio": 0.09411764705882353, "old_tokens": 765, "matched_old_tokens": 72}
TEXT_MAP {"old_id": "postgresql-14-internals-p42", "status": "mapped", "new_ids": ["postgresql-14-internals-p66", "postgresql-14-internals-p67"], "coverage_ratio": 0.8754605747973471, "max_single_parent_ratio": 0.8275607958732498, "old_tokens": 1357, "matched_old_tokens": 1188}
GATE_VERDICT {"verdict": "PASS", "conditions": {"hard_ndcg_drop_lte_0.010": true, "hard_recall_drop_lte_0.005": true, "sanity_recall_gte_0.80": true}, "hard_ndcg_drop": 0.003451411130527382, "hard_recall_drop": 0.0, "sanity_recall10": 0.9333333333333333}
HARD_SUBGROUPS {"touched": {"queries": 7, "control_cpu": {"ndcg": 0.5138607587644363, "hits": 5, "recall10": 0.7142857142857143}, "candidate": {"ndcg": 0.5434473272911743, "hits": 6, "recall10": 0.8571428571428571}, "control_gpu": {"ndcg": 0.5138607587644363, "hits": 5, "recall10": 0.7142857142857143}}, "untouched": {"queries": 431, "control_cpu": {"ndcg": 0.7427909300807467, "hits": 412, "recall10": 0.9559164733178654}, "candidate": {"ndcg": 0.738802939234208, "hits": 411, "recall10": 0.9535962877030162}, "control_gpu": {"ndcg": 0.7429418699881126, "hits": 412, "recall10": 0.9559164733178654}}}
```

## Sources

- Huy’s M1c instructions, received 2026-10-14, and resume instruction received 2026-10-15: overlap threshold, grade transfer, fixed verdict, CPU limits, all six CPU arm/set runs and PAUSE protocol.

- [M1 REPORT.md](../M1/REPORT.md), run 2026-10-14: frozen v10 payload and fresh GPU-control provenance. Original payload source date: not found.

- [M1b REPORT.md](../M1b/REPORT.md), run 2026-10-14: current-file collection audit and the prior result with stale labels. The current PostgreSQL file was checked against that snapshot on 2026-10-14.

- [mapping.json](mapping.json) and [labels/](labels/), generated 2026-10-14: normalized literal overlaps, exact-block hashes, original/remapped query file fingerprints and full grade mappings.

- [Original private evaluator](../M1/private-code/eval_retrieval.py) and [embedder](../M1/private-code/embedder.py), read 2026-10-14; original source date: not found. Their fingerprints match the original fresh control. [scripts/](scripts/) holds the observation, checkpoint and supervisor code.

- [gate/decision.json](gate/decision.json), [gate/final-state.json](gate/final-state.json), per-set JSON/JSONL/metadata and resource records, generated 2026-10-14 through 2026-10-15: measured results and read-only protection checks.

- [REVIEW.md](REVIEW.md), [RUNBOOK.md](RUNBOOK.md), tests and controller logs, generated 2026-10-14 through 2026-10-15: validation, execution boundaries and resume evidence.

All technical claims above are local code observations or measurements from this run. No external factual claim requires a web source. Forecasts are explicitly marked as inferences.
