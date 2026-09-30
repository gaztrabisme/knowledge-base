#!/usr/bin/env python3
"""Build resumable vector caches and an isolated Phase B philosophy collection."""

from __future__ import annotations

import argparse
import array
import hashlib
import json
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Mapping

from qdrant_client import QdrantClient, models

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
WORKS_JSON = ROOT / "data" / "philosophy" / "works.json"
CHUNKS_DIR = ROOT / "data" / "chunks" / "philosophy"
CACHE_PATH = ROOT / "data" / "philosophy-vectors"
SOURCE_COLLECTION = "philosophy"
MODEL = "jinaai/jina-embeddings-v5-text-small-retrieval"
# Bump this when any dense/sparse encoder implementation or task changes.
CACHE_VECTOR_RECIPE = (
    f"{MODEL}:retrieval.passage|remote_index_philosophy.sparse-v1|Qdrant/bm25"
)
EXCLUDED_WORKS = {
    "original-library", "zhuan-falun", "tao-te-ching-jonathan-star",
    "tao-te-ching-stephen-mitchell", "tao-te-ching-tse-lao",
}


def iter_phase_b_chunks(
    works_json: str | Path = WORKS_JSON,
    chunks_dir: str | Path = CHUNKS_DIR,
) -> Iterable[dict[str, Any]]:
    """Yield included Phase B child records with the exact production input text."""
    registry = json.loads(Path(works_json).read_text(encoding="utf-8"))
    for work in registry.get("works", []):
        work_id = work.get("work_id", "")
        if work_id in EXCLUDED_WORKS:
            continue
        for lang, language in (work.get("languages") or {}).items():
            if language.get("status") != "included":
                continue
            file_name = language.get("chunks_file")
            if not file_name:
                raise ValueError(f"Included language has no chunks_file: {work_id}/{lang}")
            path = Path(chunks_dir) / Path(file_name).name
            if not path.exists():
                path = ROOT / file_name
            data = json.loads(path.read_text(encoding="utf-8"))
            parents = {parent["parent_id"]: parent["text"] for parent in data.get("parents", [])}
            for child in data.get("children", []):
                meta = child.get("metadata", {})
                vector_text = "\n\n".join(
                    part for part in [meta.get("section_title", ""), child["text"]] if part
                )[:8000]
                yield {
                    "work_id": work_id,
                    "lang": lang,
                    "data": data,
                    "child": child,
                    "parent_text": parents.get(child.get("parent_id", ""), ""),
                    "vector_text": vector_text,
                }


def _field(record: Any, name: str) -> Any:
    return record[name] if isinstance(record, Mapping) else getattr(record, name)


def _record_hash(record: Any) -> str:
    material = CACHE_VECTOR_RECIPE + "\0" + _field(record, "vector_text")
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _sparse_parts(vector: Any) -> tuple[list[int], list[float]]:
    if isinstance(vector, Mapping):
        indices, values = vector["indices"], vector["values"]
    else:
        indices, values = vector.indices, vector.values
    if hasattr(indices, "tolist"):
        indices = indices.tolist()
    if hasattr(values, "tolist"):
        values = values.tolist()
    return [int(i) for i in indices], [float(v) for v in values]


