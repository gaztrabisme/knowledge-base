# v8 Technical Shelf Intake

**Status:** C2 ingest, chunk, audit, regression, and sanity-set work is complete. All 166 manifest rows marked `ingest` have Markdown and nonempty chunk files.

The intake covers 185 files: 166 ingest rows, 2 byte-identical duplicate copies, 11 already-indexed works, and 6 philosophy-library files. The source links and catalog registration were completed during C1; see the [C1 report](../data/intake/C1-report.md).

The C2 audit passes strictly with 16 documented low-density exceptions. No front matter, trailing index, chapter-structure, garble, empty-chunk, or token-cap flags remain. PDF density was calibrated on 44 of 126 existing books at a 1,093 Markdown-character-per-page p05 floor. The 15-book regression set is byte-identical, and the 60-row sanity set resolves to chunks from 60 distinct new books across all 15 domains.

The full per-book metrics and rule changes are in the [C2 report](../data/intake/C2-report.md); exception evidence is in `data/intake/audit-exceptions.json`. No embeddings or retrieval index were generated. The outputs are ready for the later embedding/index stage on the other machine.
