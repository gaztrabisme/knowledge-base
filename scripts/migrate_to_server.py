"""One-shot migration: copy all points from the embedded file store (data/qdrant)
into a running Qdrant server at KB_QDRANT_URL (default 127.0.0.1:6333).

No re-embedding — vectors (dense + bm25 sparse) and payloads are copied verbatim.
Requires the embedded store to be UNLOCKED (stop all MCP servers first).
"""
import os
import sys

from qdrant_client import QdrantClient, models

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from knowledge_base.config import COLLECTION_NAME, QDRANT_DIR  # noqa: E402
from knowledge_base.index import ensure_collection  # noqa: E402

URL = os.environ.get("KB_QDRANT_URL", "http://127.0.0.1:6333")


def main() -> int:
    local = QdrantClient(path=str(QDRANT_DIR))
    server = QdrantClient(url=URL)

    src = local.count(COLLECTION_NAME).count
    print(f"source (embedded) points: {src}")

    ensure_collection(server)
    dst0 = server.count(COLLECTION_NAME).count
    if dst0:
        print(f"server already has {dst0} points in '{COLLECTION_NAME}' — aborting to avoid dup/partial.")
        print("If you want a clean re-copy, delete the server collection first.")
        return 1

    # Inspect one point so we know the vector shape before bulk copy.
    sample, _ = local.scroll(COLLECTION_NAME, limit=1, with_vectors=True, with_payload=False)
    if sample:
        v = sample[0].vector
        print(f"vector shape: type={type(v).__name__}, "
              f"keys={list(v.keys()) if isinstance(v, dict) else 'plain-list'}")

    offset = None
    moved = 0
    while True:
        points, offset = local.scroll(
            COLLECTION_NAME, limit=256, with_payload=True, with_vectors=True, offset=offset
        )
        if not points:
            break
        server.upsert(
            COLLECTION_NAME,
            points=[models.PointStruct(id=p.id, vector=p.vector, payload=p.payload) for p in points],
            wait=True,
        )
        moved += len(points)
        print(f"  moved {moved}/{src}", flush=True)
        if offset is None:
            break

    dst = server.count(COLLECTION_NAME).count
    print(f"DONE — moved {moved}, server now has {dst} points (source {src})")
    return 0 if dst == src else 2


if __name__ == "__main__":
    raise SystemExit(main())
