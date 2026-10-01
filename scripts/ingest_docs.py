#!/usr/bin/env python3
"""Convert selected official frontend documentation into KB books and chunks.

Usage:
  python scripts/ingest_docs.py convert
  python scripts/ingest_docs.py chunk
  python scripts/ingest_docs.py all
  python scripts/ingest_docs.py counts
"""
from __future__ import annotations

import argparse
import html
from html.parser import HTMLParser
import json
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DOCS_ROOT = ROOT / "data" / "sources" / "docs"
MARKDOWN_DIR = ROOT / "data" / "markdown"
CHUNKS_DIR = ROOT / "data" / "chunks"
MANIFEST_PATH = ROOT / "data" / "intake" / "v10-docs-manifest.json"
SOURCES_PATH = DOCS_ROOT / "SOURCES.md"
TICK = chr(96)

BOOKS = {
    "mdn-web-docs": {
        "title": "MDN Web Docs",
        "url": "https://developer.mozilla.org/",
        "repository": "https://github.com/mdn/content",
        "commit": "827686870ee416d6f01739a48931618b61f4ce4e",
        "license": "CC BY-SA 2.5 prose; CC0 code samples",
        "attribution": "MDN contributors",
    },
    "web-dev-baseline": {
        "title": "web.dev Baseline and Web Performance Articles",
        "url": "https://web.dev/baseline/",
        "repository": "https://github.com/GoogleChrome/web.dev",
        "commit": "a64d870f59c25431bbedf0ef06aa635072c43a2e",
        "license": "Archived repository content: CC BY 3.0 prose and Apache-2.0 code; current Baseline page: CC BY 4.0 per the research inventory",
        "attribution": "Google Chrome and web.dev contributors",
    },
    "whatwg-html": {
        "title": "WHATWG HTML Standard",
        "url": "https://html.spec.whatwg.org/multipage/",
        "repository": "https://github.com/whatwg/html",
        "commit": "bae538d057faf3fd81cd43e3187b8f9fb7fca9cb",
        "license": "CC BY 4.0 prose; BSD-3-Clause for source-code portions",
        "attribution": "WHATWG and its contributors",
    },
    "wai-aria-apg": {
        "title": "WAI-ARIA Authoring Practices Guide",
        "url": "https://www.w3.org/WAI/ARIA/apg/",
        "repository": "https://github.com/w3c/aria-practices",
        "commit": "0f765e4dc33e966026114ac12a8380db1de3b787",
        "license": "W3C Software and Document License",
        "attribution": "W3C contributors",
    },
    "wcag-22": {
        "title": "Web Content Accessibility Guidelines (WCAG) 2.2",
        "url": "https://www.w3.org/TR/WCAG22/",
        "repository": "https://github.com/w3c/wcag",
        "commit": "71c891a49f50f58766597a8980f6b2d2eedd5679",
        "license": "W3C Document License (verbatim copies only; prose retained verbatim and markup normalized)",
        "attribution": "W3C Web Accessibility Initiative",
    },
    "react-dev": {
        "title": "React Documentation",
        "url": "https://react.dev/",
        "repository": "https://github.com/reactjs/react.dev",
        "commit": "75ef18a9172e4c100b5d5650ae14c395c5c8ef42",
        "license": "CC BY 4.0 documentation; MIT code",
        "attribution": "Meta and React contributors",
    },
    "angular-dev": {
        "title": "Angular Documentation",
        "url": "https://angular.dev/assets/context/llms-full.txt",
        "extra_urls": ["https://angular.dev/assets/context/best-practices.md"],
        "repository": "https://github.com/angular/angular",
        "commit": "",
        "license": "CC BY 4.0 documentation; MIT code",
        "attribution": "Google and Angular contributors",
    },
    "playwright-docs": {
        "title": "Playwright Documentation",
        "url": "https://playwright.dev/docs/",
        "repository": "https://github.com/microsoft/playwright",
        "commit": "46c9a5331a2744e0c022842d8c7681d45acc0b38",
        "license": "Apache-2.0",
        "attribution": "Microsoft and Playwright contributors",
    },
}

