# P1g — baseline check after the approved Gemma switch

Owner: Gary. Date: 2026-10-16. Branch: `unit/fp-P1g`.

## Scope and acceptance

Preserve `data/baseline/baseline.json` as the frozen v10 reference. Add an exact,
owner-approved serving-stack amendment bound to the v11 gate and the existing
2026-10-16 approval evidence. Keep physical v10 collection, data, schema/tool
contracts, and frozen query-result checks intact. Use the same pinned checker
interpreter/validator for the shell gate and baseline tests.

Required coordinator checks outside the sandbox:

- `bash scripts/fp/check-baseline.sh`
- `.venv/bin/python -m pytest -q tests/test_fp_baseline.py`

No commits, merges, pushes, protected-file edits, model loads, GPU/Docker use,
Qdrant writes, or key output are authorized.

## Status

READY FOR COORDINATOR CONNECTED ACCEPTANCE. P1g's coordinator rerun passed all
45 tests and the Mac half, then exposed the bppc kernel drift covered by the
P1g2 addendum below. The next coordinator rerun passed 59 tests and the kernel
amendment, then exposed the OS point-release drift covered by P1g3 below.
The current extended suite passes all **60 tests** in the local `.venv`; actual
cases execute under the frozen checker runtime. The P1g3 local connected run
stops before Mac/bppc reads because the configured main checkout's
`dist/release/manifest.json` is absent. Earlier P1g/P1g2 runs reached the Mac
metadata request and were blocked by sandbox networking. No full connected
green result is claimed.

## Key decisions

- Pattern: coordinator-direct; the approval, comparison, and interpreter changes
  share one checker/test boundary.
- Frozen v10 reference remains unchanged; only explicitly approved version deltas
  may be accepted.
- Grounded: existing P1 source-policy checks, contract approval JSON, and the
  committed `data/bench/gate-v11.{md,json}` at
  `ba264d76b879a8e9672c1f05fd9c2f8f305f1c01` → retain v10 checks, bind a separate
  amendment to the gate and its recorded switch. The user identifies the owner
  as Gary; the historical gate calls the switch approver Huy and quotes "Merge
  and switch". Preserve that attribution in the evidence.
- KB cite-or-null: searched the project wiki index, decisions, and prior P1
  report for baseline/validator/Gemma precedent. P1 report documents strict
  frozen evidence and informational alias drift; no prior amendment mechanism.
  No model-backed KB search is run because model loads are excluded.
- Context → decision: the project `.venv` validator differs from the frozen
  checker. Keep dependencies untouched and make pytest delegate baseline cases
  to the checker's shared launcher, with fail-closed Python/validator/format
  checks. Reject relaxing the validator pin or skipping invalid fixtures.
- Context → decision: baseline did not capture torchvision. Record its approved
  addition (`0.29.1`) alongside transformers (`5.17.0` → `5.19.0`), then observe
  both. Bind allowed versions to the approved commit's lockfile.
- `wiki/` is protected by the brief; this requested report is the unit's durable
  record instead of editing the wiki.

## Review plan

Independent code review after implementation, focused on approval binding,
extra version drift, frozen-data preservation, and false-green test delegation.
Coordinator retains connected acceptance outside the sandbox.

Review outcome: independent `baseline_review` agent found no verified defects;
reran all 45 tests and confirmed all original 30 test identifiers remain.
Additional independent probes rejected unrelated machine fields, fastembed
drift, a rebound baseline hash, a missing approval artifact, and an extra amended
package. Review was read-only and offline; approval attribution was checked
against the brief and committed gate. The historical gate's Huy attribution is
preserved rather than rewritten as Gary's words.

## Changes and evidence

- `data/baseline/serving-stack-amendment-2026-10-16.json` records Gary's
  2026-10-16 approval, exact package deltas, unchanged baseline SHA-256, and Git
  blob/SHA-256/size bindings for both gate records and the approved `uv.lock`.
  `approval_binding_sha256` covers the whole record except that field itself
  (UTF-8 JSON, sorted keys, compact separators, literal Unicode). It detects
  binding corruption; Git evidence and the fixed approved revision establish
  which gate/versions are authorized.
