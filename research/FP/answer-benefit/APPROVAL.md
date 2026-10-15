# Gary's approval sheet — FP answer benefit

**Pending; no run authorized.** Approve the [full plan](PLAN.md) before answers;
the coordinator reads both documents in full first. Later approve the completed
freeze packet before calls. Product approval does not cover this plan.

An **arm** is a tool configuration: ordinary search/reads, or those plus
graph/coverage. Both use identical sources, model and common instructions.
**Supported** means correct, complete and cited to source spans that open and
contain the claims: credit **1**. Partial, wrong, unsupported and unjustifiably abstained
answers earn **0**. Required, evidenced “unknown” can earn 1.

Approve these recommendations or record replacements before answers:

| Decision | Recommendation |
|---|---|
| **Choose domain/sources** | **48 units** (sections, lessons, spans or files), **12 per medium**, from **2 books, 2 courses, 8 papers, 2 repositories**. Both arms read the same snapshot; approve supplements explicitly. Separate test works from tuning and prior M3 exposure. |
| Questions/labels | **96: 24 lookup, 24 relational, 24 coverage, 24 gap-review**. Coverage: **12 present + 12 checked no-support**. You curate source labels; appoint an independent checker; settle disagreements before answers. |
| **Name reviewers** | **Two independent human scorers**, arm identities hidden; you resolve disagreements. Name curator, checker and scorers. No model judge. |
| **Choose local model** | **Swift 1.5 on bppc**, if you confirm its exact model version and later compute window, or another local model. Pin software and chat template; no fallback. |
| Evidence cap | **6,000 text tokens per question/arm**, counting all gateway reads, metadata, errors and repeats. A token is a counter's text unit: **tiktoken 0.14.0 / cl100k_base**, pinned vocabulary fingerprint. Formatting rule: **gateway-content-text+canonical-tool-metadata/v1**. Fixed instructions/answers are outside it. **0 images**; no unmetered files, writes or live memory. |
| Execution | **1 attempt per question/arm = 192**; temperature **0** (least random); maximum **1,024 answer tokens, 32 tool calls, 600 seconds per arm, 0 retries**. Order seed **42**; model seed 42 if supported. Freeze prompts, tool lists and software settings. |
| Main benefit | Use **48 relational + coverage** questions. The **paired difference** is treatment minus control credit on each question. A **confidence interval** expresses sampling uncertainty. Require its **two-sided 95% lower bound above 0**, also with control failures credited 1/treatment failures 0. |
| Uncertainty | Use **10,000 bootstrap draws**, seed **42**: sample whole source groups with replacement, keeping pairs together. Prefer **14 groups**; require **at least 8**, each covering all classes. Related/cross-dependent sources stay together. Sorted ranks **250 and 9,750**, without averaging between ranks; pin Python version. No library-wide or rare-error safety claim. |
| **Set lookup-harm allowance** | Recommend **0 supported answers lost out of 24**; choose **0–24** before answers. Gains never cancel losses. Report both and a 95% harm interval, also under conservative failure scoring. Passing does not prove zero future harm. |
| Other results/failures | Report **24 gap-review**, combined **72 benefit-oriented**, class and medium results descriptively. Only one superiority claim; other intervals are not jointly 95%. Failed/missing answers score 0; no deletions. Unresolved grades, accounting violations or changed snapshots invalidate the claim. |
| Separate prerequisites | Graph unit owns **0/12 false absences, 12/12 correct unknowns** on **12 derived incomplete-scope fixtures**, **0 invalid locators**, and no silent truncation. These add no answer questions. **C118 visual benefit needs a separate plan.** |

**Record:** domain/sources, model version, reviewer names, lookup-loss allowance
and acceptance of these rules/numbers. Freeze exact file fingerprints using
SHA-256 and approve the final packet. Register the **manifest digest** (fingerprint
of the frozen-file inventory) and approval time before calls. Changes after
answers invalidate the claim. No unset choices. AB0 supplies only the plan,
schema and offline validator.
