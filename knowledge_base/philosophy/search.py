"""Hybrid retrieval for the isolated, multilingual philosophy collection."""

from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path

from qdrant_client import QdrantClient, models
from sentence_transformers import CrossEncoder

from ..config import ROOT
from ..index import text_to_sparse_vector as bm25_text_to_sparse_vector
from .sparse import text_to_sparse_vector

COLLECTION = "philosophy"
EMBEDDING_MODEL = "jinaai/jina-embeddings-v5-text-small-retrieval"
RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"
_ranker = None
_client: QdrantClient | None = None


def embed_texts(texts: list[str], task: str = "retrieval.query") -> list[list[float]]:
    """Encode with the technical index's Jina v5 model, so the server loads it once."""
    from ..index import embed_texts as shared_embed_texts
    return shared_embed_texts([text[:8000] for text in texts], task=task)


def get_ranker() -> CrossEncoder:
    global _ranker
    if _ranker is None:
        _ranker = CrossEncoder(RERANKER_MODEL, device="cpu", trust_remote_code=True)
    return _ranker


def get_client() -> QdrantClient:
    global _client
    url = os.environ.get("KB_QDRANT_URL", "http://127.0.0.1:6333")
    if _client is None:
        _client = QdrantClient(url=url, timeout=30)
    return _client


def _work_condition(work: str) -> models.Filter:
    matches = [models.FieldCondition(key="work_id", match=models.MatchValue(value=work)),
               models.FieldCondition(key="work_group", match=models.MatchValue(value=work))]
    if work == "tao-te-ching":
        return models.Filter(should=matches)
    # Accept a displayed title as a convenience, but resolve to the registered id.
    registry = ROOT / "data" / "philosophy" / "works.json"
    if registry.exists():
        try:
            data = json.loads(registry.read_text(encoding="utf-8"))
            for item in data.get("works", []):
                titles = item.get("titles", {})
                if work.casefold() in {str(v).casefold() for v in titles.values()}:
                    matches.append(models.FieldCondition(
                        key="work_id", match=models.MatchValue(value=item["work_id"]),
                    ))
        except (OSError, ValueError, KeyError, TypeError):
            pass
    return models.Filter(should=matches)


def _is_english(text: str) -> bool:
    """Plain-ASCII queries (no CJK, no Vietnamese diacritics) are treated as English."""
    return all(ord(ch) < 128 for ch in text)


def _ranker_for(query: str) -> CrossEncoder:
    """Ettin for English queries, BGE-v2-m3 otherwise.

    Ettin is English-only but the stronger English reranker; BGE reads Vietnamese and
    Chinese. Routing by query language is the only configuration that met every
    recall threshold in data/philosophy/ablation.json.
    """
    if _is_english(query):
        from ..search import get_ranker as technical_ranker
        return technical_ranker()
    return get_ranker()


def _rank(query: str, results: list[dict], top_k: int) -> list[dict]:
    if not results:
        return []
    documents = [
        "\n".join(filter(None, [item.get("section_title", ""), item.get("child_text", "")]))
        for item in results
    ]
    ranker = _ranker_for(query)
    if hasattr(ranker, "rank"):
        ranked = ranker.rank(query, documents)
        ordered = []
        for item in ranked:
            result = results[int(item["corpus_id"])]
            result["score"] = float(item["score"])
            ordered.append(result)
        return ordered[:top_k]
    pairs = [(query, document) for document in documents]
    scores = ranker.predict(pairs, show_progress_bar=False)
    return sorted(
        (dict(item, score=float(score)) for item, score in zip(results, scores)),
        key=lambda item: item["score"], reverse=True,
    )[:top_k]


def _attach_parallels(client: QdrantClient, hit: dict) -> dict:
    payload = hit.get("payload", hit)
    work_id, section_key = payload.get("work_id"), payload.get("section_key")
    if not work_id or not section_key:
        hit["parallels"] = []
        return hit
    points, _ = client.scroll(
        collection_name=COLLECTION,
        scroll_filter=models.Filter(must=[
            models.FieldCondition(key="work_id", match=models.MatchValue(value=work_id)),
            models.FieldCondition(key="section_key", match=models.MatchValue(value=section_key)),
        ]),
        limit=1000,
        with_payload=True,
        with_vectors=False,
    )
    grouped: dict[str, list[dict]] = defaultdict(list)
    for point in points:
        other = point.payload or {}
        language = other.get("lang", "")
        if not language or language == payload.get("lang"):
            continue
        chunk_id = other.get("child_id") or str(point.id)
        text = other.get("child_text", "")
        grouped[language].append({
            "chunk_id": chunk_id,
            "excerpt": text[:360].strip(),
            "lang": language,
            "section_title": other.get("section_title", ""),
        })
    hit["parallels"] = [
        {"lang": language, "chunks": chunks}
        for language, chunks in sorted(grouped.items())
    ]
    return hit