MDN_API_ROOTS = {
    "document_object_model", "canvas_api", "webgl_api", "webgl2",
    "web_animations_api", "intersection_observer_api", "resize_observer_api",
    "popover_api", "fetch_api", "performance_api",
}
MDN_API_PAGES = {
    "document", "documentfragment", "documenttype", "domimplementation",
    "element", "eventtarget", "node", "nodelist", "htmlcollection",
    "htmlelement", "window", "mutationobserver", "mutationrecord",
    "htmlcanvaselement", "canvasrenderingcontext2d", "offscreencanvas",
    "offscreencanvasrenderingcontext2d", "webglrenderingcontext",
    "webgl2renderingcontext", "webglshader", "webglprogram",
    "animation", "animationeffect", "animationtimeline",
    "animationplaybackevent", "intersectionobserver", "intersectionobserverentry",
    "resizeobserver", "resizeobserverentry", "htmldialogelement",
    "popover", "fetch", "request", "response", "headers", "performance",
    "performanceentry", "performancemark", "performancemeasure",
    "performanceobserver", "performanceobserverentrylist", "matchmedia",
}
SKIP_HTML_TAGS = {
    "head", "script", "style", "nav", "header", "footer", "aside", "button",
    "noscript", "template", "svg", "pre", "iframe",
}
VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}
BOILERPLATE_TEXT = {
    "skip to main content", "on this page", "edit this page", "edit on github",
    "view source", "back to top", "previous", "next",
}
SUPPORT_MACROS = {
    "compat", "specifications", "browsercompat", "seetable", "seetable2",
    "compatibilitytable", "embedinteractiveexample", "interactiveexample",
    "codesample",
}
RETRIEVAL_DATE = datetime.now(timezone.utc).date().isoformat()


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = re.match(r"\A---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|\Z)", text, re.S)
    if not match:
        return {}, text
    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        item = re.match(r"^([A-Za-z0-9_-]+):\s*(.*?)\s*$", line)
        if not item:
            continue
        value = item.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[item.group(1).casefold()] = value
    return values, text[match.end():]


def first_markdown_heading(text: str) -> str:
    in_code = False
    for line in text.splitlines():
        if line.strip().startswith(TICK * 3):
            in_code = not in_code
            continue
        if not in_code:
            match = re.match(r"^#\s+(.+?)\s*#*\s*$", line)
            if match:
                return match.group(1).strip()
    return ""


def clean_markdown(text: str) -> str:
    _, text = parse_frontmatter(text)
    def mdn_macro(match: re.Match[str]) -> str:
        body = match.group(1).strip()
        name = body.split("(", 1)[0].strip().casefold()
        if name in SUPPORT_MACROS or name.startswith("spec") or name.startswith("bc"):
            return ""
        quoted = re.search(r"""['"]([^'"]+)['"]""", body)
        if quoted:
            return quoted.group(1).replace("_", " ")
        if "(" not in body and body[:1].islower():
            return match.group(0)  # e.g. Angular's {{value}} interpolation
        return ""

    def clean_prose(prose: str) -> str:
        prose = re.sub(r"(?s)<!--.*?-->", "", prose)
        prose = re.sub(r"(?s)\{\s*/\*.*?\*/\s*\}", "", prose)
        prose = re.sub(r"(?s)<docs-nav-card\b[^>]*>.*?</docs-nav-card\s*>", "", prose, flags=re.I)
        prose = re.sub(r"(?s)<docs-nav-link\b[^>]*>.*?</docs-nav-link\s*>", "", prose, flags=re.I)
        for tag in ("nav", "header", "footer", "script", "style"):
            prose = re.sub(rf"(?is)<{tag}\b[^>]*>.*?</{tag}\s*>", "", prose)
        prose = re.sub(r"(?m)^\s*import\s+.*?;?\s*$", "", prose)
        prose = re.sub(r"(?m)^\s*\{%\s*(?:Img|YouTube|Embed).*?%\}\s*$", "", prose, flags=re.I)
        prose = re.sub(r"\{%.*?%\}", "", prose, flags=re.S)
        prose = re.sub(r"\{\{(.*?)\}\}", mdn_macro, prose, flags=re.S)
        prose = re.sub(r"!\[([^\]]*)\]\([^)]*\)", "", prose)
        prose = re.sub(r"(?m)^\s*:::\s*(?:note|warning|important|tip)?\s*$", "", prose, flags=re.I)
        prose = re.sub(r"(?m)^\s*:::\s*$", "", prose)
        prose = re.sub(r"(?m)^\s*(?:On this page|Skip to main content|Edit this page|Edit on GitHub)\s*$", "", prose, flags=re.I)
        # MDX components are presentation wrappers; retain their prose.
        prose = re.sub(r"</?[A-Z][A-Za-z0-9]*(?:\s+[^<>]*?)?\s*/?>", "", prose)
        prose = re.sub(r"\n[ \t]+\n", "\n\n", prose)
        return re.sub(r"\n{3,}", "\n\n", prose)

    # Cleanup is applied to prose only. Fenced examples may legitimately contain
    # imports, JSX components, template syntax, or navigation markup.
    cleaned: list[str] = []
    prose: list[str] = []
    fence_char = ""
    fence_size = 0

    def flush_prose() -> None:
        if prose:
            cleaned.append(clean_prose("".join(prose)))
            prose.clear()

    for line in text.splitlines(keepends=True):
        fence = re.match(r"^\s*(`{3,}|~{3,})", line)
        if fence:
            marker = fence.group(1)
            if not fence_char:
                flush_prose()
                fence_char, fence_size = marker[0], len(marker)
                cleaned.append(line)
            elif marker[0] == fence_char and len(marker) >= fence_size:
                cleaned.append(line)
                fence_char, fence_size = "", 0
            else:
                cleaned.append(line)
        elif fence_char:
            cleaned.append(line)
        else:
            prose.append(line)
    flush_prose()
    result = "".join(cleaned)
    result = re.sub(r"\n[ \t]+\n", "\n\n", result)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def shift_headings(text: str, amount: int) -> str:
    result: list[str] = []
    in_code = False
    for line in text.splitlines():
        if line.strip().startswith(TICK * 3):
            in_code = not in_code
            result.append(line)
            continue
        match = re.match(r"^(#{1,6})(\s+.*)$", line)
        if match and not in_code:
            level = max(1, min(6, len(match.group(1)) + amount))
            result.append("#" * level + match.group(2))
        else:
            result.append(line)
    return "\n".join(result).strip()


