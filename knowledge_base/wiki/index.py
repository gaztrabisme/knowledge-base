"""Incremental wiki indexing into the shared Qdrant server, never embedded storage."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import logging
import os
from pathlib import Path

from qdrant_client import QdrantClient, models

from ..config import BM25_MODEL, EMBEDDING_DIM, EMBEDDING_MODEL, ROOT
from ..embedder import encode_texts, load_model
from ..index import ensure_collection
from .chunk import chunk_page
from .roots import iter_pages, resolve_roots

COLLECTION = os.environ.get("KB_WIKI_COLLECTION", "wiki")
MANIFEST_PATH = ROOT / "data" / "wiki" / "manifest.json"
_model = None
_sparse_model = None


def embed_texts(texts: list[str], task: str = "retrieval.passage") -> list[list[float]]:
    """Own lazy model, same adapter and query/document prompts as the book corpus."""
    global _model
    if _model is None:
        _model = load_model(EMBEDDING_MODEL)
    return encode_texts(_model, EMBEDDING_MODEL, texts, is_query=task.startswith("retrieval.query"))


def get_sparse_model():
    global _sparse_model
    if _sparse_model is None:
        from fastembed import SparseTextEmbedding
        _sparse_model = SparseTextEmbedding(BM25_MODEL)
    return _sparse_model


def text_to_sparse_vector(text: str) -> models.SparseVector:
    sparse = next(iter(get_sparse_model().embed([text])))
    return models.SparseVector(indices=sparse.indices.tolist(), values=sparse.values.tolist())


def get_client() -> QdrantClient:
    """A server is required: never acquire the book embedded store's process lock."""
    url = os.environ.get("KB_QDRANT_URL", "http://127.0.0.1:6333")
    client = None
    try:
        client = QdrantClient(url=url, timeout=30)
        client.get_collections()
    except Exception as error:
        if client is not None:
            client.close()
        raise RuntimeError(
            f"Wiki indexing/search requires the Qdrant server at {url}; "
            "start the server or set KB_QDRANT_URL. Embedded storage is disabled for wikis."
        ) from error
    return client


@dataclass
class RootCounts:
    root: Path
    project: str
    files_seen: int = 0
    re_embedded: int = 0
    deleted: int = 0
    skipped_worktree: int = 0


def _load_manifest(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in manifest.items()
    ):
        raise ValueError(f"Invalid wiki manifest: {path}")
    return manifest


def _save_manifest(path: Path, manifest: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _delete_file(client: QdrantClient, path: str) -> None:
    client.delete(
        collection_name=COLLECTION,
        points_selector=models.FilterSelector(filter=models.Filter(must=[
            models.FieldCondition(key="path", match=models.MatchValue(value=path)),
        ])),
        wait=True,
    )


def _upsert_file(client: QdrantClient, path: Path, root, content: bytes) -> None:
    chunks = chunk_page(path, content.decode("utf-8"))
    for start in range(0, len(chunks), 32):
        batch = chunks[start:start + 32]
        texts = ["\n\n".join(filter(None, [item["heading"], item["text"]])) for item in batch]
        dense = embed_texts(texts)
        points = [models.PointStruct(
            id=int.from_bytes(hashlib.sha256(f"{path}\0{start + i}".encode()).digest()[:8], "big") >> 1,
            vector={"": dense[i], "bm25": text_to_sparse_vector(texts[i])},
            payload={
                "project": root.project, "path": str(path),
                "rel_path": path.relative_to(root.path).as_posix(), **item,
            },
        ) for i, item in enumerate(batch)]
        client.upsert(collection_name=COLLECTION, points=points, wait=True)


def index_roots(
    paths: list[str | Path] | None = None,
    *,
    dry_run: bool = False,
    client: QdrantClient | None = None,
    manifest_path: Path | None = None,
) -> list[RootCounts]:
    """Index selected roots; an injected client is the offline test seam.

    Checkpoint an empty digest before mutation. If a write is interrupted, even a
    new page is known to the next run and can be retried or removed if it vanished.
    Only successful, acknowledged upserts receive the file's real digest.
    """
    selected = resolve_roots(paths)
    manifest_path = MANIFEST_PATH if manifest_path is None else Path(manifest_path)
    manifest = _load_manifest(manifest_path)
    results = []
    owned_client = False
    try:
        if not dry_run and any(not root.skip_reason for root in selected):
            if client is None:
                client = get_client()
                owned_client = True
            if not client.collection_exists(COLLECTION):
                # A deleted/recreated collection cannot trust hashes from its old points.
                manifest = {}
            ensure_collection(client, name=COLLECTION, dim=EMBEDDING_DIM)

        for root in selected:
            counts = RootCounts(root.path, root.project)
            results.append(counts)
            if root.skip_reason:
                counts.skipped_worktree = 1
                continue
            # Complete the scan/read before deciding which pages disappeared.
            pages = {str(path): path.read_bytes() for path in iter_pages(root.path)}
            counts.files_seen = len(pages)
            deleted = [path for path in manifest
                       if Path(path).is_relative_to(root.path) and path not in pages]
            for path in deleted:
                counts.deleted += 1
                if not dry_run:
                    _delete_file(client, path)
                    del manifest[path]
                    _save_manifest(manifest_path, manifest)
            for path, content in pages.items():
                digest = hashlib.sha256(content).hexdigest()
                if manifest.get(path) == digest:
                    continue
                counts.re_embedded += 1
                if dry_run:
                    continue
                manifest[path] = ""
                _save_manifest(manifest_path, manifest)
                _delete_file(client, path)
                _upsert_file(client, Path(path), root, content)
                manifest[path] = digest
                _save_manifest(manifest_path, manifest)
    finally:
        if owned_client:
            client.close()
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", action="append", help="Wiki root (repeatable); overrides configured roots")
    parser.add_argument("--dry-run", action="store_true", help="Count changes without models, Qdrant, or writes")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        counts = index_roots(args.root, dry_run=args.dry_run)
    except (OSError, RuntimeError, ValueError) as error:
        parser.exit(1, f"Wiki index failed: {error}\n")
    if args.dry_run:
        print("Dry run: counts are planned; no vectors or manifest written.")
    for item in counts:
        print(f"{item.root} ({item.project}): files seen={item.files_seen}, "
              f"re-embedded={item.re_embedded}, deleted={item.deleted}, "
              f"skipped (worktree)={item.skipped_worktree}")
    if not counts:
        print("No wiki roots configured.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