class VectorCache:
    """SQLite-backed cache; each row is committed atomically and keyed by child ID."""

    def __init__(self, path: str | Path):
        path = Path(path)
        if path.suffix in {".db", ".sqlite", ".sqlite3"}:
            path.parent.mkdir(parents=True, exist_ok=True)
            db_path = path
        else:
            path.mkdir(parents=True, exist_ok=True)
            db_path = path / "vectors.sqlite3"
        self.connection = sqlite3.connect(db_path)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS vectors ("
            "child_id TEXT PRIMARY KEY, text_hash TEXT NOT NULL, "
            "sparse TEXT, bm25 TEXT, dense BLOB)"
        )
        self.connection.commit()

    @staticmethod
    def _child_id(record: Any) -> str:
        return str(_field(record, "child")["child_id"])

    def get_vectors(self, record: Any) -> dict[str, Any]:
        row = self.connection.execute(
            "SELECT text_hash, sparse, bm25, dense FROM vectors WHERE child_id=?",
            (self._child_id(record),),
        ).fetchone()
        if row is None or row[0] != _record_hash(record):
            return {}
        result: dict[str, Any] = {}
        for name, encoded in (("sparse", row[1]), ("bm25", row[2])):
            if encoded is not None:
                indices, values = json.loads(encoded)
                result[name] = models.SparseVector(indices=indices, values=values)
        if row[3] is not None:
            dense = array.array("f")
            dense.frombytes(row[3])
            result["dense"] = dense.tolist()
        return result

    def _store(self, record: Any, *, sparse: Any = None, bm25: Any = None, dense: Any = None) -> None:
        child_id, fingerprint = self._child_id(record), _record_hash(record)
        old = self.connection.execute(
            "SELECT text_hash, sparse, bm25, dense FROM vectors WHERE child_id=?", (child_id,),
        ).fetchone()
        same_text = old is not None and old[0] == fingerprint
        old_sparse, old_bm25, old_dense = old[1:] if same_text else (None, None, None)
        sparse_json = json.dumps(_sparse_parts(sparse), separators=(",", ":")) if sparse is not None else old_sparse
        bm25_json = json.dumps(_sparse_parts(bm25), separators=(",", ":")) if bm25 is not None else old_bm25
        dense_blob = array.array("f", dense).tobytes() if dense is not None else old_dense
        self.connection.execute(
            "INSERT OR REPLACE INTO vectors(child_id,text_hash,sparse,bm25,dense) VALUES(?,?,?,?,?)",
            (child_id, fingerprint, sparse_json, bm25_json, dense_blob),
        )
        self.connection.commit()

    def store_sparse_pair(self, record: Any, sparse: Any, bm25: Any) -> None:
        self._store(record, sparse=sparse, bm25=bm25)

    def store_dense(self, record: Any, vector: list[float]) -> None:
        self._store(record, dense=vector)

    def counts(self, records: Iterable[Any]) -> dict[str, dict[str, int]]:
        counts: dict[str, dict[str, int]] = {}
        for record in records:
            lang = str(_field(record, "lang"))
            row = counts.setdefault(lang, {"total": 0, "sparse": 0, "bm25": 0, "dense": 0})
            row["total"] += 1
            for name in ("sparse", "bm25", "dense"):
                row[name] += name in self.get_vectors(record)
        return counts


def sparse_stage(chunks: Iterable[Any], cache_path: str | Path, batch_size: int = 32) -> None:
    """Cache custom sparse and Qdrant/bm25 vectors for all supplied chunks."""
    from fastembed import SparseTextEmbedding
    from scripts.remote_index_philosophy import sparse_vector

    records = list(chunks)
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    cache = VectorCache(cache_path)
    pending = [r for r in records if not {"sparse", "bm25"} <= cache.get_vectors(r).keys()]
    if not pending:
        print(f"Sparse/BM25 cache complete: {len(records)} chunks already cached")
        return
    bm25 = SparseTextEmbedding("Qdrant/bm25")
    started = time.monotonic()
    for start in range(0, len(pending), batch_size):
        batch = pending[start:start + batch_size]
        texts = [_field(record, "vector_text") for record in batch]
        bm25_vectors = list(bm25.embed(texts))
        for record, text, bm25_item in zip(batch, texts, bm25_vectors):
            bm25_vector = models.SparseVector(
                indices=bm25_item.indices.tolist(), values=bm25_item.values.tolist(),
            )
            cache.store_sparse_pair(record, sparse_vector(text), bm25_vector)
        elapsed = max(time.monotonic() - started, 1e-9)
        done = min(start + len(batch), len(pending))
        print(f"Sparse/BM25 {done}/{len(pending)} chunks ({done / elapsed:.2f} chunks/s)")


