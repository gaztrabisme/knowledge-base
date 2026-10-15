# AB0 — answer-benefit pre-registration

Status: AB0 plan-only deliverables complete; ready for coordinator review.
Gary has not approved this pre-registration. Row 12's experiment is not run.

## AB0f — model reviewer follow-up (2026-10-15)

Status: complete; plan edits only, ready for handoff. This section supersedes AB0's human-role
recommendations below; the earlier record remains historical.

- Read the five requested AB0 deliverables before editing; confirmed branch
  `unit/fp-AB0` at `a6aabff` with a clean working tree.
- Gary's decision: "You can replace human by Fable 5.1 subagent or Codex Astra subagent."
- Updating source curation, independent label checking, blind scoring and fixed
  disagreement handling to isolated Fable 5.1 and Codex Astra lanes.
- Retained the existing scope, evidence, held-out-source, statistical and freeze
  checks; the plan requires an explicit shortfall record for unavailable source
  media and Gary's final composition approval. No model calls, retrieval, GPU,
  bppc or oMLX use.
- PLAN.md now assigns source selection and all 96 labels to Fable, independent
  original/ledger checks to Astra, and all 192 blind answer grades to each lane.
  It fixes one reconciliation round, remaining disagreement credit 0 in both
  analyses, and agreement reporting. Shared model blind spots limit the claim
  to benefit "under two independent model reviewers".
- APPROVAL.md now has four human decisions: answer model, lookup-loss allowance,
  acceptance of the model-reviewer rule, and the final composition/manifest.
- Manifest v2 replaces human reviewer names/adjudicator with model-lane records,
  pinned prompt/output-schema artifacts, family separation evidence and the
  disagreement rule. Original counts, grouping, budget, approval, hash/path and
  chronology-binding checks remain. Alternate compositions still need explicit
  pre-results approval and matching plan/schema constants; they cannot pass by
  silently weakening the existing checks.
- Dev pattern: intrinsic-artifact gate, with direct document editing. Grounding:
  Gary's supplied AB0f decision and the five AB0 files; KB retrieval and additional
  model review were not run because this unit prohibits them. The report is the
  requested durable record; wiki edits are prohibited. Independent review remains
  a coordinator handoff, not a claimed model review in this unit.
- Test-first migration: the new model-lane fixture was rejected by the old
  identity logic as expected. After implementation, the self-test passes **66**
  offline synthetic checks (all 36 original checks, adapted identities, plus 30
  new reviewer checks). Rehashed schema/alias and external-symlink cases also
  assert the expected error path, rather than passing on configuration drift.
- Final acceptance command:
  `python3 research/FP/answer-benefit/validate_manifest.py --self-test` →
  `PASS: 66 offline synthetic manifest checks; no study answers or results created`.
- Independently checked the schema with installed `jsonschema` Draft 2020-12:
  schema validity, positive model-lane fixture, and three negative cases pass.
  This remains test-only; the delivered validator still uses only the stdlib.
- Compared the schema to `HEAD`: all original protocol fields outside reviewer
  and answer-model records, plus approval/attestation/artifact definitions, are
  unchanged. Python syntax, final newlines, trailing whitespace and
  `git diff --check` pass. APPROVAL.md is about one page (628 words).
- Completed the coordinator reread of **PLAN.md and APPROVAL.md in full** after
  final edits. Confirmed the four decisions, model-role assignments, source
  shortfall path, blind reconciliation, conservative-mask precedence and claim
  limitation agree across the documents, schema and validator.
- No commit, merge or push; no changes outside the five requested deliverables.

## Scope and safeguards

- Write the row 12 scoring plan, Gary approval summary, manifest schema and offline validator.
- Read the main-checkout design and cited evidence, frozen control, catalog, bench and gateway contracts.
- No answers, model calls, retrieval runs, GPU, bppc or oMLX use; no experiment results will be collected.
- No commit, merge or push. The coordinator reviews both documents in full and commits.

## Progress

- Created this report before authoring the deliverables.
- Read the main design's graph/coverage, tool/budget, measurement and open-choice
  sections; followed the P1, grounded, A1, R3 and final M3 evidence into the main
  checkout's intake and `reports/` directory.
- Inspected the frozen baseline/contract/read-metadata shapes, P2 catalog usage,
  bench question inventories and both retrieval/statistics scripts without
  importing or executing the retrieval harness.
- The requested gateway `git show` failed: `packages/gateway/README.md` is absent
  from `unit/fp-P4b` at the inspected commit `9911905`. Read the uncommitted P4b
  worktree README instead and corroborated counter/renderer strings in its
  tokenizer source. The later freeze must pin the accepted gateway revision.
- Drafted PLAN.md, APPROVAL.md, manifest.schema.json and the stdlib-only validator.
- First validator self-test passed 33 synthetic checks; added strict non-finite
  JSON checks for a final total of 36. Reviewed document/schema/validator
  consistency and kept the approval sheet to about one page (approximately 600 words).

## Validation

