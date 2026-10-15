# FP row 12 — answer-benefit pre-registration

Owner and decision authority: Gary. Authoring unit: AB0, 2026-10-15.
Status at AB0 handoff: **PROPOSED; NOT APPROVED; NO EXPERIMENT AUTHORIZED BY THIS FILE.**

This unit writes the plan and an offline freeze validator only. It creates no study
questions, reference answers, model answers or measurements. No model, retrieval
service, GPU, bppc or oMLX is used. The experiment belongs to a later unit, after
the graph phase and Gary's recorded approval. Product approval on 2026-10-14 and
P1 contract approval do not approve this scoring plan.

## 1. Question and scope

For Gary and agents using this bounded library, does adding typed graph and
coverage tools to ordinary knowledge-base search increase **correct, supported
answers** under the same evidence allowance? Does it lose supported answers on
ordinary lookups? The unit of observation is one question answered once in each
arm. The intervention is tool availability, including its discovery and budget
cost; extraction-model quality and embedding replacement are separate studies.

The design's C037/C038/C078 requirements retain **48 source units**, 12 each from
books, courses, papers and repositories, drawn from **2 books, 2 courses, 8 papers
and 2 repositories**. A unit is a section, lesson segment, paper span or file with
enough enclosing context to interpret it. Gary chooses one technical domain and
the exact works/revisions before question writing. Record every required unit,
ordered scope membership, source hash, locator, processing state and omitted
modality. Editions/translations of one work do not count as independent sources.

The frozen v10 control is `developer_knowledge_v10`, release `v10-fp-p1` in
`data/baseline/`. Its historical retrieval scores are not answer scores. Before
freezing, the experiment owner must establish that all selected evidence is
accessible through ordinary text search/reads in **both** arms. A graph-only
source is not an eligible advantage. If the required diversity cannot be met by
the approved common text snapshot, stop for Gary's pre-results scope decision;
do not silently substitute M3's sample, change v10, reduce diversity or count
unavailable sources as absent. Any shared text supplement needs an explicitly
approved, pinned comparator before questions are frozen.

## 2. Questions and reference labels, written before answers

No frozen 24-question lookup-answer benchmark or 96-question graph-answer set
was found in the inspected intake/reports and `data/bench/` inventories. R3/P1
propose these populations; they do not supply independent answer labels.
`data/bench/questions.jsonl` (150 rows), `questions_v2.jsonl` (128 rows) and the
30-row `gate-v10/sanity-plan.jsonl` are retrieval material, not this answer study.
The 438 hard retrieval queries must remain a separate promotion gate.

The later curator writes and freezes `questions.jsonl` and `labels.jsonl`:

| Class | Number | Construction and expected reference |
|---|---:|---|
| Lookup — C038 harm | 24 | Direct, ordinary source questions over the selected units; all answerable from original text. Existing bench wording may be adapted only if its positive source is in the common snapshot; record the original qid/path and every edit. Otherwise write new questions from the source. |
| Relational — C037 benefit | 24 | Ask who applied a method to a problem, which conditions/versions constrain a claim, or what implementation/evaluation supports a relation. Label direction, negation and conditions from source text, without inspecting graph outputs. |
| Coverage — C037/C078 benefit | 24 | 12 known-present cases with source witnesses; 12 no-support cases independently checked across every required unit in an explicitly bounded, completely processed scope. A graph miss alone cannot label no-support. |
| Gap review — benefit description | 24 | Gary supplies a task and an explicit requirement set before writing. Ask which introductions, implementations, evaluations or prerequisites have support, which need review and why. Label available evidence and the appropriate processing/gap state. A library gap is never a claim about Gary's understanding or global novelty. |

This yields **96** test questions. Each record has a stable `qid`, `class`
(`lookup`, `relational`, `coverage`, `gap_review`), wording, source IDs/revisions,
required-unit IDs, scope/requirement-set IDs, origin, and `source_group_id`.
Reference labels use the same qid/group and contain `expected_state` (`answer`,
`no_support`, `unknown`), required atomic claims, acceptable alternatives, exact
evidence locators/hashes, and scope/processing qualifications. All lookup and
relational labels have state `answer`; coverage has 12 `answer` and 12
`no_support`. Gap-review states follow source review. Never invent negative
labels by withholding a known supporting span from the reference reviewer.