- `serving_amendment.py` validates that record, reads the approved versions from
  the committed lockfile, and constructs a separate expected machine record.
  It never rewrites the baseline. The checker still verifies physical v10,
  sources, data, release references, and remote controls as before. The complete
  frozen stack or complete approved stack passes; partial/extra drift fails.
- `baseline_io.py` now observes torchvision metadata as well, without importing
  any model package. Previously it was absent from the frozen observation.
- `run-python.sh` / `baseline_runtime.py` are shared by the shell checker and
  pytest cases. The existing `FP_PYTHON` selection defaults to `python3`; before
  executing either target it checks frozen Python 3.11.5, jsonschema 4.23.0,
  and working date/date-time/URI format validation. `FP_PYTHON` may select an
  equivalent installed interpreter; selecting a drifting validator fails.
  If an activated project environment puts its Python first on PATH, set
  `FP_PYTHON=/Users/GaryT/miniconda3/bin/python3` for both commands.
- Original unittest cases moved to `tests/fp_baseline_cases.py`; the pytest entry
  point discovers nonempty case IDs without importing the checker and runs each
  through the shared launcher. The two original named tests remain individually
  selectable with pytest `-k`.
- Refreshed the existing contract/instrument lock and only its hash/size reference
  in `tested-release-v10.json`. No schema or fixture changed; no data/control or
  baseline source observation was recaptured.
- `.venv/bin/python -m pytest -q tests/test_fp_baseline.py`: **45 passed in
  22.71s**, including both named regressions, approved matching change, no
  amendment, unapproved record, wrong observed versions, broken approval
  binding, rebound wrong versions, altered gate hashes/commit, missing/extra
  packages, partial switch, unchanged baseline, and unrelated machine/physical
  collection drift. The first run used a temporary symlink to main's `.venv`
  (jsonschema 4.26.0); the suite selected the pinned checker subprocess runtime.
  The symlink was then removed; a standard ignored local venv using system site
  packages was created without pip/dependency installation for coordinator use.
  Final exact-command rerun in that local venv: **45 passed in 28.99s**.
- Positive runtime output: `Python 3.11.5; jsonschema 4.23.0; formats
  date/date-time/uri`. Negative runtime probe:
  `FP_PYTHON=/Users/GaryT/Documents/Work/tools/knowledge-base/.venv/bin/python
  bash scripts/fp/check-baseline.sh` fails **before any connected read** with
  `FAIL: changed baseline: validator.jsonschema`. Separate unit cases reject a
  changed Python version, each missing required format checker, and the original
  invalid date-time fixture.
- Local integrity assertions passed: every instrument lock entry and release
  baseline/contract-inventory reference matches; protected paths and
  `baseline.json` have no Git diff. Baseline SHA-256 remains
  `6074b5d0cb8a85fc57191aab83eacb12eeebce407ba205f6d8fcb0e9232ea879`.
  `git diff --check` and shell syntax checks passed. All **210** instrument hash
  entries match. Compared against HEAD: every existing contract/fixture entry
  stays byte-identical, and every release field except the instrument lock's
  hash/size reference stays unchanged.
- Post-change connected command passed 91 schemas / 32 tool pairs / 341 fixtures
  and local source/release hashes, then failed at the Mac metadata network
  request with the same sandbox `Operation not permitted` limitation as before.
  No connected green result is claimed.

## Checker output sample

Offline sample only: physical collection and alias were fixtures; package
versions were read from installed main `.venv` metadata without importing models.
The observed package record matched the approved amendment exactly:

```text
INFO: alias now -> developer_knowledge_v11
INFO: serving-stack amendment approved by Gary on 2026-10-16; gate-v11 at ba264d76b879a8e9672c1f05fd9c2f8f305f1c01; torchvision: (not captured) -> 0.29.1; transformers: 5.17.0 -> 5.19.0
```

