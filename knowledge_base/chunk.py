"""Heading-aware parent/child chunker with code block preservation."""

import json
import re

import tiktoken

from .config import (
    BOOKS, CHUNKS_DIR, MARKDOWN_DIR,
    PARENT_MAX_TOKENS, CHILD_MAX_TOKENS, CHILD_MIN_TOKENS,
)

PARENT_MIN_TOKENS = 300

_encoder = tiktoken.get_encoding("cl100k_base")


def estimate_tokens(text: str) -> int:
    # cl100k_base tracks the Jina v5 tokenizer within ~2%; far closer than word count.
    return len(_encoder.encode(text, disallowed_special=()))


def extract_sections(markdown: str) -> list[dict]:
    """Split markdown into sections by ## headings, tracking heading hierarchy."""
    lines = markdown.split("\n")
    sections = []
    current_h1 = ""
    current_h2 = ""
    current_lines: list[str] = []
    current_heading_path = ""

    def flush():
        if current_lines:
            text = "\n".join(current_lines).strip()
            if text:
                sections.append({
                    "text": text,
                    "chapter": current_h1,
                    "section": current_h2,
                    "heading_path": current_heading_path,
                })

    in_code = False
    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
            current_lines.append(line)
            continue

        if in_code:
            current_lines.append(line)
            continue

        h1_match = re.match(r"^#\s+(.+)", line)
        h2_match = re.match(r"^##\s+(.+)", line)

        if h1_match:
            flush()
            current_h1 = h1_match.group(1).strip()
            current_h2 = ""
            current_lines = [line]
            current_heading_path = current_h1
        elif h2_match:
            flush()
            current_h2 = h2_match.group(1).strip()
            current_lines = [line]
            current_heading_path = f"{current_h1} > {current_h2}" if current_h1 else current_h2
        else:
            current_lines.append(line)

    flush()
    return sections


def merge_small_sections(sections: list[dict]) -> list[dict]:
    """Merge consecutive small sections into larger parents."""
    if not sections:
        return sections

    merged = []
    accumulator = None

    for section in sections:
        tokens = estimate_tokens(section["text"])

        if accumulator is None:
            if tokens < PARENT_MIN_TOKENS:
                accumulator = section.copy()
            else:
                merged.append(section)
            continue

        same_chapter = section["chapter"] == accumulator["chapter"]
        combined = accumulator["text"] + "\n\n" + section["text"]

        if same_chapter and estimate_tokens(combined) <= PARENT_MAX_TOKENS:
            accumulator["text"] = combined
            if section["section"]:
                accumulator["section"] = section["section"]
                accumulator["heading_path"] = section["heading_path"]
        else:
            merged.append(accumulator)
            if tokens < PARENT_MIN_TOKENS:
                accumulator = section.copy()
            else:
                merged.append(section)
                accumulator = None

    if accumulator:
        merged.append(accumulator)

    return merged


def split_large_section(section: dict) -> list[dict]:
    """If a section exceeds PARENT_MAX_TOKENS, split on ### headings."""
    if estimate_tokens(section["text"]) <= PARENT_MAX_TOKENS:
        return [section]

    lines = section["text"].split("\n")
    subsections = []
    current_lines: list[str] = []
    current_h3 = ""
    in_code = False

    def flush_sub():
        if current_lines:
            text = "\n".join(current_lines).strip()
            if text:
                path = section["heading_path"]
                if current_h3:
                    path = f"{path} > {current_h3}"
                subsections.append({
                    "text": text,
                    "chapter": section["chapter"],
                    "section": section["section"],
                    "heading_path": path,
                })

    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
            current_lines.append(line)
            continue
        if in_code:
            current_lines.append(line)
            continue

        h3_match = re.match(r"^###\s+(.+)", line)
        if h3_match:
            flush_sub()
            current_h3 = h3_match.group(1).strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    flush_sub()

    if not subsections:
        return _force_split(section)

    final = []
    for sub in subsections:
        if estimate_tokens(sub["text"]) > PARENT_MAX_TOKENS:
            final.extend(_force_split(sub))
        else:
            final.append(sub)
    return final


