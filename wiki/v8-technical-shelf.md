# v8 Technical Shelf Intake

**Status:** Manifest, metadata, domain configuration, `BOOKS` blocks, and catalog rows are prepared. The acceptance gate is blocked because the managed filesystem denies hard-link creation from the source library.

The intake covers 185 files: 166 ingest rows, 2 byte-identical duplicate copies, 11 already-indexed works, and 6 philosophy-library files. PyMuPDF opened all sources without errors. The two duplicate pairs were verified by matching SHA-256 hashes.

The user-facing record is [C1-report.md](../data/intake/C1-report.md). Reproduction scripts are `scripts/build_intake_manifest.py` and `scripts/check_intake.py`; the source decisions live in `data/intake/v8-curation.json`.

`check_catalog.py` passes with 292 entries, and `knowledge_base.books` imports cleanly. `check_intake.py` reports 166 missing hard links. `os.link` returned `EPERM` for destinations in both the workspace and `/private/tmp`, because `/Users/GaryT/Documents/books` is read-only under the current session policy. No copies or symlinks were substituted.

**Next:** Run `os.link` for the ingest rows once this environment permits links from the source directory, then rerun `scripts/check_intake.py`.