This sample proves formatting and installed package equality only. The coordinator
must obtain the actual live alias/physical collection and remote-control verdict
with the connected acceptance command.

## Remaining work

Coordinator runs both acceptance commands outside the sandbox, reads the
amendment and a connected sample including alias/amendment information. Nothing
was committed, merged, or pushed. No protected files or frozen baseline were
changed; no model load, GPU/Docker use, Qdrant write, or dependency lock change.

## P1g2 addendum — bppc kernel amendment (2026-10-16)

Owner: Gary. Scope: accept only the recorded bppc kernel transition
`7.0.0-28-generic` → `7.0.0-38-generic`, while preserving P1g and every other
frozen bppc comparison. The user reports Gary authorized the OS kernel update
reboot on 2026-10-15 at about 22:00 ICT and supplied his password; the caretaker
session performed it. This authorization is supplied by the P1g2 brief, not
inferred from the serving-stack gate.

Coordinator evidence supplied in the brief: 45 pytest cases passed outside the
sandbox; the Mac half of the connected checker passed with its amendment;
bppc then failed at `bppc frozen evidence/collection/versions.machine.kernel`.
An offline observation copied from the freeze with just the reported new kernel
reproduces that exact failure before implementation.

Pattern: coordinator-direct for the shared checker/test boundary, followed by
independent read-only review. Grounded: whole-wiki search for kernel/amendment/
frozen-evidence precedent found no applicable bppc authorization record; the P1
and P1g reports plus the current checker supply the strict comparison contract.
Context → decision: use a separate baseline-bound bppc amendment with code-pinned
from/to values; reject general field overrides and baseline recapture. The
binding digest detects corruption; the brief supplies authorization and the
checker pins its exact scope. Protected wiki pages remain untouched; this
requested report is the durable record.

Pre-registered review risks: altered from/to values accepted after rebinding;
unrelated bppc facts escaping the comparison; missing amendment passing changed
evidence; bypassing validation for unchanged observations; failure to load the
record in the real checker; changes to P1g's Mac behavior or frozen artifacts.

Changes:

- `data/baseline/bppc-machine-amendment-2026-10-15.json` records Gary's approval
  date, reason, reported reboot time and brief provenance, the unchanged frozen
  baseline fingerprint, and exactly one kernel from/to pair. It uses P1g's same
  canonical JSON binding digest. This digest is an integrity check, not an
  independent authorization source; the exact approved values are also pinned
  in `serving_amendment.py`.
- Extracted the common baseline-binding check without changing Mac approval
  behavior. The new bppc validator checks schema, owner, date, reason, binding,
  frozen baseline, exact change scope and original kernel. It validates even
  when the observation equals the original freeze.
- `verify_bppc_target` compares the complete remote observation to either the
  original freeze or a separate expected record with only `machine.kernel`
  replaced. It changes neither input. Missing or extra facts still fail. The
  connected checker loads the bppc amendment independently of the Mac amendment;
  without it, changed kernel evidence fails. All later remote artifact, redirect
  and control-population checks remain in place.
- Added the new record to the instrument lock builder and refreshed the lock.
  The release record changed only its instrument-lock SHA-256 and byte count.
  No frozen source or machine observation was recaptured.

Verification:

- Before implementation, the new positive test failed at the reported
  `bppc frozen evidence/collection/versions.machine.kernel` comparison. After
  implementation, all 14 bppc tests passed; the full exact acceptance command
  `.venv/bin/python -m pytest -q tests/test_fp_baseline.py` passed **59 tests in
  21.39s**. All original 45 test IDs remain.
- Coverage includes exact approval, unchanged freeze, absent amendment, other
  observed kernel, changed/rebound owner/date/schema/reason/from/to values,
  missing/extra amended fields, wrong baseline binding and wrong original
  kernel. It also changes each of the **1,374 non-kernel scalar facts** in the
  frozen bppc record independently and confirms rejection, plus missing/extra
  evidence at the top level and within each major dictionary. This covers
  collection, membership/payload, sparse/model file fingerprints, controls,
  redirect, aliases and remaining machine facts.
