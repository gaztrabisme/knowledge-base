# FP P1 — Baseline and contracts

Status: READY FOR COORDINATOR / GARY REVIEW (2026-10-14). Owner: P1 worktree. The connected mechanical acceptance command passes; human schema approval is pending. Original v10 index-build checkpoint provenance remains unverified, explicitly separate from the pinned current control checkpoints and preserved release bytes.

## Scope and acceptance

Freeze v10 identity, membership, model/config revisions and reference results; draft versioned shared-interface contracts and a tested-release manifest; implement `bash scripts/fp/check-baseline.sh`. Only small records enter this tree. No benchmark or model was run, GPU used, remote file/Qdrant content written, commit made or push performed.

Gary's 2026-10-14 choices supersede the older placement/host suggestions: pi-mind owns the harness-side repo and shared interface; KB and archive keep their own repos behind one installer. The Mac owns harness, memory and infrastructure; bppc runs the sandboxed LLM engine. Its existing Qdrant mirror is read solely to preserve the historical control.

## Key decisions and grounding

- Pattern: intrinsic-artifact gate, with independent review required by the dev skill before handoff. User's explicit build brief authorizes this work. No further build permission was requested.
- Grounded: approved main-checkout design/brief, the 2026-10-14 decision entry and log excerpts, `CLAUDE.md`, relevant `knowledge_base/` modules, the four requested evaluation/catalog scripts, existing edition/packaging tests and `data/bench/gate-v10.md` → preserved legacy signatures, separate snapshots/provenance, counts, read-only sources and receipt semantics. General literature search was not needed for this project-specific freeze; no KB query loaded models.
- Grounded: pi-mind `inputs.ts`, `common.ts`, `memory.ts`, server/service code, published schemas and independent fixture corpus → reused W1 field names and imported 17 schema/fixture pairs byte-for-byte. All broader-interface differences are explicit in the approval packet and disagreement register.
- Grounded: bppc frozen manifest, fresh gate outputs/metadata, offline model snapshots and M1c mapping → recorded exactly what exists; no historical benchmark scores were substituted for the fresh control.
- External effects: remote probe uses only file reads, Python/package version inspection, Docker inspect and Qdrant GET. It is sent on SSH stdin, never installed remotely. No KB/model imports or GPU calls. Proving evidence: inspected `remote_probe.py` / `baseline_io.py` and independent review.
- User-designated durable record is this report; `wiki/` remains untouched. Contract copies are staged here for review and transfer to canonical pi-mind ownership; this does not implement the gateway or move repositories.

## Frozen evidence

Canonical small records: [baseline.json](../../../data/baseline/baseline.json), [tested-release-v10.json](../../../data/baseline/tested-release-v10.json), [redirects-m1c.json](../../../data/baseline/redirects-m1c.json), [approval-source.json](../../../data/baseline/approval-source.json).

| Item | Frozen value / evidence |
|---|---|
| Mac alias at capture | `developer_knowledge` → `developer_knowledge_v10`, verified by GET; current target is informational |
| Collection | 330,778 points; 1,024-dimensional Cosine; BM25 `idf`; HNSW/optimizer/WAL/on-disk/quantization configuration recorded verbatim |
| Source membership | 328 source slugs; exact per-source counts and frozen per-source JSONL hashes; IDs/payloads/BM25 remain on bppc |
| Frozen manifest | SHA-256 `690d5cc3285ac1bd9e861b3ff3810bb7159c6828d944a8eb12e044be45c793ce` |
| Membership fingerprint | SHA-256 `ba08b7ee1686a263682632e6607c34b05e73a4c7a28a3e5c406e4e163bfc0c69` |
| Jina control checkpoint | `6856e76bb72982e58de0620458a4e8b3614da340` |
| BM25 checkpoint | `22b8d2af71a76161e18dd432d2cee0eefa66e412`; FastEmbed 0.8.0; stopword/config assets and implementation hashed |
| Ettin-150M checkpoint | `025501c4e0f9bbeb4c5b198318e0089ff061cc14` |
| Fresh hard control | 438 queries; saved NDCG@10 0.7393, query-hit recall@10 0.9521 |
| Fresh easy control | 199 queries; saved NDCG@10 0.9044, query-hit recall@10 1.0000 |
| Fresh sanity control | 30 queries; saved NDCG@10 0.6463, query-hit recall@10 0.9333 |
| Control inputs/outputs | All original labels, sanity plan, aggregate JSON, per-query JSONL and metadata by hash; metadata binds frozen manifest, query inputs, code revisions and runtime packages |
| Query/config revisions | Fresh-control source hashes and runtime overrides pinned, including descriptive-heading reranking, 50/50/50 candidates, top 10, floor 4/minimum 3, 250/1,900-token child/parent caps; repo server/config/eval sources pinned to Git commit `a7d5a90` and blob IDs |
| Server/Qdrant | KB package 0.1.0 with Git/file revisions; both Qdrant servers 1.18.2, commit `44ad62f8cd69642be5afa6441612525e24a0d063`; bppc container image ID pinned |
| Mac | macOS 26.6.2, Darwin 25.6.0 arm64; checker and project Python 3.11.5; query package versions recorded |
| bppc | Ubuntu 24.04.4 LTS, kernel 7.0.0-28-generic x86_64; system/gate Python 3.12.3; gate package versions recorded |
| Existing release | `data-v10` manifest and three actual core/philosophy parts on the main checkout, hashes/sizes verified; no parts copied into git |

