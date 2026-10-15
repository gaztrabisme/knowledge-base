#!/usr/bin/env python3
"""Offline freeze checks only: stdlib, no services, retrieval, tokenizers or models.

The local schema uses a deliberately small JSON Schema subset, checked below.
Human approval provenance and pre-results chronology require an external receipt.
"""

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import tempfile
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE / "manifest.schema.json"


class Invalid(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise Invalid(message)


def pairs(items):
    result = {}
    for key, value in items:
        need(key not in result, "duplicate JSON object key")
        result[key] = value
    return result


def reject_constant(_):
    raise Invalid("non-finite JSON number")


def finite_float(text):
    value = float(text)
    need(math.isfinite(value), "non-finite JSON number")
    return value


def decode(text):
    return json.loads(text, object_pairs_hook=pairs, parse_constant=reject_constant,
                      parse_float=finite_float)


def same(a, b):
    # JSON numbers compare numerically; booleans must not masquerade as 0/1.
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def schema_supported(node):
    supported = {"$schema", "$id", "$ref", "$defs", "title", "description", "type",
                 "const", "enum", "properties", "required", "additionalProperties",
                 "items", "minItems", "maxItems", "uniqueItems", "minLength",
                 "maxLength", "pattern", "minimum", "maximum"}
    need(not set(node) - supported, "local schema uses unsupported keywords")
    for key in ("$defs", "properties"):
        for child in node.get(key, {}).values():
            schema_supported(child)
    if "items" in node:
        schema_supported(node["items"])


def check(value, node, root, where="manifest"):
    if "$ref" in node:
        ref = node["$ref"]
        need(ref.startswith("#/$defs/"), "only local schema definitions are supported")
        check(value, root["$defs"][ref.removeprefix("#/$defs/")], root, where)
    types = {"object": lambda x: isinstance(x, dict), "array": lambda x: isinstance(x, list),
             "string": lambda x: isinstance(x, str), "integer": lambda x: type(x) is int,
             "null": lambda x: x is None}
    if "type" in node:
        wanted = node["type"] if isinstance(node["type"], list) else [node["type"]]
        need(all(t in types for t in wanted), "unsupported schema type")
        need(any(types[t](value) for t in wanted), f"{where}: wrong type")
    if "const" in node:
        need(same(value, node["const"]), f"{where}: fixed value changed")
    if "enum" in node:
        need(any(same(value, item) for item in node["enum"]), f"{where}: unapproved choice")
    if isinstance(value, dict):
        need(set(node.get("required", [])) <= value.keys(), f"{where}: required field missing")
        properties = node.get("properties", {})
        if node.get("additionalProperties") is False:
            need(value.keys() <= properties.keys(), f"{where}: undeclared field")
        for key, child in properties.items():
            if key in value:
                check(value[key], child, root, f"{where}.{key}")
    if isinstance(value, list):
        need(len(value) >= node.get("minItems", 0), f"{where}: too few items")
        need(len(value) <= node.get("maxItems", len(value)), f"{where}: too many items")
        if node.get("uniqueItems"):
            need(all(not same(x, y) for i, x in enumerate(value) for y in value[:i]),
                 f"{where}: duplicate item")
        if "items" in node:
            for i, item in enumerate(value):
                check(item, node["items"], root, f"{where}[{i}]")
    if isinstance(value, str):
        need(len(value) >= node.get("minLength", 0), f"{where}: empty/short string")
        need(len(value) <= node.get("maxLength", len(value)), f"{where}: string too long")
        if "pattern" in node:
            need(re.search(node["pattern"], value) is not None, f"{where}: invalid syntax")
    if type(value) in (int, float):
        need(value >= node.get("minimum", value), f"{where}: below minimum")
        need(value <= node.get("maximum", value), f"{where}: above maximum")


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def local_file(base, raw):
    need("\\" not in raw and not raw.startswith("/") and
         all(p not in ("", ".", "..") for p in raw.split("/")), "unsafe artifact path")
    target = (base / raw).resolve(strict=True)
    need(target.is_relative_to(base), "artifact escapes freeze directory")
    need(target.is_file(), "artifact is not a regular file")
    return target


def named(value):
    need(isinstance(value, str) and value.strip() and not re.search(
        r"\b(tbd|todo|pending|placeholder|unknown|unset)\b|gary to choose", value, re.I),
        "model/reviewer choice is unresolved")
    return value.strip().casefold()


def rows(path):
    return [decode(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def check_questions(questions, labels, protocol):
    counts, by_id, groups, owners = {}, {}, {}, {}
    for question in questions:
        need(isinstance(question, dict), "question must be an object")
        qid, kind, group = (question.get(k) for k in ("qid", "class", "source_group_id"))
        need(all(isinstance(x, str) and x.strip() for x in (qid, kind, group)),
             "question identity/class/group missing")
        need(qid not in by_id and kind in protocol["question_counts"], "duplicate qid or unknown class")
        sources = question.get("source_ids")
        need(isinstance(sources, list) and sources and all(
            isinstance(s, str) and s.strip() for s in sources), "question source IDs missing")
        need(len(set(sources)) == len(sources), "duplicate source ID within question")
        for source in sources:
            need(source not in owners or owners[source] == group, "source split across groups")
            owners[source] = group
        by_id[qid] = question
        counts[kind] = counts.get(kind, 0) + 1
        groups.setdefault(group, set()).add(kind)
    need(counts == protocol["question_counts"], "question class counts differ from plan")
    need(len(groups) >= protocol["minimum_source_groups"], "too few independent source groups")
    need(all(kinds == set(counts) for kinds in groups.values()), "group missing a question class")
    need(len(owners) == sum(protocol["source_diversity"].values()), "source count differs from plan")
    seen, coverage = set(), {"answer": 0, "no_support": 0}
    for label in labels:
        need(isinstance(label, dict), "label must be an object")
        qid = label.get("qid")
        need(isinstance(qid, str) and qid in by_id and qid not in seen, "unmatched/duplicate label qid")
        question, state = by_id[qid], label.get("expected_state")
        need(label.get("source_group_id") == question["source_group_id"], "label group mismatch")
        need(state in ("answer", "no_support", "unknown"), "reference state unresolved")
        kind = question["class"]
        if kind in ("lookup", "relational"):
            need(state == "answer", "lookup/relational label must be answerable")
        if kind == "coverage":
            need(state in coverage, "coverage test contains an incomplete-scope fixture")
            coverage[state] += 1
        seen.add(qid)
    need(seen == by_id.keys(), "missing reference labels")
    need(coverage == {"answer": 12, "no_support": 12}, "coverage present/no-support counts differ")


def validate(path, expected=None):
    path = path.resolve(strict=True)
    if expected is not None:
        need(re.fullmatch(r"[a-f0-9]{64}", expected), "invalid expected manifest SHA-256")
        need(digest(path) == expected, "manifest differs from external registration digest")
    schema = decode(SCHEMA_PATH.read_text(encoding="utf-8"))
    schema_supported(schema)
    manifest = decode(path.read_text(encoding="utf-8"))
    check(manifest, schema, schema)
    approval, protocol = manifest["approval"], manifest["protocol"]
    approved = datetime.strptime(approval["approved_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    frozen = datetime.strptime(manifest["frozen_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    need(approved <= frozen, "approval occurs after freeze")
    budget = protocol["budget"]
    need(budget["counter"] == "python-tiktoken/0.14.0:cl100k_base:" + budget["vocabulary_sha256"],
         "counter/vocabulary fingerprint mismatch")
    for value in protocol["answer_model"].values():
        named(value)
    reviewers = protocol["reviewers"]
    curator, checker = named(reviewers["source_curator"]), named(reviewers["source_checker"])
    graders = [named(name) for name in reviewers["answer_reviewers"]]
    need(curator != checker, "source checker must be independent of curator")
    need(len(set(graders)) == 2 and named(reviewers["adjudicator"]) not in graders,
         "answer scorers must be distinct from each other and adjudicator")
    files, targets = manifest["files"], {}
    for role, artifact in files.items():
        target = local_file(path.parent, artifact["path"])
        need(target != path and target not in targets.values(), "artifact paths alias another role/manifest")
        need(target.stat().st_size == artifact["bytes"] and digest(target) == artifact["sha256"],
             f"{role}: artifact bytes/hash changed")
        targets[role] = target
    for role, current in (("schema", SCHEMA_PATH), ("validator", Path(__file__).resolve())):
        need(files[role]["sha256"] == digest(current), f"{role}: checker differs from frozen version")
    for role in ("plan", "configuration", "questions", "labels"):
        need(approval[role + "_sha256"] == files[role]["sha256"], f"{role}: approval hash mismatch")
    record = decode(targets["approval_record"].read_text(encoding="utf-8"))
    need(isinstance(record, dict) and same(record.get("approval"), approval) and
         same(record.get("pre_results"), manifest["pre_results"]), "approval record binding mismatch")
    need(isinstance(record.get("human_confirmation"), str) and record["human_confirmation"].strip(),
         "human approval evidence missing")
    config = decode(targets["configuration"].read_text(encoding="utf-8"))
    need(isinstance(config, dict) and same(config.get("protocol"), protocol), "configuration/protocol mismatch")
    check_questions(rows(targets["questions"]), rows(targets["labels"]), protocol)
    return manifest


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def seal_fixture(base, manifest):
    """Synthetic test helper; never used to issue a real study freeze."""
    for artifact in manifest["files"].values():
        path = base / artifact["path"]
        artifact.update(sha256=digest(path), bytes=path.stat().st_size)
    for role in ("plan", "configuration", "questions", "labels"):
        manifest["approval"][role + "_sha256"] = manifest["files"][role]["sha256"]
    write_json(base / "approval_record", {"approval": manifest["approval"],
               "pre_results": manifest["pre_results"],
               "human_confirmation": "FICTIONAL self-test metadata; not Gary's approval."})
    artifact = manifest["files"]["approval_record"]
    artifact.update(sha256=digest(base / "approval_record"), bytes=(base / "approval_record").stat().st_size)
    write_json(base / "manifest.json", manifest)


def fixture(base, schema):
    fields = schema["properties"]["protocol"]["properties"]
    protocol = {k: copy.deepcopy(v["const"]) for k, v in fields.items() if "const" in v}
    protocol.update(maximum_lookup_losses=0,
        budget={k: copy.deepcopy(v["const"]) for k, v in fields["budget"]["properties"].items() if "const" in v},
        execution={k: copy.deepcopy(v["const"]) for k, v in fields["execution"]["properties"].items() if "const" in v},
        answer_model={"id": "synthetic-local", "revision": "test-revision", "runtime": "test-runtime",
                      "chat_template_sha256": "a" * 64},
        reviewers={"source_curator": "Gary", "source_checker": "Test Checker",
                   "answer_reviewers": ["Test Checker", "Test Scorer"], "adjudicator": "Gary"})
    protocol["budget"].update(vocabulary_sha256="a" * 64, counter="python-tiktoken/0.14.0:cl100k_base:" + "a" * 64)
    protocol["execution"].update(model_seed=None, python_version="3.11.0")
    manifest = {"schema_version": "fp-answer-benefit-manifest/v1", "run_id": "synthetic-only",
        "phase": "pre-results", "frozen_at": "2026-10-15T01:00:00Z",
        "approval": {"approved_by": "Gary", "approved_at": "2026-10-15T00:00:00Z"},
        "pre_results": {"answers_generated": False, "retrieval_run": False, "scores_seen": False},
        "protocol": protocol, "files": {}}
    for role in schema["properties"]["files"]["required"]:
        (base / role).write_text("synthetic metadata only\n", encoding="utf-8")
        manifest["files"][role] = {"path": role}
    (base / "schema").write_bytes(SCHEMA_PATH.read_bytes())
    (base / "validator").write_bytes(Path(__file__).read_bytes())
    questions, labels = [], []
    for kind in protocol["question_counts"]:
        for i in range(24):
            qid, group = f"{kind}-{i:02}", f"group-{i % 14:02}"
            questions.append({"qid": qid, "class": kind, "source_group_id": group,
                              "source_ids": [f"source-{i % 14:02}"]})
            labels.append({"qid": qid, "source_group_id": group,
                           "expected_state": "no_support" if kind == "coverage" and i >= 12 else "answer"})
    for role, data in (("questions", questions), ("labels", labels)):
        (base / role).write_text("".join(json.dumps(r) + "\n" for r in data), encoding="utf-8")
    write_json(base / "configuration", {"protocol": protocol})
    seal_fixture(base, manifest)
    return manifest


def self_test():
    schema = decode(SCHEMA_PATH.read_text(encoding="utf-8"))
    cases = [
        ("pending approval", lambda m, b: m["approval"].update(approved_by="pending")),
        ("missing artifact role", lambda m, b: m["files"].pop("prompts")),
        ("unknown result field", lambda m, b: m.update(results={})),
        ("answers already generated", lambda m, b: m["pre_results"].update(answers_generated=True)),
        ("boolean attestation impostor", lambda m, b: m["pre_results"].update(scores_seen=0)),
        ("wrong cap", lambda m, b: m["protocol"]["budget"].update(tokens_per_question_arm=6001)),
        ("wrong tokenizer", lambda m, b: m["protocol"]["budget"].update(package="tiktoken==0.13.0")),
        ("wrong renderer", lambda m, b: m["protocol"]["budget"].update(renderer_revision="other")),
        ("fingerprint mismatch", lambda m, b: m["protocol"]["budget"].update(vocabulary_sha256="b" * 64)),
        ("unset harm tolerance", lambda m, b: m["protocol"].update(maximum_lookup_losses=None)),
        ("boolean harm tolerance", lambda m, b: m["protocol"].update(maximum_lookup_losses=False)),
        ("invalid harm tolerance", lambda m, b: m["protocol"].update(maximum_lookup_losses=25)),
        ("model placeholder", lambda m, b: m["protocol"]["answer_model"].update(id="GARY TO CHOOSE")),
        ("same scorers", lambda m, b: m["protocol"]["reviewers"].update(answer_reviewers=["A", "a"])),
        ("post-freeze approval", lambda m, b: m["approval"].update(approved_at="2026-10-16T00:00:00Z")),
        ("impossible date", lambda m, b: m.update(frozen_at="2026-02-30T01:00:00Z")),
        ("traversal", lambda m, b: m["files"]["plan"].update(path="../outside")),
        ("absolute path", lambda m, b: m["files"]["plan"].update(path="/tmp/outside")),
        ("aliased roles", lambda m, b: m["files"].update(prompts=copy.deepcopy(m["files"]["plan"]))),
        ("bad approval binding", lambda m, b: m["approval"].update(plan_sha256="0" * 64)),
        ("tampered artifact", lambda m, b: (b / "prompts").write_text("changed", encoding="utf-8")),
        ("missing file", lambda m, b: (b / "graph_snapshot").unlink()),
        ("bad byte count", lambda m, b: m["files"]["plan"].update(bytes=1)),
    ]
    passed = 0
    for malformed in ('{"x": NaN}', '{"x": Infinity}', '{"x": 1e999}'):
        try:
            decode(malformed)
        except Invalid:
            passed += 1
        else:
            raise Invalid("self-test accepted a non-finite JSON number")
    with tempfile.TemporaryDirectory(prefix="ab0-manifest-test-") as tmp:
        base = Path(tmp)
        for index, (name, mutate) in enumerate([(None, None)] + cases):
            case = base / str(index)
            case.mkdir()
            manifest = fixture(case, schema)
            if mutate is None:
                validate(case / "manifest.json", digest(case / "manifest.json"))
                passed += 1
                continue
            mutate(manifest, case)
            write_json(case / "manifest.json", manifest)
            try:
                validate(case / "manifest.json")
            except (Invalid, ValueError, OSError):
                passed += 1
            else:
                raise Invalid(f"self-test did not reject: {name}")
        # Rehashed metadata exercises semantic checks, beyond mere hash mismatch.
        for name in ("question count", "missing label", "split source", "coverage state",
                     "configuration mismatch", "approval evidence", "external symlink",
                     "registration digest", "duplicate JSON key"):
            case = base / name.replace(" ", "-")
            case.mkdir()
            manifest = fixture(case, schema)
            if name in ("question count", "split source"):
                data = rows(case / "questions")
                if name == "question count":
                    data.pop()
                else:
                    data[0]["source_ids"] = ["source-01"]
                (case / "questions").write_text("".join(json.dumps(r) + "\n" for r in data), encoding="utf-8")
            elif name in ("missing label", "coverage state"):
                data = rows(case / "labels")
                if name == "missing label":
                    data.pop()
                else:
                    next(r for r in data if r["qid"].startswith("coverage"))["expected_state"] = "unknown"
                (case / "labels").write_text("".join(json.dumps(r) + "\n" for r in data), encoding="utf-8")
            elif name == "configuration mismatch":
                write_json(case / "configuration", {"protocol": {}})
            seal_fixture(case, manifest)
            if name == "approval evidence":
                write_json(case / "approval_record", {"approval": {}, "human_confirmation": ""})
                artifact = manifest["files"]["approval_record"]
                artifact.update(sha256=digest(case / "approval_record"), bytes=(case / "approval_record").stat().st_size)
                write_json(case / "manifest.json", manifest)
            if name == "external symlink":
                (case / "prompts").unlink()
                (base / "outside").write_text("synthetic metadata only\n", encoding="utf-8")
                (case / "prompts").symlink_to(base / "outside")
            if name == "duplicate JSON key":
                text = (case / "manifest.json").read_text(encoding="utf-8")
                (case / "manifest.json").write_text(text.replace('{', '{"phase":"pre-results",', 1), encoding="utf-8")
            try:
                validate(case / "manifest.json", "0" * 64 if name == "registration digest" else None)
            except (Invalid, ValueError, OSError):
                passed += 1
            else:
                raise Invalid(f"self-test did not reject: {name}")
    print(f"PASS: {passed} offline synthetic manifest checks; no study answers or results created")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", nargs="?", type=Path)
    parser.add_argument("--expected-sha256", help="digest from the independent pre-results registration receipt")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        if args.manifest or args.expected_sha256:
            parser.error("--self-test cannot be combined with manifest arguments")
    elif args.manifest is None:
        parser.error("a manifest path or --self-test is required")
    try:
        if args.self_test:
            self_test()
        else:
            validate(args.manifest, args.expected_sha256)
            print(f"PASS: {args.manifest.resolve()} — freeze structure and artifact hashes verified")
            print("External registration digest " + ("matched" if args.expected_sha256 else "not supplied") +
                  "; human approval provenance and run chronology require the later checker")
    except (ValueError, OSError, KeyError, TypeError) as exc:
        # Do not echo JSON values, approval text, configuration contents or credentials.
        detail = str(exc) if isinstance(exc, Invalid) else type(exc).__name__
        print(f"INVALID: {detail}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
