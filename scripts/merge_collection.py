#!/usr/bin/env python3
"""Copy a Qdrant collection, merge an embedded candidate, verify it, and promote an alias.

Promotion is an atomic Qdrant alias change and does not copy points. For first-time
rollout, create ``developer_knowledge_live`` -> ``developer_knowledge`` first, then
set ``"env": {"KB_COLLECTION": "developer_knowledge_live"}`` in the knowledge-base
entry of ``.mcp.json`` and restart the MCP server once. Later alias switches are
atomic and need no server configuration change or restart.

This script copies stored vectors verbatim and never loads embedding or reranking
models. ``KB_QDRANT_URL`` selects the server (default ``http://127.0.0.1:6333``).
"""

import argparse
import hashlib
import json
import os
import random
import struct
import sys
from pathlib import Path
from typing import Any, Iterator

from qdrant_client import QdrantClient, models

URL = os.environ.get("KB_QDRANT_URL", "http://127.0.0.1:6333")
BATCH_SIZE = 256


def collection_names(client: QdrantClient) -> set[str]:
    return {item.name for item in client.get_collections().collections}


def exact_count(client: QdrantClient, collection: str) -> int:
    return client.count(collection_name=collection, exact=True).count


def points(
    client: QdrantClient, collection: str, *, with_vectors: bool
) -> Iterator[models.Record]:
    for batch in point_batches(client, collection, with_vectors=with_vectors):
        yield from batch


def point_batches(
    client: QdrantClient, collection: str, *, with_vectors: bool
) -> Iterator[list[models.Record]]:
    offset = None
    while True:
        batch, offset = client.scroll(
            collection_name=collection,
            limit=BATCH_SIZE,
            offset=offset,
            with_payload=True,
            with_vectors=with_vectors,
        )
        if batch:
            yield batch
        if offset is None:
            return


def collection_signature(info: Any) -> str:
    config = info.config
    params = config.params
    def plain(value: Any) -> Any:
        if hasattr(value, "model_dump"):
            return value.model_dump(mode="json", exclude_none=False)
        if isinstance(value, dict):
            return {key: plain(item) for key, item in value.items()}
        return value

    return json.dumps(
        {
            "params": plain(params),
            "hnsw_config": plain(config.hnsw_config),
            "optimizer_config": plain(config.optimizer_config),
            "wal_config": plain(config.wal_config),
            "quantization_config": plain(config.quantization_config),
            "strict_mode_config": plain(config.strict_mode_config),
            "metadata": plain(config.metadata),
            "payload_schema": {
                name: {
                    "data_type": plain(schema.data_type),
                    "params": plain(schema.params),
                }
                for name, schema in (info.payload_schema or {}).items()
            },
        },
        sort_keys=True,
        default=str,
    )


def collection_options(info: Any) -> dict[str, Any]:
    config = info.config
    params = config.params

    def diff(value: Any, model_type: type) -> Any:
        if value is None or isinstance(value, model_type):
            return value
        return model_type(**value.model_dump(exclude_none=True))

    options = {
        "vectors_config": params.vectors,
        "sparse_vectors_config": params.sparse_vectors,
        "shard_number": params.shard_number,
        "sharding_method": params.sharding_method,
        "replication_factor": params.replication_factor,
        "write_consistency_factor": params.write_consistency_factor,
        "on_disk_payload": params.on_disk_payload,
        "payload": params.payload,
        "hnsw_config": diff(config.hnsw_config, models.HnswConfigDiff),
        "optimizers_config": diff(config.optimizer_config, models.OptimizersConfigDiff),
        "wal_config": diff(config.wal_config, models.WalConfigDiff),
        "quantization_config": config.quantization_config,
        "strict_mode_config": config.strict_mode_config,
        "metadata": config.metadata,
    }
    for key in ("read_fan_out_factor", "read_fan_out_delay_ms"):
        value = getattr(params, key, None)
        if value is not None:
            options[key] = value
    return options


def create_payload_indexes(client: QdrantClient, collection: str, info: Any) -> None:
    for name, schema in (info.payload_schema or {}).items():
        field_schema = schema.params or schema.data_type
        if field_schema is None:
            raise ValueError(f"cannot copy payload index schema for {name!r}")
        client.create_payload_index(
            collection_name=collection,
            field_name=name,
            field_schema=field_schema,
            wait=True,
        )


