"""Apply the pre-registered label-verification rules and build questions_v2.

Inputs (data/bench/analysis/verify/):
  key.jsonl          id -> set (extra | wrong | pos | neg), qid, parent_id
  grades-B.jsonl     judge B (GLM lane), every id, grade 0/1/2
  grades-ref.jsonl   reference (Claude subagent): the stratified 40, plus every pair it
                     was asked to adjudicate
Judge A is the Codex audit (data/bench/analysis/golden-audit.jsonl): it proposed every
extra (grade 2) and every wrong label (grade 0); it graded no controls.

Rules, fixed in the plan before any grade was seen:
  - B is calibrated when: pos controls graded 2 >= 0.90, neg controls graded 2 <= 0.10,
    and agreement with the reference on 2-vs-not-2 over the 40-sample >= 0.85.
    If B fails, the reference decides all 273 decision pairs.
  - extra added when A and B both give 2; otherwise the reference decides (2 = add).
  - wrong label removed when A and B both give 0; otherwise the reference decides (0 = remove).
  - new-book questions whose audit note says "Specificity: specific" accept added answers
    only from their own book.
  - questions the audit flagged ambiguous / unanswerable / leaky are dropped.

Usage:
  python3 scripts/verify_decide.py --need-ref   # write the ids the reference must adjudicate
  python3 scripts/verify_decide.py              # report + questions_v2.jsonl
"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V = ROOT / "data/bench/analysis/verify"
FLAGGED = {"ambiguous", "unanswerable", "leaky"}


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def book(pid: str) -> str:
    return pid.rsplit("-p", 1)[0]


def kappa(a: list[bool], b: list[bool]) -> float:
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def calibration(key, gb, gref):
    pos = [k["id"] for k in key if k["set"] == "pos"]
    neg = [k["id"] for k in key if k["set"] == "neg"]
    sample = json.loads((V / "ref-sample-ids.json").read_text())
    pos_rate = sum(gb[i] == 2 for i in pos) / len(pos)
    neg_rate = sum(gb[i] == 2 for i in neg) / len(neg)
    agree = sum((gb[i] == 2) == (gref[i] == 2) for i in sample) / len(sample)
    ok = pos_rate >= 0.90 and neg_rate <= 0.10 and agree >= 0.85
    return {"pos_control_rate_B": pos_rate, "neg_control_rate_B": neg_rate,
            "agreement_B_ref_on_sample": agree, "n_sample": len(sample), "B_calibrated": ok}


def need_ref(key, gb, calibrated: bool) -> list[str]:
    ids = []
    for k in key:
        if k["set"] == "extra" and (not calibrated or gb[k["id"]] != 2):
            ids.append(k["id"])
        if k["set"] == "wrong" and (not calibrated or gb[k["id"]] != 0):
            ids.append(k["id"])
    return ids


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--need-ref", action="store_true")
    args = ap.parse_args()

    key = load(V / "key.jsonl")
    gb = {g["id"]: g["grade"] for g in load(V / "grades-B.jsonl")}
    gref = {g["id"]: g["grade"] for g in load(V / "grades-ref.jsonl")}
    assert set(gb) == {k["id"] for k in key}, "judge B must grade every id"
    cal = calibration(key, gb, gref)

    todo = need_ref(key, gb, cal["B_calibrated"])
    if args.need_ref:
        pending = [i for i in todo if i not in gref]
        (V / "need-ref-ids.json").write_text(json.dumps(sorted(pending)))
        print(json.dumps(cal), f"| reference must adjudicate {len(todo)} ids, {len(pending)} not yet graded")
        return
    missing = [i for i in todo if i not in gref]
    assert not missing, f"{len(missing)} ids still need a reference grade (run --need-ref)"

    decision = [k for k in key if k["set"] in ("extra", "wrong")]
    a_bin = [k["set"] == "extra" for k in decision]          # A: extra=2, wrong=0
    b_bin = [gb[k["id"]] == 2 for k in decision]
    cal["kappa_A_B_2_vs_not2"] = kappa(a_bin, b_bin)
    cal["n_decision"] = len(decision)

    audit = {a["qid"]: a for a in load(ROOT / "data/bench/analysis/golden-audit.jsonl")}
    questions = load(ROOT / "data/bench/questions.jsonl")
    added, removed, how = {}, {}, {}
    for k in decision:
        i, qid, pid = k["id"], k["qid"], k["parent_id"]
        if k["set"] == "extra":
            if cal["B_calibrated"] and gb[i] == 2:
                added.setdefault(qid, []).append(pid); how[(qid, pid)] = "added:A2,B2"
            elif gref.get(i) == 2:
                added.setdefault(qid, []).append(pid); how[(qid, pid)] = "added:ref2"
        else:
            if (cal["B_calibrated"] and gb[i] == 0) or gref.get(i) == 0:
                removed.setdefault(qid, set()).add(pid)

    rows, stats = [], {"dropped_flagged": 0, "specific_extras_rejected": 0, "added": 0,
                       "removed": 0, "dropped_no_positive": 0}
    for q in questions:
        a = audit[q["qid"]]
        if a["verdict"] in FLAGGED:
            stats["dropped_flagged"] += 1
            continue
        keep = [p for p in q["positive_parents"] if p not in removed.get(q["qid"], set())]
        stats["removed"] += len(q["positive_parents"]) - len(keep)
        prov = {p: "original" for p in keep}
        specific = "Specificity: specific" in a["note"]
        own_books = {book(p) for p in q["positive_parents"]}
        for p in added.get(q["qid"], []):
            if specific and book(p) not in own_books:
                stats["specific_extras_rejected"] += 1
                continue
            if p not in prov:
                prov[p] = how[(q["qid"], p)]
                stats["added"] += 1
        if not prov:
            stats["dropped_no_positive"] += 1
            continue
        rows.append({**q, "positive_parents": sorted(prov), "provenance": prov})

    with open(ROOT / "data/bench/questions_v2.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    summary = {**cal, **stats, "rows": len(rows),
               "reference_adjudicated": len(todo)}
    (V / "decision-summary.json").write_text(json.dumps(summary, indent=2))
    write_report(summary, key, gb, gref)
    print(json.dumps(summary, indent=2))


def write_report(s: dict, key: list[dict], gb: dict, gref: dict) -> None:
    from collections import Counter
    by_set = {name: [k["id"] for k in key if k["set"] == name] for name in ("extra", "wrong", "pos", "neg")}
    def dist(grades, ids):
        c = Counter(grades[i] for i in ids if i in grades)
        return f"{c.get(2, 0)} / {c.get(1, 0)} / {c.get(0, 0)}"
    ok = lambda cond: "pass" if cond else "FAIL"
    lines = [
        "# Benchmark label verification",
        "",
        "Reader: whoever interprets agent-benchmark results on `data/bench/questions_v2.jsonl`.",
        "This records how the labels in that file were checked and what changed.",
        "",
        "## Method",
        "",
        "A Codex audit (judge A) proposed 258 extra correct passages and 15 wrong labels for the",
        "150 bench questions. Each proposal became a (question, full passage) pair on a blinded",
        "sheet, shuffled with 60 current labels (positive controls) and 60 unlabelled top-10",
        "search candidates (negative controls). Graders saw opaque ids only, in directories",
        "holding nothing but the sheet slice and the rubric (2 = directly answers, 1 = related or",
        "partial, 0 = does not answer).",
        "",
        "- Judge B: GLM lane (`glm-5.3-flash`), all 393 pairs.",
        "- Reference: Claude subagents, a stratified 40 (10 per set), then every pair the rules",
        "  sent to it.",
        "",
        "Rules were fixed before grading: B counts only if calibrated; an extra is added when A and",
        "B both give 2, else the reference decides; a label is removed when A and B both give 0,",
        "else the reference decides; if B fails calibration the reference decides all 273.",
        "",
        "## Judge B calibration",
        "",
        "| Check | Value | Needed | Result |",
        "|---|---:|---:|---|",
        f"| Positive controls graded 2 | {s['pos_control_rate_B']:.3f} | ≥ 0.90 | {ok(s['pos_control_rate_B'] >= 0.90)} |",
        f"| Negative controls graded 2 | {s['neg_control_rate_B']:.3f} | ≤ 0.10 | {ok(s['neg_control_rate_B'] <= 0.10)} |",
        f"| Agreement with reference, 2 vs not-2 (n={s['n_sample']}) | {s['agreement_B_ref_on_sample']:.3f} | ≥ 0.85 | {ok(s['agreement_B_ref_on_sample'] >= 0.85)} |",
        f"| Cohen's κ, A vs B on 2 vs not-2 (n={s['n_decision']}) | {s['kappa_A_B_2_vs_not2']:.3f} | reported | — |",
        "",
        f"Judge B calibrated: **{s['B_calibrated']}**. "
        + ("Its grades decide agreed pairs." if s["B_calibrated"] else
           "Its grades are discarded; the reference decided all 273 extra and wrong-label pairs."),
        "",
        "## Grade distributions (2 / 1 / 0)",
        "",
        "| Set | n | Judge B | Reference |",
        "|---|---:|---|---|",
    ]
    for name, ids in by_set.items():
        lines.append(f"| {name} | {len(ids)} | {dist(gb, ids)} | {dist(gref, ids)} (graded {sum(i in gref for i in ids)}) |")
    lines += [
        "",
        "## Result",
        "",
        f"- Questions dropped as ambiguous, unanswerable or leaky: {s['dropped_flagged']}.",
        f"- Extra passages added as correct answers: {s['added']}.",
        f"- Extras graded 2 but rejected because the question is specific to its own book: {s['specific_extras_rejected']}.",
        f"- Wrong labels removed: {s['removed']}.",
        f"- Questions dropped for having no correct passage left: {s['dropped_no_positive']}.",
        f"- Rows in `questions_v2.jsonl`: {s['rows']}.",
        "",
        "Every positive in `questions_v2.jsonl` carries its provenance (`original`, `added:A2,B2`",
        "or `added:ref2`). Raw grades: `data/bench/analysis/verify/grades-B.jsonl`,",
        "`grades-ref.jsonl`; key: `key.jsonl`.",
    ]
    (ROOT / "data/bench/analysis/golden-verify.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