Recommendation: Gary is the source curator; a named knowledgeable human checks
every label independently against preserved originals and the scope ledger.
Gary adjudicates disagreements before freeze. Keep both initial labels and the
resolution log. Ambiguous items are rewritten or replaced **before** freeze,
with reasons; no answer is generated to help choose them. No unresolved labels
may enter the experiment. Exact reviewer names are mandatory freeze inputs.

Group all neighboring units, editions and translations of a work together.
If a question or its reference depends on several works, join their groups;
take the transitive closure over **all 96 questions**. No source may occur in two
groups. Use at least **8 independent source groups**, each represented in all
four classes, so every resample contains both endpoints. Prefer the natural 14
work groups; cross-work questions may reduce this count. Freeze this assignment
from source dependencies, never from answer scores. Fewer than 8 groups requires
a new pre-results design, not a question-level interval. Eight is a proposed
minimum for this small pilot, not a power guarantee.

Development, prompt/rubric calibration and tests use separate works and source
groups, including neighboring sections. The 48 test units and their reference
labels may not tune the extraction profile, prompts, model or cutoffs. Freeze
graph/extraction code before revealing test labels to its builders. Deterministic
contract fixtures are not calibration answers. If an already-used M3 source is
chosen, disclose its prior exposure and replace it for a confirmatory claim;
M3's unblinded extraction review cannot become independent test gold.

## 3. Arms and execution held fixed

| Arm | Available evidence tools |
|---|---|
| Control | Ordinary v10 search and reads through the gateway: the eight compatible legacy tools (`search`, `search_book`, `read_chunk`, `get_chapter`, `list_books`, `grep_books`, `search_philosophy`, `list_philosophy`), their `legacy_read` wrapper, `read_metadata`, `source_list`, `source_read` and `mind_status`. Optional philosophy stays disabled unless included in the common frozen scope. |
| Treatment | Exactly the control tools, plus `graph_subgraph`, `graph_evidence`, `graph_who_tried`, `coverage` and `coverage_gaps`. |

Both arms use identical source membership/revisions, ordinary search configuration,
answer-model checkpoint/runtime, generation settings, question wording, system
and answer instructions, source-reading permissions, and evidence allowance.
Retain P1's v10 query embedding, keyword/fusion and reranker configuration;
`hyde_passage` stays empty. Pin the actual serving implementation, not a changing
worktree path. Do not introduce an embedding or search-setting comparison here.
Freeze tool schemas; the treatment's added tool descriptions are the declared
intervention. The common prompt says to use available evidence, cite each material
claim and qualify scope/unknowns; it does not disclose reference labels. Model
pretraining knowledge without source support receives no credit. No additional
catalog-only or extraction-model arm is tested here, despite R3's broader proposal.

**Answer model: GARY TO CHOOSE — Swift 1.5 on bppc, or another local model.**
Recommendation: Swift 1.5 only if Gary confirms that exact local checkpoint and
an authorized later compute window; this plan asserts neither availability nor
quality. Freeze model ID, checkpoint/content revision, runtime/build, chat
template and generation configuration. No automatic model fallback is permitted.
An unsupported generation parameter must be disclosed and settled before freeze.

Proposed execution: **1** fresh, isolated session per question/arm (**192** answer
attempts), temperature **0**, at most **1,024** newly generated answer tokens,
**32** tool-call attempts and **600 seconds** elapsed per question/arm, with **0**
automatic retries. Record all limits and actual use. Seed Python's schedule RNG
with **42**; sort qids, shuffle questions, and randomly choose first arm for each
pair. Run pairs sequentially, without concurrent study calls. Pin model seed 42
if supported, otherwise record its absence; do not claim deterministic generation.
No chat, retrieved evidence, answer or cache keyed only by question may cross arms.
Freeze backend state; new memory/annotations, writes and online learning are
disabled in both arms. Shared exact source caches may be used only with pinned
snapshot keys and disclosed cache policy. Quality, not latency, is the endpoint.

### Gateway accounting: a cumulative 6,000-token evidence cap

