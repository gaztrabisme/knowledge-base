"""Contract tests for the offline Philosophy B candidate builder."""
from __future__ import annotations

import importlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
from qdrant_client import QdrantClient, models


PHASE_A_EXCLUSIONS = {
    "original-library",
    "zhuan-falun",
    "tao-te-ching-jonathan-star",
    "tao-te-ching-stephen-mitchell",
    "tao-te-ching-tse-lao",
}


def _builder():
    # Import inside tests so a missing implementation is reported as a test
    # failure, rather than breaking pytest collection.
    return importlib.import_module("scripts.build_philosophy_candidate")


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    chunks_dir = tmp_path / "chunks"
    chunks_dir.mkdir()
    works: list[dict[str, Any]] = []

    fixture_chunks = [
        {
            "child_id": "fixture-work.en-p0-c0",
            "parent_id": "fixture-work.en-p0",
            "text": "Quartz lanterns drift through the northern archive.",
            "context_text": "",
            "metadata": {
                "work_id": "fixture-work",
                "lang": "en",
                "section_title": "Northern archive",
                "heading_path": "Northern archive",
            },
        },
        {
            "child_id": "fixture-work.en-p1-c0",
            "parent_id": "fixture-work.en-p1",
            "text": "Cobalt bells echo beneath the quiet observatory.",
            "context_text": "",
            "metadata": {
                "work_id": "fixture-work",
                "lang": "en",
                "section_title": "Quiet observatory",
                "heading_path": "Quiet observatory",
            },
        },
    ]

    def write_work(work_id: str, *, status: str = "included", children=None) -> None:
        basename = f"{work_id}.en.json"
        if children is None:
            children = [{
                "child_id": f"{work_id}.en-p0-c0",
                "parent_id": f"{work_id}.en-p0",
                "text": f"Excluded fixture text for {work_id}.",
                "context_text": "",
                "metadata": {"work_id": work_id, "lang": "en"},
            }]
        parents = []
        for child in children:
            parents.append({
                "parent_id": child["parent_id"],
                "text": f"Parent context for {child['child_id']}. " + child["text"],
                "metadata": dict(child.get("metadata", {})),
            })
        chunk_data = {
            "work_id": work_id,
            "work_group": work_id,
            "lang": "en",
            "title": f"Title for {work_id}",
            "edition": "Fixture edition",
            "translator": "",
            "derived": False,
            "children": children,
            "parents": parents,
        }
        (chunks_dir / basename).write_text(json.dumps(chunk_data), encoding="utf-8")
        works.append({
            "work_id": work_id,
            "titles": {"en": f"Title for {work_id}"},
            "languages": {
                "en": {
                    "status": status,
                    "chunks_file": basename,
                }
            },
        })

    write_work("fixture-work", children=fixture_chunks)
    for work_id in sorted(PHASE_A_EXCLUSIONS):
        write_work(work_id)
    write_work("skipped-work", status="skipped")

    works_json = tmp_path / "works.json"
    works_json.write_text(
        json.dumps({"schema_version": 1, "works": works}), encoding="utf-8"
    )
    return works_json, chunks_dir


def _field(record: Any, name: str) -> Any:
    if isinstance(record, Mapping):
        return record[name]
    return getattr(record, name)


def _sparse_parts(vector: Any) -> tuple[list[int], list[float]]:
    if isinstance(vector, Mapping):
        indices, values = vector["indices"], vector["values"]
    elif isinstance(vector, tuple) and len(vector) == 2:
        indices, values = vector
    else:
        indices, values = vector.indices, vector.values
    return [int(index) for index in indices], [float(value) for value in values]


def _assert_sparse_equal(actual: Any, expected: Any) -> None:
    actual_indices, actual_values = _sparse_parts(actual)
    expected_indices, expected_values = _sparse_parts(expected)
    assert actual_indices == expected_indices
    assert actual_values == pytest.approx(expected_values, abs=1e-6)


def _point_as_dict(point: Any) -> dict[str, Any]:
    return {
        "id": point.id,
        "payload": dict(point.payload or {}),
        "vector": point.vector,
    }


