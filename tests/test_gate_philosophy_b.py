from __future__ import annotations

import json
from pathlib import Path

import pytest
from qdrant_client import QdrantClient, models

from scripts import gate_philosophy_b as gate


@pytest.fixture
def local_qdrant(tmp_path: Path) -> tuple[QdrantClient, list[dict]]:
    client = QdrantClient(path=str(tmp_path / "qdrant-fixture"))
    for collection in ("live", "candidate_one_loss", "candidate_two_loss", "candidate_three_loss"):
        client.create_collection(
            collection_name=collection,
            vectors_config=models.VectorParams(size=2, distance=models.Distance.COSINE),
        )
    rows = []
    point_id = 1
    for group in gate.GROUPS:
        for index in range(3):
            target = f"{group}-{index}"
            rows.append({"group": group, "query": f"query {target}", "target_chunk_id": target})
            point = models.PointStruct(id=point_id, vector=[1.0, 0.0], payload={"child_id": target})
            client.upsert(collection_name="live", points=[point])
            for loss_count, collection in enumerate(
                ("candidate_one_loss", "candidate_two_loss", "candidate_three_loss"), start=1,
            ):
                if index >= loss_count:
                    client.upsert(collection_name=collection, points=[point])
            point_id += 1
    (tmp_path / "tiny-eval.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8",
    )
    rows = gate.read_jsonl(tmp_path / "tiny-eval.jsonl")
    yield client, rows
    client.close()


def _fixture_diagnostics(client: QdrantClient, collection: str, rows: list[dict]) -> list[dict]:
    diagnostics = []
    for index, row in enumerate(rows, 1):
        points, _ = client.scroll(
            collection_name=collection,
            scroll_filter=models.Filter(must=[models.FieldCondition(
                key="child_id", match=models.MatchValue(value=row["target_chunk_id"]),
            )]),
            limit=1,
            with_payload=True,
            with_vectors=False,
        )
        hit = bool(points)
        diagnostics.append({**row, "row": index, "hit": hit, "result": "hit" if hit else "miss"})
    return diagnostics


def test_filtered_gate_accepts_exactly_one_lost_query_per_group(local_qdrant: tuple[QdrantClient, list[dict]]) -> None:
    client, rows = local_qdrant
    live = _fixture_diagnostics(client, "live", rows)
    one_lost = _fixture_diagnostics(client, "candidate_one_loss", rows)
    two_lost = _fixture_diagnostics(client, "candidate_two_loss", rows)

    assert gate.compare_eval_runs(live, one_lost, 1)["passed"] is True
    assert gate.compare_eval_runs(live, two_lost, 1)["passed"] is False


def test_unfiltered_gate_accepts_exactly_two_lost_queries_per_group(local_qdrant: tuple[QdrantClient, list[dict]]) -> None:
    client, rows = local_qdrant
    live = _fixture_diagnostics(client, "live", rows)
    two_lost = _fixture_diagnostics(client, "candidate_two_loss", rows)
    three_lost = _fixture_diagnostics(client, "candidate_three_loss", rows)

    assert gate.compare_eval_runs(live, two_lost, 2)["passed"] is True
    assert gate.compare_eval_runs(live, three_lost, 2)["passed"] is False


def _sanity_fixture(hits_by_language: dict[str, int]) -> tuple[list[dict], list[dict]]:
    rows, diagnostics = [], []
    for language, hits in hits_by_language.items():
        for index in range(10):
            query = f"{language} query {index}"
            target = f"{language}-target-{index}"
            rows.append({"language": language, "query": query, "target_chunk_id": target})
            hit = index < hits
            diagnostics.append({"language": language, "query": query, "target_chunk_id": target, "hit": hit})
    return rows, diagnostics


def test_sanity_gate_accepts_exactly_080_overall_and_070_per_language() -> None:
    rows, diagnostics = _sanity_fixture({"en": 7, "vi": 9, "zh-Hans": 8, "zh-Hant": 8})
    result = gate.sanity_result(rows, diagnostics)
    assert result["overall"] == {"hits": 32, "total": 40}
    assert result["passed"] is True

    overall_below = _sanity_fixture({"en": 7, "vi": 8, "zh-Hans": 8, "zh-Hant": 8})
    assert gate.sanity_result(*overall_below)["passed"] is False
    language_below = _sanity_fixture({"en": 6, "vi": 10, "zh-Hans": 8, "zh-Hant": 8})
    assert gate.sanity_result(*language_below)["passed"] is False


