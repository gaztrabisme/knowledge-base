# KBch: printed chapter numbers

Owner: Gary. Verified 2026-10-20 on branch `unit/fp-KBch`; changes are uncommitted.

## Behavior

Numeric technical-book queries now select an exact printed chapter number before
falling back to a 1-based position. Fallback responses begin with
`[Used positional index N; no printed chapter label matched.]`.
Case-insensitive `Chapter N`, `N Title`, and `N. Title` labels are supported.
Numeric queries cannot fall through to substring matching (12 cannot select 120).

One parser supplies chapter titles and extraction boundaries. It includes chapters
under parts and explicit `Chapter N` headings behind intermediate wrappers, ignores
fenced examples, and ends a chapter at its next sibling or ancestor heading.
Title, prefix, partial-title, and part-title reads remain supported. Error messages
list all discovered headings with their printed labels and explicit positions;
`list_books` retains its existing fields and shares those titles through
`book_chapters`.

## Evidence

- Before implementation, fixture tests reproduced unreachable nested chapter 12,
  front matter being returned for chapter 1, and missing fallback notices. The
  focused suite had 21 failures, 8 passes, and 2 real-data skips.
- Independent read-only review found explicit chapters hidden behind a book-title
  or intermediate part wrapper. Both added regression cases failed before the
  correction. The final review reported no remaining findings.
- `uv run pytest -q tests -k "chapter or server"`: **40 passed, 245 deselected**,
  no skips, 5 dependency deprecation warnings, 22.63 seconds.
- `bash scripts/fp/check-baseline.sh`: **PASS**, including 91 schemas,
  32 tool pairs, 341 fixtures, Mac/bppc checks and frozen controls.
- `bash scripts/fp/check-catalog.sh`: **PASS**, including 11 checker tests,
  425,307 child/parent locators, live payload checks and 4,756 frozen control hits.
- Frozen contract fixtures are unchanged; neither gate required a fixture update.
- `git diff --check`: **PASS**.

Actual reads returned `## Chapter 12 Reversing arm64 macOS Malware` for
`arm-assembly-internals`, chapter 12, and `# Chapter 22: Patching Binaries` for
`ghidra-book`, chapter 22. Both conditional real-book tests ran successfully.

## Local test setup and scope

The worktree initially omitted `data/markdown` and the philosophy chunk required
by an existing selected test. Four ignored, mode-0444 copies were read from the
main checkout into this worktree: both technical books' markdown plus Mitchell's
Tao Te Ching markdown and chunks. No source data or main-checkout file was changed.
The tests remain conditional when the two technical books are absent elsewhere.

A worktree-local `.venv` uses the supplied Python 3.11.5 with system site packages.
FastMCP 4.0.5, pytest 9.1.1 and OpenCC 0.1.7 were installed locally. The pytest
command used `UV_NO_SYNC=true`, `UV_CACHE_DIR=/private/tmp/KBch-uv-cache`, and
`PYTHONDONTWRITEBYTECODE=1`, preserving protected dependency files and caches.
The baseline/catalog scripts used their original checker runtime.

Pattern: coordinator-direct implementation with independent review. Grounded in
the existing books/server code, heading-recovery fixtures, and actual book
headings; no general literature search or model execution was needed for this
local markdown-layout defect. This report is the completion record because
`wiki/` is explicitly protected. Search, indexing, all protected paths, and the
main checkout were left unchanged.