Use **6,000 per question per arm**, not per call. The gateway is the accounting
authority: **`tiktoken==0.14.0`, `cl100k_base`**, with vocabulary fingerprint and
counter string `python-tiktoken/0.14.0:cl100k_base:<fingerprint>` frozen in the
configuration. The renderer revision is
**`gateway-content-text+canonical-tool-metadata/v1`**: join all text content
blocks with newline, append newline and compact JSON of the complete tool
`_meta`, with sorted object keys and Unicode unescaped. Do not render mirrored
`structuredContent` a second time. Use the gateway implementation's fixed-point
charge for budget fields; save rendered-byte hashes and token charges.

Count searches, catalog/graph/coverage results, source/chapter/chunk reads,
metadata and explicit `read_metadata` responses, locators, annotations if any,
errors, omissions, pagination notices and repeated content on every delivery.
Follow-up and paginated reads consume the same allowance. Failed delivery may
consume tokens; replays are charged again. Initial fixed question/system/tool
instructions and generated output are outside this **evidence** allowance;
record them separately and keep their common parts identical. This counter is
not the answer model's native context limit. Before freeze, verify with synthetic
inputs that the model's full native context accommodates instructions, tool
definitions, evidence and output in both arms without silent input clipping.

The trusted adapter/operator binds a unique budget with `active_budget: {id,
cap: 6000}` for each question/arm. IDs select existing bound budgets through MCP
request `_meta.mind.question_budget_id` or CLI `--budget`; they cannot create,
reset or raise budgets. Omission of an ID must still use the active budget.
Every route, including legacy calls and metadata reads, must pass through that
authority. No raw Python, filesystem, offline file fallback or unmetered direct
backend access is permitted. Budget-limit notices are evidence-limit events,
never proof of absence. A notice that cannot fit may be refused without content.

This text-only study allows **0 image/pixel reads in both arms**; preserved page
text may be read through the metered source reader. Figure ranking and visual
content stay disabled. Before study execution the later adapter must prove
renderer parity, cumulative accounting, unique budget binding, and no bypass
using synthetic protocol fixtures, without looking at study answers. Log each
question/arm budget ID, read IDs, source/index/graph snapshots, returned-text
hashes, omission/error states, used/remaining tokens and terminal status. A cap,
renderer, counter, snapshot, privacy or isolation violation invalidates the run.

## 4. Rubric and blind human review

**Support** requires a cited source span that opens through the frozen catalog
at the pinned revision and actually contains the claim, including relationship
direction, negation, version and conditions. A matching quote alone is insufficient.
Catalog/ledger witnesses can support scope and processing counts; they cannot
substitute for source text supporting a substantive relation. A source ID, graph
edge or citation-shaped string alone is not support. `verification: exact` in
P2 means frozen payload identity, not proof of original-edition truth.

Two named knowledgeable human reviewers independently score **every** answer,
with arm/model/tool identities hidden and randomized answer IDs. They see the
frozen question/reference packet and catalog evidence, but not the paired answer
or interim totals. Retain original wording/citations; remove transport traces
and arm labels without changing substantive content. Some coverage wording may
reveal the arm; record reviewer arm guesses and this blinding limitation.
Reviewers must be independent of answer generation and graph implementation.
Gary is the final human adjudicator, with arm labels hidden until grades lock.
The reference checker may be one scorer; a second distinct scorer is required.
No automated/model judge is authorized by this plan. No stopping on interim scores.

Apply categories in this precedence order, and retain per-claim notes:

| Category | Operational rule | Primary credit |
|---|---|---:|
| Wrong | Any material claim contradicts the reference/source, including a false absence, incorrect scope, relation direction or version. | 0 |
| Unsupported | No established contradiction, but any material asserted claim lacks an opening, entailing citation; includes fabricated or broken evidence. | 0 |
| Supported | Every required part is correct, cited and sufficiently complete, with required scope/processing qualifications and no material wrong/unsupported additions. | 1 |
| Partial | Correct, supported substance answers some but not all required parts; no material wrong/unsupported additions. | 0 |
| Abstained | No substantive answer, or only a refusal/unknown statement that does not fulfill the labeled task. | 0 |

A correct, bounded `no_support` or `unknown` conclusion is **supported**, not an
abstention, only when the label calls for it and the answer cites the required
scope/ledger/review evidence. Complete extraction alone licenses only “no indexed
evidence in this scope”; a confirmed library gap requires original-text review.
Incomplete required material requires unknown for absence. Supported positive
evidence can coexist with unknown broader coverage. Unjustified unknowns on
known-present cases receive no supported credit. The 12 incomplete-scope fixtures
are excluded from the answer-benefit denominator (section 7).