def point_struct(point: Any) -> models.PointStruct:
    return models.PointStruct(id=point.id, vector=point.vector, payload=point.payload)


def same_point(origin: Any, candidate: Any) -> bool:
    return (
        normalized(origin.vector, vector=True) == normalized(candidate.vector, vector=True)
        and normalized(origin.payload) == normalized(candidate.payload)
    )


def retrieve_by_id(client: QdrantClient, collection: str, ids: list[int | str]) -> dict[Any, Any]:
    if not ids:
        return {}
    return {
        point.id: point
        for point in client.retrieve(
            collection_name=collection, ids=ids, with_payload=True, with_vectors=True
        )
    }


def validate_child_id(point: Any) -> None:
    child_id = (point.payload or {}).get("child_id")
    if not isinstance(child_id, str) or not child_id:
        raise ValueError(f"point {point.id} has no non-empty string child_id")
    expected = int.from_bytes(hashlib.sha256(child_id.encode()).digest()[:8], "big") >> 1
    if point.id != expected:
        raise ValueError(f"point {point.id} does not match sha256(child_id)[:8] >> 1")


def scan_ids(client: QdrantClient, collection: str, *, validate: bool = False) -> set[int | str]:
    found = set()
    for point in points(client, collection, with_vectors=False):
        if validate:
            validate_child_id(point)
        found.add(point.id)
    return found


def upsert_batch(client: QdrantClient, collection: str, batch: list[Any]) -> None:
    if batch:
        client.upsert(
            collection_name=collection,
            points=[point_struct(point) for point in batch],
            wait=True,
        )


def build(args: argparse.Namespace) -> int:
    server = QdrantClient(url=args.url, timeout=60)
    embedded = None
    try:
        server_names = collection_names(server)
        if args.src not in server_names:
            raise ValueError(f"source collection does not exist: {args.src}")
        if args.src == args.dst:
            raise ValueError("source and destination must be different collections")
        if args.add_collection not in collection_names(
            embedded := QdrantClient(path=str(Path(args.add).expanduser()))
        ):
            raise ValueError(f"embedded collection does not exist: {args.add_collection}")

        src_info = server.get_collection(args.src)
        src_count = exact_count(server, args.src)
        add_count = exact_count(embedded, args.add_collection)
        dst_exists = args.dst in server_names
        if dst_exists:
            dst_count = exact_count(server, args.dst)
            if dst_count and not args.resume:
                raise ValueError(f"destination {args.dst} is non-empty; pass --resume to continue")
            if collection_signature(server.get_collection(args.dst)) != collection_signature(src_info):
                raise ValueError("destination collection configuration does not match source")

        src_ids = scan_ids(server, args.src)
        add_ids = scan_ids(embedded, args.add_collection, validate=True)
        collisions = src_ids & add_ids
        if collisions and not args.allow_overwrite:
            raise ValueError(
                f"{len(collisions)} added point id(s) already exist in source; "
                "pass --allow-overwrite to declare these overwrites"
            )

        if not dst_exists:
            server.create_collection(
                collection_name=args.dst,
                **collection_options(src_info),
            )
            create_payload_indexes(server, args.dst, src_info)

        present = scan_ids(server, args.dst) if args.resume else set()
        copied = skipped_source = repaired_source = added = skipped_add = repaired_add = 0
        for source_batch in point_batches(server, args.src, with_vectors=True):
            existing_ids = [p.id for p in source_batch if args.resume and p.id in present]
            existing = retrieve_by_id(server, args.dst, existing_ids)
            to_copy = []
            for point in source_batch:
                current = existing.get(point.id)
                if current is not None and same_point(point, current):
                    skipped_source += 1
                else:
                    if point.id in present:
                        repaired_source += 1
                    to_copy.append(point)
                present.add(point.id)
            upsert_batch(server, args.dst, to_copy)
            copied += len(to_copy)

        for add_batch in point_batches(embedded, args.add_collection, with_vectors=True):
            existing_ids = [
                p.id for p in add_batch
                if args.resume and p.id in present
                and not (args.allow_overwrite and p.id in collisions)
            ]
            existing = retrieve_by_id(server, args.dst, existing_ids)
            to_add = []
            for point in add_batch:
                must_overwrite = args.allow_overwrite and point.id in collisions
                current = existing.get(point.id)
                if args.resume and point.id in present and not must_overwrite:
                    if current is not None and same_point(point, current):
                        skipped_add += 1
                        continue
                    repaired_add += 1
                to_add.append(point)
                present.add(point.id)
            upsert_batch(server, args.dst, to_add)
            added += len(to_add)

        expected = src_count + add_count - len(collisions)
        dst_count = exact_count(server, args.dst)
        result = {
            "src": args.src,
            "src_count": src_count,
            "copied_from_src": copied,
            "skipped_src_existing": skipped_source,
            "repaired_src_existing": repaired_source,
            "add_collection": args.add_collection,
            "add_count": add_count,
            "upserted_from_add": added,
            "skipped_add_existing": skipped_add,
            "repaired_add_existing": repaired_add,
            "overwrites": len(collisions),
            "dst": args.dst,
            "dst_count": dst_count,
            "expected_dst_count": expected,
        }
        print(json.dumps(result, sort_keys=True))
        if dst_count != expected:
            raise ValueError(f"destination count {dst_count} != expected {expected}")
        return 0
    finally:
        if embedded is not None:
            embedded.close()
        server.close()


