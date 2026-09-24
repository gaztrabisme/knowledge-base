"""FastMCP server exposing semantic search over ML books."""

import json
import os
import re
import subprocess

from fastmcp import FastMCP

from .calllog import logged
from .config import BOOKS, CHUNKS_DIR, MARKDOWN_DIR
from .books import DOMAINS, _chapter_title, book_chapters, book_domain, load_catalog, resolve_book
from .search import get_client, hybrid_search

_CHUNK_ID_RE = re.compile(r"^(.+)-p(\d+)-c(\d+)$")

mcp = FastMCP(
    "Developer Knowledge Base",
    instructions="Semantic search over technical books: ML, databases, security, distributed systems",
)

TOOL_DESCRIPTIONS = {
    "search": {
        "default": (
            "Search the library for passages that answer a technical question. "
            "If you don't know which books cover the topic, call find_books first. "
            "For follow-up searches, reuse words from related_headings or "
            "find_books matching_sections instead of guessing vocabulary. "
            "Use read_chunk(chunk_id) to read around a hit."
        ),
        "hyde": (
            "Search the library for passages that answer a technical question. "
            "For conceptual questions, always write a hyde_passage: a 3–5 sentence "
            "hypothetical textbook answer. If you don't know which books cover the "
            "topic, call find_books first. Use read_chunk(chunk_id) to read around a hit."
        ),
    },
    "search_book": "Search a selected book for passages that answer a technical question.",
    "read_chunk": "Read a search hit with neighboring chunks and its parent passage.",
    "get_chapter": "Read a chapter by book and chapter number or title.",
    "list_books": "List the library catalog or one book's chapters.",
    "find_books": {
        "default": (
            "Find books that cover a topic and show the vocabulary used in their sections. "
            "Call this first if you don't know which books cover the topic."
        ),
        "hyde": "Find books that cover a topic and show the vocabulary used in their sections.",
    },
    "grep_books": "Find exact text matches in the books.",
}
_TOOL_DOC_MODE = "hyde" if os.environ.get("KB_TOOL_DOCS") == "hyde" else "default"


def _tool_description(name: str) -> str:
    description = TOOL_DESCRIPTIONS[name]
    if isinstance(description, dict):
        return description[_TOOL_DOC_MODE]
    return description


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


