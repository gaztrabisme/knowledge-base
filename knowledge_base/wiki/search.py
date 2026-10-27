"""Wiki-only dense + BM25 DBSF retrieval and root-confined page reads."""

from __future__ import annotations

import os
from pathlib import Path

from qdrant_client import QdrantClient, models

from . import index
from .chunk import headings
from .roots import configured_roots

COLLECTION = index.COLLECTION
_client: QdrantClient | None = None


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = index.get_client()
    return _client


def embed_texts(texts: list[str], task: str = "retrieval.query") -> list[list[float]]:
    return index.embed_texts(texts, task=task)


def get_ranker():
    from ..search import get_ranker as ettin_ranker
    return ettin_ranker()


def wiki_search(query: str, project: str | None = None, limit: int = 8) -> list[dict]:
    """Search project wikis. KB_WIKI_RERANK=0/false/no/off disables Ettin reranking."""
    if limit < 1 or not query.strip():
        return []
    client = get_client()
    search_filter = models.Filter(must=[
        models.FieldCondition(key="project", match=models.MatchValue(value=project)),
    ]) if project is not None else None
    rerank = os.environ.get("KB_WIKI_RERANK", "1").lower() not in {"0", "false", "no", "off"}
    candidates = max(limit, 50) if rerank else limit
    points = client.query_points(
        collection_name=COLLECTION,
        prefetch=[
            models.Prefetch(query=embed_texts([query])[0], using="", filter=search_filter, limit=candidates),
            models.Prefetch(query=index.text_to_sparse_vector(query), using="bm25", filter=search_filter, limit=candidates),
        ],
        query=models.FusionQuery(fusion=models.Fusion.DBSF),
        limit=candidates, with_payload=True,
    ).points
    hits = [{**(point.payload or {}), "score": float(point.score)} for point in points]
    if rerank and hits:
        documents = ["\n\n".join(filter(None, [item.get("heading"), item.get("text")])) for item in hits]
        ranker = get_ranker()
        if hasattr(ranker, "rank"):
            hits = [dict(hits[int(item["corpus_id"])], score=float(item["score"]))
                    for item in ranker.rank(query, documents)]
        else:
            scores = ranker.predict([(query, doc) for doc in documents], show_progress_bar=False)
            hits = sorted((dict(hit, score=float(score)) for hit, score in zip(hits, scores)),
                          key=lambda hit: hit["score"], reverse=True)
    return [{
        "project": hit["project"], "path": hit["path"], "rel_path": hit["rel_path"],
        "heading": hit["heading"], "date": hit.get("date"),
        "snippet": hit["text"][:1200], "score": hit["score"],
    } for hit in hits[:limit]]


def wiki_read(path: str, heading: str | None = None) -> str:
    """Read a configured wiki page, optionally one heading and its subsections.

    Accept the absolute path from wiki_search. Heading can be a full heading path
    ("Page > Section") or the exact heading title; the first matching section wins.
    """
    page = Path(path).expanduser().resolve()
    if not any(page.is_relative_to(root) for root in configured_roots()):
        raise ValueError(f"Path is outside every configured wiki root: {path}")
    if page.suffix.lower() != ".md":
        raise ValueError("wiki_read requires a markdown (.md) page")
    text = page.read_text(encoding="utf-8")
    if heading is None:
        return text
    sections = headings(text)
    for i, section in enumerate(sections):
        if heading in {section.path, section.title}:
            end = next((other.start for other in sections[i + 1:]
                        if other.level <= section.level), len(text))
            return text[section.start:end]
    raise ValueError(f"No heading {heading!r} in wiki page {page}")
