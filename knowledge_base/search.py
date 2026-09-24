"""Hybrid search (dense + BM25) with Ettin-150m cross-encoder reranking."""

import os
import sys
from dataclasses import dataclass

from qdrant_client import QdrantClient, models
from sentence_transformers import CrossEncoder

from .config import (
    COLLECTION_NAME,
    QDRANT_DIR,
    RERANKER_MODEL,
    RERANKER_MIN_RESULTS,
    RERANKER_SCORE_FLOOR,
)
from .index import embed_texts, text_to_sparse_vector

_reranker: CrossEncoder | None = None
_client: QdrantClient | None = None


def get_ranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(RERANKER_MODEL, trust_remote_code=True)
    return _reranker


def get_client() -> QdrantClient:
    # ⚡2: long-lived singleton, reused for the process lifetime.
    # Prefer a shared Qdrant *server* (KB_QDRANT_URL, default 127.0.0.1:6333) so
    # multiple concurrent MCP servers / Claude Code sessions can all read at once —
    # the file-based store takes an exclusive single-process lock and only one
    # session could use it. Fall back to the embedded store if the server is down
    # (single-session mode, same as before).
    global _client
    if _client is None:
        url = os.environ.get("KB_QDRANT_URL", "http://127.0.0.1:6333")
        try:
            c = QdrantClient(url=url, timeout=30)
            c.get_collections()  # ping — raises if the server is unreachable
            _client = c
        except Exception as e:
            print(f"[kb] Qdrant server {url} unreachable ({e}); "
                  f"falling back to embedded store {QDRANT_DIR}", file=sys.stderr)
            _client = QdrantClient(path=str(QDRANT_DIR))
    return _client


@dataclass
class SearchResult:
    score: float
    book: str
    book_title: str
    chapter: str
    section: str
    heading_path: str
    content: str
    child_match: str
    parent_id: str = ""
    child_id: str = ""

    def to_dict(self) -> dict:
        return {
            "score": round(float(self.score), 4),
            "book": self.book_title,
            "chapter": self.chapter,
            "section": self.section,
            "heading_path": self.heading_path,
            "content": self.content,
            "child_match": self.child_match,
            # chunk_id lets the agent expand context via read_chunk(chunk_id)
            "chunk_id": self.child_id,
        }


def hybrid_search(
    query: str,
    client: QdrantClient,
    top_k: int = 10,
    candidates: int = 50,
    book_filter: str | list[str] | None = None,
    rerank: bool = True,
    hyde_passage: str | None = None,
    extra_queries: list[str] | None = None,
    bm25_keywords: list[str] | None = None,
    domain_filter: str | None = None,
) -> list[SearchResult]:
    # ⚡4: embed the query, the optional HyDE passage, and all extra-query variants
    # in ONE batch instead of one embed_texts() call per variant.
    #
    # HyDE is AUGMENT, not replace: the original query vector is ALWAYS a dense leg
    # (the anchor); a hyde_passage adds a SECOND dense leg rather than replacing the
    # query. Measured 2026-05-31 — replace-mode HyDE drifted off the chunks the bare
    # query matched, breaking 5 previously-working hard queries and rescuing none of
    # the never-retrieved recall misses (NDCG 0.7921→0.7753). Keeping the query anchor
    # in fusion prevents that drift while still reaching for the passage's recall.
    dense_texts = [query]
    if hyde_passage:
        dense_texts.append(hyde_passage)
    dense_texts.extend(extra_queries or [])
    dense_vectors = embed_texts(dense_texts, task="retrieval.query")

    bm25_text = " ".join(bm25_keywords) if bm25_keywords else query
    query_sparse = text_to_sparse_vector(bm25_text)

    must = []
    if isinstance(book_filter, str) and book_filter:
        must.append(models.FieldCondition(
            key="book",
            match=models.MatchValue(value=book_filter),
        ))
    elif book_filter:
        must.append(models.FieldCondition(
            key="book",
            match=models.MatchAny(any=book_filter),
        ))
    if domain_filter is not None:
        must.append(models.FieldCondition(
            key="domain",
            match=models.MatchValue(value=domain_filter),
        ))
    filter_conditions = models.Filter(must=must) if must else None

    def _dense_prefetch(vec):
        return models.Prefetch(query=vec, using="", filter=filter_conditions, limit=candidates)

    def _sparse_prefetch(sparse):
        return models.Prefetch(
            query=models.SparseVector(indices=sparse.indices, values=sparse.values),
            using="bm25", filter=filter_conditions, limit=candidates,
        )

    # One dense leg per embedded text (query [+ hyde] [+ extra_queries]); BM25 on the
    # original query plus each extra query. HyDE prose is not a keyword query, so it
    # gets no BM25 leg.
    prefetches = [_dense_prefetch(v) for v in dense_vectors]
    prefetches.append(_sparse_prefetch(query_sparse))
    for eq in (extra_queries or []):
        prefetches.append(_sparse_prefetch(text_to_sparse_vector(eq)))

    fused = client.query_points(
        collection_name=COLLECTION_NAME,
        prefetch=prefetches,
        query=models.FusionQuery(fusion=models.Fusion.DBSF),
        limit=candidates if rerank else top_k,
        with_payload=True,
    ).points

    merged = [
        {"id": str(p.id), "score": p.score, "payload": p.payload}
        for p in fused
    ]

    if rerank and merged:
        merged = _rerank(query, merged, top_k)
    else:
        merged = merged[:top_k]

    return _deduplicate_parents(merged)


