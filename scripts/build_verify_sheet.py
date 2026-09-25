"""Build the blinded grading sheet that verifies the benchmark question labels.

Each row pairs one bench question with one full parent passage. Rows carry an opaque
id only; which set a pair came from (audit extra, audit wrong label, positive control,
negative control) is written to a separate key file that graders never see.

Sets (fixed by the plan, seed 42):
  extra  - every extra_positive_parents entry in golden-audit.jsonl (258)
  wrong  - every wrong_positive_parents entry (15)
  pos    - 60 random current positive labels, not flagged wrong, from unflagged questions
  neg    - 60 random top-10 pool candidates that are not labelled, not an audit extra,
           at most one per question

Usage:
  python3 scripts/build_verify_sheet.py
"""

import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/bench/analysis/verify"
SEED = 42
FLAGGED = {"ambiguous", "unanswerable", "leaky"}
# One live parent is a 118k-character back-of-book index page; cap passages so a grader
# reads it, not the whole index. Every other parent is under 12k characters.
MAX_PASSAGE_CHARS = 16000


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def parent_texts(parent_ids: set[str]) -> dict[str, tuple[str, str]]:
    """parent_id -> (book title, parent text), reading each book's chunk file once."""
    books: dict[str, set[str]] = {}
    for pid in parent_ids:
        books.setdefault(pid.rsplit("-p", 1)[0], set()).add(pid)
    catalog = json.loads((ROOT / "data/catalog.json").read_text())
    out = {}
    for book, pids in books.items():
        data = json.loads((ROOT / f"data/chunks/{book}.json").read_text())
        title = catalog.get(book, {}).get("title", book)
        for parent in data["parents"]:
            if parent["parent_id"] in pids:
                out[parent["parent_id"]] = (title, parent["text"])
    missing = parent_ids - out.keys()
    if missing:
        raise SystemExit(f"parents not found in data/chunks: {sorted(missing)[:5]}")
    return out


def main() -> None:
    rng = random.Random(SEED)
    questions = {q["qid"]: q for q in load_jsonl(ROOT / "data/bench/questions.jsonl")}
    audit = {a["qid"]: a for a in load_jsonl(ROOT / "data/bench/analysis/golden-audit.jsonl")}
    pool = {p["qid"]: p for p in load_jsonl(ROOT / "data/bench/analysis/golden-audit-pool.jsonl")}

    pairs: list[tuple[str, str, str]] = []  # (set, qid, parent_id)
    for qid in sorted(audit):
        for pid in audit[qid]["extra_positive_parents"]:
            pairs.append(("extra", qid, pid))
        for pid in audit[qid]["wrong_positive_parents"]:
            pairs.append(("wrong", qid, pid))

    pos_candidates = [
        (qid, pid)
        for qid in sorted(questions)
        if audit[qid]["verdict"] not in FLAGGED
        for pid in questions[qid]["positive_parents"]
        if pid not in audit[qid]["wrong_positive_parents"]
    ]
    pairs += [("pos", qid, pid) for qid, pid in rng.sample(pos_candidates, 60)]

    neg_candidates = []
    for qid in sorted(pool):
        labelled = set(questions[qid]["positive_parents"]) | set(audit[qid]["extra_positive_parents"])
        top = [c["parent_id"] for c in pool[qid]["pool"][:10] if c["parent_id"] not in labelled]
        if top:
            neg_candidates.append((qid, top))
    for qid, top in rng.sample(neg_candidates, 60):
        pairs.append(("neg", qid, rng.choice(top)))

    seen = set()
    for _, qid, pid in pairs:
        if (qid, pid) in seen:
            raise SystemExit(f"duplicate pair {qid} {pid}")
        seen.add((qid, pid))

    texts = parent_texts({pid for _, _, pid in pairs})
    rng.shuffle(pairs)

    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "sheet.jsonl", "w") as sheet, open(OUT / "key.jsonl", "w") as key:
        for set_name, qid, pid in pairs:
            pair_id = "v" + hashlib.sha256(f"{SEED}|{qid}|{pid}".encode()).hexdigest()[:10]
            title, text = texts[pid]
            if len(text) > MAX_PASSAGE_CHARS:
                text = text[:MAX_PASSAGE_CHARS] + "\n[passage truncated]"
            sheet.write(json.dumps({"id": pair_id, "question": questions[qid]["query"],
                                    "book": title, "passage": text}) + "\n")
            key.write(json.dumps({"id": pair_id, "set": set_name, "qid": qid,
                                  "parent_id": pid}) + "\n")
    counts = {name: sum(1 for p in pairs if p[0] == name) for name in ("extra", "wrong", "pos", "neg")}
    print(f"{len(pairs)} pairs {counts} -> {OUT}")


if __name__ == "__main__":
    main()