def normalize_markdown_page(raw: str, fallback_title: str) -> tuple[str, str]:
    metadata, body = parse_frontmatter(raw)
    title = metadata.get("title", "").strip() or first_markdown_heading(body) or fallback_title
    body = clean_markdown(body)
    first_h1 = first_markdown_heading(body)
    if first_h1 and first_h1.casefold().strip() == title.casefold().strip():
        body = re.sub(r"(?m)^#\s+" + re.escape(first_h1) + r"\s*#*\s*$", "", body, count=1)
    body = shift_headings(body, 1)
    return title, f"## {title}\n\n{body}".strip()


class HTMLToMarkdown(HTMLParser):
    """Small deterministic HTML reader for docs, specs, and APG source pages."""

    def __init__(
        self,
        source: str,
        *,
        whatwg: bool = False,
        preserve_pre: bool = False,
        main_only: bool | None = None,
    ):
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.whatwg = whatwg
        self.preserve_pre = preserve_pre
        self.main_only = bool(re.search(r"<main\b", source, re.I)) if main_only is None else main_only
        self.main_depth = 0
        self.skip_tags: list[str] = []
        self.list_depth = 0
        self.in_pre = False

    def _emit(self, value: str) -> None:
        if self.main_only and self.main_depth == 0:
            return
        if self.skip_tags:
            return
        self.out.append(value)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = {key.casefold(): value or "" for key, value in attrs}
        # The WHATWG source has a few intentionally sketchy table fragments in
        # its editor-only markup. Their closing tags are not always balanced,
        # so recover at the next real chapter boundary.
        if self.whatwg and tag == "h2" and "split-filename" in attrs_map:
            self.skip_tags.clear()
        if self.main_only and tag == "main":
            self.main_depth += 1
            return
        if self.main_only and self.main_depth == 0:
            return
        if self.in_pre:
            return
        if self.skip_tags:
            if tag not in VOID_TAGS:
                self.skip_tags.append(tag)
            return
        if tag == "pre" and self.preserve_pre:
            self.in_pre = True
            self._emit("\n\n" + TICK * 3 + "\n")
            return
        classes = set(attrs_map.get("class", "").casefold().split())
        ident = attrs_map.get("id", "").casefold()
        suppress = (
            tag in SKIP_HTML_TAGS
            or bool(classes & {"breadcrumb", "skip-link", "site-nav", "toc", "toc-container"})
            or (self.whatwg and tag == "h2" and "no-toc" in classes)
            or ident in {"toc", "table-of-contents", "contents", "full-toc", "fulltoc", "skip-link", "page-footer", "site-nav"}
            or (self.whatwg and any(name in attrs_map for name in ("w-dev", "w-nohtml", "w-noreview", "w-nosnap")))
        )
        if suppress:
            if tag not in VOID_TAGS:
                self.skip_tags = [tag]
            return
        if re.fullmatch(r"h[1-6]", tag):
            self._emit("\n\n" + "#" * int(tag[1]) + " ")
        elif tag in {"p", "div", "section", "article", "blockquote", "figure", "figcaption"}:
            self._emit("\n\n")
        elif tag in {"ul", "ol"}:
            self.list_depth += 1
            self._emit("\n")
        elif tag == "li":
            self._emit("\n" + "  " * max(0, self.list_depth - 1) + "- ")
        elif tag == "br":
            self._emit("\n")
        elif tag in {"strong", "b"}:
            self._emit("**")
        elif tag in {"em", "i"}:
            self._emit("*")
        elif tag == "code":
            self._emit(TICK)
        elif tag == "tr":
            self._emit("\n| ")
        elif tag in {"td", "th"}:
            self._emit(" | ")
        elif tag == "hr":
            self._emit("\n\n")
        elif tag == "img":
            alt = attrs_map.get("alt", "").strip()
            if alt:
                self._emit("[Image: " + alt + "]")

    def handle_endtag(self, tag: str) -> None:
        if self.main_only and tag == "main" and self.main_depth:
            self.main_depth -= 1
            return
        if self.main_only and self.main_depth == 0:
            return
        if self.in_pre:
            if tag == "pre":
                self._emit("\n" + TICK * 3 + "\n")
                self.in_pre = False
            return
        if self.skip_tags:
            for index in range(len(self.skip_tags) - 1, -1, -1):
                if self.skip_tags[index] == tag:
                    del self.skip_tags[index:]
                    break
            return
        if re.fullmatch(r"h[1-6]", tag):
            self._emit("\n\n")
        elif tag in {"p", "div", "section", "article", "blockquote", "figure", "figcaption", "li"}:
            self._emit("\n")
        elif tag in {"ul", "ol"}:
            self.list_depth = max(0, self.list_depth - 1)
            self._emit("\n")
        elif tag in {"strong", "b", "em", "i"}:
            self._emit("**" if tag in {"strong", "b"} else "*")
        elif tag == "code":
            self._emit(TICK)
        elif tag == "tr":
            self._emit(" |")

    def handle_data(self, data: str) -> None:
        if self.in_pre:
            self._emit(data)
            return
        value = re.sub(r"\s+", " ", data)
        if value.strip().casefold() in BOILERPLATE_TEXT:
            return
        if value.strip():
            self._emit(value)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "br":
            self._emit("\n")

    def markdown(self) -> str:
        value = html.unescape("".join(self.out))
        value = re.sub(r"[ \t]+\n", "\n", value)
        value = re.sub(r"\n[ \t]+", "\n", value)
        value = re.sub(r"\n{3,}", "\n\n", value)
        return value.strip()