def dense_stage(
    chunks: Iterable[Any], cache_path: str | Path, device: str = "mps",
    limit: int | None = None, batch_size: int = 32,
) -> None:
    """Embed uncached passage texts with the shared Jina v5 encoder and persist batches."""
    if device not in {"mps", "cpu", "cuda"}:
        raise ValueError("device must be mps, cpu, or cuda")
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    records = list(chunks)
    if limit is not None:
        records = records[:limit]
    cache = VectorCache(cache_path)
    pending = [record for record in records if "dense" not in cache.get_vectors(record)]
    if not pending:
        print(f"Dense cache complete: {len(records)} selected chunks already cached")
        return
    from knowledge_base.embedder import encode_texts, load_model

    model = load_model(MODEL)
    model.to(device)
    completed = 0
    for start in range(0, len(pending), batch_size):
        batch = pending[start:start + batch_size]
        started = time.monotonic()
        vectors = encode_texts(
            model, MODEL, [_field(record, "vector_text") for record in batch],
            is_query=False, batch_size=batch_size,
        )
        for record, vector in zip(batch, vectors):
            cache.store_dense(record, vector)
        completed += len(batch)
        elapsed = max(time.monotonic() - started, 1e-9)
        print(
            f"Dense {completed}/{len(pending)} chunks ({len(batch) / elapsed:.2f} chunks/s; "
            f"batch {elapsed:.2f}s; device={device})",
            flush=True,
        )


def _point_id(child_id: str) -> int:
    return int.from_bytes(hashlib.sha256(child_id.encode()).digest()[:8], "big") >> 1


def _candidate_point(record: Any, vectors: Mapping[str, Any]) -> models.PointStruct:
    child, data = _field(record, "child"), _field(record, "data")
    meta = child.get("metadata", {})
    child_id = child["child_id"]
    return models.PointStruct(
        id=_point_id(child_id),
        vector={"": vectors["dense"], "sparse": vectors["sparse"], "bm25": vectors["bm25"]},
        payload={
            "child_id": child_id,
            "parent_id": child["parent_id"],
            "child_text": child["text"],
            "context_text": child.get("context_text", ""),
            "parent_text": _field(record, "parent_text"),
            "book": _field(record, "work_id"),
            "book_title": data.get("title", _field(record, "work_id")),
            "work_id": _field(record, "work_id"),
            "work_group": meta.get("work_group", data.get("work_group", _field(record, "work_id"))),
            "lang": meta.get("lang", data.get("lang", "")),
            "section_key": meta.get("section_key", ""),
            "section_title": meta.get("section_title", ""),
            "translator": meta.get("translator", data.get("translator", "")),
            "edition": meta.get("edition", data.get("edition", "")),
            "derived": bool(meta.get("derived", data.get("derived", False))),
            "chapter": meta.get("chapter", ""),
            "heading_path": meta.get("heading_path", ""),
            "chunk_type": meta.get("chunk_type", "prose"),
        },
    )


def _all_points(client: QdrantClient, collection: str) -> Iterable[list[Any]]:
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=collection, limit=256, offset=offset,
            with_payload=True, with_vectors=True,
        )
        if points:
            yield points
        if offset is None:
            break


