# P1g4 handoff — 2026-10-19

Owner: Gary; coordinator accepts the Mac update on Gary's delegation supplied
by Brief P1g4. Changes are uncommitted in `unit/fp-P1g4`. No main-checkout
writes were made.

## Completed

- Added the evidence-bound Mac amendment for exactly `kernel` `25.6.0` →
  `27.0.0` and `os` `macOS 26.6.2` → `macOS 27.0.1`. Local `uname -r`,
  `sw_vers`, `platform.release()` and `platform.mac_ver()[0]` confirm the
  new values. Build `26A434` is evidence only: neither the baseline nor
  the live collector records a build field.
- Approval binding uses the existing canonical JSON SHA-256 algorithm:
  `d46903de76aeb9b02fe8ee4940ffc0d6b4ac1b32fe8f7d8506a27c4a36217e04`.
  Schema, approver, date, reason, complete before/after map and frozen baseline
  fingerprint are checked; rebinding cannot authorize other fields or values.
- The checker loads and reports the Mac amendment alongside the serving-stack
  and bppc amendments. Other machine facts and the physical collection remain
  strict. Tests cover composition, unrelated drift, partial updates, record
  tampering, baseline binding and input immutability.
- Enabled `-m` dispatch in the pinned runtime launcher for the requested pytest
  invocation. Runtime checks still run before module or script execution.
- Refreshed the instrument inventory and its release reference: **212** file
  fingerprints match. The release changes only its `contract_inventory`
  fingerprint. `baseline.json` is byte-identical to HEAD: **141323 bytes**,
  SHA-256 `6074b5d0cb8a85fc57191aab83eacb12eeebce407ba205f6d8fcb0e9232ea879`.

## Verification

```sh
bash scripts/fp/run-python.sh -m pytest -q tests/test_fp_baseline.py
```

**73 passed in 31.33s**, exit 0, under Python 3.11.5/jsonschema 4.23.0.
The prior 60 cases remain covered, with the integrated case extended to all
three amendments; 12 Mac cases and one module-launcher case were added.
`git diff --check` and shell syntax checks passed.

Before implementation, an offline observation using the reported update
reproduced `changed baseline: Mac versions.kernel`. The exact-pair and module
launcher regression cases failed against the unchanged implementation.

## Left for coordinator

Run **outside the sandbox**, from this worktree:

```sh
cd /Users/GaryT/Documents/Work/tools/knowledge-base-wt/P1g4
bash scripts/fp/check-baseline.sh
```

The post-change sandbox attempt passed **91 schemas, 32 tool pairs, 341
fixtures; local source/release hashes**, then exited 1 at the first Mac Qdrant
read with `FAIL: <urlopen error [Errno 1] Operation not permitted>`. It did not
reach a live Mac or bppc verdict. A connected exit-0 result remains required;
no full connected PASS is claimed. No implementation work remains known.

## Decision and review record

Pattern: coordinator-direct for a bounded extension of the existing amendment
contract, with independent read-only code review. Key decision: pin the exact
two-field map as for bppc, preserve the complete machine comparison, and leave
the frozen baseline intact. No new external effect or recovery boundary.

Grounded: whole-wiki search for baseline/amendment/kernel/macOS and the wiki
index → no relevant Mac authorization precedent; existing P1g/P1g3 records,
checker code and Brief P1g4 supply the contract and authorization. The quoted
2026-10-19 delegation is attributed to the brief: the dated decision was not
found in either accessible wiki copy. No model-backed KB query was necessary
for these local machine facts. This requested unit handoff is the durable
record for the focused change.

Review risks: rebound changes escaping exact scope, partial updates passing,
unlisted drift passing, frozen inputs changing, stale instrument hashes and
regressions to the earlier amendments.

Independent read-only review (`p1g4_review`): **no verified defects**. The reviewer
reran **73 tests in 26.68s** through the pinned launcher with pytest's cache
disabled, rejected **54** additional machine/collection drift and malformed
approval probes, and verified all 212 inventory fingerprints, release references
and baseline preservation. Review stayed offline. The inherited comparison
accepts the original frozen machine or the complete amended machine; partial
combinations of the serving-stack and OS updates remain rejected.
