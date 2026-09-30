from __future__ import annotations

import importlib
import json
import os

from scripts import eval_philosophy
from knowledge_base.philosophy import search as philosophy_search


def test_custom_eval_file_allows_short_rows_and_drops_all_filters(tmp_path) -> None:
    eval_path = tmp_path / "phase-b.jsonl"
    original = {
        "group": "en",
        "query": "A custom test query",
        "target_chunk_id": "target-1",
        "work_filter": "one-work",
        "language_filter": "en",
    }
    eval_path.write_text(json.dumps(original) + "\n", encoding="utf-8")

    rows, is_default = eval_philosophy._load_eval_rows(eval_path, no_filters=True)

    assert is_default is False
    assert len(rows) == 1
    assert rows[0]["work_filter"] is None
    assert rows[0]["language_filter"] is None
    assert original["work_filter"] == "one-work"
    assert original["language_filter"] == "en"


def test_eval_diagnostics_record_hit_miss_and_top_ten_ids(tmp_path) -> None:
    rows = [
        {"group": "en", "query": "hit", "target_chunk_id": "chunk-0"},
        {"group": "en", "query": "miss", "target_chunk_id": "absent"},
    ]

    def runner(row):
        return [{"chunk_id": f"chunk-{index}"} for index in range(12)]

    recall, diagnostics = eval_philosophy._evaluate(rows, runner)
    out_path = tmp_path / "nested" / "hits.json"
    eval_philosophy._write_diagnostics(out_path, diagnostics)

    assert recall == {"en": 0.5}
    assert [row["result"] for row in diagnostics] == ["hit", "miss"]
    assert diagnostics[0]["top10_chunk_ids"] == [f"chunk-{index}" for index in range(10)]
    assert json.loads(out_path.read_text(encoding="utf-8")) == diagnostics


def test_search_collection_env_override_and_default(monkeypatch) -> None:
    original = os.environ.get("KB_PHILOSOPHY_COLLECTION", "philosophy")
    with monkeypatch.context() as scoped:
        scoped.delenv("KB_PHILOSOPHY_COLLECTION", raising=False)
        assert importlib.reload(philosophy_search).COLLECTION == "philosophy"
        scoped.setenv("KB_PHILOSOPHY_COLLECTION", "philosophy_b")
        assert importlib.reload(philosophy_search).COLLECTION == "philosophy_b"
    assert importlib.reload(philosophy_search).COLLECTION == original
