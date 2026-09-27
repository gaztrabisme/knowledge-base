"""FastMCP server exposing semantic search over ML books."""

import json
import re
import subprocess

from fastmcp import FastMCP

from .calllog import logged
from .config import BOOKS, CHUNKS_DIR, MARKDOWN_DIR
from .books import _chapter_title, book_chapters, book_domain, resolve_book
from .search import get_client, hybrid_search

_CHUNK_ID_RE = re.compile(r"^(.+)-p(\d+)-c(\d+)$")

mcp = FastMCP(
    "Developer Knowledge Base",
    instructions=(
        "Hybrid semantic and keyword search over 126 technical books: ML and deep learning, "
        "AI engineering, databases, security, software architecture and engineering, "
        "distributed systems, Rust, and systems/ops."
    ),
)


def _unknown_book_error(book: str, suggestions: list[str]) -> str:
    closest = ", ".join(suggestions)
    return f"Unknown book '{book}'. Closest slugs: {closest}. Call list_books() for all slugs."


def _format_search_result(result, detail: str) -> dict:
    if detail == "brief":
        return {
            "score": round(float(result.score), 4),
            "book": result.book,
            "book_title": result.book_title,
            "heading_path": result.heading_path,
            "text": result.child_match,
            "chunk_id": result.child_id,
        }
    full = result.to_dict()
    full["book_slug"] = result.book
    return full


@mcp.tool()
@logged
def search(
    query: str,
    top_k: int = 10,
    book: str | None = None,
    hyde_passage: str | None = None,
    extra_queries: list[str] | None = None,
    bm25_keywords: list[str] | None = None,
    detail: str = "brief",
) -> list[dict]:
    """Search across all indexed books using hybrid semantic + keyword search.

    Args:
        query: Natural language search query.
        top_k: Number of results to return (default 10).
        book: Optional book slug or title to filter results to a single book.
        hyde_passage: Optional hypothetical answer paragraph. When provided, this
            text is embedded instead of the query for the dense retrieval leg,
            bridging vocabulary gaps between questions and textbook prose. The
            BM25 keyword leg still uses the original query (or bm25_keywords).
        extra_queries: Optional list of alternative query phrasings to broaden
            recall. Each extra query adds its own dense + BM25 retrieval legs,
            and all candidates are fused before reranking.
        bm25_keywords: Optional list of exact terms for the BM25 keyword leg
            (e.g. ["MVCC", "xmin", "snapshot isolation"]). When provided, these
            terms drive lexical matching instead of the natural-language query,
            separating semantic intent (dense leg) from exact-term matching.
            Use when you know the precise vocabulary the source text would use.
        detail: "brief" returns short passages for scanning; call read_chunk(chunk_id)
            for the surrounding passage, or use "full" for the full result.

    Returns:
        List of search results. Brief results contain the matching child passage;
        full results include the parent passage and legacy fields.
    """
    if detail not in {"brief", "full"}:
        return [{"error": "detail must be 'brief' or 'full'"}]
    book_slug = None
    if book is not None:
        book_slug, suggestions = resolve_book(book)
        if book_slug is None:
            return [{"error": _unknown_book_error(book, suggestions)}]

    # ⚡2: reuse the long-lived client singleton (no per-call open/close).
    client = get_client()
    results = hybrid_search(
        query=query,
        client=client,
        top_k=top_k,
        book_filter=book_slug,
        hyde_passage=hyde_passage,
        extra_queries=extra_queries,
        bm25_keywords=bm25_keywords,
    )
    return [_format_search_result(r, detail) for r in results]


@mcp.tool()
@logged
def search_book(
    book: str,
    query: str,
    top_k: int = 5,
    detail: str = "brief",
) -> list[dict]:
    """Search within a specific book.

    Args:
        book: Book slug or title (use list_books() to see available books).
        query: Natural language search query.
        top_k: Number of results to return (default 5).
        detail: "brief" returns short passages for scanning; call read_chunk(chunk_id)
            for the surrounding passage, or use "full" for the full result.

    Returns:
        List of search results scoped to the specified book.
    """
    if detail not in {"brief", "full"}:
        return [{"error": "detail must be 'brief' or 'full'"}]
    book_slug, suggestions = resolve_book(book)
    if book_slug is None:
        return [{"error": _unknown_book_error(book, suggestions)}]

    # ⚡2: reuse the long-lived client singleton (no per-call open/close).
    client = get_client()
    results = hybrid_search(
        query=query,
        client=client,
        top_k=top_k,
        book_filter=book_slug,
    )
    return [_format_search_result(r, detail) for r in results]


