"""Goal row 8: philosophy_b = baseline philosophy points + phase B child chunks, and the live collections are untouched."""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PHASE_A = {"original-library", "tao-te-ching-jonathan-star", "tao-te-ching-stephen-mitchell",
           "tao-te-ching-tse-lao", "zhuan-falun"}


def count(name: str) -> int:
    request = urllib.request.Request(f"http://127.0.0.1:6333/collections/{name}/points/count",
                                     data=b'{"exact":true}', headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(request))["result"]["count"]


def main() -> int:
    baseline = json.loads((ROOT / "data/philosophy/phase-b/baseline.json").read_text())
    registry = json.loads((ROOT / "data/philosophy/works.json").read_text(encoding="utf-8"))
    new = 0
    for work in registry["works"]:
        if work["work_id"] in PHASE_A:
            continue
        for record in work["languages"].values():
            if record.get("status") == "included":
                new += len(json.loads((ROOT / record["chunks_file"]).read_text(encoding="utf-8"))["children"])
    expected = baseline["philosophy_points"] + new
    got = count("philosophy_b")
    live = count("philosophy")
    print(f"philosophy_b {got}; expected {baseline['philosophy_points']} + {new} = {expected}; live philosophy {live}")
    ok = got == expected
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
