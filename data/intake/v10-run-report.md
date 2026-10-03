# v10 official frontend docs candidate run report

Run date: 2026-10-02. Candidate only; no alias promotion was performed.

## Preflight

- Mac Qdrant `developer_knowledge_v9`: green, 286,723 points. `developer_knowledge_v8` and `philosophy` were left untouched.
- Mac alias snapshot: `developer_knowledge` → `developer_knowledge_v9`.
- bppc (`192.168.1.17`, LAN first): v9 green, 286,723 points; no aliases. GPU preflight showed RTX 5080 with 136 MiB used and 15,729 MiB free.
- Candidate name `developer_knowledge_v10` was absent; add collection `developer_knowledge_v10_add`. The add contains 44,055 child vectors, below the 60,000 cap.

## Sources and child counts

Retrieved 2026-10-01. URLs, pinned source commits, licence terms, attribution and per-book front matter are recorded in [`data/sources/docs/SOURCES.md`](../sources/docs/SOURCES.md). Source data collections BCD and web-features are live links only and were not indexed.

| Book | Child vectors |
|---|---:|
| `mdn-web-docs` | 27,255 |
| `web-dev-baseline` | 2,795 |
| `whatwg-html` | 3,240 |
| `wai-aria-apg` | 358 |
| `wcag-22` | 305 |
| `react-dev` | 4,912 |
| `angular-dev` | 1,004 |
| `playwright-docs` | 4,186 |
| **Total** | **44,055 / 60,000** |

Source licence summary: MDN CC BY-SA 2.5 prose / CC0 samples; web.dev archived prose CC BY 3.0 and code Apache-2.0, current Baseline supplement CC BY 4.0; WHATWG CC BY 4.0 prose / BSD-3-Clause code portions; WAI-ARIA APG W3C Software and Document License; WCAG 2.2 W3C Document License; React CC BY 4.0 docs / MIT code; Angular CC BY 4.0 docs / MIT code; Playwright Apache-2.0. BCD is CC0-1.0 and web-features Apache-2.0; both are data and not indexed.

## Acquisition, conversion and transfer

Eight prose sources were acquired from their official repositories or generated assets and converted to one Markdown book each with a book H1 and page/section headings beneath it. `scripts/ingest_docs.py` strips site chrome and source macros while preserving meaningful prose and code examples. The converter's 8 tests passed through the CPU wrapper; `git diff --check` passed. Child counts are in `data/intake/v10-docs-chunk-counts.json`.

Chunk files were transferred to bppc over LAN and all 8 SHA-256 checks matched. On bppc, `remote_index.py` built exactly 44,055 vectors in `developer_knowledge_v10_add`. The closed embedded add store was transferred back over LAN (736,641,024 bytes; 704 MiB on disk) and its local exact point count was 44,055.

An initial bppc run was stopped during model loading before indexing; it wrote no vectors. The final run used a clean `~/kb-work/v10/qdrant-final` store.

## Candidate build and verification

The bppc mirror was built from v9 plus the add collection and verified before running the gate. The exact build and verify JSON is also saved in `data/intake/build-bppc.json` and `data/intake/verify-bppc.json`.

- bppc build:

```json
{"add_collection":"developer_knowledge_v10_add","add_count":44055,"copied_from_src":286723,"dst":"developer_knowledge_v10","dst_count":330778,"expected_dst_count":330778,"overwrites":0,"repaired_add_existing":0,"repaired_src_existing":0,"skipped_add_existing":0,"skipped_src_existing":0,"src":"developer_knowledge_v9","src_count":286723,"upserted_from_add":44055}
```

- bppc verify:

```json
{"add_count":44055,"dst_count":330778,"expected_dst_count":330778,"identical":true,"overwrites":0,"sampled_add":100,"sampled_src":100,"src_count":286723}
```

- Mac build (saved in `data/intake/v10-build-mac.json`):

```json
{"add_collection":"developer_knowledge_v10_add","add_count":44055,"copied_from_src":286723,"dst":"developer_knowledge_v10","dst_count":330778,"expected_dst_count":330778,"overwrites":0,"repaired_add_existing":0,"repaired_src_existing":0,"skipped_add_existing":0,"skipped_src_existing":0,"src":"developer_knowledge_v9","src_count":286723,"upserted_from_add":44055}
```

- Mac verify (saved in `data/intake/v10-verify-mac.json`):

```json
{"add_count":44055,"dst_count":330778,"expected_dst_count":330778,"identical":true,"overwrites":0,"sampled_add":100,"sampled_src":100,"src_count":286723}
```
- The Mac candidate is green at 330,778 points. Alias remains mapped to v9.

## Gate results

Same RTX 5080 on bppc, same hybrid retrieval and reranking pipeline, 50 candidates. Hard and easy v9 query sets were identical between runs. The 30-query sanity plan with expected source and section was written before retrieval results were viewed.

| Gate metric | Threshold | v9 | v10 | Result |
|---|---:|---:|---:|---|
| Hard NDCG@10 drop | ≤ 0.010 | 0.7409 | 0.7393 | drop 0.0016 — PASS |
| Hard recall@10 drop | ≤ 0.005 | 0.9521 | 0.9521 | drop 0.0000 — PASS |
| New-doc sanity recall@10 | ≥ 0.80 | — | 28/30 = 0.9333 | PASS |
| Easy NDCG@10 (informational) | — | 0.9041 | 0.9044 | +0.0003 |
| Easy recall@10 (informational) | — | 1.0000 | 1.0000 | unchanged |

**Verdict: PASS.** Full table and query-level record: [`data/bench/gate-v10.md`](../bench/gate-v10.md). The two sanity misses were:

1. `web-dev-baseline` / “Optimize Interaction to Next Paint”: “When optimizing INP, how can developers reduce the delay before an event handler begins running?”
2. `whatwg-html` / “The popover target attributes”: “How can a button declare which popover it controls in HTML, including the relationship used to invoke it?”

Both gold documents reached fusion top 50 but fell outside the reranked top 10. Paired significance: hard NDCG delta −0.0017 (95% CI [−0.0035, −0.0002], sign p .8238, Wilcoxon p .1044; classified as noise by the existing gate script), with no recall changes. Easy NDCG delta +0.0004 by per-query scores, 95% CI [0, +0.0011], p=1.0; no recall changes.

## MDN scope and omissions

MDN contained 12,294 Markdown pages. The selected scope was 3,382 pages (3,382 included, 8,912 excluded): guides and references for HTML, CSS, ARIA/accessibility, SVG, plus the requested DOM, Canvas, WebGL basics, Web Animations, Intersection/Resize Observer, Popover, Dialog, Fetch, Performance and Media Queries API topics. It produced 27,255 child vectors, so no further cap-driven trim was needed.

MDN pages left out by scope: 6,891 API pages outside the requested API set; 1,308 exhaustive JavaScript built-in/reference pages; HTTP 328; MathML 55; media 1; performance 1; privacy 6; progressive web apps 52; security 46; URI 14; WebDriver 102; XML 106; CSS index 1; root index 1. The JavaScript guides were retained. The machine-readable browser compatibility dataset was not indexed.

## Acceptance

The exact required acceptance chain exited 0 and printed `ACCEPTANCE PASS`: branch `docs-v10`; `data/bench/gate-v10.md` exists with `Verdict: PASS`; Mac `developer_knowledge_v10` is green; `/aliases` still maps `developer_knowledge` to `developer_knowledge_v9`.
