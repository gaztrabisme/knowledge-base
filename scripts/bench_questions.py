"""Build the reproducible 120-question agent benchmark set."""

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "data/golden/golden_queries_hard.jsonl"
OUTPUT = ROOT / "data/bench/questions.jsonl"


def _largest_remainder(weights: dict[str, int], total: int) -> dict[str, int]:
    weight_sum = sum(weights.values())
    exact = {key: total * value / weight_sum for key, value in weights.items()}
    allocated = {key: int(value) for key, value in exact.items()}
    remainder = total - sum(allocated.values())
    order = sorted(weights, key=lambda key: (-(exact[key] - allocated[key]), key))
    for key in order[:remainder]:
        allocated[key] += 1
    return allocated


def _parents(row: dict) -> list[str]:
    grades = row.get("relevance_grades", {})
    if isinstance(grades, dict) and grades:
        return sorted(parent for parent, grade in grades.items() if float(grade) >= 1)
    if row.get("positive_parents"):
        return sorted(set(row["positive_parents"]))
    parents = set()
    for child_id in row.get("positive_child_ids", []):
        parents.add(child_id.rsplit("-c", 1)[0])
    return sorted(parents)


def _shape(row: dict, qid: str, stratum: str) -> dict:
    return {
        "qid": qid,
        "query": row["query"],
        "domain": row["domain"],
        "archetype": row["archetype"],
        "stratum": stratum,
        "positive_parents": _parents(row),
    }


def build_questions(extra_path: str | None = None) -> list[dict]:
    golden = [json.loads(line) for line in GOLDEN.read_text(encoding="utf-8").splitlines() if line]
    by_domain: dict[str, list[tuple[int, dict]]] = defaultdict(list)
    for index, row in enumerate(golden):
        by_domain[row["domain"]].append((index, row))

    domain_sizes = Counter({domain: len(rows) for domain, rows in by_domain.items()})
    domain_targets = {"distributed": 7, "databases": 12}
    domain_targets.update(_largest_remainder(
        {domain: domain_sizes[domain] for domain in ("ml", "rust", "security")}, 101
    ))

    rng = random.Random(42)
    selected: list[tuple[int, dict]] = []
    for domain in sorted(domain_targets):
        domain_rows = by_domain[domain]
        by_archetype: dict[str, list[tuple[int, dict]]] = defaultdict(list)
        for item in domain_rows:
            by_archetype[item[1]["archetype"]].append(item)
        quotas = _largest_remainder(
            {archetype: len(rows) for archetype, rows in by_archetype.items()},
            domain_targets[domain],
        )
        for archetype in sorted(quotas):
            selected.extend(rng.sample(by_archetype[archetype], quotas[archetype]))

    selected.sort(key=lambda item: item[0])
    questions = [_shape(row, f"h{index:04d}", "golden") for index, row in selected]
    if extra_path:
        extras = [json.loads(line) for line in Path(extra_path).read_text(encoding="utf-8").splitlines() if line]
        questions.extend(_shape(row, f"n{index:03d}", "new-books") for index, row in enumerate(extras))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in questions), encoding="utf-8")
    return questions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extra", help="Optional JSONL questions from newly indexed books")
    args = parser.parse_args()
    questions = build_questions(args.extra)
    counts = Counter((row["domain"], row["archetype"]) for row in questions)
    print(f"Wrote {len(questions)} questions to {OUTPUT}")
    print("domain × archetype")
    print("domain         archetype       count")
    for domain, archetype in sorted(counts):
        print(f"{domain:14s} {archetype:15s} {counts[(domain, archetype)]:5d}")
    print("domain totals")
    for domain in sorted({row["domain"] for row in questions}):
        print(f"{domain:14s} {sum(row['domain'] == domain for row in questions):5d}")


if __name__ == "__main__":
    main()
