"""Phase 1B — retrieval evaluation harness.

The tool-agnostic gate for every retrieval change (enrichment, reranker, chunking,
embeddings). Runs the golden query set through the REAL hybrid_search() pipeline and
scores ranking quality at PARENT granularity (the agent receives parent content, and
the pipeline dedups by parent, so parent-level is the meaningful unit).

Two views per query:
  - full pipeline  (rerank + adaptive cutoff, top_k=10) → NDCG@10 / Recall@10 / MRR
                     = what the agent actually gets.
  - retrieval ceiling (fusion only, no rerank, top_k=50) → Recall@50
                     = did we retrieve the positive at all? Separates "never found"
                       from "found but reranker/cutoff dropped it".

Usage:
  python3 scripts/eval_retrieval.py --label v6-no-enrichment
  python3 scripts/eval_retrieval.py --label v6-enriched   # after Phase 3, compare
"""

import argparse
import glob
import json
import math
from collections import defaultdict

from knowledge_base.config import CHUNKS_DIR
from knowledge_base.search import get_client, hybrid_search

GOLDEN_PATH = CHUNKS_DIR.parent / "golden" / "golden_queries.jsonl"
RESULTS_DIR = CHUNKS_DIR.parent / "golden" / "eval_runs"
CEILING_K = 50


def child_to_parent_map() -> dict[str, str]:
    m = {}
    for f in glob.glob(str(CHUNKS_DIR / "*.json")):
        data = json.loads(open(f).read())
        for c in data["children"]:
            m[c["child_id"]] = c["parent_id"]
    return m


def dcg(rels: list[int]) -> float:
    return sum(rel / math.log2(i + 2) for i, rel in enumerate(rels))


def ndcg_at_k(ranked_parents: list[str], positives: set[str], k: int) -> float:
    rels = [1 if p in positives else 0 for p in ranked_parents[:k]]
    ideal = sorted(rels, reverse=True)
    idcg = dcg(ideal)
    return dcg(rels) / idcg if idcg > 0 else 0.0


def first_hit_rank(ranked_parents: list[str], positives: set[str]) -> int | None:
    for i, p in enumerate(ranked_parents):
        if p in positives:
            return i + 1
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True, help="run label, e.g. v6-no-enrichment")
    ap.add_argument("--golden", default=str(GOLDEN_PATH), help="path to golden JSONL")
    ap.add_argument("--limit", type=int, default=0, help="eval only first N queries (debug)")
    ap.add_argument("--candidates", type=int, default=50, help="fusion candidate depth fed to reranker (⚡3 sweep)")
    ap.add_argument("--hyde", default="", help="path to hyde_<tag>.jsonl {query, hyde_passage}; "
                                               "routes the dense leg through the hypothetical passage "
                                               "(BM25 stays on the original query). Measures the "
                                               "agent-augmented production path, not the bare-query floor.")
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(args.golden)]
    if args.limit:
        rows = rows[: args.limit]
    c2p = child_to_parent_map()

    hyde_map = {}
    if args.hyde:
        hyde_map = {json.loads(l)["query"]: json.loads(l)["hyde_passage"] for l in open(args.hyde)}
        missing = sum(1 for r in rows if r["query"] not in hyde_map)
        print(f"HyDE mode: {len(hyde_map)} passages loaded · {missing} queries without a passage (fall back to bare query)")

    client = get_client()
    per_domain = defaultdict(lambda: {"ndcg": [], "recall10": [], "mrr": [], "recall_ceiling": []})
    misses = []

    for n, r in enumerate(rows, 1):
        positives = {c2p[cid] for cid in r["positive_child_ids"] if cid in c2p}
        if not positives:
            continue
        dom = r["domain"]
        hyde = hyde_map.get(r["query"]) or None

        # full pipeline (what the agent gets)
        results = hybrid_search(r["query"], client, top_k=10, candidates=args.candidates, rerank=True, hyde_passage=hyde)
        ranked = [res.parent_id for res in results]
        ndcg = ndcg_at_k(ranked, positives, 10)
        rank = first_hit_rank(ranked, positives)
        recall10 = 1.0 if rank else 0.0
        mrr = 1.0 / rank if rank else 0.0

        # retrieval ceiling (fusion only, no rerank/cutoff)
        ceil = hybrid_search(r["query"], client, top_k=CEILING_K, rerank=False, hyde_passage=hyde)
        ceil_hit = 1.0 if positives & {x.parent_id for x in ceil} else 0.0

        per_domain[dom]["ndcg"].append(ndcg)
        per_domain[dom]["recall10"].append(recall10)
        per_domain[dom]["mrr"].append(mrr)
        per_domain[dom]["recall_ceiling"].append(ceil_hit)

        if not recall10:
            misses.append({"query": r["query"], "book": r["book"], "domain": dom,
                           "in_ceiling": bool(ceil_hit), "heading_path": r["heading_path"]})
        if n % 25 == 0:
            print(f"  {n}/{len(rows)}...")

    client.close()

    def agg(key):
        allv = [v for d in per_domain.values() for v in d[key]]
        return sum(allv) / len(allv) if allv else 0.0

    report = {"label": args.label, "n_queries": sum(len(d["ndcg"]) for d in per_domain.values()),
              "aggregate": {k: round(agg(k), 4) for k in ["ndcg", "recall10", "mrr", "recall_ceiling"]},
              "per_domain": {}}
    for dom, d in sorted(per_domain.items()):
        report["per_domain"][dom] = {
            "n": len(d["ndcg"]),
            **{k: round(sum(d[k]) / len(d[k]), 4) for k in ["ndcg", "recall10", "mrr", "recall_ceiling"]},
        }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"{args.label}.json"
    out.write_text(json.dumps({"report": report, "misses": misses}, indent=2))

    print(f"\n===== {args.label}  (n={report['n_queries']}) =====")
    a = report["aggregate"]
    print(f"  NDCG@10={a['ndcg']:.4f}  Recall@10={a['recall10']:.4f}  "
          f"MRR={a['mrr']:.4f}  Recall@{CEILING_K}(ceiling)={a['recall_ceiling']:.4f}")
    print("  per-domain:")
    for dom, d in report["per_domain"].items():
        print(f"    {dom:12s} n={d['n']:3d}  NDCG@10={d['ndcg']:.3f}  R@10={d['recall10']:.3f}  "
              f"MRR={d['mrr']:.3f}  R@{CEILING_K}={d['recall_ceiling']:.3f}")
    gap = a["recall_ceiling"] - a["recall10"]
    print(f"\n  retrieval ceiling - delivered recall = {gap:.4f} "
          f"({'reranker/cutoff dropping hits' if gap > 0.05 else 'reranker keeping retrieved hits'})")
    print(f"  full report + {len(misses)} misses -> {out}")


if __name__ == "__main__":
    main()
