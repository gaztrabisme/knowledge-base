#!/usr/bin/env python3
"""Copy the remotely embedded philosophy collection into the local Qdrant server."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from qdrant_client import QdrantClient, models


def ensure_collection(client: QdrantClient) -> None:
    names = {item.name for item in client.get_collections().collections}
    if "philosophy" not in names:
        client.create_collection(
            collection_name="philosophy",
            vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE),
            sparse_vectors_config={
                "sparse": models.SparseVectorParams(modifier=models.Modifier.IDF),
                "bm25": models.SparseVectorParams(modifier=models.Modifier.IDF),
            },
        )


def main() -> None:
    source_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("qdrant-philosophy")
    target_url = os.environ.get("KB_QDRANT_URL", "http://127.0.0.1:6333")
    source = QdrantClient(path=str(source_path))
    target = QdrantClient(url=target_url, timeout=60)
    ensure_collection(target)
    offset = None
    copied = 0
    while True:
        points, next_offset = source.scroll(
            collection_name="philosophy", offset=offset, limit=128,
            with_payload=True, with_vectors=True,
        )
        if not points:
            break
        target.upsert(collection_name="philosophy", points=[
            models.PointStruct(id=point.id, vector=point.vector, payload=point.payload or {})
            for point in points
        ])
        copied += len(points)
        if next_offset is None:
            break
        offset = next_offset
        print(f"Copied {copied} points")
    source.close()
    target.close()
    print(f"Upserted {copied} philosophy points into {target_url}")


if __name__ == "__main__":
    main()