def test_sparse_stage_caches_production_vectors_and_resumes(tmp_path: Path) -> None:
    builder = _builder()
    works_json, chunks_dir = _fixture(tmp_path)
    records = list(builder.iter_phase_b_chunks(works_json=works_json, chunks_dir=chunks_dir))

    assert len(records) == 2
    assert { _field(record, "work_id") for record in records } == {"fixture-work"}
    assert { _field(record, "lang") for record in records } == {"en"}
    assert all(_field(record, "parent_text") for record in records)
    assert all(_field(record, "vector_text") for record in records)

    from fastembed import SparseTextEmbedding
    from scripts.remote_index_philosophy import sparse_vector

    bm25_model = SparseTextEmbedding(model_name="Qdrant/bm25")
    expected_bm25 = {
        _field(record, "child")["child_id"]: next(
            bm25_model.embed([_field(record, "vector_text")])
        )
        for record in records
    }
    expected_custom = {
        _field(record, "child")["child_id"]: sparse_vector(_field(record, "vector_text"))
        for record in records
    }

    cache_path = tmp_path / "vectors"
    builder.sparse_stage(records, cache_path, batch_size=2)
    first_cache = builder.VectorCache(cache_path)
    first = { _field(record, "child")["child_id"]: first_cache.get_vectors(record) for record in records }

    for record in records:
        child_id = _field(record, "child")["child_id"]
        vectors = first[child_id]
        assert {"sparse", "bm25"} <= set(vectors)
        _assert_sparse_equal(vectors["sparse"], expected_custom[child_id])
        _assert_sparse_equal(vectors["bm25"], expected_bm25[child_id])

    # Reopening the on-disk cache and rerunning the stage must preserve the
    # already cached vector values for both fixture chunks.
    reopened_before = builder.VectorCache(cache_path)
    before = {
        _field(record, "child")["child_id"]: reopened_before.get_vectors(record)
        for record in records
    }
    builder.sparse_stage(records, cache_path, batch_size=1)
    reopened_after = builder.VectorCache(cache_path)
    after = {
        _field(record, "child")["child_id"]: reopened_after.get_vectors(record)
        for record in records
    }
    for child_id in before:
        _assert_sparse_equal(after[child_id]["sparse"], before[child_id]["sparse"])
        _assert_sparse_equal(after[child_id]["bm25"], before[child_id]["bm25"])


def test_dense_stage_accepts_cuda_and_cli_forwards_cache(tmp_path: Path, monkeypatch) -> None:
    builder = _builder()
    works_json, chunks_dir = _fixture(tmp_path)
    records = list(builder.iter_phase_b_chunks(works_json=works_json, chunks_dir=chunks_dir))

    import knowledge_base.embedder as embedder

    class FakeModel:
        device = None

        def to(self, device: str) -> None:
            self.device = device

    model = FakeModel()
    monkeypatch.setattr(embedder, "load_model", lambda _name: model)
    monkeypatch.setattr(
        embedder,
        "encode_texts",
        lambda *_args, **_kwargs: [[1.0] + [0.0] * 1023 for _ in records],
    )
    cache_path = tmp_path / "cuda-cache.sqlite3"
    builder.dense_stage(records, cache_path, device="cuda", batch_size=2)
    assert model.device == "cuda"
    cache = builder.VectorCache(cache_path)
    assert all("dense" in cache.get_vectors(record) for record in records)

    forwarded: dict[str, Any] = {}
    monkeypatch.setattr(builder, "iter_phase_b_chunks", lambda: iter(()))
    monkeypatch.setattr(
        builder,
        "dense_stage",
        lambda _chunks, path, **kwargs: forwarded.update(path=path, **kwargs),
    )
    monkeypatch.setattr(
        "sys.argv",
        ["build_philosophy_candidate.py", "--stage", "dense", "--device", "cuda", "--cache", str(cache_path)],
    )
    assert builder.main() == 0
    assert forwarded["path"] == cache_path
    assert forwarded["device"] == "cuda"


def _create_phase_a_source(client: QdrantClient) -> dict[str, Any]:
    dense = [1.0] + [0.0] * 1023
    sparse = models.SparseVector(indices=[2, 19], values=[0.5, 1.25])
    bm25 = models.SparseVector(indices=[7, 41], values=[0.75, 1.5])
    payload = {
        "child_id": "phase-a-child",
        "parent_id": "phase-a-parent",
        "child_text": "An unchanged source point.",
        "context_text": "",
        "parent_text": "Phase A source parent text.",
        "book": "phase-a-work",
        "book_title": "Phase A source point",
        "work_id": "phase-a-work",
        "work_group": "phase-a-work",
        "lang": "en",
        "section_key": "phase-a-section",
        "section_title": "Source section",
        "translator": "",
        "edition": "Fixture edition",
        "derived": False,
        "chapter": "",
        "heading_path": "",
        "chunk_type": "prose",
    }
    client.create_collection(
        collection_name="philosophy",
        vectors_config={"": models.VectorParams(size=1024, distance=models.Distance.COSINE)},
        sparse_vectors_config={
            "sparse": models.SparseVectorParams(),
            "bm25": models.SparseVectorParams(),
        },
    )
    client.upsert(
        collection_name="philosophy",
        points=[models.PointStruct(id=17, vector={"": dense, "sparse": sparse, "bm25": bm25}, payload=payload)],
        wait=True,
    )
    return {"id": 17, "vector": {"": dense, "sparse": sparse, "bm25": bm25}, "payload": payload}


