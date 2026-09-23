"""Reconcile golden sets against the LIVE corpus after sources are removed.

Like clean_golden_after_strip.py, but reads rows from git HEAD and takes
postgresql-14-internals ids from Qdrant: its on-disk re-chunk diverges from the
live index, so the disk ids would wrongly mark its labeled positives as dead.
"""
import glob, json, subprocess, sys
from pathlib import Path
from qdrant_client import QdrantClient, models

DIVERGENT = "postgresql-14-internals"
live_c, live_p = set(), set()
for f in glob.glob("data/chunks/*.json"):
    if Path(f).stem == DIVERGENT:
        continue
    for ch in json.load(open(f))["children"]:
        live_c.add(ch["child_id"]); live_p.add(ch["parent_id"])
c = QdrantClient(url="http://127.0.0.1:6333", timeout=120)
flt = models.Filter(must=[models.FieldCondition(key="book", match=models.MatchValue(value=DIVERGENT))])
off = None
while True:
    pts, off = c.scroll("developer_knowledge", scroll_filter=flt, limit=1000, offset=off,
                        with_payload=["child_id", "parent_id"], with_vectors=False)
    for p in pts:
        live_c.add(p.payload["child_id"]); live_p.add(p.payload["parent_id"])
    if off is None:
        break

for path in sys.argv[1:]:
    rows = [json.loads(l) for l in subprocess.check_output(["git", "show", f"HEAD:{path}"], text=True).splitlines()]
    kept, dropped, pruned = [], [], 0
    for r in rows:
        pos = [x for x in r.get("positive_child_ids", []) if x in live_c]
        if not pos:
            dropped.append(r.get("book")); continue
        if len(pos) != len(r.get("positive_child_ids", [])): pruned += 1
        r["positive_child_ids"] = pos
        if "relevance_grades" in r:
            r["relevance_grades"] = {k: g for k, g in r["relevance_grades"].items() if k in live_p}
        if "hard_negative_child_ids" in r:
            r["hard_negative_child_ids"] = [x for x in r["hard_negative_child_ids"] if x in live_c]
        kept.append(r)
    Path(path).write_text("".join(json.dumps(r) + "\n" for r in kept))
    print(f"{path}: {len(rows)} -> {len(kept)}  dropped {dropped}  pruned {pruned}")
