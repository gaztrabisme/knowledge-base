"""Build the blind work-matching review packet (U3) from selection.json.

The packet shows each multi-language group's titles and opening text, with no work_id and
no match basis, in shuffled order. `key.json` (kept out of the reviewer's folder) maps
group numbers back to work_ids.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = Path("/Users/GaryT/Documents/books/falun-dafa-pdf-archive")
PHASE_B = ROOT / "data" / "philosophy" / "phase-b"


def excerpt(path: Path, limit: int = 700) -> str:
    text = ""
    with pymupdf.open(str(path)) as doc:
        for page in doc:
            text += " ".join(page.get_text().split()) + " "
            if len(text) >= limit:
                break
    return text[:limit].strip()


def main(out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ARCHIVE / "manifest.json").read_text(encoding="utf-8"))
    outputs = {o["output_id"]: o for o in manifest["outputs"]}
    selection = json.loads((PHASE_B / "selection.json").read_text(encoding="utf-8"))
    groups = [g for g in selection["groups"] if g["work_id"] != "zhuan-falun"]
    multi = [g for g in groups if len(g["languages"]) > 1]
    single = [g for g in groups if len(g["languages"]) == 1]
    random.Random(20260930).shuffle(multi)
    key, rows = {}, []
    for number, group in enumerate(multi, 1):
        key[number] = group["work_id"]
        langs = {}
        for lang, record in group["languages"].items():
            entry = {"title": group["titles"][lang]}
            if record["status"] == "included":
                path = ARCHIVE / outputs[record["output_id"]]["pdf_path"] if record.get("output_id") else Path(record["file"])
                entry["pages"] = record.get("pages")
                entry["opening_text"] = excerpt(path)
            else:
                entry["opening_text"] = None
                entry["note"] = f"no usable text for this language ({record['status']})"
            langs[lang] = entry
        rows.append({"group": number, "kind": group["kind"], "languages": langs})
    (out / "groups.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    singles = []
    for group in single:
        (lang, record), = group["languages"].items()
        entry = {"language": lang, "kind": group["kind"], "title": group["titles"][lang]}
        if record["status"] == "included":
            path = ARCHIVE / outputs[record["output_id"]]["pdf_path"] if record.get("output_id") else Path(record["file"])
            entry["opening_text"] = excerpt(path, 300)
        singles.append(entry)
    (out / "singles.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in singles), encoding="utf-8")
    (PHASE_B / "work-match-key.json").write_text(json.dumps(key, indent=1), encoding="utf-8")
    print(f"multi-language groups {len(rows)}, single-language works {len(singles)}")


if __name__ == "__main__":
    main(sys.argv[1])
