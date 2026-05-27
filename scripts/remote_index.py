#!/usr/bin/env python3
"""Standalone indexing script for running on a remote GPU machine.
Reads chunk JSONs, embeds with Jina v5, writes Qdrant file-based index."""

import json
import sys
from pathlib import Path

from fastembed import SparseTextEmbedding
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

COLLECTION_NAME = "developer_knowledge"
EMBEDDING_DIM = 1024
EMBEDDING_MODEL = "jinaai/jina-embeddings-v5-text-small-retrieval"

BOOKS = {
    "kagglebook_secondedition": "Kaggle Book, 2nd Edition",
    "machinelearningwithpytorchandscikit-learn": "Machine Learning with PyTorch and Scikit-Learn",
    "masteringpytorch_secondedition": "Mastering PyTorch, 2nd Edition",
    "bayesiananalysiswithpython_thirdedition": "Bayesian Analysis with Python, 3rd Edition",
    "moderntimeseriesforecastingwithpython_secondedition": "Modern Time Series Forecasting with Python, 2nd Edition",
    "causalinferenceanddiscoveryinpython": "Causal Inference and Discovery in Python",
    "deepreinforcementlearninghands-on_thirdedition": "Deep Reinforcement Learning Hands-On, 3rd Edition",
    "graphmachinelearning_secondedition": "Graph Machine Learning, 2nd Edition",
    "machinelearningengineeringwithpython_secondedition": "Machine Learning Engineering with Python, 2nd Edition",
    "scikit-learncookbook_thirdedition": "Scikit-Learn Cookbook, 3rd Edition",
    "pythonmachinelearningbyexample_fourthedition": "Python Machine Learning by Example, 4th Edition",
    "mathematicsofmachinelearning": "Mathematics of Machine Learning",
    "pandascookbook_thirdedition": "Pandas Cookbook, 3rd Edition",
    "machinelearningforalgorithmictradingsecondedition": "Machine Learning for Algorithmic Trading, 2nd Edition",
    "artificialintelligenceforcybersecurity": "Artificial Intelligence for Cybersecurity",
    "hands-onartificialintelligenceforiot_secondedition": "Hands-On AI for IoT, 2nd Edition",
    "azureai-102certificationessentials": "Azure AI-102 Certification Essentials",
    "hands-onmachinelearningwithcplusplus_secondedition": "Hands-On Machine Learning with C++, 2nd Edition",
    "production-rag-guide": "Production RAG Guide",
    # Databases
    "postgresql-14-internals": "PostgreSQL 14 Internals",
    "database-design-2nd-ed": "Database Design, 2nd Edition",
    "redis-for-dummies": "Redis for Dummies",
    "little-redis-book": "The Little Redis Book",
    "digitalocean-redis": "DigitalOcean Redis Guide",
    # Distributed Systems
    "designing-distributed-systems": "Designing Distributed Systems",
    "distributed-systems-fun-profit": "Distributed Systems for Fun and Profit",
    # Security
    "boneh-shoup-applied-cryptography": "Applied Cryptography (Boneh & Shoup)",
    "crypto-101": "Crypto 101",
    "joy-of-cryptography": "The Joy of Cryptography",
    "owasp-developer-guide": "OWASP Developer Guide",
    "owasp-wstg-v4.2": "OWASP Web Security Testing Guide v4.2",
    "owasp-asvs-v5": "OWASP ASVS v5",
    "oauth-rfcs-book": "OAuth RFCs Book",
}


def text_to_sparse_vector(text: str, sparse_model: SparseTextEmbedding) -> models.SparseVector:
    """Convert text to a sparse vector using FastEmbed's Qdrant/bm25 model."""
    results = list(sparse_model.embed([text]))
    if not results:
        return models.SparseVector(indices=[0], values=[0.0])
    sparse = results[0]
    return models.SparseVector(
        indices=sparse.indices.tolist(),
        values=sparse.values.tolist(),
    )


def main():
    work_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    chunks_dir = work_dir / "chunks"
    qdrant_dir = work_dir / "qdrant"
    qdrant_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading dense model {EMBEDDING_MODEL}...")
    model = SentenceTransformer(EMBEDDING_MODEL, trust_remote_code=True)
    print("Loading sparse model Qdrant/bm25...")
    sparse_model = SparseTextEmbedding("Qdrant/bm25")
    print("Models loaded.")

    client = QdrantClient(path=str(qdrant_dir))
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=EMBEDDING_DIM, distance=models.Distance.COSINE),
            sparse_vectors_config={"bm25": models.SparseVectorParams(modifier=models.Modifier.IDF)},
        )

    batch_size = 16
    total_indexed = 0

    for chunk_file in sorted(chunks_dir.glob("*.json")):
        slug = chunk_file.stem
        print(f"Indexing: {slug}")

        existing = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=models.Filter(must=[
                models.FieldCondition(key="book", match=models.MatchValue(value=slug))
            ]),
            limit=1,
        )
        if existing[0]:
            print(f"  Already indexed, skipping.")
            continue

        with open(chunk_file) as f:
            data = json.load(f)

        parent_map = {p["parent_id"]: p["text"] for p in data["parents"]}
        children = data["children"]
        if not children:
            print(f"  No children, skipping.")
            continue

        for i in range(0, len(children), batch_size):
            batch = children[i:i + batch_size]
            enriched_texts = []
            for child in batch:
                ctx = child.get("context_text", "")
                text = child["text"]
                enriched_texts.append(f"{ctx}\n\n{text}" if ctx else text)

            truncated = [t[:8000] if len(t) > 8000 else t for t in enriched_texts]
            dense_vectors = model.encode(truncated, task="retrieval.passage", show_progress_bar=False, batch_size=batch_size).tolist()

            points = []
            for j, child in enumerate(batch):
                parent_text = parent_map.get(child["parent_id"], "")
                sparse = text_to_sparse_vector(enriched_texts[j], sparse_model)
                meta = child.get("metadata", {})

                point = models.PointStruct(
                    id=abs(hash(child["child_id"])) % (2**63),
                    vector={"": dense_vectors[j], "bm25": sparse},
                    payload={
                        "child_id": child["child_id"],
                        "parent_id": child["parent_id"],
                        "child_text": child["text"],
                        "context_text": child.get("context_text", ""),
                        "parent_text": parent_text,
                        "book": meta.get("book", slug),
                        "book_title": meta.get("book_title", BOOKS.get(slug, slug)),
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
            print(f"  {min(i + batch_size, len(children))}/{len(children)}")

    client.close()
    print(f"\nDone. {total_indexed} vectors indexed in {qdrant_dir}")


if __name__ == "__main__":
    main()