def normalize_html_page(raw: str, fallback_title: str, *, preserve_pre: bool = False) -> tuple[str, str]:
    parser = HTMLToMarkdown(raw, preserve_pre=preserve_pre)
    parser.feed(raw)
    body = clean_markdown(parser.markdown())
    title = first_markdown_heading(body) or fallback_title
    if first_markdown_heading(body):
        body = re.sub(r"(?m)^#\s+" + re.escape(title) + r"\s*#*\s*$", "", body, count=1)
    body = shift_headings(body, 1)
    return title, f"## {title}\n\n{body}".strip()


def mdn_selected(path: Path, root: Path) -> bool:
    parts = [part.casefold() for part in path.relative_to(root).parts]
    if not parts or path.suffix.casefold() != ".md":
        return False
    if any(part in {"guides", "guide"} for part in parts):
        return True
    if parts[0] in {"html", "css", "accessibility", "svg"}:
        return True
    if parts[0] != "api":
        return False
    api_root = parts[1] if len(parts) > 1 else ""
    if api_root in MDN_API_ROOTS:
        return True
    return api_root in MDN_API_PAGES


def webdev_selected(path: Path, root: Path) -> bool:
    parts = [part.casefold() for part in path.relative_to(root).parts]
    joined = "/".join(parts)
    if any(part in {"baseline", "vitals", "performance"} for part in parts):
        return True
    return any(term in joined for term in ("inp", "core-web-vitals", "web-vitals", "interaction-to-next-paint"))


