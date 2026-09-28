#!/usr/bin/env python3
"""Re-ingest a fixed v7.1/v6 sample and require byte-identical markdown."""

import difflib
import tempfile
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from knowledge_base.config import MARKDOWN_DIR, SOURCE_DIRS
from knowledge_base.ingest import convert_pdf_with_toc, ingest_epub, ingest_pdf

V71_BOOKS = (
    "ai-powered-search", "llms-in-production", "building-reliable-ai-systems",
    "generative-ai-in-action", "transformers-in-action", "human-in-the-loop-ml",
    "interpretable-ai", "ml-platform-engineering", "coding-with-ai",
    "software-testing-with-genai",
)
OLDER_PDF_BOOKS = (
    "designing-great-web-apis", "production-ready-microservices",
    "digitalocean-redis", "release-it", "oauth-rfcs-book",
)


def find_source(slug: str, require_toc: bool = False) -> Path | None:
    for source_dir in SOURCE_DIRS.values():
        for source in source_dir.glob(f"{slug}.*"):
            if source.suffix.lower() not in {".pdf", ".epub"}:
                continue
            if require_toc and (source.suffix.lower() != ".pdf" or convert_pdf_with_toc(source) is None):
                continue
            return source
    return None


def main() -> int:
    failures = []
    compared = 0
    with tempfile.TemporaryDirectory(prefix="kb-ingest-regression-") as temp:
        tempdir = Path(temp)
        for slug in V71_BOOKS + OLDER_PDF_BOOKS:
            source = find_source(slug, require_toc=slug in OLDER_PDF_BOOKS)
            baseline_path = MARKDOWN_DIR / f"{slug}.md"
            if not source or not baseline_path.exists():
                failures.append((slug, "missing source or baseline markdown", ""))
                print(f"FAIL {slug}: missing source or baseline markdown")
                continue
            output = tempdir / f"{slug}.md"
            try:
                if source.suffix.lower() == ".pdf":
                    ingest_pdf(source, output)
                else:
                    ingest_epub(source, output)
                actual = output.read_text(encoding="utf-8")
            except Exception as error:
                failures.append((slug, f"re-ingest error: {error}", ""))
                print(f"FAIL {slug}: re-ingest error: {error}")
                continue

            compared += 1
            expected = baseline_path.read_text(encoding="utf-8")
            if actual == expected:
                print(f"PASS {slug}: byte-identical")
                continue
            diff = "".join(difflib.unified_diff(
                expected.splitlines(keepends=True), actual.splitlines(keepends=True),
                fromfile=f"data/markdown/{slug}.md", tofile=f"reingested/{slug}.md", n=2,
            ))
            failures.append((slug, "markdown differs", diff))
            print(f"FAIL {slug}: markdown differs\n{''.join(diff.splitlines(keepends=True)[:50])}")

    print(f"\nRegression result: {compared}/{len(V71_BOOKS) + len(OLDER_PDF_BOOKS)} compared; "
          f"{len(failures)} differences/errors.")
    return 1 if failures or compared != len(V71_BOOKS) + len(OLDER_PDF_BOOKS) else 0


if __name__ == "__main__":
    raise SystemExit(main())