def normalized(value: Any, *, vector: bool = False) -> Any:
    if hasattr(value, "model_dump"):
        return normalized(value.model_dump(mode="json", exclude_none=False), vector=vector)
    if hasattr(value, "tolist"):
        return normalized(value.tolist(), vector=vector)
    if isinstance(value, dict):
        if vector and {"indices", "values"} <= value.keys():
            return {
                "indices": list(value["indices"]),
                "values": [struct.pack("!f", float(item)) for item in value["values"]],
            }
        return {key: normalized(item, vector=vector) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalized(item, vector=vector) for item in value]
    if vector and isinstance(value, (int, float)):
        # Qdrant stores these vectors as float32. The REST response rounds their
        # decimal rendering, while the embedded client can expose the full value.
        return struct.pack("!f", float(value))
    return value


def reservoir_ids(
    client: QdrantClient,
    collection: str,
    size: int,
    rng: random.Random,
    excluded: set[int | str] | None = None,
) -> list[int | str]:
    selected = []
    seen = 0
    for point in points(client, collection, with_vectors=False):
        if excluded and point.id in excluded:
            continue
        seen += 1
        if len(selected) < size:
            selected.append(point.id)
        else:
            index = rng.randrange(seen)
            if index < size:
                selected[index] = point.id
    return selected


def compare_samples(
    origin: QdrantClient,
    origin_name: str,
    destination: QdrantClient,
    destination_name: str,
    ids: list[int | str],
) -> None:
    if not ids:
        return
    expected = origin.retrieve(
        collection_name=origin_name, ids=ids, with_payload=True, with_vectors=True
    )
    actual = destination.retrieve(
        collection_name=destination_name, ids=ids, with_payload=True, with_vectors=True
    )
    by_id = {point.id: point for point in actual}
    for point in expected:
        candidate = by_id.get(point.id)
        if candidate is None:
            raise ValueError(f"sampled id missing in destination: {point.id}")
        if normalized(point.vector, vector=True) != normalized(candidate.vector, vector=True):
            keys = set(point.vector or {}) | set(candidate.vector or {})
            mismatched = [
                key for key in keys
                if normalized((point.vector or {}).get(key), vector=True)
                != normalized((candidate.vector or {}).get(key), vector=True)
            ]
            raise ValueError(f"vector mismatch for sampled id {point.id}, vector names: {mismatched}")
        if normalized(point.payload) != normalized(candidate.payload):
            raise ValueError(f"payload mismatch for sampled id {point.id}")


