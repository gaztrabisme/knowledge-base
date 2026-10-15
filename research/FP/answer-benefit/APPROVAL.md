# Gary's approval sheet — FP answer benefit (AB0f)

**Pending; no run authorized.** The coordinator reads this sheet and the
[full plan](PLAN.md) in full. This unit edits the plan only. Product approval
does not approve this study.

An **arm** is a tool configuration: ordinary search and source reads (**control**),
or those plus graph and coverage tools (**treatment**). Both use the same sources, answer model and common
instructions. A **supported answer** is correct, complete and backed by source
spans that open and contain its claims. It earns 1; other answers earn 0. A
properly evidenced “unknown” can earn 1 when the question calls for it.

Your remaining decisions are:

| Decision | Recommendation / approval needed |
|---|---|
| **Choose the answer model** | Swift 1.5 on bppc, with its checkpoint (saved model version) and compute window confirmed, or another local model. Its model family (lineage) must differ from both Claude and GPT. Recommend temperature 0 (least random), seed 42 (repeatability, if supported) and a 1,024-token answer limit (tokens are text units). Freeze supported settings. |
| **Set the lookup-harm allowance** | Recommend **0 supported lookup answers lost out of 24**; choose 0–24 before answers. A loss means control earns 1 and treatment 0. Gains never cancel losses; passing does not prove zero future harm. |
| **Accept the model-reviewer rule** | Fable 5.1 selects sources and writes questions/labels (expected claims and evidence); Codex Astra checks every label. Both independently score all 192 answers with arm, answer-model and tool identities hidden. For disputes, each sees the other's claim notes and re-grades once, still blind. Remaining disagreement earns **0 in both analyses**. Report agreement before/after. Your audits are optional. |
| **Approve the final freeze packet** | A freeze packet is the complete, fixed study record. Approve its composition, shortfalls and **manifest** (file inventory and fingerprints): model and command-line tool (CLI) versions, prompts (reviewer instructions), JSON output schemas (rules for machine-readable records), settings, checked labels and answer/reviewer family separation. Approve and register it before any answer. |

Fable proposes a topic and **14 works: 2 books, 2 courses, 8 papers and 2
repositories**, eligible only if in both the common frozen text collection and phase 2 catalog
(source inventory).
The target is **48 source units**, 12 per medium; a unit is a section, lesson,
paper span or file. v10 holds books; no real course or repository is archived yet.
If media are missing, Fable records the shortfall and proposes the closest feasible
composition for your freeze-packet decision. Diversity is never silently reduced;
changed counts require an approved matching plan/schema before freeze.

The **96 questions** comprise 24 each for lookup, relationships, coverage and gap
review. Labels precede every answer and receive independent source checks. Keep
test works separate from development. Group related works together; require
**at least 8 source groups**, each covering all four question classes.

Each arm gets **6,000 text evidence tokens**, **0 images**, **32 tool attempts**,
**600 seconds** and **0 retries** per question. The gateway (tool-access layer)
counts reads, metadata, errors and repeated text. Main benefit uses the 48 relationship/coverage
questions. Require a positive lower bound of a **95% confidence interval** (a
range expressing sampling uncertainty), from **10,000 draws of whole source
groups**, allowing groups to repeat, and lookup losses within your allowance. Both gates must also pass a
failure-conservative analysis: give control failures 1 and treatment failures 0,
then keep any remaining reviewer disagreement at 0. No failed pairs are dropped.
Other results describe findings without supporting extra benefit claims. Graph
correctness checks remain prerequisites.

Model reviewers replace human judgement. Two strong models can share a blind
spot that survives reconciliation. Any benefit claim must say **“under two
independent model reviewers.”** Your decision sets aside the design's
no-model-judge recommendation. This does not establish human agreement or
library-wide benefit.
