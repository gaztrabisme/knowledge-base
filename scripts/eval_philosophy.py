#!/usr/bin/env python3
"""Evaluate philosophy known-item retrieval; run after the remote index is loaded."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from qdrant_client import models
from sentence_transformers import CrossEncoder

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from knowledge_base.philosophy import search as philosophy_search

EVAL_FILE = ROOT / "data" / "philosophy" / "eval.jsonl"
THRESHOLDS = {"en": 0.85, "vi": 0.75, "zh": 0.75, "cross": 0.80}


def _is_hit(row: dict, results: list[dict]) -> bool:
    target = row["target_chunk_id"]
    if any(hit.get("chunk_id") == target or hit.get("child_id") == target for hit in results):
        return True
    if row["group"] != "cross":
        return False
    for hit in results:
        parallels = hit.get("parallels", [])
        for group in (parallels.values() if isinstance(parallels, dict) else parallels):
            if not isinstance(group, dict):
                continue
            for chunk in group.get("chunks", []):
                if chunk.get("chunk_id") == target:
                    return True
    return False


def _recall(rows: list[dict], runner) -> dict[str, float]:
    grouped: dict[str, list[bool]] = defaultdict(list)
    for index, row in enumerate(rows, start=1):
        hits = runner(row)
        grouped[row["group"]].append(_is_hit(row, hits))
        print(f"  {index:02d}/{len(rows)} {row['group']}: {'hit' if grouped[row['group']][-1] else 'miss'}")
    return {group: sum(values) / len(values) for group, values in sorted(grouped.items())}


def _baseline_runner(client):
    """Use the same dense query leg, FastEmbed BM25, and the shipped Ettin ranker."""
    from fastembed import SparseTextEmbedding

    bm25 = SparseTextEmbedding("Qdrant/bm25")
    ranker = CrossEncoder("cross-encoder/ettin-reranker-150m-v1", device="cpu", trust_remote_code=True)

    def run(row):
        dense = philosophy_search.embed_texts([row["query"]], task="retrieval.query")[0]
        sparse = list(bm25.embed([row["query"]]))[0]
        query_sparse = models.SparseVector(indices=sparse.indices.tolist(), values=sparse.values.tolist())
        must = []
        language = row.get("language_filter")
        if language == "zh":
            must.append(models.FieldCondition(key="lang", match=models.MatchAny(any=["zh-Hans", "zh-Hant"])))
        elif language:
            must.append(models.FieldCondition(key="lang", match=models.MatchValue(value=language)))
        if row.get("work_filter"):
            must.append(philosophy_search._work_condition(row["work_filter"]))
        query_filter = models.Filter(must=must) if must else None
        points = client.query_points(
            collection_name="philosophy",
            prefetch=[
                models.Prefetch(query=dense, using="", filter=query_filter, limit=80),
                models.Prefetch(query=query_sparse, using="bm25", filter=query_filter, limit=80),
            ],
            query=models.FusionQuery(fusion=models.Fusion.DBSF),
            limit=80,
            with_payload=True,
        ).points
        candidates = [{"chunk_id": (point.payload or {}).get("child_id", str(point.id)),
                       **(point.payload or {})} for point in points]
        documents = ["\n".join(filter(None, [p.get("section_title", ""), p.get("child_text", "")]))
                     for p in candidates]
        if candidates:
            ranked = ranker.rank(row["query"], documents)
            candidates = [candidates[int(item["corpus_id"])] for item in ranked[:10]]
        return [philosophy_search._attach_parallels(client, item) for item in candidates]

    return run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", action="store_true", help="also run Ettin + FastEmbed BM25 baseline")
    args = parser.parse_args()
    rows = [json.loads(line) for line in EVAL_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != 60:
        raise ValueError(f"Expected 60 philosophy eval queries, found {len(rows)}")
    client = philosophy_search.get_client()
    print("Primary: BGE reranker + custom multilingual sparse tokenizer")
    primary = _recall(rows, lambda row: philosophy_search.hybrid_search(
        row["query"], client=client, top_k=10, language=row.get("language_filter"),
        work=row.get("work_filter"), parallel=True, rerank=True,
    ))
    print("Primary recall@10:")
    for group in THRESHOLDS:
        value = primary.get(group, 0.0)
        print(f"  {group}: {value:.3f} ({value:.0%}) — threshold {THRESHOLDS[group]:.2f}")
    baseline_ok = True
    if args.baseline:
        print("Baseline: Ettin reranker + FastEmbed BM25, same dense leg")
        baseline = _recall(rows, _baseline_runner(client))
        print("Baseline recall@10:")
        for group in THRESHOLDS:
            print(f"  {group}: {baseline.get(group, 0.0):.3f}")
        baseline_ok = all(baseline.get(group, 0.0) >= THRESHOLDS[group] for group in THRESHOLDS)
    client.close()
    primary_ok = all(primary.get(group, 0.0) >= threshold for group, threshold in THRESHOLDS.items())
    return 0 if primary_ok and baseline_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
