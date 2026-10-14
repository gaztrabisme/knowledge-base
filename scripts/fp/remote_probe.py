"""Read-only v10 evidence probe. Send on SSH stdin; never install it remotely.

Only the standard library, file reads, Docker inspect and Qdrant GET are used.
No KB/model imports, GPU calls, point writes, container starts or remote output files.
"""
import hashlib
import json
import platform
import subprocess
import sys
import urllib.request
from pathlib import Path


def fingerprint(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return {"sha256": digest.hexdigest(), "bytes": path.stat().st_size}


def api(path):
    with urllib.request.urlopen("http://127.0.0.1:6333" + path, timeout=15) as response:
        return json.load(response)


def probe(root):
    manifest = json.loads((root / "frozen/manifest.json").read_text())
    paths = {"frozen/manifest.json", "m1c/mapping.json", "scripts/freeze_v10.py",
             "scripts/run_gate.py", "gate/reranker-model.json"}
    paths.update("frozen/" + name for name in manifest["frozen_files_sha256"])
    controls = {}
    for name, query in manifest["queries"].items():
        paths.add(query["path"])
        for suffix in ["json", "jsonl", "meta.json"]:
            paths.add(f"gate/v10-{name}.{suffix}")
        meta = json.loads((root / f"gate/v10-{name}.meta.json").read_text())
        paths.update(meta["identity"]["code_sha256"])
        labels = [json.loads(line) for line in (root / query["path"]).read_text().splitlines()]
        rows = [json.loads(line) for line in (root / f"gate/v10-{name}.jsonl").read_text().splitlines()]
        assert len(labels) == len(rows) == query["count"]
        assert [x["query"] for x in labels] == [x["query"] for x in rows]
        assert len({x["query"] for x in rows}) == len(rows)
        result = json.loads((root / f"gate/v10-{name}.json").read_text())
        assert result["report"]["n_queries"] == query["count"]
        controls[name] = {"count": len(rows), "identity": meta["identity"],
                          "aggregate": result["report"]["aggregate"],
                          "output_sha256": meta["output_sha256"],
                          "per_query_sha256": meta["per_query_sha256"]}
    paths.add("kb/data/gate-v10/sanity-plan.jsonl")
    paths.update(["m1c/kb/data/chunks/postgresql-14-internals.json", "m1b/plan/manifest.json", "m1b/gate/audit-current.json", "m1c/scripts/map_labels.py"])
    paths.update(str(p.relative_to(root)) for p in (root / "m1c/labels").glob("*.jsonl"))
    models = {}
    for model in ["jinaai/jina-embeddings-v5-text-small-retrieval", "cross-encoder/ettin-reranker-150m-v1"]:
        directory = root / "hf-cache/hub" / ("models--" + model.replace("/", "--")) / "snapshots"
        revisions = sorted(p.name for p in directory.iterdir() if p.is_dir())
        assert len(revisions) == 1, f"Ambiguous cached revision: {model}"
        snapshot = directory / revisions[0]
        assert any(p.is_file() for p in snapshot.iterdir()), f"Empty model: {model}"
        files = [p for p in snapshot.rglob("*") if p.is_file()]
        # Hash weights too: this proves cached assets, without loading a model.
        paths.update(str(p.relative_to(root)) for p in files)
        models[model] = {"revision": revisions[0], "snapshot": str(snapshot.relative_to(root)),
                         "revision_basis": "single offline M1 cache snapshot; gate runner sets HF_HUB_OFFLINE=1"}
    sparse = root / "cache/fastembed/models--Qdrant--bm25"
    revision = (sparse / "refs/main").read_text().strip()
    paths.add(str((sparse / "refs/main").relative_to(root)))
    paths.update(str(p.relative_to(root)) for p in (sparse / "snapshots" / revision).iterdir() if p.is_file())
    implementation = root / "venv/lib/python3.12/site-packages/fastembed/sparse/bm25.py"
    paths.add(str(implementation.relative_to(root)))
    models["Qdrant/bm25"] = {"revision": revision, "implementation": str(implementation.relative_to(root)),
                              "package_version": controls["hard"]["identity"]["packages"]["fastembed"]}
    hashes = {name: fingerprint(root / name) for name in sorted(paths)}
    for name, expected in manifest["frozen_files_sha256"].items():
        assert hashes["frozen/" + name]["sha256"] == expected, f"Frozen drift: {name}"
    for name, query in manifest["queries"].items():
        assert hashes[query["path"]]["sha256"] == query["sha256"]
        control = controls[name]
        assert hashes[f"gate/v10-{name}.json"]["sha256"] == control["output_sha256"]
        assert hashes[f"gate/v10-{name}.jsonl"]["sha256"] == control["per_query_sha256"]
        assert hashes["frozen/manifest.json"]["sha256"] == control["identity"]["frozen_manifest_sha256"]
        for path, digest in control["identity"]["code_sha256"].items():
            assert hashes[path]["sha256"] == digest, f"Gate code drift: {path}"
    mapping = json.loads((root / "m1c/mapping.json").read_text())
    assert hashes["frozen/postgresql-14-internals.jsonl"]["sha256"] == mapping["old_file_sha256"]
    assert hashes["m1c/kb/data/chunks/postgresql-14-internals.json"]["sha256"] == mapping["current_file_sha256"]
    assert hashes["m1b/plan/manifest.json"]["sha256"] == mapping["m1b_manifest_sha256"]
    assert hashes["m1b/gate/audit-current.json"]["sha256"] == mapping["m1b_audit_sha256"]
    for name, label in mapping["labels"].items():
        for variant in ["original", "remapped"]:
            assert hashes["m1c/" + label[variant + "_path"]]["sha256"] == label[variant + "_sha256"]
    redirects = {old: {key: value[key] for key in ["status", "new_ids", "coverage_ratio"]}
                 for old, value in mapping["parents"].items()}
    os_release = dict(line.split("=", 1) for line in Path("/etc/os-release").read_text().splitlines() if "=" in line)
    machine = {"os": os_release["PRETTY_NAME"].strip('"'), "kernel": platform.release(),
               "architecture": platform.machine(), "python_system": platform.python_version(),
               "python_gate": subprocess.check_output([str(root / "venv/bin/python"), "--version"], text=True).strip(),
               "qdrant": {key: api("/")[key] for key in ["version", "commit"]},
               "container": subprocess.check_output(["docker", "inspect", "--format",
                   "{{.Config.Image}} {{.Image}}", "kb-qdrant"], text=True).strip()}
    collection = api("/collections/developer_knowledge_v10")["result"]
    return {"files": hashes, "machine": machine, "models": models, "controls": controls,
            "collection": {"name": manifest["control"], "points_count": collection["points_count"],
                           "config": collection["config"]},
            "aliases": api("/aliases")["result"]["aliases"],
            "membership": {"sha256": manifest["membership_sha256"], "points": manifest["points"],
                           "sources": len(manifest["books"]), "per_source_counts": manifest["books"],
                           "source_children_excluded": manifest["source_children_excluded"],
                           "source_children_missing_from_files": manifest["source_children_missing_from_files"],
                           "payload_source_differences": manifest["payload_source_differences"]},
            "redirect": {"method": mapping["method"], "threshold": mapping["threshold"],
                         "old_file_sha256": mapping["old_file_sha256"],
                         "current_file_sha256": mapping["current_file_sha256"],
                         "touched_query_counts": mapping["touched_query_counts"], "labels": mapping["labels"], "parents": redirects}}


if __name__ == "__main__":
    print(json.dumps(probe(Path(sys.argv[1]).expanduser()), sort_keys=True))
