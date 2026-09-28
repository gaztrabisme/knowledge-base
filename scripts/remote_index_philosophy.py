#!/usr/bin/env python3
"""Build the phase-A philosophy Qdrant store on a CUDA box.

Copy this script, `embedder.py`, and `chunks/philosophy/*.json` to the remote
machine. The first positional argument is that work directory. The output store
defaults to ``<workdir>/qdrant-philosophy`` (override with
``KB_PHILOSOPHY_QDRANT_DIR``). Install ``opencc-python-reimplemented`` on the
remote machine (``python -m pip install opencc-python-reimplemented``) before
indexing. No collection is embedded on the Mac.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

try:
    from opencc import OpenCC
except ImportError as exc:
    raise RuntimeError(
        "Remote philosophy indexing requires opencc-python-reimplemented for "
        "Traditional/Simplified Chinese normalization; install it with "
        "'python -m pip install opencc-python-reimplemented'."
    ) from exc

from fastembed import SparseTextEmbedding
from qdrant_client import QdrantClient, models

MODEL = "jinaai/jina-embeddings-v5-text-small-retrieval"
DIMENSION = 1024
COLLECTION = "philosophy"
_TOKEN_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\U00020000-\U0002fa1f]+|[^\W\d_]+", re.UNICODE)
_T2S = OpenCC("t2s")


def is_cjk(char: str) -> bool:
    code = ord(char)
    return (0x3400 <= code <= 0x4DBF or 0x4E00 <= code <= 0x9FFF
            or 0x20000 <= code <= 0x2FA1F)


def tokenize(text: str) -> list[str]:
    result: list[str] = []
    simplified = _T2S.convert(text)
    normalized = unicodedata.normalize("NFC", simplified).casefold()
    for match in _TOKEN_RE.finditer(normalized):
        token = match.group(0)
        if is_cjk(token[0]):
            chars = list(token)
            result.extend(chars)
            result.extend(chars[i] + chars[i + 1] for i in range(len(chars) - 1))
        else:
            result.append(token)
    return result


def sparse_vector(text: str) -> models.SparseVector:
    counts = Counter(tokenize(text))
    hashed: Counter[int] = Counter()
    for token, count in counts.items():
        index = int.from_bytes(hashlib.blake2b(token.encode("utf-8"), digest_size=4).digest(), "big") & 0x7FFFFFFF
        hashed[index] += count
    indices = sorted(hashed)
    return models.SparseVector(indices=indices, values=[float(hashed[i]) for i in indices])


def ensure_collection(client: QdrantClient) -> None:
    names = {item.name for item in client.get_collections().collections}
    if COLLECTION not in names:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(size=DIMENSION, distance=models.Distance.COSINE),
            sparse_vectors_config={
                "sparse": models.SparseVectorParams(modifier=models.Modifier.IDF),
                "bm25": models.SparseVectorParams(modifier=models.Modifier.IDF),
            },
        )


def main() -> None:
    from embedder import encode_texts, load_model

    workdir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    chunks_dir = workdir / "chunks" / "philosophy"
    store = Path(os.environ.get("KB_PHILOSOPHY_QDRANT_DIR", str(workdir / "qdrant-philosophy")))
    if not chunks_dir.is_dir():
        raise FileNotFoundError(f"Expected chunk directory: {chunks_dir}")
    store.mkdir(parents=True, exist_ok=True)
    print(f"Loading {MODEL} and Qdrant/bm25; target={store} collection={COLLECTION}")
    model = load_model(MODEL)
    bm25 = SparseTextEmbedding("Qdrant/bm25")
    client = QdrantClient(path=str(store))
    ensure_collection(client)
    batch_size = int(os.environ.get("KB_INDEX_BATCH", "48"))
    indexed = 0

    for path in sorted(chunks_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        work_id = data["work_id"]
        # One work has several language files, so a file is done only when every
        # child of this work+language is present. Point ids are deterministic, so
        # a partially indexed file is simply re-upserted.
        present = client.count(
            collection_name=COLLECTION,
            count_filter=models.Filter(must=[
                models.FieldCondition(key="work_id", match=models.MatchValue(value=work_id)),
                models.FieldCondition(key="lang", match=models.MatchValue(value=data.get("lang", ""))),
            ]),
            exact=True,
        ).count
        if present >= len(data.get("children", [])):
            print(f"{path.name}: already indexed; skipping")
            continue
        parent_map = {parent["parent_id"]: parent["text"] for parent in data.get("parents", [])}
        children = data.get("children", [])
        for start in range(0, len(children), batch_size):
            batch = children[start:start + batch_size]
            texts = []
            for child in batch:
                meta = child.get("metadata", {})
                texts.append("\n\n".join(part for part in [meta.get("section_title", ""), child["text"]] if part)[:8000])
            dense = encode_texts(model, MODEL, texts, is_query=False, batch_size=batch_size)
            bm25_results = list(bm25.embed(texts))
            points = []
            for i, child in enumerate(batch):
                meta = child.get("metadata", {})
                child_id = child["child_id"]
                bm25_item = bm25_results[i]
                bm25_vector = models.SparseVector(indices=bm25_item.indices.tolist(), values=bm25_item.values.tolist())
                points.append(models.PointStruct(
                    id=int.from_bytes(hashlib.sha256(child_id.encode()).digest()[:8], "big") >> 1,
                    vector={"": dense[i], "sparse": sparse_vector(texts[i]), "bm25": bm25_vector},
                    payload={
                        "child_id": child_id,
                        "parent_id": child["parent_id"],
                        "child_text": child["text"],
                        "context_text": child.get("context_text", ""),
                        "parent_text": parent_map.get(child["parent_id"], ""),
                        "book": work_id,
                        "book_title": data.get("title", work_id),
                        "work_id": work_id,
                        "work_group": meta.get("work_group", data.get("work_group", work_id)),
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
                ))
            client.upsert(collection_name=COLLECTION, points=points)
            indexed += len(points)
            print(f"{path.name}: {min(start + len(batch), len(children))}/{len(children)}")
    client.close()
    print(f"Indexed {indexed} points into {store}")


if __name__ == "__main__":
    main()