def react_selected(path: Path, root: Path) -> bool:
    parts = path.relative_to(root).parts
    return bool(parts) and parts[0] in {"learn", "reference", "errors", "blog"}


def apg_selected(path: Path, root: Path) -> bool:
    rel = path.relative_to(root).as_posix()
    if rel in {
        "apg-home.html",
        "about/introduction/introduction.html",
        "about/aria-basics/aria-basics.html",
    }:
        return True
    if rel.startswith("practices/"):
        return path.suffix.casefold() == ".html"
    return rel.startswith("patterns/") and rel.endswith("-pattern.html")


def iter_markdown_pages(slug: str) -> list[Path]:
    base = DOCS_ROOT / slug / "repo"
    if slug == "mdn-web-docs":
        root = base / "files" / "en-us" / "web"
        return sorted(p for p in root.rglob("*.md") if mdn_selected(p, root))
    if slug == "web-dev-baseline":
        root = base / "src" / "site" / "content" / "en"
        return sorted(p for p in root.rglob("*.md") if webdev_selected(p, root))
    if slug == "react-dev":
        root = base / "src" / "content"
        return sorted(p for p in root.rglob("*.md") if react_selected(p, root))
    if slug == "playwright-docs":
        return sorted((base / "docs" / "src").rglob("*.md"))
    return []


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def frontmatter(slug: str, retrieved: str) -> str:
    book = BOOKS[slug]
    urls = [book["url"], *book.get("extra_urls", [])]
    values = [
        "---",
        f"title: {yaml_quote(book['title'])}",
        f"book_slug: {slug}",
        f"source_url: {json.dumps(urls, ensure_ascii=False)}",
        f"source_repository: {book['repository']}",
        f"source_commit: {book['commit'] or 'generated official asset'}",
        f"license: {yaml_quote(book['license'])}",
        f"attribution: {yaml_quote(book['attribution'])}",
        f"retrieval_date: {retrieved}",
        "---",
    ]
    return "\n".join(values)


def convert_book(slug: str, retrieved: str = RETRIEVAL_DATE) -> tuple[str, int, list[str]]:
    if slug not in BOOKS:
        raise ValueError(f"unknown docs book slug: {slug}")
    title = BOOKS[slug]["title"]
    pages: list[str] = []
    included: list[str] = []

    if slug == "whatwg-html":
        source = DOCS_ROOT / slug / "repo" / "source"
        raw = source.read_text(encoding="utf-8")
        parser = HTMLToMarkdown(raw, whatwg=True, main_only=False)
        parser.feed(raw)
        body = parser.markdown()
        body = re.sub(r"(?m)^#\s+(?:HTML|HTML Standard)\s*$", "", body, count=1)
        pages.append(body)
        included.append("repo/source")
    elif slug == "wcag-22":
        root = DOCS_ROOT / slug
        candidates = [root / "wcag22.html"]
        candidates.extend(sorted((root / "repo" / "understanding" / "22").rglob("*.html")))
        for path in candidates:
            if not path.is_file():
                continue
            _, page = normalize_html_page(
                path.read_text(encoding="utf-8"),
                path.stem.replace("-", " ").title(),
                preserve_pre=True,
            )
            pages.append(page)
            included.append(path.relative_to(root).as_posix())
    elif slug == "wai-aria-apg":
        root = DOCS_ROOT / slug / "repo" / "content"
        files = sorted(p for p in root.rglob("*.html") if apg_selected(p, root))
        for path in files:
            _, page = normalize_html_page(path.read_text(encoding="utf-8"), path.stem.replace("-", " ").title())
            pages.append(page)
            included.append(path.relative_to(root).as_posix())
    elif slug == "angular-dev":
        root = DOCS_ROOT / slug
        full = clean_markdown((root / "llms-full.txt").read_text(encoding="utf-8"))
        full = shift_headings(full, 1)
        if full:
            pages.append(full)
            included.append("llms-full.txt")
        best = (root / "best-practices.md").read_text(encoding="utf-8")
        _, best_page = normalize_markdown_page(best, "Angular best practices for AI code generation")
        pages.append(best_page)
        included.append("best-practices.md")
    else:
        files = iter_markdown_pages(slug)
        for path in files:
            raw = path.read_text(encoding="utf-8")
            metadata, _ = parse_frontmatter(raw)
            fallback = metadata.get("title", "") or path.parent.name.replace("-", " ").replace("_", " ").title()
            _, page = normalize_markdown_page(raw, fallback)
            if len(re.sub(r"\W", "", page)) < 80:
                continue
            pages.append(page)
            if slug == "mdn-web-docs":
                included.append(path.relative_to(DOCS_ROOT / slug / "repo" / "files" / "en-us" / "web").as_posix())
            else:
                root = DOCS_ROOT / slug / "repo" / ("src/site/content/en" if slug == "web-dev-baseline" else "src/content" if slug == "react-dev" else "docs/src")
                included.append(path.relative_to(root).as_posix())

        if slug == "web-dev-baseline":
            live = DOCS_ROOT / slug / "baseline-current.html"
            if live.exists():
                _, page = normalize_html_page(live.read_text(encoding="utf-8"), "Baseline")
                pages.append(page)
                included.append("baseline-current.html")

    if not pages:
        raise ValueError(f"no eligible prose pages found for {slug}; check sparse source checkout")
    document = f"{frontmatter(slug, retrieved)}\n\n# {title}\n\n" + "\n\n".join(pages).strip() + "\n"
    return document, len(pages), included