def verify(args: argparse.Namespace) -> int:
    if args.sample <= 0:
        raise ValueError("--sample must be positive")
    server = QdrantClient(url=args.url, timeout=60)
    embedded = None
    try:
        names = collection_names(server)
        if args.src not in names or args.dst not in names:
            raise ValueError("source or destination collection does not exist")
        embedded = QdrantClient(path=str(Path(args.add).expanduser()))
        if args.add_collection not in collection_names(embedded):
            raise ValueError(f"embedded collection does not exist: {args.add_collection}")
        if collection_signature(server.get_collection(args.src)) != collection_signature(
            server.get_collection(args.dst)
        ):
            raise ValueError("destination vector schema does not match source")

        src_ids = scan_ids(server, args.src)
        add_ids = scan_ids(embedded, args.add_collection, validate=True)
        overlaps = src_ids & add_ids
        if overlaps and not args.allow_overwrite:
            raise ValueError(f"{len(overlaps)} source/add id collision(s) were not declared")
        src_count = exact_count(server, args.src)
        add_count = exact_count(embedded, args.add_collection)
        dst_count = exact_count(server, args.dst)
        expected_count = src_count + add_count - len(overlaps)
        if dst_count != expected_count:
            raise ValueError(f"destination count {dst_count} != expected {expected_count}")

        src_sample = reservoir_ids(
            server, args.src, args.sample, random.Random(args.seed),
            excluded=overlaps if args.allow_overwrite else None,
        )
        add_sample = reservoir_ids(
            embedded, args.add_collection, args.sample, random.Random(args.seed ^ 0xC3)
        )
        compare_samples(server, args.src, server, args.dst, src_sample)
        compare_samples(embedded, args.add_collection, server, args.dst, add_sample)
        print(json.dumps({
            "src_count": src_count,
            "add_count": add_count,
            "overwrites": len(overlaps),
            "expected_dst_count": expected_count,
            "dst_count": dst_count,
            "sampled_src": len(src_sample),
            "sampled_add": len(add_sample),
            "identical": True,
        }, sort_keys=True))
        return 0
    finally:
        if embedded is not None:
            embedded.close()
        server.close()


def promote(args: argparse.Namespace) -> int:
    client = QdrantClient(url=args.url, timeout=60)
    try:
        names = collection_names(client)
        if args.to not in names:
            raise ValueError(f"target collection does not exist: {args.to}")
        if args.alias in names:
            raise ValueError(f"alias name conflicts with a collection: {args.alias}")
        aliases = {item.alias_name: item.collection_name for item in client.get_aliases().aliases}
        current = aliases.get(args.alias)
        if current != args.to:
            actions = []
            if current is not None:
                actions.append(models.DeleteAliasOperation(
                    delete_alias=models.DeleteAlias(alias_name=args.alias)
                ))
            actions.append(models.CreateAliasOperation(
                create_alias=models.CreateAlias(collection_name=args.to, alias_name=args.alias)
            ))
            client.update_collection_aliases(change_aliases_operations=actions)
        print(f"Alias {args.alias!r} -> {args.to!r}")
        print(
            f'Config: add "env": {{"KB_COLLECTION": "{args.alias}"}} '
            'to the knowledge-base entry in .mcp.json'
        )
        return 0
    finally:
        client.close()


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--url", default=URL, help="Qdrant server URL (default: KB_QDRANT_URL)")
    commands = root.add_subparsers(dest="command", required=True)

    build_parser = commands.add_parser("build", help="copy a collection and merge an embedded store")
    build_parser.add_argument("--src", required=True)
    build_parser.add_argument("--dst", required=True)
    build_parser.add_argument("--add", required=True, help="embedded Qdrant store directory")
    build_parser.add_argument("--add-collection", default="developer_knowledge")
    build_parser.add_argument("--resume", action="store_true")
    build_parser.add_argument("--allow-overwrite", action="store_true")
    build_parser.set_defaults(run=build)

    verify_parser = commands.add_parser("verify", help="check counts and seeded point samples")
    verify_parser.add_argument("--src", required=True)
    verify_parser.add_argument("--dst", required=True)
    verify_parser.add_argument("--add", required=True, help="embedded Qdrant store directory")
    verify_parser.add_argument("--add-collection", default="developer_knowledge")
    verify_parser.add_argument("--sample", type=int, default=100)
    verify_parser.add_argument("--seed", type=int, default=42)
    verify_parser.add_argument("--allow-overwrite", action="store_true")
    verify_parser.set_defaults(run=verify)

    promote_parser = commands.add_parser("promote", help="atomically point an alias at a collection")
    promote_parser.add_argument("--alias", required=True)
    promote_parser.add_argument("--to", required=True)
    promote_parser.set_defaults(run=promote)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        return args.run(args)
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
