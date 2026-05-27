"""Hybrid search (dense + BM25) with FlashRank reranking."""

from dataclasses import dataclass

from flashrank import Ranker, RerankRequest
from qdrant_client import QdrantClient, models

from .config import COLLECTION_NAME, QDRANT_DIR, RERANKER_MODEL
from .index import embed_texts, text_to_sparse_vector

_ranker: Ranker | None = None


def get_ranker() -> Ranker:
    global _ranker
    if _ranker is None:
        _ranker = Ranker(model_name=RERANKER_MODEL)
    return _ranker


def get_client() -> QdrantClient:
    return QdrantClient(path=str(QDRANT_DIR))


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
) -> list[SearchResult]:
    query_vector = embed_texts([query], task="retrieval.query")[0]
    query_sparse = text_to_sparse_vector(query)

    filter_conditions = None
    if book_filter:
        filter_conditions = models.Filter(
            must=[models.FieldCondition(
                key="book",
                match=models.MatchValue(value=book_filter),
            )]
        )

    fused = client.query_points(
        collection_name=COLLECTION_NAME,
        prefetch=[
            models.Prefetch(
                query=query_vector,
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
        ],
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
    ranker = get_ranker()

    passages = []
    for r in results:
        p = r["payload"]
        text = p.get("child_text", "")
        ctx = p.get("context_text", "")
        passages.append({"id": r["id"], "text": f"{ctx}\n{text}" if ctx else text})

    request = RerankRequest(query=query, passages=passages)
    ranked = ranker.rerank(request)

    id_to_result = {r["id"]: r for r in results}
    reranked = []
    for item in ranked[:top_k]:
        result = id_to_result[item["id"]]
        result["score"] = float(item["score"])
        reranked.append(result)

    return reranked


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
        ))

    return deduped