def write_sources_doc(retrieved: str = RETRIEVAL_DATE) -> None:
    lines = [
        "# Frontend documentation sources (v10 candidate)",
        "",
        f"Retrieval date: {retrieved}. Prose documents below were acquired for local indexing; source content and names remain attributed to their owners.",
        "",
        "| Source | Source URL / repository | Licence and attribution | Retrieval | Indexing |",
        "|---|---|---|---|---|",
    ]
    for slug, book in BOOKS.items():
        urls = [book["url"], *book.get("extra_urls", [])]
        source = "<br>".join(urls + [book["repository"]])
        commit = f"; commit {book['commit']}" if book["commit"] else "; official generated assets"
        licence = book["license"].replace("|", "\\|")
        lines.append(f"| {slug} | {source} | {licence}; attribution: {book['attribution']} | {retrieved}{commit} | indexed as one book |")
    lines.extend([
        f"| MDN browser-compat-data | https://github.com/mdn/browser-compat-data | CC0-1.0; MDN contributors | live link checked {retrieved} | data, not indexed; link live |",
        f"| web-features / webstatus.dev | https://github.com/web-platform-dx/web-features<br>https://webstatus.dev/ | Apache-2.0; WebDX Community Group | live link checked {retrieved} | data, not indexed; link live |",
        "",
        "## Acquisition notes",
        "",
        "- Repository checkouts are shallow, sparse clones of the documentation source paths. Commit IDs above pin the retrieved tree.",
        "- Angular generated assets were downloaded from the official /assets/context/ URLs. The root .txt route served the web app shell, so it was not used.",
        "- The archived GoogleChrome/web.dev repository declares CC BY 3.0 prose and Apache-2.0 code. The research inventory records CC BY 4.0 for the current web.dev site footer; both notices are retained because the selected material combines repository pages and the current Baseline page.",
        "- WCAG text is retained verbatim with its structure represented by Markdown headings and lists; only site navigation and HTML markup are removed. The published normative page is acquired directly from the W3C TR URL because the repository provides the Understanding pages but not the rendered Recommendation.",
        "- The web.dev current Baseline page is an official-page supplement because its source repository is archived.",
        "",
    ])
    SOURCES_PATH.parent.mkdir(parents=True, exist_ok=True)
    SOURCES_PATH.write_text("\n".join(lines), encoding="utf-8")