@mcp.tool()
@logged
def read_chunk(chunk_id: str, window: int = 1) -> dict:
    """Expand context around a search hit: read a chunk plus its neighbours.

    Pass the `chunk_id` from a search() / search_book() result to pull the exact
    chunk, its parent passage, and the adjacent sibling chunks — without
    re-searching or loading a whole chapter via get_chapter(). Useful for
    following a promising hit forward/backward through the surrounding text.

    Args:
        chunk_id: A chunk id from search results, e.g. "crypto-101-p0-c1".
        window: Number of sibling chunks to include on each side (default 1;
            window=0 returns only the chunk itself).

    Returns:
        Dict with the chunk text, its parent passage, neighbouring siblings
        (`previous`/`next`), heading_path, and `seen_chunk_ids` (every id
        returned) so repeated calls can skip already-seen chunks.
    """
    m = _CHUNK_ID_RE.match(chunk_id)
    if not m:
        return {"error": f"Malformed chunk_id (expected 'slug-pN-cM'): {chunk_id}"}
    slug, p_idx, _ = m.groups()
    parent_id = f"{slug}-p{p_idx}"

    chunk_path = CHUNKS_DIR / f"{slug}.json"
    if not chunk_path.exists():
        return {"error": f"Book not found: {slug}"}

    data = json.loads(chunk_path.read_text(encoding="utf-8"))
    siblings = [c for c in data.get("children", []) if c["parent_id"] == parent_id]
    ids = [c["child_id"] for c in siblings]
    if chunk_id not in ids:
        return {"error": f"Chunk not found: {chunk_id}"}
    idx = ids.index(chunk_id)

    lo = max(0, idx - window)
    hi = min(len(siblings), idx + window + 1)
    parent = next((p for p in data.get("parents", []) if p["parent_id"] == parent_id), None)
    target = siblings[idx]
    meta = target.get("metadata", {})

    def _slim(c: dict) -> dict:
        return {"chunk_id": c["child_id"], "text": c["text"]}

    return {
        "chunk_id": chunk_id,
        "book": meta.get("book_title", slug),
        "heading_path": meta.get("heading_path", ""),
        "text": target["text"],
        "parent_text": parent["text"] if parent else "",
        "previous": [_slim(c) for c in siblings[lo:idx]],
        "next": [_slim(c) for c in siblings[idx + 1:hi]],
        "seen_chunk_ids": ids[lo:hi],
    }


@mcp.tool()
@logged
def get_chapter(book: str, chapter: str | int) -> str:
    """Get the full text of a specific chapter from a book.

    Args:
        book: Book slug or title (use list_books() to see available books).
        chapter: 1-based chapter index, exact or partial title, or title prefix.

    Returns:
        Full markdown text of the chapter, or an error message.
    """
    slug, suggestions = resolve_book(book)
    if slug is None:
        return _unknown_book_error(book, suggestions)

    md_path = MARKDOWN_DIR / f"{slug}.md"
    if not md_path.exists():
        return f"Book markdown not found: {slug}"

    text = md_path.read_text(encoding="utf-8")
    chapter_titles = book_chapters(slug)
    chapter_query = str(chapter).strip()
    chapter_lower = chapter_query.casefold()
    selected_index = None

    if isinstance(chapter, int) and not isinstance(chapter, bool):
        index = chapter
    elif chapter_query.isdigit():
        index = int(chapter_query)
    else:
        index = None
    if index is not None and 1 <= index <= len(chapter_titles):
        selected_index = index
    if selected_index is None:
        for i, title in enumerate(chapter_titles, start=1):
            if title.casefold() == chapter_lower:
                selected_index = i
                break
        if selected_index is None:
            for i, title in enumerate(chapter_titles, start=1):
                if title.casefold().startswith(chapter_lower):
                    selected_index = i
                    break
        if selected_index is None:
            for i, title in enumerate(chapter_titles, start=1):
                title_lower = title.casefold()
                if chapter_lower in title_lower or title_lower in chapter_lower:
                    selected_index = i
                    break

    if selected_index is None:
        available = "; ".join(
            f"{i}. {title}" for i, title in enumerate(chapter_titles[:10], start=1)
        )
        suffix = f" Available chapters: {available}." if available else " No chapters found."
        return f"Chapter '{chapter}' not found in {slug}.{suffix}"

    capturing = False
    chapter_lines: list[str] = []
    in_code = False
    heading_index = 0

    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            if capturing:
                chapter_lines.append(line)
            in_code = not in_code
            continue

        heading = None if in_code else _chapter_title(line)
        if heading:
            heading_index += 1
            if capturing:
                break
            if heading_index == selected_index:
                capturing = True

        if capturing:
            chapter_lines.append(line)

    if not chapter_lines:
        available = "; ".join(
            f"{i}. {title}" for i, title in enumerate(chapter_titles[:10], start=1)
        )
        return f"Chapter '{chapter}' not found in {slug}. Available chapters: {available}."

    result = "\n".join(chapter_lines).strip()
    if len(result) > 50000:
        result = result[:50000] + "\n\n[... truncated at 50,000 characters ...]"
    return result


@mcp.tool()
@logged
def list_books(book: str | None = None) -> list[dict] | dict:
    """List the catalog, or the chapters for one book.

    Call without arguments for the catalog; pass a book slug or title for its chapters.

    Returns:
        Catalog rows, or one book with indexed chapter titles.
    """
    if book is not None:
        slug, suggestions = resolve_book(book)
        if slug is None:
            return {"error": _unknown_book_error(book, suggestions)}
        chapters = book_chapters(slug)
        return {
            "slug": slug,
            "title": BOOKS[slug],
            "domain": book_domain(slug),
            "chapters": [
                {"index": i, "title": title}
                for i, title in enumerate(chapters, start=1)
            ],
        }

    return [
        {
            "slug": slug,
            "title": title,
            "domain": book_domain(slug),
            "chapter_count": len(book_chapters(slug)),
        }
        for slug, title in sorted(
            BOOKS.items(), key=lambda item: (book_domain(item[0]), item[1].casefold())
        )
    ]