def hybrid_search(
    query: str,
    client: QdrantClient | None = None,
    top_k: int = 5,
    language: str | None = None,
    work: str | None = None,
    parallel: bool = True,
    rerank: bool = True,
) -> list[dict]:
    """Search philosophy passages with dense+sparse DBSF and optional parallels."""
    client = client or get_client()
    must = []
    if language:
        if language == "zh":
            must.append(models.FieldCondition(key="lang", match=models.MatchAny(any=["zh-Hans", "zh-Hant"])))
        else:
            must.append(models.FieldCondition(key="lang", match=models.MatchValue(value=language)))
    if work:
        work_filter = _work_condition(work)
        must.append(work_filter)
    search_filter = models.Filter(must=must) if must else None
    query_dense = embed_texts([query], task="retrieval.query")[0]
    query_sparse = text_to_sparse_vector(query)
    candidates = max(top_k * 8, 30)
    points = client.query_points(
        collection_name=COLLECTION,
        prefetch=[
            models.Prefetch(query=query_dense, using="", filter=search_filter, limit=candidates),
            models.Prefetch(
                query=query_sparse, using="sparse", filter=search_filter, limit=candidates,
            ),
            models.Prefetch(
                query=bm25_text_to_sparse_vector(query), using="bm25",
                filter=search_filter, limit=candidates,
            ),
        ],
        query=models.FusionQuery(fusion=models.Fusion.DBSF),
        limit=candidates if rerank else top_k,
        with_payload=True,
    ).points
    hits = []
    for point in points:
        payload = point.payload or {}
        hit = {"chunk_id": payload.get("child_id", str(point.id)),
               "score": float(point.score), **payload}
        hit["derived"] = bool(payload.get("derived", False))
        hits.append(hit)
    if rerank:
        hits = _rank(query, hits, top_k)
    else:
        hits = hits[:top_k]
    if parallel:
        hits = [_attach_parallels(client, hit) for hit in hits]
    else:
        for hit in hits:
            hit["parallels"] = []
    return hits


def list_philosophy(work: str | None = None) -> dict:
    """List registered philosophy works and languages, optionally aligned units."""
    path = ROOT / "data" / "philosophy" / "works.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    selected = []
    for item in data.get("works", []):
        if work and work not in {item.get("work_id"), item.get("work_group")}:
            titles = item.get("titles", {})
            if work.casefold() not in {str(title).casefold() for title in titles.values()}:
                continue
        selected.append(item)
    if work and len(selected) == 1:
        item = selected[0]
        aligned = {}
        for lang, record in item.get("languages", {}).items():
            if record.get("status") != "included":
                aligned[lang] = {"status": record.get("status"), "section_count": 0, "sections": []}
                continue
            chunk_path = Path(record.get("chunks_file") or "")
            if not chunk_path.is_absolute():
                chunk_path = ROOT / chunk_path if str(chunk_path) else ROOT / "data/chunks/philosophy" / f"{item['work_id']}.{lang}.json"
            chunks = json.loads(chunk_path.read_text(encoding="utf-8"))
            sections = {}
            for child in chunks.get("children", []):
                meta = {**child.get("metadata", {}), **child}
                sections.setdefault(meta.get("section_key"), meta.get("section_title", ""))
            aligned[lang] = {"status": "included", "section_count": len(sections),
                             "sections": [{"section_key": k, "section_title": v} for k, v in sections.items()]}
        return {"work_id": item["work_id"], "titles": item.get("titles", {}), "languages": aligned}
    return {"works": [{"work_id": item["work_id"], "work_group": item.get("work_group"),
                       "titles": item.get("titles", {}),
                       "languages": {lang: {"status": rec.get("status"),
                                            "section_count": rec.get("section_count", 0)}
                                     for lang, rec in item.get("languages", {}).items()}}
                      for item in selected]}