def _scroll_all(client: QdrantClient, collection: str) -> list[Any]:
    points, _ = client.scroll(
        collection_name=collection,
        limit=100,
        with_payload=True,
        with_vectors=True,
    )
    return points


def test_load_copies_phase_a_and_upserts_candidate_without_source_mutation(tmp_path: Path) -> None:
    builder = _builder()
    works_json, chunks_dir = _fixture(tmp_path)
    records = list(builder.iter_phase_b_chunks(works_json=works_json, chunks_dir=chunks_dir))
    cache_path = tmp_path / "vectors"
    builder.sparse_stage(records, cache_path, batch_size=2)

    cache = builder.VectorCache(cache_path)
    for index, record in enumerate(records):
        dense = [0.0] * 1024
        dense[index] = 1.0
        cache.store_dense(record, dense)

    source = QdrantClient(":memory:")
    target = QdrantClient(":memory:")
    target_again = QdrantClient(":memory:")
    try:
        original_source_point = _create_phase_a_source(source)
        source_before = _scroll_all(source, "philosophy")
        assert len(source_before) == 1

        source_params = source.get_collection("philosophy").config.params
        target.create_collection(
            collection_name="philosophy_b",
            vectors_config=source_params.vectors,
            sparse_vectors_config=source_params.sparse_vectors,
        )
        target.upsert(
            collection_name="philosophy_b",
            points=[models.PointStruct(
                id=999,
                vector={
                    "": [1.0] + [0.0] * 1023,
                    "sparse": models.SparseVector(indices=[3], values=[1.0]),
                    "bm25": models.SparseVector(indices=[5], values=[1.0]),
                },
                payload={"child_id": "stale-candidate-point"},
            )],
            wait=True,
        )

        builder.load_candidate(records, cache_path, source, target, "philosophy_b")
        target_points = _scroll_all(target, "philosophy_b")
        assert len(target_points) == 3
        assert all(point.id != 999 for point in target_points)

        copied = next(point for point in target_points if point.id == original_source_point["id"])
        assert copied.payload == original_source_point["payload"]
        _assert_sparse_equal(copied.vector["sparse"], original_source_point["vector"]["sparse"])
        _assert_sparse_equal(copied.vector["bm25"], original_source_point["vector"]["bm25"])
        assert copied.vector[""] == original_source_point["vector"][""]

        candidates = [point for point in target_points if point.id != original_source_point["id"]]
        assert len(candidates) == 2
        assert {point.payload["child_id"] for point in candidates} == {
            _field(record, "child")["child_id"] for record in records
        }
        for point in candidates:
            assert set(point.payload) == set(original_source_point["payload"])
        candidate_ids = {point.payload["child_id"]: point.id for point in candidates}

        # A fresh target build gives the same child-to-point IDs, proving the
        # candidate ID assignment is deterministic.
        builder.load_candidate(records, cache_path, source, target_again, "philosophy_b")
        repeated = _scroll_all(target_again, "philosophy_b")
        repeated_ids = {point.payload["child_id"]: point.id for point in repeated if point.id != 17}
        assert repeated_ids == candidate_ids

        source_after = _scroll_all(source, "philosophy")
        assert len(source_after) == len(source_before) == 1
        assert _point_as_dict(source_after[0]) == _point_as_dict(source_before[0])

        refusal_target = QdrantClient(":memory:")
        try:
            with pytest.raises(ValueError, match="philosophy"):
                builder.load_candidate(records, cache_path, source, refusal_target, "philosophy")
            assert not refusal_target.collection_exists("philosophy")
            assert _point_as_dict(_scroll_all(source, "philosophy")[0]) == _point_as_dict(source_before[0])
        finally:
            refusal_target.close()
    finally:
        source.close()
        target.close()
        target_again.close()


def test_load_refuses_missing_cached_vectors_before_creating_target(tmp_path: Path) -> None:
    builder = _builder()
    works_json, chunks_dir = _fixture(tmp_path)
    records = list(builder.iter_phase_b_chunks(works_json=works_json, chunks_dir=chunks_dir))
    source = QdrantClient(":memory:")
    target = QdrantClient(":memory:")
    try:
        with pytest.raises(ValueError, match="Missing cached"):
            builder.load_candidate(records, tmp_path / "empty-cache", source, target, "philosophy_b")
        assert not target.collection_exists("philosophy_b")
    finally:
        source.close()
        target.close()