def _force_split(section: dict) -> list[dict]:
    """Last resort: split on paragraph boundaries when still too large."""
    paragraphs = _split_preserving_code(section["text"])
    bounded = []
    for para in paragraphs:
        if estimate_tokens(para) > PARENT_MAX_TOKENS:
            bounded.extend(_hard_split_block(para, PARENT_MAX_TOKENS))
        else:
            bounded.append(para)
    parts = []
    current: list[str] = []
    for para in bounded:
        candidate = "\n\n".join(current + [para])
        if current and estimate_tokens(candidate) > PARENT_MAX_TOKENS:
            parts.append("\n\n".join(current))
            current = [para]
        else:
            current.append(para)

    if current:
        parts.append("\n\n".join(current))

    final_parts = []
    for part in parts:
        if estimate_tokens(part) <= PARENT_MAX_TOKENS:
            final_parts.append(part)
        else:
            final_parts.extend(_hard_split_block(part, PARENT_MAX_TOKENS))

    return [
        {
            "text": part,
            "chapter": section["chapter"],
            "section": section["section"],
            "heading_path": f"{section['heading_path']} (part {i+1})",
        }
        for i, part in enumerate(final_parts)
    ]


def _split_preserving_code(text: str) -> list[str]:
    """Split text into paragraphs, keeping code blocks as single units."""
    blocks = []
    current: list[str] = []
    in_code = False

    for line in text.split("\n"):
        if line.strip().startswith("```"):
            if not in_code:
                if current:
                    para_text = "\n".join(current).strip()
                    if para_text:
                        blocks.extend(p for p in para_text.split("\n\n") if p.strip())
                    current = []
                in_code = True
                current = [line]
            else:
                current.append(line)
                blocks.append("\n".join(current))
                current = []
                in_code = False
        else:
            current.append(line)

    if current:
        para_text = "\n".join(current).strip()
        if para_text:
            blocks.extend(p for p in para_text.split("\n\n") if p.strip())

    return blocks


def _hard_split_block(block: str, max_tokens: int) -> list[str]:
    """Split a single oversized block (code or prose) into token-bounded pieces.

    Code blocks are split by lines and re-fenced so each piece stays valid
    markdown; prose is split by sentences, falling back to words for a single
    monster sentence. Children are match units, so aggressive splitting is fine
    — the parent still returns the whole block as context.
    """
    if block.strip().startswith("```"):
        lines = block.split("\n")
        fence = lines[0] if lines[0].strip().startswith("```") else "```"
        body = lines[1:]
        if body and body[-1].strip().startswith("```"):
            body = body[:-1]
        pieces, current = [], []

        def flush_code():
            if current:
                pieces.append(f"{fence}\n" + "\n".join(current) + "\n```")
                current.clear()

        for line in body:
            if estimate_tokens(line) > max_tokens - 8:
                flush_code()
                for fragment in _split_words_bounded(line, max_tokens - 8):
                    pieces.append(f"{fence}\n{fragment}\n```")
                continue
            candidate = f"{fence}\n" + "\n".join(current + [line]) + "\n```"
            if current and estimate_tokens(candidate) > max_tokens:
                flush_code()
            current.append(line)
        flush_code()
        return pieces or [block]

    return _split_words_bounded(block, max_tokens)


def _split_long_word(word: str, max_tokens: int) -> list[str]:
    pieces = []
    start = 0
    while start < len(word):
        low, high, end = start + 1, len(word), start + 1
        while low <= high:
            middle = (low + high) // 2
            if estimate_tokens(word[start:middle]) <= max_tokens:
                end = middle
                low = middle + 1
            else:
                high = middle - 1
        pieces.append(word[start:end])
        start = end
    return pieces


def _split_words_bounded(text: str, max_tokens: int) -> list[str]:
    """Pack words below a hard cap, splitting a single oversized word string."""
    pieces, current = [], []
    for word in text.split():
        fragments = _split_long_word(word, max_tokens) if estimate_tokens(word) > max_tokens else [word]
        for fragment in fragments:
            candidate = " ".join(current + [fragment])
            if current and estimate_tokens(candidate) > max_tokens:
                pieces.append(" ".join(current))
                current = [fragment]
            else:
                current.append(fragment)
    if current:
        pieces.append(" ".join(current))
    return pieces or [text]


