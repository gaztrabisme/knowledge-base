# C1: v8 Technical Shelf Intake Report

**Verdict: FAIL — metadata and registration are ready, but the required hard links could not be created in this session.**

No files were ingested, chunked, or indexed.

## Counts by action

| Action | Files |
|---|---:|
| `ingest` | 166 |
| `skip-duplicate` | 2 |
| `skip-indexed` | 11 |
| `philosophy` | 6 |

## Counts by domain

| Domain | Manifest rows | Ingest rows |
|---|---:|---:|
| `ai-engineering` | 12 | 12 |
| `applied-ml` | 12 | 12 |
| `architecture` | 13 | 6 |
| `cpp` | 22 | 22 |
| `data-engineering` | 25 | 24 |
| `data-science` | 13 | 13 |
| `databases` | 5 | 5 |
| `design` | 20 | 19 |
| `distributed-systems` | 3 | 2 |
| `frontend` | 17 | 17 |
| `management` | 11 | 5 |
| `reverse-engineering` | 6 | 6 |
| `rust` | 1 | 0 |
| `security` | 11 | 11 |
| `software-engineering` | 6 | 5 |
| `systems-ops` | 8 | 7 |

## Skips and reasons

| Action | File | Reason |
|---|---|---|
| `skip-duplicate` | `Analytics Tools for Optimizing UX (Simon Mackie)-1.pdf` | byte-identical copy of the kept file Analytics Tools for Optimizing UX (Simon Mackie).pdf |
| `skip-indexed` | `Architecture Patterns with Python (Bob Gregory, Harry Percival).pdf` | already registered in BOOKS as architecture-patterns-with-python |
| `skip-indexed` | `Building Microservices (Sam Newman).pdf` | same work is already registered as building-microservices-2e; the live second edition is retained |
| `skip-indexed` | `Building Microservices Designing Fine-Grained Systems (Sam Newman).pdf` | second edition is already registered as building-microservices-2e |
| `skip-indexed` | `Building Multi-Tenant SaaS Architectures (Tod Golding).pdf` | already registered in BOOKS as building-multi-tenant-saas |
| `skip-indexed` | `Designing distributed systems patterns and paradigms for scalable, reliable services (Brendan Burns).pdf` | already registered in BOOKS as designing-distributed-systems |
| `skip-indexed` | `Learning API Styles (for Raymond Rhine) (Lukasz Dynowski, Marcin Dulak).pdf` | already registered in BOOKS as learning-api-styles |
| `skip-indexed` | `Learning Domain-Driven Design Aligning Software Architecture and Business Strategy (Vladik Khononov).pdf` | already registered in BOOKS as learning-domain-driven-design |
| `philosophy` | `ORIGINAL LIBRARY - ENGLISH VERSION.docx.pdf` | personal philosophical library material; excluded from the technical shelf |
| `skip-duplicate` | `Practical Lakehouse Architecture (Gaurav Ashok Thalpati)-1.pdf` | byte-identical copy of the kept file Practical Lakehouse Architecture (Gaurav Ashok Thalpati).pdf |
| `skip-indexed` | `Production-Ready Microservices Building Standardized Systems Across an Engineering Organization (Susan J. Fowler).pdf` | already registered in BOOKS as production-ready-microservices |
| `skip-indexed` | `Site Reliability Engineering How Google Runs Production Systems (Betsy Beyer, Chris Jones, Jennifer Petoff etc.).pdf` | already registered in BOOKS as site-reliability-engineering |
| `skip-indexed` | `Software Architecture Metrics Case Studies to Improve the Quality of Your Architecture (Christian Ciceri, Dave Farley, Neal Ford etc.).pdf` | already registered in BOOKS as software-architecture-metrics |
| `philosophy` | `Tao Te Ching (Lao Tzu, Jonathan Star).epub` | Tao Te Ching philosophical work; excluded from the technical shelf |
| `philosophy` | `Tao Te Ching (Stephen Mitchell, Lao Tzu).pdf` | Tao Te Ching philosophical work; excluded from the technical shelf |
| `philosophy` | `Tao Te Ching (Tse Lao).epub` | Tao Te Ching philosophical work; excluded from the technical shelf |
| `philosophy` | `Thư Viện - Master OS .pdf` | personal philosophical library material; excluded from the technical shelf |
| `skip-indexed` | `rustforcplusplusdeveloper.epub` | already registered in BOOKS as rustforcplusplusdeveloper |
| `philosophy` | `本源圖書館 - 繁體中文版.docx.pdf` | personal philosophical library material; excluded from the technical shelf |

## Readability

PyMuPDF opened and extracted TOCs/opening text for all 185 source files with no extraction exceptions. The opening-page text for `Exploratory Data Analysis (John W. Tukey).pdf` was blank; its TOC was extracted and used for classification.

**Files that could not be opened:** none.

## Validation

- `scripts/build_intake_manifest.py`: PASS — wrote 185 manifest rows (166 ingest, 19 excluded).
- Duplicate check: PASS — both `-1.pdf` copies have byte-identical SHA-256 hashes to their retained copies.
- `scripts/check_catalog.py data/catalog.json`: PASS — `OK: 292 entries pass`.
- `import knowledge_base.books`: PASS — imported cleanly.
- `scripts/check_intake.py`: FAIL — inventory, domains, `BOOKS`, and catalog checks pass; 166/166 expected hard links are missing.

## Blocker and remaining work

Creating a hard link with `os.link` from `/Users/GaryT/Documents/books` returned `EPERM` (errno 1). The same operation failed with targets in both the workspace and `/private/tmp`, confirming that the managed filesystem exposes the source directory as read-only. The domain directories, `BOOKS` blocks in `knowledge_base/config.py` and `scripts/remote_index.py`, and 166 catalog entries are present. No copy or symlink was substituted for a hard link.

To finish, the task environment must permit hard-link creation from the source tree. Then create each ingest target at `knowledge-base/<domain>/<slug>.<ext>` and rerun `scripts/check_intake.py`; the report and metadata do not need to be regenerated.