After independent grades, retain disagreements and Gary's written source-based
resolution. No unresolved grade permits a confirmatory claim. A discovered gold
error after answers exist is reported against the original labels and invalidates
the confirmatory claim; do not relabel or drop the item to recover a win. A revised
benchmark needs fresh held-out sources and new approval.

## 5. Statistics fixed before measurement

For question i, let C_i and T_i be binary supported credit in control and
treatment. The paired difference is d_i = T_i − C_i, taking −1, 0 or +1.
Report means as proportions and differences in percentage points.

**One confirmatory benefit endpoint:** the question-weighted mean d_i across
the **48 relational + coverage questions**, matching the design's proposed
relational/coverage gate. The **24 gap-review** questions, the pooled **72**
benefit-oriented questions, each individual class and medium are descriptive
secondary views; none can rescue a failed primary endpoint or license a separate
superiority claim. Partial answers receive no half-credit in this endpoint.

**Lookup harm:** for the separate **24** lookups, h_i = 1 when C_i = 1 and
T_i = 0, otherwise 0. Report gross supported-answer losses L = sum(h_i),
H = L/24, gains G = count(C_i = 0, T_i = 1), and signed mean d_i = (G−L)/24.
Gains never cancel losses for the harm gate. Also report category transitions,
wrong/unsupported changes, abstentions, all failures and their question IDs.

**Interval algorithm:** paired, source-group cluster percentile bootstrap,
**10,000** replicates, **two-sided 95%**, Python `random.Random(42)` with the
Python version pinned. Sort frozen source-group IDs lexicographically; let K be
their count. For each replicate, draw K group indices independently with
replacement using `rng.randrange(K)` K times. Keep all questions and both arm
scores in each drawn group, duplicating whole groups when selected repeatedly.
For each endpoint,
recompute sum of its item values divided by number of its included questions
in that resample, preserving question weighting. Never resample arms, spans,
individual questions or extraction attempts independently. Use the same draws
for every endpoint. Every group must contain all four classes (section 2).

Sort the 10,000 replicate values. Endpoints are **zero-based order statistics
249 and 9749**, with no interpolation (ranks 250 and 9750). Report the observed
point estimate alongside these limits for primary d, lookup H, lookup signed d,
gap-review d, pooled-72 d, and individual classes. Per-medium point estimates and
counts are descriptive; no extra inferential tests or post-hoc favorable slices.
Provide group counts and per-group scores so dependence and precision are visible.

The sole superiority claim uses one 95% interval, so no multiplicity correction
is needed for it. The harm count is an additional required veto, not a second
chance to claim superiority. All other 95% intervals are **marginal descriptive
intervals**, not simultaneous 95% coverage. Any later class-, model- or medium-
specific superiority claim needs a new pre-results multiplicity plan. No
p-value/sign/Wilcoxon test or optional stopping is added to the decision rule.
`scripts/significance.py` is reference code only: it resamples individual retrieval
queries, intersects available IDs and has a different verdict rule; do not invoke
or reuse it unchanged. `scripts/eval_retrieval.py` measures retrieval, not answers.

This purposive, small-source pilot cannot establish library-wide benefit,
rare-error safety or statistical power for a chosen minimum gain. Cluster
percentile intervals can be coarse or degenerate, particularly at zero observed
losses; [0,0] for harm is not proof of zero future risk. No pilot variance or
minimum detectable improvement is measured in AB0. Report inconclusive precision
honestly; do not add questions after seeing results to narrow an interval.

### Failures and missingness

Every frozen qid appears exactly once per arm; no pairwise deletion or replacement.
Timeout, crash, exhausted tool/output limit, blank/missing response and ordinary
backend failure receive supported credit 0, with terminal failure status separate
from the rubric (use abstained for a missing response). A returned partial or
unsupported answer is graded as written. Budget exhaustion alone is not a
protocol violation if accounting is intact. The 600-second cutoff stops further
reads; do not cherry-pick successful retries. A gateway-wide admission/configuration
failure before study start blocks the study rather than fabricating 192 failures.