def convert_all(retrieved: str = RETRIEVAL_DATE) -> dict[str, dict[str, object]]:
    MARKDOWN_DIR.mkdir(parents=True, exist_ok=True)
    collisions = []
    for slug in BOOKS:
        existing = MARKDOWN_DIR / f"{slug}.md"
        if existing.exists():
            metadata, _ = parse_frontmatter(existing.read_text(encoding="utf-8"))
            if metadata.get("book_slug") != slug:
                collisions.append(str(existing))
    if collisions:
        raise FileExistsError("refusing to overwrite unrelated markdown file(s): " + ", ".join(collisions))
    report: dict[str, dict[str, object]] = {}
    for slug in BOOKS:
        document, page_count, included = convert_book(slug, retrieved)
        out = MARKDOWN_DIR / f"{slug}.md"
        out.write_text(document, encoding="utf-8")
        report[slug] = {
            "title": BOOKS[slug]["title"],
            "pages": page_count,
            "markdown_bytes": len(document.encode("utf-8")),
            "included_paths": included,
        }
        print(f"{slug}: {page_count} pages -> {out} ({report[slug]['markdown_bytes']} bytes)")
    write_sources_doc(retrieved)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps({"retrieval_date": retrieved, "books": report}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def chunk_book(slug: str, *, overwrite: bool = False) -> dict[str, object]:
    md_path = MARKDOWN_DIR / f"{slug}.md"
    out = CHUNKS_DIR / f"{slug}.json"
    if not md_path.is_file():
        raise FileNotFoundError(f"Markdown not found: {md_path}")
    if out.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite existing chunk file: {out}")
    from knowledge_base import chunk as kb_chunk

    text = md_path.read_text(encoding="utf-8")
    _, text = parse_frontmatter(text)
    with tempfile.TemporaryDirectory(prefix="kb-docs-chunk-") as temp:
        temp_dir = Path(temp)
        (temp_dir / md_path.name).write_text(text, encoding="utf-8")
        previous_dir = kb_chunk.MARKDOWN_DIR
        kb_chunk.MARKDOWN_DIR = temp_dir
        try:
            data = kb_chunk.chunk_book(slug)
        finally:
            kb_chunk.MARKDOWN_DIR = previous_dir
    title = BOOKS[slug]["title"]
    for parent in data["parents"]:
        parent["metadata"]["book_title"] = title
    for child in data["children"]:
        child["metadata"]["book_title"] = title
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "slug": slug,
        "parents": len(data["parents"]),
        "children": len(data["children"]),
        "path": str(out),
    }


def chunk_all(*, overwrite: bool = False) -> list[dict[str, object]]:
    global CHUNKS_DIR
    rows: list[dict[str, object]] = []
    target_dir = CHUNKS_DIR
    with tempfile.TemporaryDirectory(prefix="kb-docs-chunks-") as temp:
        CHUNKS_DIR = Path(temp)
        try:
            rows = [chunk_book(slug, overwrite=True) for slug in BOOKS]
        finally:
            CHUNKS_DIR = target_dir
        total = sum(int(row["children"]) for row in rows)
        if total > 60_000:
            raise ValueError(f"docs child-vector cap exceeded: {total} > 60000; no chunk files written")
        target_dir.mkdir(parents=True, exist_ok=True)
        collisions = [target_dir / f"{slug}.json" for slug in BOOKS if (target_dir / f"{slug}.json").exists()]
        if collisions and not overwrite:
            raise FileExistsError("refusing to overwrite existing chunk file(s): " + ", ".join(map(str, collisions)))
        for slug in BOOKS:
            (target_dir / f"{slug}.json").write_bytes((Path(temp) / f"{slug}.json").read_bytes())
        for row in rows:
            row["path"] = str(target_dir / f"{row['slug']}.json")
    summary = {"books": rows, "total_children": total, "cap": 60_000}
    out = ROOT / "data" / "intake" / "v10-docs-chunk-counts.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    for row in rows:
        print(f"{row['slug']}: {row['children']} children / {row['parents']} parents")
    print(f"total: {total} children (cap 60000)")
    return rows


def read_counts() -> dict[str, int]:
    counts: dict[str, int] = {}
    for slug in BOOKS:
        path = CHUNKS_DIR / f"{slug}.json"
        if path.exists():
            counts[slug] = len(json.loads(path.read_text(encoding="utf-8"))["children"])
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices={"convert", "chunk", "all", "counts"})
    parser.add_argument("--retrieved", default=RETRIEVAL_DATE)
    parser.add_argument("--overwrite-chunks", action="store_true")
    args = parser.parse_args()
    if args.command == "convert":
        convert_all(args.retrieved)
    elif args.command == "chunk":
        chunk_all(overwrite=args.overwrite_chunks)
    elif args.command == "all":
        convert_all(args.retrieved)
        chunk_all(overwrite=args.overwrite_chunks)
    else:
        counts = read_counts()
        print(json.dumps({"books": counts, "total_children": sum(counts.values())}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
