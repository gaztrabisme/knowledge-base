"""Hybrid retrieval for the isolated, multilingual philosophy collection."""

from __future__ import annotations

import json
import os
from pathlib import Path

from qdrant_client import QdrantClient, models
from sentence_transformers import CrossEncoder

from ..config import ROOT
from ..index import text_to_sparse_vector as bm25_text_to_sparse_vector
from .sparse import text_to_sparse_vector

COLLECTION = os.environ.get("KB_PHILOSOPHY_COLLECTION", "philosophy")
EMBEDDING_MODEL = "jinaai/jina-embeddings-v5-text-small-retrieval"
RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"
_ranker = None
_client: QdrantClient | None = None


_model = None


def embed_texts(texts: list[str], task: str = "retrieval.query") -> list[list[float]]:
    """Encode with Jina v5, which built the philosophy collection.

    The technical index may use a different model, so this loads its own copy
    instead of sharing index.get_model().
    """
    global _model
    from ..embedder import encode_texts, load_model
    if _model is None:
        _model = load_model(EMBEDDING_MODEL)
    return encode_texts(_model, EMBEDDING_MODEL, [text[:8000] for text in texts],
                        is_query=task.startswith("retrieval.query"))


def get_ranker() -> CrossEncoder:
    global _ranker
    if _ranker is None:
        _ranker = CrossEncoder(RERANKER_MODEL, trust_remote_code=True, max_length=512)
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


def _translation_pairs(
    client: QdrantClient, work_group: str, section_key: str,
) -> list[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    offset = None
    parallel_filter = models.Filter(must=[
        models.FieldCondition(key="work_group", match=models.MatchValue(value=work_group)),
        models.FieldCondition(key="section_key", match=models.MatchValue(value=section_key)),
    ])
    while True:
        points, offset = client.scroll(
            collection_name=COLLECTION,
            scroll_filter=parallel_filter,
            limit=1000,
            offset=offset,
            with_payload=["work_id", "lang"],
            with_vectors=False,
        )
        for point in points:
            payload = point.payload or {}
            work_id, language = payload.get("work_id"), payload.get("lang")
            if work_id and language:
                pairs.add((work_id, language))
        if offset is None:
            break
    return sorted(pairs)


def _attach_parallels(
    client: QdrantClient,
    hit: dict,
    dense_vector: list[float] | dict[str, list[float]] | None = None,
    pair_cache: dict[tuple[str, str], list[tuple[str, str]]] | None = None,
) -> dict:
    payload = hit.get("payload", hit)
    work_id, language = payload.get("work_id"), payload.get("lang")
    work_group, section_key = payload.get("work_group"), payload.get("section_key")
    if (not work_group or not work_id or not language or not section_key
            or section_key == "ttc-notes" or dense_vector is None):
        hit["parallels"] = []
        return hit
    if isinstance(dense_vector, dict):
        dense_vector = dense_vector.get("") or next(
            (vector for vector in dense_vector.values() if isinstance(vector, list)), None,
        )
    if dense_vector is None:
        hit["parallels"] = []
        return hit

    pair_key = (work_group, section_key)
    if pair_cache is not None and pair_key in pair_cache:
        pairs = pair_cache[pair_key]
    else:
        pairs = _translation_pairs(client, work_group, section_key)
        if pair_cache is not None:
            pair_cache[pair_key] = pairs

    groups = []
    for other_work_id, other_language in pairs:
        if (other_work_id, other_language) == (work_id, language):
            continue
        points = client.query_points(
            collection_name=COLLECTION,
            query=dense_vector,
            query_filter=models.Filter(must=[
                models.FieldCondition(
                    key="work_id", match=models.MatchValue(value=other_work_id),
                ),
                models.FieldCondition(
                    key="lang", match=models.MatchValue(value=other_language),
                ),
                models.FieldCondition(
                    key="section_key", match=models.MatchValue(value=section_key),
                ),
            ]),
            limit=2,
            with_payload=True,
            with_vectors=False,
        ).points
        chunks = []
        for point in points:
            other = point.payload or {}
            text = str(other.get("child_text", ""))
            chunks.append({
                "chunk_id": other.get("child_id") or str(point.id),
                "work_id": other.get("work_id", other_work_id),
                "lang": other.get("lang", other_language),
                "section_key": other.get("section_key", section_key),
                "section_title": other.get("section_title", ""),
                "derived": bool(other.get("derived", False)),
                "excerpt": text[:600].strip(),
            })
        if chunks:
            groups.append({
                "work_id": other_work_id,
                "lang": other_language,
                "chunks": chunks,
            })
    hit["parallels"] = groups
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
    candidates = min(max(top_k * 8, 30), 40)
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
        with_vectors=parallel,
    ).points
    hits = []
    for point in points:
        payload = point.payload or {}
        hit = {"chunk_id": payload.get("child_id", str(point.id)),
               "score": float(point.score), **payload}
        hit["derived"] = bool(payload.get("derived", False))
        if parallel:
            hit["_dense_vector"] = point.vector
        hits.append(hit)
    if rerank:
        hits = _rank(query, hits, top_k)
    else:
        hits = hits[:top_k]
    if parallel:
        pair_cache: dict[tuple[str, str], list[tuple[str, str]]] = {}
        for hit in hits:
            dense_vector = hit.pop("_dense_vector", None)
            _attach_parallels(client, hit, dense_vector, pair_cache)
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
    if not work:
        return {"works": [{"work_id": item["work_id"], "titles": item.get("titles", {}),
                           "languages": sorted(item.get("languages", {}))}
                          for item in selected]}

    detailed = []
    for item in selected:
        languages = {}
        for lang, record in item.get("languages", {}).items():
            if record.get("status") != "included":
                languages[lang] = {"status": record.get("status"), "section_count": 0, "sections": []}
                continue
            chunk_path = Path(record.get("chunks_file") or "")
            if not chunk_path.is_absolute():
                chunk_path = ROOT / chunk_path if str(chunk_path) else ROOT / "data/chunks/philosophy" / f"{item['work_id']}.{lang}.json"
            chunks = json.loads(chunk_path.read_text(encoding="utf-8"))
            sections = {}
            for child in chunks.get("children", []):
                meta = {**child.get("metadata", {}), **child}
                sections.setdefault(meta.get("section_key"), meta.get("section_title", ""))
            languages[lang] = {"status": "included", "section_count": len(sections),
                               "sections": [{"section_key": key, "section_title": title}
                                            for key, title in sections.items()]}
        detailed.append({"work_id": item["work_id"], "titles": item.get("titles", {}),
                         "languages": languages})
    if len(detailed) == 1:
        return detailed[0]
    return {"works": detailed}
