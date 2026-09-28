"""Ablate the philosophy retrieval stack on the eval set: which sparse leg and which
reranker give the recall per language group.

Sparse legs: the custom multilingual tokenizer ("sparse"), FastEmbed BM25 ("bm25"),
or both. Rerankers: BGE-v2-m3, Ettin-150m, none (DBSF fusion order), and "route"
(Ettin for English queries, BGE otherwise). Same dense leg and candidate depth (80)
as scripts/eval_philosophy.py, so the numbers are comparable with its report.

Usage: python scripts/ablate_philosophy.py   (KB_QDRANT_URL points at the server)
"""

from __future__ import annotations

import itertools
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastembed import SparseTextEmbedding  # noqa: E402
from qdrant_client import models  # noqa: E402
from sentence_transformers import CrossEncoder  # noqa: E402

from knowledge_base.philosophy import search as ps  # noqa: E402
from knowledge_base.philosophy.sparse import text_to_sparse_vector  # noqa: E402
from scripts.eval_philosophy import EVAL_FILE, THRESHOLDS, _is_hit  # noqa: E402

CANDIDATES = 80


def ps_is_english(text: str) -> bool:
    """True when the query is plain ASCII: no CJK and no Vietnamese diacritics."""
    return all(ord(ch) < 128 for ch in text)


def main() -> int:
    rows = [json.loads(line) for line in EVAL_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    client = ps.get_client()
    bm25 = SparseTextEmbedding("Qdrant/bm25")
    rankers = {
        "bge": CrossEncoder("BAAI/bge-reranker-v2-m3"),
        "ettin": CrossEncoder("cross-encoder/ettin-reranker-150m-v1", trust_remote_code=True),
    }

    def candidates(row, legs):
        dense = ps.embed_texts([row["query"]], task="retrieval.query")[0]
        must = []
        language = row.get("language_filter")
        if language == "zh":
            must.append(models.FieldCondition(key="lang", match=models.MatchAny(any=["zh-Hans", "zh-Hant"])))
        elif language:
            must.append(models.FieldCondition(key="lang", match=models.MatchValue(value=language)))
        if row.get("work_filter"):
            must.append(ps._work_condition(row["work_filter"]))
        flt = models.Filter(must=must) if must else None
        prefetch = [models.Prefetch(query=dense, using="", filter=flt, limit=CANDIDATES)]
        if "sparse" in legs:
            prefetch.append(models.Prefetch(query=text_to_sparse_vector(row["query"]), using="sparse",
                                            filter=flt, limit=CANDIDATES))
        if "bm25" in legs:
            s = list(bm25.embed([row["query"]]))[0]
            prefetch.append(models.Prefetch(query=models.SparseVector(indices=s.indices.tolist(),
                                                                      values=s.values.tolist()),
                                            using="bm25", filter=flt, limit=CANDIDATES))
        points = client.query_points(collection_name="philosophy", prefetch=prefetch,
                                     query=models.FusionQuery(fusion=models.Fusion.DBSF),
                                     limit=CANDIDATES, with_payload=True).points
        return [{"chunk_id": (p.payload or {}).get("child_id", str(p.id)), **(p.payload or {})} for p in points]

    def rerank(row, hits, name):
        if name == "none" or not hits:
            return hits[:10]
        if name == "route":
            name = "ettin" if ps_is_english(row["query"]) else "bge"
        docs = ["\n".join(filter(None, [h.get("section_title", ""), h.get("child_text", "")])) for h in hits]
        ranked = rankers[name].rank(row["query"], docs)
        return [hits[int(r["corpus_id"])] for r in ranked[:10]]

    legsets = {"sparse": ("sparse",), "bm25": ("bm25",), "both": ("sparse", "bm25")}
    results = {}
    for (lname, legs), rname in itertools.product(legsets.items(), ["bge", "ettin", "route", "none"]):
        grouped = defaultdict(list)
        for row in rows:
            hits = [ps._attach_parallels(client, h) for h in rerank(row, candidates(row, legs), rname)]
            grouped[row["group"]].append(_is_hit(row, hits))
        results[f"{lname}+{rname}"] = {g: sum(v) / len(v) for g, v in sorted(grouped.items())}
        r = results[f"{lname}+{rname}"]
        passed = all(r[g] >= THRESHOLDS[g] for g in THRESHOLDS)
        print(f"{lname:>6}+{rname:<5} " + "  ".join(f"{g}={r[g]:.3f}" for g in THRESHOLDS)
              + f"  {'PASS' if passed else 'fail'}", flush=True)
    (ROOT / "data" / "philosophy" / "ablation.json").write_text(json.dumps(results, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