def create_children(parent_text: str, parent_id: str) -> list[dict]:
    """Split a parent chunk into children on paragraph boundaries."""
    raw_paragraphs = _split_preserving_code(parent_text)
    paragraphs = []
    for para in raw_paragraphs:
        if estimate_tokens(para) > CHILD_MAX_TOKENS:
            paragraphs.extend(_hard_split_block(para, CHILD_MAX_TOKENS))
        else:
            paragraphs.append(para)
    children = []
    current: list[str] = []

    def flush_child():
        if current:
            text = "\n\n".join(current).strip()
            if estimate_tokens(text) >= CHILD_MIN_TOKENS:
                children.append({
                    "child_id": f"{parent_id}-c{len(children)}",
                    "parent_id": parent_id,
                    "text": text,
                    "context_text": "",
                    "chunk_type": "code" if text.strip().startswith("```") else "prose",
                })

    for para in paragraphs:
        pt = estimate_tokens(para)

        if current and estimate_tokens("\n\n".join(current + [para])) > CHILD_MAX_TOKENS:
            flush_child()
            current = [para]
        else:
            current.append(para)

    flush_child()

    if not children and parent_text.strip():
        children.append({
            "child_id": f"{parent_id}-c0",
            "parent_id": parent_id,
            "text": parent_text.strip(),
            "context_text": "",
            "chunk_type": "prose",
        })

    return children


def _extract_last_sentences(text: str, n: int = 2) -> str:
    """Extract last N sentences from text, skipping code blocks."""
    lines = text.split("\n")
    prose_lines = []
    in_code = False
    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if not in_code:
            prose_lines.append(line)

    prose = " ".join(prose_lines)
    sentences = re.split(r"(?<=[.!?])\s+", prose.strip())
    sentences = [s for s in sentences if len(s) > 20]
    if not sentences:
        return ""
    return " ".join(sentences[-n:])


def chunk_book(book_slug: str) -> dict:
    """Chunk a single book into parent/child structure."""
    md_path = MARKDOWN_DIR / f"{book_slug}.md"
    if not md_path.exists():
        raise FileNotFoundError(f"Markdown not found: {md_path}")

    text = md_path.read_text(encoding="utf-8")
    sections = extract_sections(text)
    sections = merge_small_sections(sections)

    all_parts = []
    for section in sections:
        all_parts.extend(split_large_section(section))

    for i in range(1, len(all_parts)):
        if all_parts[i]["chapter"] == all_parts[i - 1]["chapter"] and all_parts[i]["chapter"]:
            overlap = _extract_last_sentences(all_parts[i - 1]["text"])
            if overlap:
                all_parts[i]["text"] = f"{overlap}\n\n{all_parts[i]['text']}"

    bounded_parts = []
    for part in all_parts:
        if estimate_tokens(part["text"]) > PARENT_MAX_TOKENS:
            bounded_parts.extend(_force_split(part))
        else:
            bounded_parts.append(part)
    all_parts = bounded_parts

    parents = []
    all_children = []
    chapter_num = 0

    for part in all_parts:
        parent_id = f"{book_slug}-p{len(parents)}"

        if part["chapter"] and part["chapter"] != (parents[-1]["metadata"]["chapter_title"] if parents else ""):
            chapter_num += 1

        parent = {
            "parent_id": parent_id,
            "text": part["text"],
            "metadata": {
                "book": book_slug,
                "book_title": BOOKS.get(book_slug, book_slug),
                "chapter": str(chapter_num),
                "chapter_title": part["chapter"],
                "section": part["section"],
                "heading_path": part["heading_path"],
            },
        }
        parents.append(parent)

        children = create_children(part["text"], parent_id)
        for child in children:
            child["metadata"] = parent["metadata"].copy()
            child["metadata"]["chunk_type"] = child.pop("chunk_type")
        all_children.extend(children)

    return {"parents": parents, "children": all_children}


def chunk_all() -> dict[str, dict]:
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
    results = {}

    for md_file in sorted(MARKDOWN_DIR.glob("*.md")):
        slug = md_file.stem
        output = CHUNKS_DIR / f"{slug}.json"
        if output.exists():
            print(f"  Skipping (exists): {slug}")
            with open(output) as f:
                results[slug] = json.load(f)
            continue

        print(f"  Chunking: {slug}")
        data = chunk_book(slug)
        with open(output, "w") as f:
            json.dump(data, f, indent=2)
        results[slug] = data
        print(f"    → {len(data['parents'])} parents, {len(data['children'])} children")

    return results


if __name__ == "__main__":
    print("Chunking markdown files...")
    all_data = chunk_all()
    total_parents = sum(len(d["parents"]) for d in all_data.values())
    total_children = sum(len(d["children"]) for d in all_data.values())
    print(f"Done. {total_parents} parents, {total_children} children across {len(all_data)} books")