- An integrated offline checker case loads both real amendment files, accepts
  both exact deltas, then rejects a changed hard-control output hash. Only
  external reads are stubbed; amendment loading and comparisons run normally.
- `bash scripts/fp/check-baseline.sh` passed **91 schemas / 32 tool pairs /
  341 fixtures**, local source/release checks and the updated instrument lock,
  then failed at the Mac request with `Operation not permitted`. It did not
  reach live bppc verification in this sandbox. Coordinator connected acceptance
  remains required; no remote green result is claimed.
- All **211 instrument fingerprints** match their files. Compared with the
  saved P1g worktree state, only the intended checker/amendment/test/lock/report
  paths changed, plus the new bppc record. Existing Mac amendment, runtime,
  launcher and metadata-observation changes are preserved. `baseline.json`,
  `pyproject.toml` and `uv.lock` remain byte-identical to HEAD. Baseline SHA-256
  remains `6074b5d0cb8a85fc57191aab83eacb12eeebce407ba205f6d8fcb0e9232ea879`.
  `git diff --check` and both shell syntax checks passed.

Independent read-only review: `bppc_amendment_review` found no verified defects
or material hypothesized gaps. It independently reran all **59 tests in 22.20s**
and checked two passing observations plus **26 rejected negative probes**:
rebound wrong from/to values under both original and amended observations,
missing required amendment fields, and replacements of each remote top-level
section. The review confirmed validation precedes the unchanged-observation
shortcut, the real checker loads the record, the full remote comparison remains,
and P1g's Mac behavior is preserved. All pre-registered risks were covered by
code inspection or discriminating tests/probes. Review was offline/read-only;
the root separately verified instrument-lock freshness and the preserved P1g
worktree state.

Offline fixture output (not a live SSH observation):

```text
INFO: bppc machine amendment approved by Gary on 2026-10-15; OS kernel update reboot; kernel: 7.0.0-28-generic -> 7.0.0-38-generic
```

Handoff: coordinator reruns both acceptance commands outside the sandbox. No
protected file edits, dependency changes, model loads, GPU/Docker operations,
Qdrant writes, key output, commits, merges or pushes were performed.

## P1g3 addendum — bppc OS point release (2026-10-16)

Owner: Gary. Extend the existing bppc amendment to exactly the two machine
changes from the same Gary-authorized OS update reboot on 2026-10-15:
`kernel` `7.0.0-28-generic` → `7.0.0-38-generic` and `os`
`Ubuntu 24.04.4 LTS` → `Ubuntu 24.04.5 LTS`. P1g and P1g2 work is preserved.
The prior addendum records P1g2's kernel-only scope; this addendum supersedes
that scope without changing the frozen baseline.

Coordinator evidence supplied by Brief P1g3: **59 tests passed** outside the
sandbox; Mac checks and the kernel amendment passed, then the checker failed
at `bppc frozen evidence/collection/versions.machine.os`. The brief reports
unchanged x86_64 architecture, Python 3.12.3, Qdrant image/digest, version
1.18.2 and commit 44ad62f8…; the OS point release came from the same authorized
update. These are coordinator observations, not new remote measurements here.

Pattern: coordinator-direct for this narrow shared checker/test boundary, with
independent read-only review. KB cite-or-null: whole-wiki search for
baseline/amendment/kernel/Ubuntu and the wiki index yielded no applicable
point-release authorization precedent; the P1 report, P1g/P1g2 addendum and
current checker establish the comparison contract. Brief P1g3 supplies the
additional authority. No model-backed KB search is run under the no-model-load
constraint. The requested report remains the durable record; wiki is protected.

Context → decision: pin the complete two-key before/after map in the validator,
then check each before value against its frozen machine field. Retain approval
and baseline bindings and the complete remote comparison. Reject arbitrary
record-driven overrides, missing entries, extra fields, altered values and
partial observed updates. No new external effect or recovery boundary is added;
only reversible local code/record changes are in scope.