The saved metrics above are reported M1 results, not measurements rerun by P1. P1 directly verified file hashes, populations, source identity and target versions.

M1c redirect: nine PostgreSQL parents, eight mapped and one explicitly unmapped (`postgresql-14-internals-p140`); seven hard and four easy queries touched, zero sanity. The mapping, old/new PostgreSQL inputs, M1b manifest/audit and original/remapped label files are hashed and cross-checked. It records literal token-overlap correspondence, not semantic relevance approval or automatic locator reattachment. Original v10 labels are preserved.

The frozen manifest's original source-file hashes predate M1's restored PostgreSQL inputs. Those source files were not an exact v10 payload match at freeze time (463 source children missing from files, 518 excluded, 1,160 parent-text differences). Frozen v10 payload/BM25 JSONL and the original release parts are the authority for this baseline; today's source files are not silently substituted.

## Deliverables and operations

- `data/baseline/contracts/v1/`: 91 versioned schemas, including 32 request/response pairs covering every design tool, source identity, six locator variants, evidence/catalog, exact W1 memory types, proposed annotation extensions, read metadata and P7 release format.
- `data/baseline/fixtures/v1/`: 341 positive/negative cases, including imported independent W1 fixtures and explicit unavailable-backend/locator/false-absence branches.
- [CONTRACTS.md](../../../data/baseline/CONTRACTS.md): approval page. [disagreements.json](../../../data/baseline/disagreements.json) records each compatibility difference, current behavior and proposed shape; no disagreement is treated as approved.
- `contracts-lock.json`: schema, fixture, provenance, generator, checker and test hashes. The checker verifies exact pi-mind copy equality against commit `9911905ced69d4a3d5fee2ca8ed5b7344f2b7f34` as well as every pinned source; equality with pi-mind's working tree is diagnostic.
- `.gitignore`: a scoped `data/baseline/` exception so normal review/add includes these small files. Largest individual baseline record is under 150 KB. No large payload/model/release data enters git.
- `scripts/fp/build_contracts.py`: durable schema generator using syntax-only inspection of legacy Python signatures and an export of pi-mind TypeBox inputs; no service/model imports.
- `scripts/fp/capture_baseline.py`: first-capture builder, refuses to overwrite a freeze. `remote_probe.py` can obtain a read-only observation over SSH stdin.
- `scripts/fp/refresh_contract_lock.py`: explicitly refreshes draft schema/instrument hashes after review edits. It never recaptures source observations and is never called by the acceptance checker.
- `scripts/fp/validate_contracts.py`: offline validation of all schemas/references/fixtures or a selected instance; standard `jsonschema==4.23.0` is pinned in `requirements.txt`.

Coordinator rerun from this worktree: `bash scripts/fp/check-baseline.sh`. It needs the Mac Qdrant endpoint, main-checkout release files, pinned repo/pi-mind Git commits and read-only SSH to bppc. There is no offline-success bypass. Explicit location overrides are `FP_MAIN_CHECKOUT`, `FP_PI_MIND_ROOT`, `FP_BPPC_ROOT`, `FP_BPPC_HOST`, `FP_QDRANT_URL` and `FP_PYTHON`; effective inputs are printed. Missing commits/blobs, changed frozen hashes, collection configuration/versions or immutable release files fail. Working-tree changes, edits to uncommitted intake documents and alias promotion are informational. Approval excerpts are checked without freezing unrelated future wiki additions.

The P7 manifest remains `baseline-only`: it verifies v10 artifact/control identity and explicitly leaves joined-product installation/activation and the supported harness subset pending. Its installation matrix records the named capability per receipt; identity inspection is not represented as a gateway installation test. A future tested/released manifest must contain receipts for every included installation row and no pending included capability; unavailable clients can remain explicitly excluded from the selected matrix.

## Verification and independent review

Original P1 acceptance: `bash scripts/fp/check-baseline.sh` **PASS**, including 420 bppc file hashes, all frozen membership/payload/sparse/model assets, 438/199/30 controls and original/remapped labels, actual local release parts, Mac live alias/config/versions, pi-mind schema/fixture equality and release declaration reconciliation. Captured output: [P1-check-baseline.txt](P1-check-baseline.txt). P1f verification is recorded below.