def test_alignment_gate_accepts_exactly_36_of_40() -> None:
    rows = [{"verdict": "match" if index < 36 else "partial"} for index in range(40)]
    assert gate.alignment_result(rows) == {"passed": True, "matches": 36, "total": 40}
    rows[35] = {"verdict": "partial"}
    assert gate.alignment_result(rows)["passed"] is False


def test_chinese_text_gate_accepts_passed_or_derived_records() -> None:
    assert gate.chinese_text_result([
        {"text_check_passed": True, "derived": False},
        {"text_check_passed": False, "derived": True},
    ])["passed"] is True
    assert gate.chinese_text_result([{"text_check_passed": False, "derived": False}])["passed"] is False


def test_technical_gate_requires_same_ordered_top_ten_for_all_fifty_queries() -> None:
    before = [{"query": f"query {index}", "candidates": [{"parent_id": f"p-{index}-{rank}"} for rank in range(10)]}
              for index in range(50)]
    after = json.loads(json.dumps(before))
    assert gate.technical_result(before, after)["passed"] is True
    after[49]["candidates"][0]["parent_id"] = "different-parent"
    result = gate.technical_result(before, after)
    assert result["passed"] is False
    assert result["identical"] == 49


def test_report_lists_misses_and_alignment_history_and_ends_with_verdict(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    a_live, a_candidate, b_live, b_candidate = [], [], [], []
    for group in gate.GROUPS:
        for index in range(15):
            row = {"group": group, "query": f"{group} query {index}", "target_chunk_id": f"{group}-{index}", "hit": True}
            a_live.append(row)
            a_candidate.append(dict(row))
            b_live.append(row)
            b_candidate.append(dict(row))
    for name, rows in (("a-live", a_live), ("a-candidate", a_candidate), ("b-live", b_live), ("b-candidate", b_candidate)):
        (run_dir / f"{name}.json").write_text(json.dumps(rows), encoding="utf-8")

    sanity_rows, sanity_output = _sanity_fixture({"en": 7, "vi": 9, "zh-Hans": 8, "zh-Hant": 8})
    for index, row in enumerate(sanity_output):
        if not row["hit"]:
            row["result"] = "miss"
        row["row"] = index + 1
    gate.write_jsonl(run_dir / "sanity-b-filtered.jsonl", sanity_rows)
    (run_dir / "sanity-candidate.json").write_text(json.dumps(sanity_output), encoding="utf-8")
    gate.write_jsonl(run_dir / "alignment-sample.jsonl", [{"verdict": "match"} for _ in range(40)])
    history = run_dir / "alignment-review-history"
    gate.write_jsonl(history / "alignment-review-4.jsonl", [{"verdict": "match"} for _ in range(8)] + [{"verdict": "partial"}])
    (run_dir / "chinese-included-records.json").write_text(json.dumps([
        {"text_check_passed": True, "derived": False},
    ]), encoding="utf-8")
    technical = [{"query": f"tech {index}", "candidates": [{"parent_id": f"p-{index}-{rank}"} for rank in range(10)]}
                 for index in range(50)]
    gate.write_jsonl(run_dir / "tech-before.jsonl", technical)
    gate.write_jsonl(run_dir / "tech-after.jsonl", technical)

    report, failures = gate._render_report(run_dir)

    assert failures == []
    assert all(f"({letter}) " in report for letter in "abcdef")
    assert "en: en query 7 — target `en-target-7`" in report
    assert "alignment-review-4.jsonl: 8/9 match" in report
    assert report.rstrip().endswith("Verdict: PROMOTE")


def test_report_fails_loud_for_missing_and_malformed_measurements(tmp_path: Path) -> None:
    run_dir = tmp_path / "incomplete-run"
    run_dir.mkdir()
    (run_dir / "a-live.json").write_text("not-json", encoding="utf-8")

    report, failures = gate._render_report(run_dir)

    assert failures == list("abcdef")
    assert "unavailable" in report
    assert report.rstrip().endswith("Verdict: DO NOT PROMOTE — failing letters: a, b, c, d, e, f")


def test_candidate_command_set_uses_cpu_wrapper_and_artifact_paths() -> None:
    commands = gate.candidate_commands(gate.ARTIFACTS / "fixture-run")
    assert [item["name"] for item in commands] == [
        "a-live", "a-candidate", "b-live", "b-candidate", "c-candidate", "f-technical-after",
    ]
    assert all(item["args"][:2] == [".venv/bin/python", ".claude/plan-goal/verify/cpu.py"]
               for item in commands)
    assert "--report-out" in commands[-1]["args"]