# Rust book slugs — the domain where heading_path is descriptive enough to help the
# cross-encoder (e.g. "Async > Futures > Pinning"). In security/ml/db the headings are
# generic or formal section titles that add tokens orthogonal to a developer-symptom
# query, diluting the content match (measured: diag-rerank-positions, 2026-05-31).
_RUST_BOOKS = frozenset({
    "asynchronousprogramminginrust", "creativeprojectsforrustprogrammers",
    "designpatternsandbestpracticesinrust", "gamedevelopmentwithrustandwebassembly",
    "hands-onconcurrencywithrust", "practicalsystemprogrammingforrustdevelopers",
    "rust_ebook", "rustforblockchainapplicationdevelopment", "rustforcplusplusdeveloper",
    "rustprogramminghandbook", "rustwebdevelopmentwithrocket", "rustwebprogramming",
    "speedupyourpythonwithrust",
})

# Generic/formal-heading books — databases (ops), distributed, security (crypto
# formalism, OWASP section numbers). Headings here are tokens orthogonal to a
# developer-symptom query, so the cross-encoder does better on bare child text.
_GENERIC_HEADING_BOOKS = frozenset({
    # databases
    "postgresql-14-internals", "database-design-2nd-ed", "redis-for-dummies",
    "little-redis-book", "digitalocean-redis",
    # distributed
    "designing-distributed-systems", "distributed-systems-fun-profit",
    # security
    "boneh-shoup-applied-cryptography", "crypto-101", "joy-of-cryptography",
    "owasp-developer-guide", "owasp-wstg-v4.2", "owasp-asvs-v5", "oauth-rfcs-book",
})


def _rerank_doc(p: dict) -> str:
    """Build the text the cross-encoder scores for one candidate.

    ⚡1 (v6.1) prepended heading_path globally — but the rank diagnostic (2026-05-31)
    showed that helps {ml, rust} and HURTS {security, databases, distributed}, whose
    headings are formal/generic tokens orthogonal to a developer-symptom query
    (joy-of-crypto positive moved rerank-rank 23→9 with the heading removed). The A/B
    over the golden gates picked `descriptive-heading`: hard NDCG 0.7921→0.8021,
    easy 0.9434→0.9379 (easy R@10 unchanged — no recall lost, pure reorder).
    Modes (env override `KB_RERANK_INPUT`, default is the shipped winner):
      descriptive-heading — heading for {ml, rust}, child for generic-heading books (DEFAULT)
      heading             — heading_path + context + child   (v6.1 global)
      child               — context + child                  (pre-⚡1)
      rust-heading        — heading only for rust books
    """
    mode = os.environ.get("KB_RERANK_INPUT", "descriptive-heading")
    ctx, text = p.get("context_text", ""), p.get("child_text", "")
    heading = p.get("heading_path", "")
    book = p.get("book", "")
    if mode == "child":
        use_heading = False
    elif mode == "rust-heading":
        use_heading = book in _RUST_BOOKS
    elif mode == "descriptive-heading":
        # heading for {ml, rust} (descriptive section titles), child for the
        # generic/formal-heading books (security, databases, distributed).
        use_heading = book not in _GENERIC_HEADING_BOOKS
    else:  # "heading" (default, v6.1)
        use_heading = True
    parts = [heading, ctx, text] if use_heading else [ctx, text]
    return "\n".join(x for x in parts if x)


def _rerank(query: str, results: list[dict], top_k: int) -> list[dict]:
    reranker = get_ranker()

    documents = [_rerank_doc(r["payload"]) for r in results]

    rankings = reranker.rank(query, documents)

    scored = []
    for item in rankings:
        result = results[int(item["corpus_id"])]
        result["score"] = float(item["score"])
        scored.append(result)

    return _adaptive_cutoff(scored, top_k)


def _adaptive_cutoff(results: list[dict], top_k: int) -> list[dict]:
    kept = [r for r in results if r["score"] >= RERANKER_SCORE_FLOOR]
    kept = kept[:top_k]
    if len(kept) < RERANKER_MIN_RESULTS:
        kept = results[:RERANKER_MIN_RESULTS]
    return kept


def _deduplicate_parents(results: list[dict]) -> list[SearchResult]:
    seen_parents: set[str] = set()
    deduped = []

    for r in results:
        p = r["payload"]
        parent_id = p.get("parent_id", "")
        if parent_id in seen_parents:
            continue
        seen_parents.add(parent_id)

        deduped.append(SearchResult(
            score=r["score"],
            book=p.get("book", ""),
            book_title=p.get("book_title", ""),
            chapter=p.get("chapter", ""),
            section=p.get("section", ""),
            heading_path=p.get("heading_path", ""),
            content=p.get("parent_text", ""),
            child_match=p.get("child_text", ""),
            parent_id=parent_id,
            child_id=p.get("child_id", ""),
        ))

    return deduped
