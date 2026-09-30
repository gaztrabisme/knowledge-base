#!/usr/bin/env python3
"""Run the six pre-set promotion checks for the Philosophy B candidate."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "data" / "bench" / "gate-philosophy-b"
REPORT = ROOT / "data" / "bench" / "gate-philosophy-b.md"
CPU = Path(".claude/plan-goal/verify/cpu.py")
PYTHON = Path(".venv/bin/python")
GROUPS = ("en", "vi", "zh", "cross")
SANITY_LANGUAGES = ("en", "vi", "zh-Hans", "zh-Hant")


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{number}: {exc.msg}") from exc
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def load_diagnostics(path: Path) -> list[dict]:
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read evaluator output {path}: {exc}") from exc
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"evaluator output is not a JSON array of rows: {path}")
    return rows


def compare_eval_runs(
    live: list[dict], candidate: list[dict], loss_limit: int,
    *, expected_total: int | None = None,
) -> dict:
    if len(live) != len(candidate):
        raise ValueError(f"live/candidate query counts differ: {len(live)} vs {len(candidate)}")
    grouped: dict[str, dict[str, int]] = defaultdict(lambda: {"n": 0, "live": 0, "candidate": 0})
    for index, (base, trial) in enumerate(zip(live, candidate), 1):
        base_key = (base.get("group"), base.get("query"), base.get("target_chunk_id"))
        trial_key = (trial.get("group"), trial.get("query"), trial.get("target_chunk_id"))
        if base_key != trial_key:
            raise ValueError(f"live/candidate row {index} does not describe the same query")
        group = str(base.get("group", ""))
        counts = grouped[group]
        counts["n"] += 1
        counts["live"] += bool(base.get("hit", base.get("result") == "hit"))
        counts["candidate"] += bool(trial.get("hit", trial.get("result") == "hit"))
    if expected_total is not None and len(live) != expected_total:
        raise ValueError(f"expected {expected_total} queries, found {len(live)}")
    if set(grouped) != set(GROUPS):
        raise ValueError(f"expected groups {GROUPS}, found {tuple(sorted(grouped))}")
    if expected_total is not None:
        expected_per_group = expected_total // len(GROUPS)
        wrong_sizes = {group: grouped[group]["n"] for group in GROUPS if grouped[group]["n"] != expected_per_group}
        if wrong_sizes:
            raise ValueError(f"expected {expected_per_group} queries per group, found {wrong_sizes}")
    for group in GROUPS:
        counts = grouped[group]
        counts["lost"] = max(0, counts["live"] - counts["candidate"])
        counts["live_misses"] = counts["n"] - counts["live"]
        counts["candidate_misses"] = counts["n"] - counts["candidate"]
    return {"passed": all(grouped[group]["lost"] <= loss_limit for group in GROUPS), "groups": dict(grouped)}


def sanity_result(rows: list[dict], diagnostics: list[dict]) -> dict:
    if len(rows) != len(diagnostics):
        raise ValueError(f"sanity input/output counts differ: {len(rows)} vs {len(diagnostics)}")
    totals: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    misses = []
    for source, result in zip(rows, diagnostics):
        if source.get("query") != result.get("query") or source.get("target_chunk_id") != result.get("target_chunk_id"):
            raise ValueError("sanity evaluator output is not aligned with its filtered input")
        language = str(source.get("language", ""))
        hit = bool(result.get("hit", result.get("result") == "hit"))
        totals[language][1] += 1
        totals[language][0] += hit
        if not hit:
            misses.append({"language": language, "query": source["query"], "target": source["target_chunk_id"]})
    if not totals:
        raise ValueError("sanity set has no retained queries")
    overall_hits = sum(item[0] for item in totals.values())
    overall_total = sum(item[1] for item in totals.values())
    language_ok = all(
        language in totals and totals[language][0] * 10 >= totals[language][1] * 7
        for language in SANITY_LANGUAGES
    )
    return {
        "passed": overall_hits * 5 >= overall_total * 4 and language_ok,
        "overall": {"hits": overall_hits, "total": overall_total},
        "languages": {key: {"hits": value[0], "total": value[1]} for key, value in sorted(totals.items())},
        "misses": misses,
    }


def alignment_result(rows: list[dict]) -> dict:
    matches = sum(row.get("verdict") == "match" for row in rows)
    return {"passed": len(rows) == 40 and matches >= 36, "matches": matches, "total": len(rows)}


def chinese_text_result(records: list[dict]) -> dict:
    failures = [row for row in records if row.get("text_check_passed") is not True and row.get("derived") is not True]
    return {"passed": not failures, "total": len(records), "failures": failures}


def top_ten(row: dict) -> list[str | None]:
    return [item.get("parent_id") or item.get("child_id") or item.get("chunk_id") for item in row.get("candidates", [])[:10]]


def technical_result(before: list[dict], after: list[dict]) -> dict:
    if len(before) != len(after):
        raise ValueError(f"technical query counts differ: {len(before)} vs {len(after)}")
    mismatches = []
    for index, (base, trial) in enumerate(zip(before, after), 1):
        same = base.get("query") == trial.get("query") and top_ten(base) == top_ten(trial)
        if not same:
            mismatches.append({"row": index, "query": base.get("query", "")})
    return {"passed": len(before) == 50 and not mismatches, "identical": len(before) - len(mismatches), "total": len(before), "mismatches": mismatches}


def candidate_commands(run_dir: Path) -> list[dict]:
    def eval_command(name: str, collection: str, output: str, *, no_filters: bool = False, eval_file: str = "data/philosophy/eval.jsonl") -> dict:
        args = [str(PYTHON), str(CPU), "scripts/eval_philosophy.py", "--eval-file", eval_file, "--json-out", output]
        if no_filters:
            args.append("--no-filters")
        return {"name": name, "args": args, "env": {"KB_PHILOSOPHY_COLLECTION": collection}}

    commands = [
        eval_command("a-live", "philosophy", _relative(run_dir / "a-live.json")),
        eval_command("a-candidate", "philosophy_b", _relative(run_dir / "a-candidate.json")),
        eval_command("b-live", "philosophy", _relative(run_dir / "b-live.json"), no_filters=True),
        eval_command("b-candidate", "philosophy_b", _relative(run_dir / "b-candidate.json"), no_filters=True),
        eval_command("c-candidate", "philosophy_b", _relative(run_dir / "sanity-candidate.json"), eval_file=_relative(run_dir / "sanity-b-filtered.jsonl")),
        {
            "name": "f-technical-after",
            "args": [str(PYTHON), str(CPU), "scripts/eval_retrieval.py", "--label", "phaseb-tech-after",
                     "--golden", "data/golden/golden_queries_hard.jsonl", "--limit", "50",
                     "--per-query", _relative(run_dir / "tech-after.jsonl"),
                     "--report-out", _relative(run_dir / "tech-after-summary.json")],
            "env": {},
        },
    ]
    return commands


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def print_commands(commands: list[dict]) -> None:
    for index, command in enumerate(commands, 1):
        env = " ".join(f"{key}={shlex.quote(value)}" for key, value in command["env"].items())
        argv = " ".join(shlex.quote(value) for value in command["args"])
        print(f"{index}. {env + ' ' if env else ''}{argv}")


def _copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def _included_chinese_records(registry_path: Path) -> list[dict]:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    records = []
    for work in registry.get("works", []):
        for language, metadata in work.get("languages", {}).items():
            if language.startswith("zh") and metadata.get("status") == "included":
                check = metadata.get("text_check") or {}
                records.append({
                    "work_id": work.get("work_id", ""), "language": language,
                    "status": metadata.get("status"), "text_check_passed": check.get("passed") is True,
                    "derived": metadata.get("derived") is True,
                })
    return records


def _snapshot_inputs(run_dir: Path) -> tuple[list[dict], list[dict]]:
    sanity_path = ROOT / "data/philosophy/phase-b/sanity-b-reviewed.jsonl"
    sample_path = ROOT / "data/philosophy/phase-b/alignment-sample.jsonl"
    before_path = ROOT / "data/philosophy/phase-b/tech-before.jsonl"
    sanity = [row for row in read_jsonl(sanity_path) if row.get("verdict") != "drop"]
    write_jsonl(run_dir / "sanity-b-filtered.jsonl", sanity)
    write_jsonl(run_dir / "alignment-sample.jsonl", read_jsonl(sample_path))
    _copy(before_path, run_dir / "tech-before.jsonl")
    history_dir = run_dir / "alignment-review-history"
    for path in sorted((ROOT / "data/philosophy/phase-b").glob("alignment-review-*.jsonl")):
        _copy(path, history_dir / path.name)
    chinese = _included_chinese_records(ROOT / "data/philosophy/works.json")
    (run_dir / "chinese-included-records.json").write_text(json.dumps(chinese, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return sanity, chinese


def _run_commands(commands: list[dict], run_dir: Path) -> dict[str, dict]:
    outcomes = {}
    for index, command in enumerate(commands, 1):
        env = os.environ.copy()
        env.update(command["env"])
        if command["name"] == "f-technical-after":
            env.pop("KB_PHILOSOPHY_COLLECTION", None)
        shown = command["args"]
        print(f"[{index}/{len(commands)}] {command['name']}: " + " ".join(shlex.quote(part) for part in shown), flush=True)
        try:
            completed = subprocess.run(shown, cwd=ROOT, env=env, text=True, capture_output=True, check=False)
            (run_dir / f"{command['name']}.stdout.log").write_text(completed.stdout, encoding="utf-8")
            (run_dir / f"{command['name']}.stderr.log").write_text(completed.stderr, encoding="utf-8")
            outcomes[command["name"]] = {"returncode": completed.returncode}
        except OSError as exc:
            outcomes[command["name"]] = {"returncode": None, "error": str(exc)}
            (run_dir / f"{command['name']}.stderr.log").write_text(str(exc) + "\n", encoding="utf-8")
    return outcomes


def _result_or_error(action, *args) -> dict:
    try:
        return action(*args)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {"passed": False, "error": str(exc)}


def _format_ratio(count: dict) -> str:
    hits, total = count["hits"], count["total"]
    return f"{hits}/{total} ({hits / total:.3f})" if total else "0/0 (N/A)"


def _render_report(run_dir: Path) -> tuple[str, list[str]]:
    failures = []
    report_lines = ["# Philosophy B promotion gate", "", "Reader: Gary.", ""]

    def add(letter: str, sentence: str, result: dict) -> None:
        state = "PASS" if result.get("passed") else "FAIL"
        report_lines.append(f"({letter}) {sentence} {state}.")
        if not result.get("passed"):
            failures.append(letter)

    a = _result_or_error(lambda: compare_eval_runs(
        load_diagnostics(run_dir / "a-live.json"), load_diagnostics(run_dir / "a-candidate.json"), 1,
        expected_total=60,
    ))
    if "groups" in a:
        values = "; ".join(f"{g}: live {a['groups'][g]['live']}/{a['groups'][g]['n']}, candidate {a['groups'][g]['candidate']}/{a['groups'][g]['n']}, lost {a['groups'][g]['lost']}" for g in GROUPS)
        a_sentence = f"The filtered 60-query eval may lose at most one live hit per group; {values}."
    else:
        a_sentence = f"The filtered 60-query eval may lose at most one live hit per group; unavailable ({a.get('error', 'invalid output')})."
    add("a", a_sentence, a)

    b = _result_or_error(lambda: compare_eval_runs(
        load_diagnostics(run_dir / "b-live.json"), load_diagnostics(run_dir / "b-candidate.json"), 2,
        expected_total=60,
    ))
    if "groups" in b:
        values = "; ".join(f"{g}: live {b['groups'][g]['live']}/{b['groups'][g]['n']}, candidate {b['groups'][g]['candidate']}/{b['groups'][g]['n']}, lost {b['groups'][g]['lost']}" for g in GROUPS)
        b_sentence = f"The same 60 queries without filters may lose at most two live hits per group; {values}."
    else:
        b_sentence = f"The no-filter 60-query eval may lose at most two live hits per group; unavailable ({b.get('error', 'invalid output')})."
    add("b", b_sentence, b)

    c = _result_or_error(lambda: sanity_result(
        read_jsonl(run_dir / "sanity-b-filtered.jsonl"), load_diagnostics(run_dir / "sanity-candidate.json"),
    ))
    if "overall" in c:
        by_language = "; ".join(f"{language} {_format_ratio(c['languages'].get(language, {'hits': 0, 'total': 0}))}" for language in SANITY_LANGUAGES)
        c_sentence = f"The reviewed sanity set must reach 0.80 overall and 0.70 in each language; overall {_format_ratio(c['overall'])}, {by_language}."
    else:
        c_sentence = f"The reviewed sanity set must reach 0.80 overall and 0.70 in each language; unavailable ({c.get('error', 'invalid output')})."
    add("c", c_sentence, c)
    report_lines.extend(["", "Missed sanity queries (language and target):"])
    if c.get("misses"):
        report_lines.extend(f"- {miss['language']}: {miss['query']} — target `{miss['target']}`" for miss in c["misses"])
    elif c.get("passed"):
        report_lines.append("- None.")
    else:
        report_lines.append("- Unavailable because the candidate sanity output could not be read.")

    alignment_rows = _result_or_error(read_jsonl, run_dir / "alignment-sample.jsonl")
    d = _result_or_error(alignment_result, alignment_rows) if isinstance(alignment_rows, list) else alignment_rows
    if "matches" in d:
        d_sentence = f"At least 36 of the 40 reviewed aligned section pairs must match; {d['matches']}/{d['total']} match."
    else:
        d_sentence = f"At least 36 of the 40 reviewed aligned section pairs must match; unavailable ({d.get('error', 'invalid sample')})."
    add("d", d_sentence, d)
    report_lines.extend(["", "Alignment review history (match counts):"])
    history_files = sorted((run_dir / "alignment-review-history").glob("alignment-review-*.jsonl"))
    if history_files:
        for path in history_files:
            history = _result_or_error(read_jsonl, path)
            if isinstance(history, list):
                count = sum(row.get("verdict") == "match" for row in history)
                report_lines.append(f"- {path.name}: {count}/{len(history)} match")
            else:
                report_lines.append(f"- {path.name}: unavailable ({history.get('error', 'invalid file')})")
    else:
        report_lines.append("- No alignment review history files were present.")

    chinese_rows = _result_or_error(lambda path: json.loads(path.read_text(encoding="utf-8")), run_dir / "chinese-included-records.json")
    e = _result_or_error(chinese_text_result, chinese_rows) if isinstance(chinese_rows, list) else chinese_rows
    if "total" in e:
        e_sentence = f"Every included Chinese work needs a passed text check or a derived flag; {e['total'] - len(e['failures'])}/{e['total']} meet that rule."
    else:
        e_sentence = f"Every included Chinese work needs a passed text check or a derived flag; unavailable ({e.get('error', 'invalid registry snapshot')})."
    add("e", e_sentence, e)

    before = _result_or_error(read_jsonl, run_dir / "tech-before.jsonl")
    after = _result_or_error(read_jsonl, run_dir / "tech-after.jsonl")
    f = _result_or_error(technical_result, before, after) if isinstance(before, list) and isinstance(after, list) else (before if not isinstance(before, list) else after)
    if "identical" in f:
        f_sentence = f"The first 50 technical queries must keep identical ordered top-10 results; {f['identical']}/{f['total']} queries match."
    else:
        f_sentence = f"The first 50 technical queries must keep identical ordered top-10 results; unavailable ({f.get('error', 'invalid output')})."
    add("f", f_sentence, f)

    verdict = "Verdict: PROMOTE" if not failures else f"Verdict: DO NOT PROMOTE — failing letters: {', '.join(failures)}"
    report_lines.extend(["", verdict, ""])
    return "\n".join(report_lines), failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="print the complete evaluator command list")
    args = parser.parse_args()
    run_name = datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%SZ")
    run_dir = ARTIFACTS / run_name
    commands = candidate_commands(run_dir)
    if args.dry_run:
        print_commands(commands)
        return 0

    run_dir.mkdir(parents=True, exist_ok=False)
    errors = []
    try:
        _snapshot_inputs(run_dir)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(f"input snapshot: {exc}")
    outcomes = _run_commands(commands, run_dir)
    (run_dir / "command-results.json").write_text(json.dumps({"outcomes": outcomes, "setup_errors": errors}, indent=2) + "\n", encoding="utf-8")
    report, failures = _render_report(run_dir)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="utf-8")
    print(report)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
