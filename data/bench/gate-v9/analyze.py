"""Summarize gate-v9 per-query evals and trace the ten largest hard-set drops."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
METRICS = ("ndcg", "recall10", "mrr", "ceiling_hit")


def load(label):
    rows = [json.loads(line) for line in (HERE / f"{label}-per-query.jsonl").open()]
    return {row["query"]: row for row in rows}


def mean(rows, metric):
    return sum(row[metric] for row in rows) / len(rows) if rows else 0.0


def metrics(rows):
    return {metric: mean(rows, metric) for metric in METRICS}


def main():
    hard_v8, hard_v9 = load("gate-v9-v8-hard"), load("gate-v9-v9-hard")
    easy_v8, easy_v9 = load("gate-v9-v8-easy"), load("gate-v9-v9-easy")
    sanity = load("gate-v9-v9-sanity")
    assert hard_v8.keys() == hard_v9.keys() and len(hard_v8) == 438
    assert easy_v8.keys() == easy_v9.keys() and len(easy_v8) == 199
    assert len(sanity) == 29

    hard_changes = [(q, hard_v9[q]["ndcg"] - hard_v8[q]["ndcg"]) for q in hard_v8]
    counts = {
        "regressed": sum(delta < 0 for _, delta in hard_changes),
        "improved": sum(delta > 0 for _, delta in hard_changes),
        "did_not_move": sum(delta == 0 for _, delta in hard_changes),
        "basis": "per-query NDCG@10",
    }
    new_books = {row["book"] for row in sanity.values()}
    worst = []
    for query, delta in sorted((x for x in hard_changes if x[1] < 0), key=lambda x: (x[1], x[0]))[:10]:
        old, new = hard_v8[query], hard_v9[query]
        old_ranks = {c["parent_id"]: c["rank"] for c in old["candidates"]}
        new_ranks = {c["parent_id"]: c["rank"] for c in new["candidates"]}
        positive_ids = set(old["positive_parent_ids"])
        displaced = {}
        # NDCG can fall when a later gold parent moves down even if first-hit rank
        # stays fixed. Track every relevant parent; rank 11 represents a top-10 miss.
        for parent_id in positive_ids:
            old_rank = old_ranks.get(parent_id, 11)
            new_rank = new_ranks.get(parent_id, 11)
            if new_rank <= old_rank:
                continue
            for candidate in new["candidates"]:
                if candidate["is_labeled_positive"] or candidate["rank"] >= new_rank:
                    continue
                prior_rank = old_ranks.get(candidate["parent_id"])
                if prior_rank is None or prior_rank > old_rank:
                    item = displaced.setdefault(candidate["parent_id"], {
                        "candidate": candidate,
                        "prior_rank": prior_rank,
                        "pushed_parent_ids": [],
                        "rank_drop_total": 0,
                    })
                    item["pushed_parent_ids"].append(parent_id)
                    item["rank_drop_total"] += new_rank - old_rank
        selected = sorted(
            displaced.values(),
            key=lambda x: (-len(x["pushed_parent_ids"]), -x["rank_drop_total"], x["candidate"]["rank"]),
        )
        item = selected[0] if selected else None
        candidate = item["candidate"] if item else None
        prior_rank = item["prior_rank"] if item else None
        book = candidate["book"] if candidate else None
        worst.append({
            "query": query,
            "ndcg_v8": old["ndcg"],
            "ndcg_v9": new["ndcg"],
            "delta_v9_minus_v8": delta,
            "rank_v8": old["rank"],
            "rank_v9": new["rank"],
            "displacer_book": book,
            "displacer_parent_id": candidate["parent_id"] if candidate else None,
            "displacer_rank_v9": candidate["rank"] if candidate else None,
            "displacer_rank_v8": prior_rank,
            "displacer_labeled_parents_pushed": item["pushed_parent_ids"] if item else [],
            "displacer_is_v9_book": book in new_books if book else None,
        })

    hard_a, hard_b = metrics(list(hard_v8.values())), metrics(list(hard_v9.values()))
    easy_a, easy_b = metrics(list(easy_v8.values())), metrics(list(easy_v9.values()))
    sanity_m = metrics(list(sanity.values()))
    summary = {
        "hard_queries": len(hard_v8),
        "easy_queries": len(easy_v8),
        "sanity_queries": len(sanity),
        "sanity_books_covered": len(new_books),
        "hard_v8": hard_a,
        "hard_v9": hard_b,
        "hard_delta_v9_minus_v8": {m: hard_b[m] - hard_a[m] for m in METRICS},
        "easy_v8": easy_a,
        "easy_v9": easy_b,
        "easy_delta_v9_minus_v8": {m: easy_b[m] - easy_a[m] for m in METRICS},
        "sanity_v9": sanity_m,
        "hard_regression_breakdown": counts,
        "ten_worst_hard_regressions": worst,
    }
    (HERE / "analysis-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