def load_candidate(
    chunks: Iterable[Any], cache_path: str | Path, source_client: QdrantClient,
    target_client: QdrantClient, collection_name: str,
) -> None:
    """Clone Phase A into a candidate collection and upsert all Phase B points."""
    aliases = {alias.alias_name for alias in source_client.get_aliases().aliases}
    protected = {SOURCE_COLLECTION, "developer_knowledge", "developer_knowledge_v9"} | aliases
    if collection_name in protected:
        raise ValueError(f"Refusing to write to protected collection or alias {collection_name!r}")
    records = list(chunks)
    cache = VectorCache(cache_path)
    missing = [
        _field(record, "child")["child_id"] for record in records
        if not {"dense", "sparse", "bm25"} <= cache.get_vectors(record).keys()
    ]
    if missing:
        raise ValueError(f"Missing cached dense/sparse/BM25 vectors for {len(missing)} chunks: {missing[:5]}")
    if not source_client.collection_exists(SOURCE_COLLECTION):
        raise ValueError(f"Source collection {SOURCE_COLLECTION!r} does not exist")
    source_info = source_client.get_collection(SOURCE_COLLECTION)
    source_params = source_info.config.params
    source_vectors = source_params.vectors
    source_sparse = source_params.sparse_vectors

    candidate_ids = {_point_id(_field(record, "child")["child_id"]) for record in records}
    source_ids = {
        point.id for batch in _all_points(source_client, SOURCE_COLLECTION)
        for point in batch
    }
    collisions = candidate_ids & source_ids
    if collisions:
        raise ValueError(f"Candidate point IDs collide with Phase A IDs: {sorted(collisions)[:5]}")

    if not target_client.collection_exists(collection_name):
        target_client.create_collection(
            collection_name=collection_name,
            vectors_config=source_vectors,
            sparse_vectors_config=source_sparse,
        )
    else:
        target_params = target_client.get_collection(collection_name).config.params
        if target_params.vectors != source_vectors or target_params.sparse_vectors != source_sparse:
            raise ValueError(f"Existing target {collection_name!r} has incompatible vector configuration")

    for batch in _all_points(source_client, SOURCE_COLLECTION):
        target_client.upsert(
            collection_name=collection_name,
            points=[models.PointStruct(id=p.id, vector=p.vector, payload=p.payload) for p in batch],
            wait=True,
        )
    batch_size = 128
    for start in range(0, len(records), batch_size):
        batch = records[start:start + batch_size]
        target_client.upsert(
            collection_name=collection_name,
            points=[_candidate_point(r, cache.get_vectors(r)) for r in batch],
            wait=True,
        )
    expected_ids = source_ids | candidate_ids
    stale_ids = [
        point.id for batch in _all_points(target_client, collection_name)
        for point in batch if point.id not in expected_ids
    ]
    for start in range(0, len(stale_ids), batch_size):
        target_client.delete(
            collection_name=collection_name,
            points_selector=models.PointIdsList(points=stale_ids[start:start + batch_size]),
            wait=True,
        )
    print(f"Loaded {len(records)} Phase B points into {collection_name}; copied Phase A unchanged")


def _client() -> QdrantClient:
    return QdrantClient(url=os.environ.get("KB_QDRANT_URL", "http://127.0.0.1:6333"), timeout=60)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("sparse", "dense", "load"))
    parser.add_argument("--device", choices=("mps", "cpu", "cuda"), default="mps")
    parser.add_argument(
        "--cache", type=Path, default=CACHE_PATH,
        help="vector cache directory or SQLite file",
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument("--collection", default="philosophy_b")
    parser.add_argument("--check", action="store_true", help="print cached vector counts by language")
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()
    if args.check and args.stage is None:
        cache = VectorCache(args.cache)
        counts = cache.counts(iter_phase_b_chunks())
        for lang, values in sorted(counts.items()):
            print(
                f"{lang}: total={values['total']} sparse={values['sparse']} "
                f"bm25={values['bm25']} dense={values['dense']}"
            )
        return 0
    if args.stage is None:
        parser.error("choose --stage or use --check")
    chunks = list(iter_phase_b_chunks())
    if args.stage == "sparse":
        sparse_stage(chunks, args.cache, batch_size=args.batch_size)
    elif args.stage == "dense":
        dense_stage(chunks, args.cache, device=args.device, limit=args.limit, batch_size=args.batch_size)
    else:
        client = _client()
        try:
            load_candidate(chunks, args.cache, client, client, args.collection)
        finally:
            client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
