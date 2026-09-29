# v9 C2 Report

**Updated:** 2026-09-30  
**Verdict:** PASS. All 29 v9 ingest rows have Markdown and nonempty chunks; the four books with index back matter were regenerated. The strict audit has one documented heading-count exception and no unexcepted flags.

## Results

- Markdown: 19,135,645 characters across 29 books.
- Parent chunks: **4,799**.
- Child chunks: **20,076**. This is the exact v9 child count and planned new-vector count.
- Back-of-book index cleanup: the three authoritative maps now cut at their back-matter anchors after the last mapped heading. `research-methods-psychology` had 22 named-index children and 5 index-only parents removed.
- Non-v9 integrity: **582/582** pre-existing Markdown/chunk files match `/tmp/u6-before.sha256` byte-for-byte.
- Regression: `scripts/regression_ingest.py` passed **15/15** byte-identical comparisons.
- No indexing, embedding, or Qdrant operation was run.

## Back-matter anchors

- `practical-cloud-security`: `Index`; the printed contents moves from the final chapter to the index.
- `bargaining-for-advantage`: `Notes`; the printed contents lists Notes, Selected Bibliography, and Index after Appendix B, so the appendices remain content.
- `how-to-read-a-paper`: `χ2-test see chi-squared test`, the first index-entry line after Appendix 2; both appendices remain content.
- The cleanup recognizes top-level `Names Index`, `Subject Index`, `Author Index`, and `Index of …` headings and was run only with `--slugs-from data/intake/v9-manifest.json`.

## Flag resolutions

- **Recovered EPUB front matter — `flawless-consulting`, `meddicc`, `research-ethics-integrity-social-scientists`, `hands-on-site-reliability-engineering`:** when EPUB heading recovery changes the text, ingestion now reapplies front/back stripping. The recovery-only fallback cuts after the leading front-matter heading sequence when the EPUB has no explicit “Chapter 1” label, while preserving the book title H1. A no-change recovery result gets no second pass.
- **PMBOK — `pmbok-guide-7e`:** the authoritative map's leading `Notice` and `Preface` entries were removed using `_is_front_matter_heading`; the first retained entry is `The Standard for Project Management`. The remaining 200 entries are unchanged. The map gate places 200/200 headings with no foreign headings.
- **Critical thinking — `critical-thinking-about-research`:** the PDF Markdown starts with `## 1 Seeking Trustworthy Knowledge`; the copyright line is at line 33, after that numbered opening heading. The audit had only treated explicit Chapter/Part labels and H1 headings as chapter starts, so it mistook the in-chapter copyright running header for front matter. Audit chapter detection now uses the same `_is_chapter_heading` rule as ingestion. This resolves the false positive without deleting extracted text.
- **Accepted heading-count exception — `getting-to-yes`:** Intentional heading-count exception: 14 chapters and 3 part headings from the EPUB navigation are represented at H1 after EPUB normalization, leaving only 4 headings at level H2 or deeper. This matches the navigation hierarchy, so promoting the H1 entries would misstate the source structure.

## Parents and children per book

| v9 slug | Parents | Children | Audit |
| --- | ---: | ---: | --- |
| `pmbok-guide-7e` | 117 | 523 | PASS |
| `agentic-mesh` | 330 | 755 | PASS |
| `bargaining-for-advantage` | 123 | 541 | PASS |
| `container-security` | 102 | 353 | PASS |
| `critical-thinking-about-research` | 141 | 824 | PASS |
| `designing-ai-interfaces` | 97 | 358 | PASS |
| `flawless-consulting` | 138 | 557 | PASS |
| `getting-to-yes` | 64 | 397 | EXCEPTION: only 4 headings at level >=2 |
| `hbr-guide-business-writing` | 103 | 364 | PASS |
| `hands-on-site-reliability-engineering` | 114 | 377 | PASS |
| `head-first-pmp` | 496 | 1,258 | PASS |
| `high-performance-browser-networking` | 228 | 696 | PASS |
| `how-to-read-a-paper` | 226 | 897 | PASS |
| `key-account-management` | 155 | 772 | PASS |
| `meddicc` | 66 | 359 | PASS |
| `practical-cloud-security` | 85 | 357 | PASS |
| `privacy-in-context` | 123 | 767 | PASS |
| `project-planning-scheduling-control` | 102 | 649 | PASS |
| `python-for-devops` | 254 | 1,112 | PASS |
| `real-world-software-development` | 130 | 410 | PASS |
| `research-ethics-integrity-social-scientists` | 85 | 718 | PASS |
| `research-methods-psychology` | 292 | 1,638 | PASS |
| `selling-to-big-companies` | 112 | 399 | PASS |
| `software-engineering-at-google` | 309 | 1,255 | PASS |
| `art-of-assembly-language` | 315 | 1,538 | PASS |
| `challenger-sale` | 109 | 439 | PASS |
| `flawless-consulting-fieldbook-companion-2e` | 136 | 533 | PASS |
| `new-ethics-of-journalism` | 89 | 522 | PASS |
| `value-based-fees` | 158 | 708 | PASS |
| **Total** | **4,799** | **20,076** | **29 books** |

## Acceptance

- `bash .claude/plan-goal/verify/u6c.sh` — PASS (exit 0): index-text checks and u6 pass; the five map-placement checks pass.
- Its one loose index-like text match is `research-methods-psychology-p113-c3`, a numeric regression table under `Chapter Review`, not index content.
- `bash .claude/plan-goal/verify/u3.sh` — PASS (exit 0): regression 15/15; broken-book repairs 8/8; clean source books newly flagged: none.
- `.venv/bin/python -m pytest tests -q` — PASS: 103 passed.
- `/tmp/u6-before.sha256` comparison — PASS: 582/582 pre-existing Markdown/chunk files match.
