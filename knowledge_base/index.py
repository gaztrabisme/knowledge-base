"""Embedding + Qdrant indexing with dense and sparse vectors."""

import hashlib
import json
import os
import sys

from fastembed import SparseTextEmbedding
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

from .config import (
    BOOKS, CHUNKS_DIR, COLLECTION_NAME, EMBEDDING_DIM,
    EMBEDDING_MODEL, QDRANT_DIR,
)
from .embedder import encode_texts as _encode_texts, load_model

_model: SentenceTransformer | None = None
_sparse_model: SparseTextEmbedding | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = load_model(EMBEDDING_MODEL)
    return _model


def get_sparse_model() -> SparseTextEmbedding:
    global _sparse_model
    if _sparse_model is None:
        _sparse_model = SparseTextEmbedding("Qdrant/bm25")
    return _sparse_model


def get_client() -> QdrantClient:
    # Prefer the shared Qdrant server (KB_QDRANT_URL, default 127.0.0.1:6333) so
    # indexing writes into the same store every session reads from, and concurrent
    # access is allowed. Fall back to the embedded file store when the server is down.
    url = os.environ.get("KB_QDRANT_URL", "http://127.0.0.1:6333")
    try:
        c = QdrantClient(url=url, timeout=60)
        c.get_collections()  # ping
        return c
    except Exception as e:
        print(f"[kb] Qdrant server {url} unreachable ({e}); "
              f"using embedded store {QDRANT_DIR}", file=sys.stderr)
        QDRANT_DIR.mkdir(parents=True, exist_ok=True)
        return QdrantClient(path=str(QDRANT_DIR))


def ensure_collection(
    client: QdrantClient, name: str = COLLECTION_NAME, dim: int = EMBEDDING_DIM,
) -> None:
    collections = [c.name for c in client.get_collections().collections]
    if name in collections:
        return
    client.create_collection(
        collection_name=name,
        vectors_config=models.VectorParams(
            size=dim,
            distance=models.Distance.COSINE,
        ),
        sparse_vectors_config={
            "bm25": models.SparseVectorParams(
                modifier=models.Modifier.IDF,
            ),
        },
    )


def text_to_sparse_vector(text: str) -> models.SparseVector:
    """Convert text to a sparse vector using FastEmbed's Qdrant/bm25 model."""
    model = get_sparse_model()
    results = list(model.embed([text]))
    if not results:
        return models.SparseVector(indices=[0], values=[0.0])
    sparse = results[0]
    return models.SparseVector(
        indices=sparse.indices.tolist(),
        values=sparse.values.tolist(),
    )


def embed_texts(texts: list[str], task: str = "retrieval.passage") -> list[list[float]]:
    # `task` kept for back-compat with callers (search.py passes "retrieval.query");
    # the adapter maps it to the model-appropriate query/passage idiom.
    is_query = task.startswith("retrieval.query")
    return _encode_texts(get_model(), EMBEDDING_MODEL, texts, is_query=is_query)


def index_book(book_slug: str, client: QdrantClient | None = None) -> int:
    chunk_path = CHUNKS_DIR / f"{book_slug}.json"
    if not chunk_path.exists():
        raise FileNotFoundError(f"Chunks not found: {chunk_path}")

    with open(chunk_path) as f:
        data = json.load(f)

    if client is None:
        client = get_client()
        ensure_collection(client)

    parent_map = {p["parent_id"]: p["text"] for p in data["parents"]}

    existing = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=models.Filter(
            must=[models.FieldCondition(
                key="book",
                match=models.MatchValue(value=book_slug),
            )]
        ),
        limit=1,
    )
    if existing[0]:
        print(f"    Already indexed: {book_slug}")
        return 0

    children = data["children"]
    if not children:
        return 0

    batch_size = 32
    total_indexed = 0

    for i in range(0, len(children), batch_size):
        batch = children[i:i + batch_size]
        enriched_texts = []
        for child in batch:
            heading = child.get("metadata", {}).get("heading_path", "")
            ctx = child.get("context_text", "")
            text = child["text"]
            parts = [p for p in [heading, ctx, text] if p]
            enriched_texts.append("\n\n".join(parts))

        dense_vectors = embed_texts(enriched_texts)

        points = []
        for j, child in enumerate(batch):
            parent_text = parent_map.get(child["parent_id"], "")
            enriched = enriched_texts[j]
            sparse = text_to_sparse_vector(enriched)
            meta = child.get("metadata", {})

            point = models.PointStruct(
                id=int.from_bytes(hashlib.sha256(child["child_id"].encode()).digest()[:8], "big") >> 1,
                vector={
                    "": dense_vectors[j],
                    "bm25": sparse,
                },
                payload={
                    "child_id": child["child_id"],
                    "parent_id": child["parent_id"],
                    "child_text": child["text"],
                    "context_text": child.get("context_text", ""),
                    "parent_text": parent_text,
                    "book": meta.get("book", book_slug),
                    "book_title": meta.get("book_title", BOOKS.get(book_slug, book_slug)),
                    "chapter": meta.get("chapter", ""),
                    "chapter_title": meta.get("chapter_title", ""),
                    "section": meta.get("section", ""),
                    "heading_path": meta.get("heading_path", ""),
                    "chunk_type": meta.get("chunk_type", "prose"),
                },
            )
            points.append(point)

        client.upsert(collection_name=COLLECTION_NAME, points=points)
        total_indexed += len(points)

        if (i + batch_size) % 128 == 0 or i + batch_size >= len(children):
            print(f"    Indexed {min(i + batch_size, len(children))}/{len(children)} chunks")

    return total_indexed


def index_all() -> int:
    client = get_client()
    ensure_collection(client)
    total = 0

    chunk_files = sorted(CHUNKS_DIR.glob("*.json"))
    for chunk_file in chunk_files:
        slug = chunk_file.stem
        print(f"  Indexing: {slug}")
        count = index_book(slug, client)
        total += count

    client.close()
    return total


if __name__ == "__main__":
    print("Indexing chunks into Qdrant...")
    count = index_all()
    print(f"Done. {count} vectors indexed.")