def _normalized_heading(value: str) -> str:
    heading = re.sub(r"\s*\(part\s+\d+\)\s*$", "", value, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", heading).strip()


def _search_response(results, overflow, detail: str) -> dict:
    formatted = [_format_search_result(result, detail) for result in results]
    result_headings = {_normalized_heading(result.heading_path) for result in results}
    related_headings = []
    for result in overflow:
        heading = _normalized_heading(result.heading_path)
        if heading and heading not in result_headings and heading not in related_headings:
            related_headings.append(heading)
            if len(related_headings) == 8:
                break
    return {"results": formatted, "related_headings": related_headings}


def _token_count(value: object) -> int:
    import tiktoken

    return len(tiktoken.get_encoding("cl100k_base").encode(json.dumps(value)))


def _catalog_book(slug: str, fallback_title: str | None = None) -> dict:
    entry = load_catalog().get(slug, {})
    return {
        "slug": slug,
        "title": entry.get("title") or fallback_title or slug,
        "domain": entry.get("domain") or book_domain(slug),
        "tags": entry.get("tags") or [],
        "summary": entry.get("summary") or "",
    }


def _catalog_tags() -> list[str]:
    return sorted({
        tag
        for entry in load_catalog().values()
        for tag in entry.get("tags", [])
    })


@mcp.tool(description=_tool_description("search"))
@logged
def search(
    query: str,
    top_k: int = 10,
    book: str | None = None,
    hyde_passage: str | None = None,
    extra_queries: list[str] | None = None,
    bm25_keywords: list[str] | None = None,
    detail: str = "brief",
    books: list[str] | None = None,
    domain: str | None = None,
) -> dict | list[dict]:
    """Search the library.

    Args:
        query: Natural-language question or topic.
        top_k: Maximum number of hits to return.
        book: Optional legacy single-book filter.
        hyde_passage: Advanced: hypothetical answer added as a second dense query; helps broad concepts and can hurt precise terminology.
        extra_queries: Advanced: alternative phrasings added as dense and BM25 queries.
        bm25_keywords: Advanced: exact terms used for the BM25 leg instead of the query.
        detail: Use "brief" hits or "full" parent passages.
        books: Optional book filters; use find_books to choose them.
        domain: Optional library domain filter.
    """
    if detail not in {"brief", "full"}:
        return [{"error": "detail must be 'brief' or 'full'"}]
    if domain is not None and domain not in DOMAINS:
        return [{"error": f"Unknown domain '{domain}'. Domains: {', '.join(DOMAINS)}"}]

    resolved_books: list[str] = []
    for name in books or []:
        slug, suggestions = resolve_book(name)
        if slug is None:
            return [{"error": _unknown_book_error(name, suggestions)}]
        if slug not in resolved_books:
            resolved_books.append(slug)

    legacy_slug = None
    if book is not None:
        legacy_slug, suggestions = resolve_book(book)
        if legacy_slug is None:
            return [{"error": _unknown_book_error(book, suggestions)}]
        if legacy_slug not in resolved_books:
            resolved_books.append(legacy_slug)

    if books is None and book is not None:
        book_filter: str | list[str] | None = legacy_slug
    else:
        book_filter = resolved_books or None

    # ⚡2: reuse the long-lived client singleton (no per-call open/close).
    client = get_client()
    overflow = []
    results = hybrid_search(
        query=query,
        client=client,
        top_k=top_k,
        book_filter=book_filter,
        domain_filter=domain,
        hyde_passage=hyde_passage,
        extra_queries=extra_queries,
        bm25_keywords=bm25_keywords,
        overflow=overflow,
    )
    return _search_response(results, overflow, detail)


@mcp.tool(description=_tool_description("search_book"))
@logged
def search_book(
    book: str,
    query: str,
    top_k: int = 5,
    detail: str = "brief",
) -> dict | list[dict]:
    """Search within one book.

    Args:
        book: Book slug or title.
        query: Natural-language question or topic.
        top_k: Maximum number of hits to return.
        detail: Use "brief" hits or "full" parent passages.
    """
    if detail not in {"brief", "full"}:
        return [{"error": "detail must be 'brief' or 'full'"}]
    book_slug, suggestions = resolve_book(book)
    if book_slug is None:
        return [{"error": _unknown_book_error(book, suggestions)}]

    # ⚡2: reuse the long-lived client singleton (no per-call open/close).
    client = get_client()
    overflow = []
    results = hybrid_search(
        query=query,
        client=client,
        top_k=top_k,
        book_filter=book_slug,
        overflow=overflow,
    )
    return _search_response(results, overflow, detail)


@mcp.tool(description=_tool_description("read_chunk"))
@logged
def read_chunk(chunk_id: str, window: int = 1) -> dict:
    """Read the chunk and surrounding context.

    Args:
        chunk_id: Chunk id from a search result.
        window: Number of sibling chunks to include on each side.
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


@mcp.tool(description=_tool_description("get_chapter"))
@logged
def get_chapter(book: str, chapter: str | int) -> str:
    """Read a chapter from a book.

    Args:
        book: Book slug or title.
        chapter: 1-based number or exact, partial, or prefix title.
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


@mcp.tool(description=_tool_description("list_books"))
@logged
def list_books(book: str | None = None) -> list[dict] | dict:
    """List books or chapters.

    Args:
        book: Optional slug or title to list that book's chapters.
    """
    if book is not None:
        slug, suggestions = resolve_book(book)
        if slug is None:
            return {"error": _unknown_book_error(book, suggestions)}
        chapters = book_chapters(slug)
        entry = _catalog_book(slug, BOOKS[slug])
        return {
            "slug": slug,
            "title": entry["title"],
            "domain": entry["domain"],
            "tags": entry["tags"],
            "chapters": [
                {"index": i, "title": title}
                for i, title in enumerate(chapters, start=1)
            ],
        }

    rows = []
    for slug, title in sorted(
        BOOKS.items(), key=lambda item: (_catalog_book(item[0], item[1])["domain"], item[1].casefold())
    ):
        entry = _catalog_book(slug, title)
        rows.append({
            "slug": slug,
            "title": entry["title"],
            "domain": entry["domain"],
            "chapter_count": len(book_chapters(slug)),
            "tags": entry["tags"],
        })
    if _token_count(rows) > 8000:
        for row in rows:
            row.pop("tags")
    return rows


@mcp.tool(description=_tool_description("find_books"))
@logged
def find_books(
    query: str | None = None,
    domain: str | None = None,
    tags: list[str] | None = None,
    top_k: int = 5,
) -> list[dict]:
    """Find books by topic and optional filters.

    Args:
        query: Optional topic or question to rank books for.
        domain: Optional library domain filter.
        tags: Optional tags; books must have every supplied tag.
        top_k: Maximum number of ranked books to return.
    """
    if domain is not None and domain not in DOMAINS:
        return [{"error": f"Unknown domain '{domain}'. Domains: {', '.join(DOMAINS)}"}]

    valid_tags = _catalog_tags()
    invalid_tags = sorted(set(tags or []) - set(valid_tags))
    if invalid_tags:
        return [{
            "error": f"Unknown tag(s) {', '.join(invalid_tags)}. Tags: {', '.join(valid_tags)}"
        }]

    catalog = load_catalog()
    source = catalog or {slug: {} for slug in BOOKS}
    rows = []
    for slug, fallback in source.items():
        row = _catalog_book(slug, fallback.get("title") or BOOKS.get(slug, slug))
        if domain is not None and row["domain"] != domain:
            continue
        if not set(tags or []).issubset(row["tags"]):
            continue
        rows.append(row)

    limit = max(0, top_k)
    if query is None:
        # Browsing returns every match; top_k only limits a ranked query.
        rows.sort(key=lambda row: (row["domain"], row["title"].casefold()))
        # Over the cap, drop summaries before dropping books: a silently shortened catalog
        # reads as the whole library.
        if _token_count(rows) >= 10000:
            rows = [{k: v for k, v in row.items() if k != "summary"} for row in rows]
        return rows

    client = get_client()
    reranked = hybrid_search(
        query=query,
        client=client,
        top_k=40,
        candidates=100,
        domain_filter=domain,
    )
    fusion_only = hybrid_search(
        query=query,
        client=client,
        rerank=False,
        top_k=100,
        candidates=100,
        domain_filter=domain,
    )

    ranked_books: dict[str, dict] = {}
    for weight, hits in ((1.0, reranked), (0.5, fusion_only)):
        for rank, hit in enumerate(hits):
            slug = hit.book
            book_row = ranked_books.setdefault(
                slug, {**_catalog_book(slug, hit.book_title), "score": 0.0, "matching_sections": []}
            )
            book_row["score"] += weight / (rank + 1)
            heading = re.sub(r"\s*\(part\s+\d+\)\s*$", "", hit.heading_path, flags=re.IGNORECASE)
            heading = re.sub(r"\s+", " ", heading).strip()
            if heading and heading not in book_row["matching_sections"]:
                book_row["matching_sections"].append(heading)

    ranked = sorted(
        ranked_books.values(),
        key=lambda row: (-row["score"], row["domain"], row["title"].casefold(), row["slug"]),
    )
    if tags:
        required_tags = set(tags)
        ranked = [row for row in ranked if required_tags.issubset(row["tags"])]

    output = []
    for row in ranked[:limit]:
        output.append({
            "slug": row["slug"],
            "title": row["title"],
            "domain": row["domain"],
            "tags": row["tags"],
            "summary": row["summary"],
            "score": round(row["score"], 3),
            "matching_sections": row["matching_sections"][:4],
        })
        if _token_count(output) > 1500:
            output.pop()
            break
    return output


@mcp.tool(description=_tool_description("grep_books"))
@logged
def grep_books(
    pattern: str,
    book: str | None = None,
    max_results: int = 20,
) -> list[dict]:
    """Find exact text matches in book markdown.

    Args:
        pattern: Case-insensitive regex pattern.
        book: Optional book slug filter.
        max_results: Maximum number of matches to return.
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
