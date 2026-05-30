"""Hybrid search (dense + BM25) with Ettin-150m cross-encoder reranking."""

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
    # ⚡2: long-lived singleton. Opening a file-based 48K-point collection re-scans
    # all segment metadata (~5.9s); reopening per query cost ~7s/call. Reuse one
    # client for the process lifetime. The MCP server is the intended caller and
    # holds the single-process lock for as long as it runs (it must be DOWN during
    # any offline delete/index — see index.py).
    global _client
    if _client is None:
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
        }


def hybrid_search(
    query: str,
    client: QdrantClient,
    top_k: int = 10,
    candidates: int = 50,
    book_filter: str | None = None,
    rerank: bool = True,
    hyde_passage: str | None = None,
    extra_queries: list[str] | None = None,
    bm25_keywords: list[str] | None = None,
) -> list[SearchResult]:
    # ⚡4: embed the primary query and all extra-query variants in ONE batch
    # instead of one embed_texts() call per variant.
    dense_text = hyde_passage if hyde_passage else query
    dense_texts = [dense_text] + list(extra_queries or [])
    dense_vectors = embed_texts(dense_texts, task="retrieval.query")
    dense_vector = dense_vectors[0]
    bm25_text = " ".join(bm25_keywords) if bm25_keywords else query
    query_sparse = text_to_sparse_vector(bm25_text)

    filter_conditions = None
    if book_filter:
        filter_conditions = models.Filter(
            must=[models.FieldCondition(
                key="book",
                match=models.MatchValue(value=book_filter),
            )]
        )

    prefetches = [
        models.Prefetch(
            query=dense_vector,
            using="",
            filter=filter_conditions,
            limit=candidates,
        ),
        models.Prefetch(
            query=models.SparseVector(
                indices=query_sparse.indices,
                values=query_sparse.values,
            ),
            using="bm25",
            filter=filter_conditions,
            limit=candidates,
        ),
    ]

    if extra_queries:
        for i, eq in enumerate(extra_queries):
            eq_vector = dense_vectors[i + 1]
            eq_sparse = text_to_sparse_vector(eq)
            prefetches.append(models.Prefetch(
                query=eq_vector,
                using="",
                filter=filter_conditions,
                limit=candidates,
            ))
            prefetches.append(models.Prefetch(
                query=models.SparseVector(
                    indices=eq_sparse.indices,
                    values=eq_sparse.values,
                ),
                using="bm25",
                filter=filter_conditions,
                limit=candidates,
            ))

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


def _rerank(query: str, results: list[dict], top_k: int) -> list[dict]:
    reranker = get_ranker()

    # ⚡1: feed the cross-encoder the same signal the dense embedding sees —
    # heading_path + context_text + child_text. Previously the reranker scored
    # bare child_text, blind to the section breadcrumb (heading_path), so it
    # could not use "PostgreSQL 14 Internals > Snapshots"-style context to
    # disambiguate generically-worded chunks.
    documents = []
    for r in results:
        p = r["payload"]
        heading = p.get("heading_path", "")
        ctx = p.get("context_text", "")
        text = p.get("child_text", "")
        documents.append("\n".join(x for x in [heading, ctx, text] if x))

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