Publish a conservative sensitivity calculation on the same frozen resamples:
assign **control failures credit 1** and **treatment failures credit 0**, retaining
all nonfailed scores, and recompute primary and lookup endpoints. A benefit claim
must also have a positive primary lower bound under this assignment; the harm
gate must pass under its loss count too. Missing/unresolved human grades, missing
budget logs or protocol violations invalidate the claim rather than count as
favorable model outcomes. Keep all attempts and report the invalidity.

## 6. Decisions Gary must approve before answers

Benefit is claimed only when the primary paired 95% lower bound is **strictly
above 0**, in both the main and failure-conservative analysis, and all validity,
grading and harm gates pass. A bound equal to 0 is inconclusive. A wholly negative
interval is evidence of loss in this pilot; an interval spanning 0 is inconclusive.
Report losses, gains and negative secondary findings alongside any positive claim.

**Allowed lookup harm: GARY TO SET, integer 0–24 supported-answer losses.**
Recommendation: **0 lost supported answers out of 24**, including the conservative
failure analysis, to preserve ordinary search utility. This is a finite-pilot
veto, not a population non-inferiority guarantee. Gary may choose a larger count
only before any answer or score exists; record both the count and its fraction
of 24. The manifest rejects an unset value. Report the 95% harm interval even
when the observed count passes. Do not substitute a retrieval-score threshold.

Graph integrity and C078 fixture acceptance must pass before the experiment;
answer benefit cannot override false absence, invalid locators or silent
truncation. Keep ordinary search as the default when benefit is inconclusive,
harm exceeds tolerance or the run is invalid. A rerun after inspection requires
a separately registered study with new held-out groups; retain the first result.

## 7. Separate work and prerequisite gates

- **C078 coverage fixtures:** the graph unit implements 0 false absences among
  12 known-present cases and 12/12 correct unknowns after changing required-unit
  state in the 12 no-support cases; it also checks 0 invalid locators and no silent
  truncation. These 12 derived incomplete-scope probes are protocol fixtures,
  not 12 extra independent answer questions. The 24 coverage questions remain
  in this answer study, with independently frozen labels. Fixture passes alone
  do not establish answer benefit. Pin the graph unit's receipt and snapshots.
- **C118 visual answer benefit:** a separate later pre-registration must supply
  a text/page-access control, figure-ranking arm, equal image/page allowances,
  render resolution, latency accounting and independent answer labels. Neither
  C118 nor M2 page hits are required answer endpoints for row 12 in this brief.
- Embedding/search promotion, the 438 hard retrieval gate, sanity recall,
  extraction throughput, graph precision/recall, memory adoption and eight-harness
  compatibility remain their own gates. No prior M3 answer benefit is assumed.

## 8. Freeze and later checker interface

1. The coordinator reads **PLAN.md and APPROVAL.md in full**, resolves Gary's
   choices and obtains his explicit approval of the plan **before any study
   answer generation, retrieval run or score**. Preserve the human approval;
   product/contract approval and a validator pass do not substitute for it.
2. Later, assemble source-held-out questions, independent labels, disagreement
   log, prompts, exact source/index/graph pins, model/runtime, named reviewers,
   tool allowlists, budget instrument and analysis implementation. Gary approves
   the completed freeze packet and its exact choices before execution. Changes
   to the approved plan need renewed approval before any answer exists.
3. Create a new, immutable directory such as `freezes/<run-id>/` containing
   `manifest.json` and local copies of every required artifact. Paths are relative
   to that directory; no traversal, external symlink, secret, bearer token or
   signed URL. SHA-256 and byte length bind the exact bytes, not normalized text.
   Required roles: `plan`, `approval_summary`, `questions`, `labels`, `prompts`,
   `configuration`, `source_snapshot`, `baseline`, `graph_snapshot`,
   `gateway_contract`, `analysis_implementation`, `label_review`, `approval_record`,
   `schema` and `validator`. Snapshot files are inventories binding revisions,
   hashes, catalog storage and fixture receipts, not mutable paths alone. Include
   the read source documents and dependencies in those inventories; the analysis
   implementation must bind its own runtime/dependency lock too.
4. `configuration` is JSON containing `protocol` equal to the manifest's
   `protocol`, plus complete tool/arm/runtime/snapshot configuration. The protocol
   contains approved counts, budget pins, model identity, reviewer identities,
   execution limits and lookup-loss tolerance. Question/label JSONL uses the
   fields in section 2; additional reference detail is retained, not exposed to
   the answer model. The schema fixes method constants; a changed method needs
   a new plan and schema revision before results.