- `python3 research/FP/answer-benefit/validate_manifest.py --self-test` →
  `PASS: 36 offline synthetic manifest checks; no study answers or results created`.
  Temporary fixtures contain metadata only, not experiment answers.
- Independently checked the schema with installed `jsonschema`'s Draft 2020-12
  validator, a synthetic positive and three negative cases. This test-only package
  is not a runtime dependency of the delivered stdlib validator.
- Exercised the CLI: valid externally bound digest exits 0; wrong digest exits 1.
- JSON parsing, final newlines, trailing whitespace and `git diff --check` pass.
- Only the five requested deliverables are new. No tracked files were modified;
  no checker shell script, real freeze, questions, labels or results were created.
  No model/service, GPU, remote host, retrieval harness, commit, merge or push ran.

## Handoff

Delivered:

- `research/FP/answer-benefit/PLAN.md`
- `research/FP/answer-benefit/APPROVAL.md`
- `research/FP/answer-benefit/manifest.schema.json`
- `research/FP/answer-benefit/validate_manifest.py`
- This report.

The coordinator must read PLAN.md and APPROVAL.md in full before sending them to
Gary. He must choose the domain/sources, exact local model and reviewers, set
lookup harm tolerance, and approve all proposed rules before study answers exist.
The later experiment unit freezes the actual artifacts and writes
`scripts/fp/check-answer-benefit.sh`. Before freezing, pin the accepted gateway
commit/bytes; the contract inspected here is an uncommitted P4b observation.

## Pre-data fit check

| Dimension | State at AB0 handoff |
|---|---|
| Signal volume | 96 questions planned; none newly written or scored. No power/variance estimate is claimed. |
| Signal latency | Human reference labels precede generation; blind grades lock after all attempts, without interim totals. |
| Signal breadth | Both arms answer all qids; all failures remain. Reviewer appointments and label completeness are freeze gates. |
| Budget | Shared 6,000 gateway evidence tokens per question/arm; proposed common call/time/output limits and zero image reads. |
| Failure mode | Hash/protocol drift fails visibly; missed evidence cannot establish absence. Bad gold discovered after answers invalidates the claim. |
| Instrument stability | Counter/renderer are pinned proposals corroborated by P4b source; adapter parity, native context fit and runtime behavior remain later prerequisites. |

## Key decisions and limits

- Grounded: design C037/C038/C078 + R3/P1 → preserve 48 units/96 questions and
  source grouping; A1 → separate answer harm from retrieval promotion;
  final M3 → do not borrow its sample, unblinded labels or extraction checks as
  answer evidence. No KB retrieval search was run: the user's prohibition takes
  precedence over skill search guidance.
- Recommend one 48-question relational/coverage superiority endpoint, with
  gap-review and pooled benefit results descriptive. Recommend zero gross
  supported-answer lookup losses out of 24; this is not yet Gary's choice.
- Use paired source-group percentile intervals and retain failed/missing pairs;
  require a conservative failure analysis as well as ordinary scores.
- No real freeze is produced: questions, labels, graph receipts, reviewer names
  and Gary's choices are later inputs. A valid synthetic manifest is not human
  approval, proof of chronology or evidence of benefit.
- The dev skill is scoped to an intrinsic artifact check. No subagents or model
  reviewers are used under the user's no-model-calls constraint. Independent
  document review remains with the coordinator before Gary. Requested unit
  artifacts replace skill wiki/log outputs because wiki edits are prohibited.

## Read-only source observations

These are observed working-tree bytes, not accepted gateway pins or experiment
freeze hashes. Main intake paths are relative to its `kbu-2026-10-07` directory.

| Observed source | SHA-256 |
|---|---|
| `design-spec.md` | `3eb020c6106e8d534a3320f914c02a08b3f84701ef84813d7ba73129a2cd39b8` |
| `product-brief.md` | `7b5f19ef63f96b14580b90aa9a75a25a108277cd479719fe9d1875572b5e318c` |
| `grounded.md` | `be6a1dac23a8ea4fbaf69a5b88351134185d45d26652f34ccddbbe42153e1b35` |
| `audit.md` | `c07132920b608281b0bfb52f0fb09e9f81cc3764ce73a30fe3ad56f57e9ebd37` |
| `reports/R3-REPORT.md` | `740f179444e61039715a6c9a52b822857068d3cf7146ffa2953817186d70fd06` |
| `reports/M3-REPORT.md` | `d1d37136ad8f96f30600e2e69abf644e8e071ce8e08bcc546821f3dcf47f923f` |
| `pi-mind-wt/P4b/packages/gateway/README.md` | `25420dcd343a1f76c42fc86680f0001ab336727f3456ae202c19dfbad06fb36f` |
| `pi-mind-wt/P4b/packages/gateway/src/tokenizer.ts` | `62fb3485c979d58a812273f8449b8eccb2bf2b6d59655c11cd108631ad0f1917` |
| `pi-mind-wt/P4b/packages/gateway/src/tokenizer.py` | `9ce642f9d329d28deec58e060912c98c34c950e1f965aac7c396fc5bf8dd5d54` |