@mcp.tool()
@logged
def grep_books(
    pattern: str,
    book: str | None = None,
    max_results: int = 20,
) -> list[dict]:
    """Exact-match keyword search across book markdown files using ripgrep (with Python fallback).

    Unlike semantic search, this finds exact text matches — useful for finding specific
    function names, error messages, code snippets, or terms that semantic search may miss.

    Args:
        pattern: Regex pattern to search for (case-insensitive).
        book: Optional book slug to restrict search to a single book.
        max_results: Maximum total results to return (default 20).

    Returns:
        List of matches with book slug, line_number, and context (matching line + 1 line of surrounding context).
    """
    if book is not None:
        slug, suggestions = resolve_book(book)
        if slug is None:
            return [{"error": _unknown_book_error(book, suggestions)}]
        book = slug

    # Build list of markdown files to search
    if book is not None:
        md_files = [MARKDOWN_DIR / f"{book}.md"]
    else:
        md_files = sorted(
            p for p in MARKDOWN_DIR.glob("*.md")
            if p.stem in BOOKS
        )

    if not md_files:
        return []

    per_file_limit = max(3, max_results // len(md_files))

    try:
        return _grep_ripgrep(pattern, md_files, per_file_limit, max_results)
    except FileNotFoundError:
        return _grep_python(pattern, md_files, per_file_limit, max_results)


def _grep_ripgrep(
    pattern: str,
    md_files: list,
    per_file_limit: int,
    max_results: int,
) -> list[dict]:
    """Search using ripgrep for speed."""
    paths = [str(p) for p in md_files]
    cmd = [
        "rg",
        "--ignore-case",
        "--line-number",
        "--with-filename",
        "--context", "1",
        "--max-count", str(per_file_limit),
        pattern,
        *paths,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    # rg returns 1 when no matches found, 2+ on error
    if proc.returncode > 1:
        return []

    results: list[dict] = []
    # Group consecutive lines by file:linenum blocks separated by "--"
    current_block_lines: list[str] = []
    current_book: str | None = None
    current_match_lineno: int | None = None

    def _flush_block():
        nonlocal current_book, current_match_lineno, current_block_lines
        if current_book is not None and current_match_lineno is not None:
            context = "\n".join(current_block_lines)[:500]
            results.append({
                "book": current_book,
                "line_number": current_match_lineno,
                "context": context,
            })
        current_block_lines = []
        current_book = None
        current_match_lineno = None

    for raw_line in proc.stdout.splitlines():
        if len(results) >= max_results:
            break

        # Block separator from --context
        if raw_line == "--":
            _flush_block()
            continue

        # Match lines: file:linenum:text  or context lines: file-linenum-text
        # When searching multiple files, rg prefixes with filename
        # Match line format: /path/to/file.md:123:matched text
        # Context line format: /path/to/file.md-122-context text
        match = re.match(r"^(.+?)([:-])(\d+)\2(.*)$", raw_line)
        if not match:
            continue

        filepath, separator, lineno_str, text = match.groups()
        slug = filepath.rsplit("/", 1)[-1].removesuffix(".md")
        lineno = int(lineno_str)

        if separator == ":":
            # This is a match line
            if current_book is not None:
                _flush_block()
            current_book = slug
            current_match_lineno = lineno
            current_block_lines.append(text)
        else:
            # Context line (separator is "-")
            current_block_lines.append(text)

    # Flush last block
    _flush_block()

    return results[:max_results]


def _grep_python(
    pattern: str,
    md_files: list,
    per_file_limit: int,
    max_results: int,
) -> list[dict]:
    """Pure Python fallback when ripgrep is not installed."""
    try:
        compiled = re.compile(pattern, re.IGNORECASE)
    except re.error:
        return [{"error": f"Invalid regex pattern: {pattern}"}]

    results: list[dict] = []

    for md_path in md_files:
        if len(results) >= max_results:
            break
        if not md_path.exists():
            continue

        lines = md_path.read_text(encoding="utf-8").splitlines()
        file_matches = 0
        slug = md_path.stem

        for i, line in enumerate(lines):
            if file_matches >= per_file_limit or len(results) >= max_results:
                break

            if compiled.search(line):
                # Build context: 1 line before + match + 1 line after
                context_lines = []
                if i > 0:
                    context_lines.append(lines[i - 1])
                context_lines.append(line)
                if i < len(lines) - 1:
                    context_lines.append(lines[i + 1])

                context = "\n".join(context_lines)[:500]
                results.append({
                    "book": slug,
                    "line_number": i + 1,  # 1-based
                    "context": context,
                })
                file_matches += 1

    return results[:max_results]


def main():
    mcp.run()


if __name__ == "__main__":
    main()