Pre-registered review risks: a rebound record authorizing other keys/values;
missing OS entry passing; mismatched frozen before values passing; partial or
unrelated observed drift escaping comparison; mutation of frozen inputs;
instrument-lock staleness; regression of P1g/P1g2 behavior.

Before implementation, an offline copy of the frozen observation with the
reported new kernel and OS reproduced the exact `.machine.os` failure through
the pinned launcher. The updated positive test and new missing-OS-entry test
both failed against the unchanged validator at that comparison.

Changes:

- The existing bppc JSON now records both exact transitions and cites the
  P1g2/P1g3 briefs for the same authorized reboot. Its evidence, scope, reason
  and canonical approval-binding digest were updated together.
- `amended_bppc_machine` compares the complete change map to the pinned two-key
  map, verifies each frozen before value and builds a separate expected machine
  record. The checker prints both transitions. Approval validation still
  precedes the unchanged-observation shortcut; all remote evidence and later
  artifact/control checks remain strict.
- Existing tests now exercise both fields, rebound wrong from/to values for
  each, either missing entry, extra keys, wrong frozen before values, wrong
  observed OS/kernel values and partial updates. The integrated offline checker
  accepts both real amendments and still rejects changed hard-control output.
  The new case specifically rejects changed OS evidence with no OS amendment
  entry. All **59 prior test IDs** are preserved, for **60** total.
- Refreshed the instrument lock and release inventory reference. Exactly four
  lock entries changed: the bppc record, validator, checker and case file. The
  release record changed only its contract-inventory SHA-256 and byte count.

Verification:

- `.venv/bin/python -m pytest -q tests/test_fp_baseline.py`: **60 passed in
  21.68s**. The suite runs baseline cases under Python 3.11.5/jsonschema 4.23.0.
  The exhaustive strictness case independently alters each of the **1,373
  other frozen bppc scalar facts** and confirms rejection.
- `bash scripts/fp/check-baseline.sh`: **blocked before connected reads** by
  missing `/Users/GaryT/Documents/Work/tools/knowledge-base/dist/release/manifest.json`.
  A direct existence check confirms the configured release directory and
  manifest are absent. No source/release PASS line or live Mac/bppc verdict
  was reached in this run. Coordinator acceptance remains required.
- All **211 instrument fingerprints** match the actual files. Against the saved
  P1g/P1g2 starting worktree, exactly the intended seven
  checker/validator/cases/amendment/lock/release/report paths changed; earlier
  Mac amendment, launcher, runtime and metadata changes remain byte-identical.
  `baseline.json`, `pyproject.toml` and `uv.lock` remain byte-identical to HEAD.
  Frozen baseline SHA-256 remains
  `6074b5d0cb8a85fc57191aab83eacb12eeebce407ba205f6d8fcb0e9232ea879`.
  `git diff --check` and both shell syntax checks pass.

Independent read-only review: `p1g3_review` found **no verified defects** in the
increment against the saved P1g/P1g2 worktree. It confirmed exact two-key scope,
both frozen-before checks, the full observation comparison and unchanged Mac
logic; independently reran **60 tests** with
`.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_fp_baseline.py`; and
verified lock/release hashes and byte counts plus the unchanged frozen baseline.
The pre-registered risks were addressed by these code/record checks and the
negative regression cases. The reviewer made no edits or connected checks.

Offline sample from a frozen-record copy with only the approved pair changed
(not a live SSH observation):

```text
INFO: bppc machine amendment approved by Gary on 2026-10-15; OS update reboot; kernel: 7.0.0-28-generic -> 7.0.0-38-generic; os: Ubuntu 24.04.4 LTS -> Ubuntu 24.04.5 LTS
PASS: exact two-field offline observation
```

Handoff: coordinator reruns `bash scripts/fp/check-baseline.sh` and
`.venv/bin/python -m pytest -q tests/test_fp_baseline.py` outside the sandbox.
The connected run must have its existing main-checkout release artifacts
available. No full connected PASS is claimed. No protected file edits,
dependency changes, model loads, GPU/Docker operations, Qdrant writes, key
output, commits, merges or pushes were performed.
