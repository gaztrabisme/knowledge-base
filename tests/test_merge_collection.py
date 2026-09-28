import hashlib
import json
import math
import os
import random
import subprocess
import uuid
from pathlib import Path

import pytest

os.environ["ORT_DISABLE_TELEMETRY"] = "1"

from qdrant_client import QdrantClient, models

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / "bin" / "python"
SCRIPT = ROOT / "scripts" / "merge_collection.py"
URL = os.environ.get("KB_QDRANT_URL", "http://127.0.0.1:6333")


def run_cli(*args: str, success: bool = True) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["KB_QDRANT_URL"] = URL
    result = subprocess.run(
        [str(PYTHON), str(SCRIPT), *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if success:
        assert result.returncode == 0, result.stdout + result.stderr
    else:
        assert result.returncode != 0, result.stdout + result.stderr
    return result


def make_point(child_id: str, rng: random.Random, marker: str) -> models.PointStruct:
    point_id = int.from_bytes(hashlib.sha256(child_id.encode()).digest()[:8], "big") >> 1
    dense = [rng.random() for _ in range(1024)]
    norm = math.sqrt(sum(value * value for value in dense))
    dense = [value / norm for value in dense]
    return models.PointStruct(
        id=point_id,
        vector={
            "": dense,
            "bm25": models.SparseVector(indices=[3, 17, 99], values=[0.25, 1.5, 0.75]),
        },
        payload={"child_id": child_id, "fake_payload": marker},
    )


def as_diff(value, model_type):
    return model_type(**value.model_dump(exclude_none=True)) if value is not None else None


def test_build_verify_promote_and_cleanup_scratch(tmp_path: Path) -> None:
    server = QdrantClient(url=URL, timeout=10)
    try:
        server.get_collections()
    except Exception as error:
        server.close()
        pytest.skip(f"Qdrant server unavailable at {URL}: {error}")

    created_collections: list[str] = []
    alias_name = f"c3_scratch_alias_{uuid.uuid4().hex[:8]}"
    local: QdrantClient | None = None
    try:
        names = {item.name for item in server.get_collections().collections}
        assert names == {"developer_knowledge"}
        baseline_count = server.count("developer_knowledge", exact=True).count
        assert baseline_count == 132_623

        suffix = uuid.uuid4().hex[:8]
        scratch_src = f"c3_scratch_src_{suffix}"
        scratch_dst = f"c3_scratch_dst_{suffix}"
        scratch_collision = f"c3_scratch_collision_{suffix}"
        created_collections.extend([scratch_src, scratch_dst, scratch_collision])

        live_info = server.get_collection("developer_knowledge")
        source_points, _ = server.scroll(
            "developer_knowledge", limit=50, with_payload=True, with_vectors=True
        )
        assert len(source_points) == 50
        params = live_info.config.params
        server.create_collection(
            collection_name=scratch_src,
            vectors_config=params.vectors,
            sparse_vectors_config=params.sparse_vectors,
            shard_number=params.shard_number,
            sharding_method=params.sharding_method,
            replication_factor=params.replication_factor,
            write_consistency_factor=params.write_consistency_factor,
            on_disk_payload=params.on_disk_payload,
            payload=params.payload,
            hnsw_config=as_diff(live_info.config.hnsw_config, models.HnswConfigDiff),
            optimizers_config=as_diff(
                live_info.config.optimizer_config, models.OptimizersConfigDiff
            ),
            wal_config=as_diff(live_info.config.wal_config, models.WalConfigDiff),
            quantization_config=live_info.config.quantization_config,
            strict_mode_config=live_info.config.strict_mode_config,
            metadata=live_info.config.metadata,
        )
        for field_name, schema in live_info.payload_schema.items():
            server.create_payload_index(
                scratch_src,
                field_name=field_name,
                field_schema=schema.params or schema.data_type,
                wait=True,
            )
        server.upsert(
            scratch_src,
            points=[models.PointStruct(id=p.id, vector=p.vector, payload=p.payload) for p in source_points],
            wait=True,
        )

        embedded_path = tmp_path / "embedded"
        local = QdrantClient(path=str(embedded_path))
        local.create_collection(
            collection_name="developer_knowledge",
            vectors_config=params.vectors,
            sparse_vectors_config=params.sparse_vectors,
        )
        rng = random.Random(3817)
        synthetic = [make_point(f"c3-synthetic-{i}-{suffix}", rng, f"point-{i}") for i in range(20)]
        source_ids = {point.id for point in source_points}
        assert source_ids.isdisjoint(point.id for point in synthetic)
        local.upsert("developer_knowledge", points=synthetic, wait=True)

        # A one-point collision store proves preflight refusal and declared overwrite behavior.
        local.create_collection(
            collection_name="collision_add",
            vectors_config=params.vectors,
            sparse_vectors_config=params.sparse_vectors,
        )
        original = source_points[0]
        collision = models.PointStruct(
            id=original.id,
            vector=make_point(original.payload["child_id"], rng, "replacement").vector,
            payload={"child_id": original.payload["child_id"], "fake_payload": "replacement"},
        )
        local.upsert("collision_add", points=[collision], wait=True)
        local.close()
        local = None

        build = run_cli(
            "build", "--src", scratch_src, "--dst", scratch_dst,
            "--add", str(embedded_path),
        )
        build_summary = json.loads(build.stdout)
        assert build_summary["src_count"] == 50
        assert build_summary["add_count"] == 20
        assert build_summary["dst_count"] == 70
        assert build_summary["overwrites"] == 0

        refused = run_cli(
            "build", "--src", scratch_src, "--dst", scratch_dst,
            "--add", str(embedded_path), success=False,
        )
        assert "non-empty" in refused.stderr
        corrupt_ids = [source_points[1].id, synthetic[0].id]
        for point in server.retrieve(
            scratch_dst, ids=corrupt_ids, with_payload=True, with_vectors=True
        ):
            payload = dict(point.payload or {})
            payload["corrupt_for_resume_test"] = True
            server.upsert(
                scratch_dst,
                points=[models.PointStruct(id=point.id, vector=point.vector, payload=payload)],
                wait=True,
            )
        resumed = run_cli(
            "build", "--src", scratch_src, "--dst", scratch_dst,
            "--add", str(embedded_path), "--resume",
        )
        resumed_summary = json.loads(resumed.stdout)
        assert resumed_summary["skipped_src_existing"] == 49
        assert resumed_summary["skipped_add_existing"] == 19
        assert resumed_summary["repaired_src_existing"] == 1
        assert resumed_summary["repaired_add_existing"] == 1

        collision_refused = run_cli(
            "build", "--src", scratch_src, "--dst", scratch_collision,
            "--add", str(embedded_path), "--add-collection", "collision_add",
            success=False,
        )
        assert "already exist in source" in collision_refused.stderr
        assert scratch_collision not in {
            item.name for item in server.get_collections().collections
        }
        collision_built = run_cli(
            "build", "--src", scratch_src, "--dst", scratch_collision,
            "--add", str(embedded_path), "--add-collection", "collision_add",
            "--allow-overwrite",
        )
        assert json.loads(collision_built.stdout)["dst_count"] == 50
        collision_verified = run_cli(
            "verify", "--src", scratch_src, "--dst", scratch_collision,
            "--add", str(embedded_path), "--add-collection", "collision_add",
            "--sample", "100", "--seed", "42", "--allow-overwrite",
        )
        assert json.loads(collision_verified.stdout)["overwrites"] == 1

        verified = run_cli(
            "verify", "--src", scratch_src, "--dst", scratch_dst,
            "--add", str(embedded_path), "--sample", "100", "--seed", "42",
        )
        verify_summary = json.loads(verified.stdout)
        assert verify_summary["dst_count"] == 70
        assert verify_summary["sampled_src"] == 50
        assert verify_summary["sampled_add"] == 20
        assert verify_summary["identical"] is True
        invalid_sample = run_cli(
            "verify", "--src", scratch_src, "--dst", scratch_dst,
            "--add", str(embedded_path), "--sample", "0", success=False,
        )
        assert "--sample must be positive" in invalid_sample.stderr

        run_cli("promote", "--alias", alias_name, "--to", scratch_dst)
        aliases = {item.alias_name: item.collection_name for item in server.get_aliases().aliases}
        assert aliases[alias_name] == scratch_dst
        run_cli("promote", "--alias", alias_name, "--to", scratch_src)
        aliases = {item.alias_name: item.collection_name for item in server.get_aliases().aliases}
        assert aliases[alias_name] == scratch_src
    finally:
        if local is not None:
            local.close()
        aliases = {item.alias_name for item in server.get_aliases().aliases}
        if alias_name in aliases:
            server.update_collection_aliases(
                change_aliases_operations=[models.DeleteAliasOperation(
                    delete_alias=models.DeleteAlias(alias_name=alias_name)
                )]
            )
        for collection in created_collections:
            if collection in {item.name for item in server.get_collections().collections}:
                server.delete_collection(collection)
        remaining = {item.name for item in server.get_collections().collections}
        assert remaining == {"developer_knowledge"}
        assert server.count("developer_knowledge", exact=True).count == 132_623
        server.close()