Original P1 focused failure suite: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_fp_baseline.py -v` **PASS**, 17 tests. Cases discriminate changed/missing local and remote files, alias/point drift under the original gate, root escape, unreachable schema references, wrong legacy payload/arguments, unknown versions, altered evidence text/metadata, false absence over failed or zero-processed required units, and unsupported release/routing/model/component/part claims. Schema fixture suite passes 91 schemas / 32 tool pairs / 341 cases.

Independent reviewer `/root/p1_review` inspected code/artifacts and ran offline tests only. Pre-registered weaknesses: omitted source references, false-positive check paths, unbound release claims, overly loose schemas, missing disagreement disclosure and inaccurate capability claims. First pass found five defects: release declarations not reconciled to baseline; false absence allowed zero processed units; evidence metadata not bound to returned evidence; verified/released installation claims too loose; baseline directory hidden by ignore rule. All were fixed, with regression cases. Focused re-review rejected every original counterexample and found no remaining consequential code defect in that scope. Connected acceptance was rerun by the parent; no reviewer SSH/model/GPU operations occurred.

An amendment added captured component pins to the baseline record and strengthened contract/instrument checks after review. The frozen remote files, aliases, model/control/label identities and machine observations did not change. Tracked protected paths have no diff; only `.gitignore` and the P1-specific new artifact/script/test/report paths changed.

## Remaining decisions and evidence limits

1. Gary/coordinator must approve the actual contract packet. This work does not claim row 3's human approval from a green shell command.
2. Current Jina/BM25/Ettin offline control revisions and assets are pinned. **Original v10 dense index-build checkpoint provenance is not found** in the preserved release/gate records; it cannot be inferred merely from one cache snapshot. Original index bytes remain preserved by the real `data-v10` part hashes. Exact historical rebuild provenance remains an unmet evidence item, not a fabricated revision or a reason to change stored v10.
3. P2/P4/P7 must prove authenticated scope enforcement, source target identities, selector reattachment, transactional recovery, joined response adapters, per-hit legacy metadata/clipping/budget fidelity, installed routing and cross-harness reads. P1's structural validator does not certify those running-service behaviors.
4. The 6,000-token budget is for the answer-benefit experiment only; the one-write-retry policy is receipt-first and service-enforced. Mac end-to-end speed acceptance ratio remains Gary's open choice 10.

No commit/push or promotion was made. Wiki, Library, `.cache`, README/distribution files and all prohibited search/index/config files were left unchanged.

## P1f — Frozen-evidence follow-up

Status: READY FOR COORDINATOR (2026-10-14). Owner: P1 worktree; coordinator commits.

- Scope: pin repository sources to baseline commit `a7d5a90`, retain P1's hashes/byte counts for uncommitted documents as observations, verify physical v10 independently of the live alias, and pin imported W1 copies to their pi-mind commit. Release manifest/parts remain strict.
- Pattern: intrinsic-artifact gate. Temporary repositories and fixtures discriminate mutable drift from changed frozen evidence; no real source files were edited for tests.
- Grounded: P1 report, checker, shared I/O and baseline record → the original gate hashed live source files and compared the whole Mac observation, including aliases. This project-specific provenance change is grounded in those records; no literature or model query was needed.
- Implementation: `baseline.json` now records `source_revisions`, 53 Git blob IDs (13 repo, 40 pi-mind) and two explicit uncommitted-document observations. Original SHA-256 values/byte counts, component pins and captured remote/Mac observations are preserved. Four main-checkout release artifacts remain strict. Release references use the same source policy, so duplicate code pins cannot reintroduce a live-file failure.
- Reproduction: the original `verify_artifact` rejected a temporary code file after a legitimate edit (`missing/changed artifact: test:config.py`). New tests use temporary repos/files only, including later commits and deleted working-tree files; no protected real source is modified.
- Mechanical verification: `python3 -m unittest discover -s tests -p test_fp_baseline.py` **PASS**, 30 tests, including an integrated checker test with temporary code/document drift, a moved alias and stubbed services, plus changed release bytes failing. Connected `bash scripts/fp/check-baseline.sh` **PASS**: 91 schemas / 32 pairs / 341 fixtures, physical v10, immutable release files and 420 bppc hashes. Both commands were rerun after the review fix. `contracts-lock.json` and release baseline/inventory/receipt references were refreshed with `refresh_contract_lock.py`; original observations were not recaptured. `git diff --check` passes.
- Review scope/expected weaknesses: Git pin failures incorrectly demoted to observations, duplicate release references reintroducing live code checks, relaxed immutable release checks, copies checked against the wrong pi-mind version, and aliases masking changed physical v10. Independent reviewer `/root/p1f_review` found one verified capture defect: a missing Git blob could be classified as an uncommitted observation. Capture now determines membership with `git ls-tree` and requires the committed blob for tracked paths. Regression tests reject missing blobs/commits and allow truly uncommitted documents. Read-only re-review verified the original corrupt-object counterexample and missing-tree failures are rejected, all 30 tests and refreshed lock/reference hashes pass, and no consequential issue remains in scope.
- Handoff: coordinator reruns both acceptance commands outside the sandbox and checks a temporary working-tree code edit. No worktree commit, merge, push, GPU or remote write was made; protected tracked paths have no diff. Human contract approval and later installation gates remain pending as before.
