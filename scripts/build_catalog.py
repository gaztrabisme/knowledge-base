"""Build the book catalog (data/catalog.json): slug -> {title, domain, tags, summary}.

`title` and `domain` are derived deterministically from knowledge_base.config and
the source tree — no LLM. `tags` and `summary` come from one schema-constrained
omlx call per book, seeded with the title, domain and a token-capped table of
contents extracted from data/markdown/<slug>.md.

Usage:
  .venv/bin/python scripts/build_catalog.py                          # all books
  .venv/bin/python scripts/build_catalog.py --books slug1,slug2 --out partial.json
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

import tiktoken

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))    # knowledge_base
sys.path.insert(0, os.path.expanduser("~/.claude/skills/omlx/scripts"))
import omlx_client as oc

from knowledge_base.config import BOOKS, MARKDOWN_DIR, ROOT, SOURCE_DIRS

MODEL = "Qwen3.8-Flash-Next-REAP-384-oQ4e-BF16-MTP-PLE"
CATALOG_PATH = ROOT / "data" / "catalog.json"
MAX_TOC_TOKENS = 3000

_enc = tiktoken.get_encoding("cl100k_base")

TAGS = [
    "machine-learning", "deep-learning", "neural-networks", "pytorch", "scikit-learn",
    "pandas", "statistics", "bayesian-inference", "probabilistic-modeling", "time-series",
    "forecasting", "causal-inference", "reinforcement-learning", "graph-ml", "computer-vision",
    "nlp", "transformers", "feature-engineering", "model-evaluation", "optimization",
    "math-foundations", "gpu-cuda", "ensembles", "kaggle", "algorithmic-trading",
    "finance", "iot-edge", "cpp", "interpretability", "active-learning",
    "data-labeling", "recommender-systems", "llm", "rag", "embeddings",
    "vector-search", "search-relevance", "prompt-engineering", "ai-agents", "fine-tuning",
    "llm-evaluation", "guardrails", "llm-serving", "mlops", "ml-platform",
    "ml-system-design", "conversational-ai", "ai-product", "ai-assisted-coding", "genai-testing",
    "cloud-ai-services", "postgresql", "sql", "database-internals", "indexing",
    "query-optimization", "transactions-mvcc", "relational-design", "redis", "caching",
    "nosql", "cryptography", "web-security", "appsec", "owasp",
    "authentication-oauth", "security-testing", "threat-modeling", "linux-hardening", "ai-security",
    "distributed-systems", "consensus-replication", "microservices", "event-driven", "messaging-integration",
    "api-design", "domain-driven-design", "software-architecture", "architecture-decisions", "enterprise-architecture",
    "data-architecture", "multi-tenant-saas", "cloud-native", "green-software", "systems-thinking",
    "scalability-reliability", "sre-operations", "observability", "clean-code", "refactoring",
    "design-patterns", "testing-tdd", "continuous-delivery", "version-control-git", "code-review",
    "platform-engineering", "algorithms-data-structures", "software-engineering-practice", "team-organization", "rust",
    "async-concurrency", "systems-programming", "webassembly", "web-development", "game-development",
    "blockchain", "python-interop", "linux", "systemd", "shell-scripting",
    "networking", "kernel", "python",
]

SCHEMA = {
    "type": "object",
    "properties": {
        "tags": {
            "type": "array",
            "items": {"type": "string", "enum": TAGS},
            "minItems": 6,
            "maxItems": 10,
            "uniqueItems": True,
        },
        "summary": {"type": "string", "maxLength": 200},
    },
    "required": ["tags", "summary"],
    "additionalProperties": False,
}

PROMPT = """You are building the catalog for a developer knowledge base of technical books.

Book title: {title}
Domain: {domain}

Table of contents:
{toc}

Choose the 6-10 tags from the allowed tag list below that best describe what a developer
would come to this book for. Then write ONE sentence of at most 25 words saying what the
book covers. The summary must not praise the book (no "essential", "invaluable",
"comprehensive guide" and the like).