5. Save a JSON approval record with `approval` and `pre_results` equal to the
   manifest fields and nonempty `human_confirmation` containing the preserved
   human evidence. It identifies Gary, exact decisions, approval time,
   plan/configuration/question/label hashes and confirmation of no study answers
   or results seen. Set `approval.approved_by` to `Gary` only from that human
   evidence. Set `pre_results` attestations truthfully as of freeze time; they
   refer to this study, not historical M3 work. The manifest contains no answers,
   scores or results.
6. Run the validator below. Record the manifest's own SHA-256 in an independent
   coordinator registration receipt **before the first study call**, together
   with human approval provenance and freeze time. Do not embed the manifest's
   own hash inside itself. A timestamp or editable `approved_by` string cannot
   prove approval or chronology; human review and the external receipt do that.
7. The later `check-answer-benefit.sh` (not written by AB0) must call this validator
   with the receipt's `--expected-sha256`, verify approval provenance and that
   every study start/read/result timestamp is later than registration, check all
   source/model/adapter pins and budget logs, require all 192 terminal records
   and locked grades, and reproduce intervals/decisions from retained data.
   Keep results in separate files referencing the manifest digest; do not edit
   the freeze to append results. Revalidate frozen files after execution.

```sh
python3 research/FP/answer-benefit/validate_manifest.py --self-test
python3 research/FP/answer-benefit/validate_manifest.py path/to/freeze/manifest.json
python3 research/FP/answer-benefit/validate_manifest.py path/to/freeze/manifest.json \
  --expected-sha256 <digest-from-pre-results-coordinator-receipt>
```

The offline validator checks schema, byte hashes, paths, approval bindings,
resolved choices, question/label identity and counts, group consistency and
configuration agreement. It does not certify semantic labels, human identity,
actual renderer/counter behavior, snapshot availability or real chronology.
Its self-test uses synthetic metadata only, without source answers or model calls.
No frozen manifest is issued by AB0 because Gary's choices and the graph/test
artifacts do not yet exist. A plan/question/label/prompt/configuration change
after answers or results exist **invalidates the confirmatory claim**, even if
rehashing makes a new manifest internally consistent. Keep exploratory analysis
clearly labeled and obtain new approval with new held-out data for a new claim.

## 9. Source basis and deliberate limits

Read-only basis, 2026-10-15: main checkout
`data/intake/kbu-2026-10-07/design-spec.md` v2 (Knowledge graph and coverage;
Agent tools/budget; C037/C038/C078/C118; Open choices 11/14), `product-brief.md`
(learning plan), `grounded.md` (owner intent), `audit.md` (A1 claim register/open
claims), `reports/R3-REPORT.md` (coverage and proposed pilot) and final
`reports/M3-REPORT.md` (sample, integrity and unblinded-review limits). The spec's
sibling-run links are relocated under that intake's `reports/`; A1 is `audit.md`.
Local contracts: `data/baseline/CONTRACTS.md`, `baseline.json`, `tools-v1.json`,
`contracts-lock.json`, `contracts/v1/read-metadata.json`, its fixtures;
`data/catalog-fp/USAGE.md`; bench question inventories; `scripts/eval_retrieval.py`
and `scripts/significance.py`, read but never executed or imported.

The requested `git show unit/fp-P4b:packages/gateway/README.md` failed because
that path is absent from the branch commit inspected. The contract was instead
read from the **uncommitted** `pi-mind-wt/P4b/packages/gateway/README.md`, with
renderer identifier corroborated by `src/tokenizer.ts` and counter format by
`src/tokenizer.py`. The later freeze must pin the accepted gateway commit and
contract/implementation hashes; this working-tree observation is not acceptance.
Source observation hashes and unresolved choices are in `../units/AB0-report.md`.

AB0 choices beyond the design (binary credit, primary 48-question gate,
source-cluster algorithm, minimum group count, conservative failures and proposed
execution limits) are recommendations for Gary, not measured findings. Rejecting
an aggregate retrieval proxy, a question-independent bootstrap, a model judge and
a visual comparison here preserves the specific answer-support question and
the plan-only boundary.
