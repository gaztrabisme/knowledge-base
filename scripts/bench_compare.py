"""Compare paired agent benchmark JSONL runs."""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from significance import bootstrap_ci_paired, mean, sign_test, wilcoxon_signed_rank


BINARY_METRICS = ("found", "cited", "gave_up")
COUNT_METRICS = (
    "prompt_tokens_total", "tool_tokens_total", "max_prompt_tokens",
    "n_calls", "invalid_calls", "empty_results",
)


def load(path: str) -> dict[str, dict]:
    rows = {}
    with open(path, encoding="utf-8") as source:
        for line in source:
            if line.strip():
                row = json.loads(line)
                rows[row["qid"]] = row
    return rows


def _verdict(metric: str, delta: float, p_value: float, ci: tuple[float, float] | None) -> str:
    if metric in BINARY_METRICS:
        if p_value >= 0.05:
            return "n.s."
        b_wins_direction = delta > 0 if metric in ("found", "cited") else delta < 0
        return "better" if b_wins_direction else "worse"
    if p_value >= 0.05 or ci is None or (ci[0] <= 0 <= ci[1]):
        return "n.s."
    return "better" if delta < 0 else "worse"


def summarize(pairs: list[tuple[dict, dict]]) -> dict:
    result = {"n": len(pairs), "metrics": {}}
    for metric in BINARY_METRICS:
        a = [bool(left[metric]) for left, _ in pairs]
        b = [bool(right[metric]) for _, right in pairs]
        deltas = [int(bi) - int(ai) for ai, bi in zip(a, b)]
        p_value, b_wins, a_wins = sign_test(deltas)
        delta = mean(deltas)
        result[metric] = {
            "rate_a": mean([int(value) for value in a]),
            "rate_b": mean([int(value) for value in b]),
            "delta_b_minus_a": delta,
            "discordant_a1_b0": a_wins,
            "discordant_a0_b1": b_wins,
            "mcnemar_p": p_value,
            "verdict": _verdict(metric, delta, p_value, None),
        }
    for metric in COUNT_METRICS:
        # claude_bench rows carry no peak-context field; skip a metric either side lacks.
        if any(metric not in left or metric not in right for left, right in pairs):
            continue
        a = [float(left[metric]) for left, _ in pairs]
        b = [float(right[metric]) for _, right in pairs]
        deltas = [bi - ai for ai, bi in zip(a, b)]
        if deltas:
            ci = bootstrap_ci_paired(deltas)
            p_value = wilcoxon_signed_rank(deltas)
            delta = mean(deltas)
        else:
            ci, p_value, delta = None, 1.0, 0.0
        result[metric] = {
            "mean_a": mean(a),
            "mean_b": mean(b),
            "delta_b_minus_a": delta,
            "ci95": list(ci) if ci else None,
            "wilcoxon_p": p_value,
            "verdict": _verdict(metric, delta, p_value, ci),
        }
    return result


def _metric_cells(metric: str, summary: dict) -> tuple[str, str, str, str]:
    item = summary[metric]
    if metric in BINARY_METRICS:
        estimate = f"{item['rate_a']:.3f} / {item['rate_b']:.3f}"
        change = (f"A1/B0={item['discordant_a1_b0']}, "
                  f"A0/B1={item['discordant_a0_b1']}")
        interval = "—"
        p_value = item["mcnemar_p"]
    else:
        estimate = f"{item['mean_a']:.1f} / {item['mean_b']:.1f}"
        change = f"{item['delta_b_minus_a']:+.1f}"
        ci = item["ci95"]
        interval = f"[{ci[0]:+.1f}, {ci[1]:+.1f}]" if ci else "—"
        p_value = item["wilcoxon_p"]
    return estimate, change, interval, f"{p_value:.4f}"


def _render_table(title: str, groups: list[tuple[str, list[tuple[dict, dict]]]]) -> str:
    lines = [f"### {title}", "", "| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |",
             "|---|---:|---:|---:|---:|---:|---:|---|"]
    for stratum, pairs in groups:
        summary = summarize(pairs)
        for metric in BINARY_METRICS + COUNT_METRICS:
            if metric not in summary:
                continue
            estimate, change, interval, p_value = _metric_cells(metric, summary)
            verdict = summary[metric]["verdict"]
            lines.append(f"| {stratum} | {metric} | {len(pairs)} | {estimate} | {change} | {interval} | {p_value} | {verdict} |")
    return "\n".join(lines)


def _paired(a: dict[str, dict], b: dict[str, dict]) -> list[tuple[dict, dict]]:
    return [(a[qid], b[qid]) for qid in sorted(set(a).intersection(b))]


def _groups(pairs: list[tuple[dict, dict]], strata: list[str]) -> list[tuple[str, list[tuple[dict, dict]]]]:
    by_stratum: dict[str, list[tuple[dict, dict]]] = defaultdict(list)
    for left, right in pairs:
        by_stratum[left.get("stratum", right.get("stratum", "unknown"))].append((left, right))
    return [("overall", pairs)] + [(stratum, by_stratum.get(stratum, [])) for stratum in strata]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", help="Two or more run JSONL files, supplied as A B pairs")
    parser.add_argument("--json", nargs="?", const="data/bench/compare.json", metavar="PATH",
                        help="Also write comparison metrics as JSON (default: data/bench/compare.json)")
    args = parser.parse_args()
    if len(args.files) % 2:
        parser.error("provide files in A.jsonl B.jsonl pairs")

    all_pairs: list[tuple[dict, dict]] = []
    reports = []
    strata = set()
    for offset in range(0, len(args.files), 2):
        path_a, path_b = args.files[offset:offset + 2]
        rows_a, rows_b = load(path_a), load(path_b)
        pairs = _paired(rows_a, rows_b)
        all_pairs.extend(pairs)
        strata.update(row.get("stratum", "unknown") for row, _ in pairs)
        model_a = next(iter(rows_a.values()), {}).get("model", Path(path_a).stem)
        model_b = next(iter(rows_b.values()), {}).get("model", Path(path_b).stem)
        label = f"{model_a} vs {model_b}"
        reports.append({
            "label": label,
            "file_a": path_a,
            "file_b": path_b,
            "paired_qids": [left["qid"] for left, _ in pairs],
            "_pairs": pairs,
        })

    # Rebuild pair groups after collecting strata, so every pair table has the same breakdown.
    for report in reports:
        pair_rows = report.pop("_pairs")
        report["groups"] = {name: summarize(group) for name, group in _groups(pair_rows, sorted(strata))}
        print(_render_table(report["label"], _groups(pair_rows, sorted(strata))))
        print()
    pooled = _groups(all_pairs, sorted(strata))
    print(_render_table("Pooled across model pairs", pooled))

    if args.json:
        output = {
            "comparisons": reports,
            "pooled": {name: summarize(group) for name, group in pooled},
        }
        path = Path(args.json)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"\nWrote JSON metrics to {path}")


if __name__ == "__main__":
    main()