Allowed tags:
{tags}"""


def find_domain(slug: str) -> str | None:
    """SOURCE_DIRS key of the directory holding the book's source file, or None.

    A book is a file with any extension whose stem is the slug, or (owasp-cheat-sheets)
    a directory named after the slug."""
    for key, d in SOURCE_DIRS.items():
        if not d.exists():
            continue
        for f in sorted(d.iterdir()):
            if f.name == slug or f.stem == slug:
                return key
    return None


def extract_toc(md_path: Path) -> str:
    """'#'/'##' heading texts from the book markdown, deduplicated and token-capped.

    Skips lines inside fenced code blocks, unwraps headings that are only a markdown
    link, and strips '(part N)' suffixes so repeated section names collapse."""
    if not md_path.exists():
        return ""
    toc: list[str] = []
    seen: set[str] = set()
    in_fence = False
    for line in md_path.read_text(errors="replace").splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"^(#{1,2})\s+(.+?)\s*$", stripped)
        if not m:
            continue
        text = m.group(2)
        link = re.fullmatch(r"\[([^\]]+)\]\([^)]*\)", text)
        if link:
            text = link.group(1)
        text = re.sub(r"\s*\([Pp]arts?\s+\d+\)\s*$", "", text).strip()
        if text and text not in seen:
            seen.add(text)
            toc.append(text)
    text = "\n".join(toc)
    ids = _enc.encode(text, disallowed_special=())
    if len(ids) > MAX_TOC_TOKENS:
        text = _enc.decode(ids[:MAX_TOC_TOKENS])
    return text


def validate_tags(obj: dict) -> str | None:
    """Error string for unusable tags/summary, or None if they pass."""
    tags = obj.get("tags")
    if not isinstance(tags, list):
        return "tags is not a list"
    if not 6 <= len(tags) <= 10:
        return f"{len(tags)} tags, need 6-10"
    if len(set(tags)) != len(tags):
        return "duplicate tags"
    bad = [t for t in tags if t not in TAGS]
    if bad:
        return f"tags outside TAGS: {bad}"
    summary = obj.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        return "empty summary"
    return None


def describe(slug: str, title: str, domain: str, toc: str) -> tuple[dict | str, str | None]:
    """One schema-constrained call per book; retry once, then record "error"."""
    prompt = PROMPT.format(title=title, domain=domain, toc=toc or "(not available)",
                           tags=", ".join(TAGS))
    err = "no attempt made"
    enforcement = None
    for _attempt in range(2):
        try:
            obj, meta = oc.chat_json(
                [{"role": "user", "content": prompt}], MODEL,
                schema=SCHEMA, name="catalog",
                require=("tags", "summary"), with_meta=True, max_tokens=400,
            )
        except Exception as e:
            err = str(e)
            continue
        enforcement = meta.get("enforcement")
        err = validate_tags(obj)
        if err is None:
            return {"tags": obj["tags"], "summary": obj["summary"].strip()}, enforcement
    print(f"  ERROR {slug}: {err}")
    return "error", enforcement


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--books", help="comma-separated book slugs (default: all)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", default=str(CATALOG_PATH))
    args = ap.parse_args()

    slugs = list(BOOKS)
    if args.books:
        slugs = [s.strip() for s in args.books.split(",") if s.strip()]
        unknown = [s for s in slugs if s not in BOOKS]
        if unknown:
            ap.error(f"unknown book slug(s): {unknown}")

    out_path = Path(args.out)
    catalog: dict = {}
    if args.books and out_path.exists():
        catalog = json.loads(out_path.read_text())  # partial runs merge, not replace

    todo = []
    for slug in slugs:
        domain = find_domain(slug) or "unknown"
        todo.append((slug, BOOKS[slug], domain, extract_toc(MARKDOWN_DIR / f"{slug}.md")))

    def one(item):
        slug, title, domain, toc = item
        described, enforcement = describe(slug, title, domain, toc)
        if described == "error":
            entry = "error"
        else:
            entry = {"title": title, "domain": domain, **described}
        return slug, entry, enforcement

    enforcements: set[str] = set()
    for slug, entry, enforcement in oc.fanout(todo, one, workers=args.workers):
        catalog[slug] = entry
        if enforcement:
            enforcements.add(enforcement)

    catalog["_meta"] = {"model": MODEL, "enforcement": ", ".join(sorted(enforcements)) or "none"}

    entries = {k: v for k, v in catalog.items() if k != "_meta"}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        json.dump(catalog, f, indent=1, sort_keys=True)
        f.write("\n")

    print(f"Wrote {len(entries)} entries -> {out_path}")
    no_domain = sorted(s for s, e in entries.items() if isinstance(e, dict) and e["domain"] == "unknown")
    if no_domain:
        print(f"domain unknown for {len(no_domain)}: {', '.join(no_domain)}")
    failed = sorted(s for s, e in entries.items() if not isinstance(e, dict))
    if failed:
        print(f"errors on {len(failed)}: {', '.join(failed)}")


if __name__ == "__main__":
    main()
