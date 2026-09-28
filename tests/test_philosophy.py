"""CPU-only contract tests for the separate philosophy corpus."""

from __future__ import annotations

import inspect
import importlib.util
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace

import pytest
from qdrant_client import QdrantClient, models

from knowledge_base import server
from knowledge_base.philosophy import search as philosophy_search
from knowledge_base.philosophy.sparse import text_to_sparse_vector, tokenize
from knowledge_base.philosophy.textcheck import check_text


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "philosophy" / "works.json"
PHILOSOPHY_CHUNKS = ROOT / "data" / "chunks" / "philosophy"


def test_sparse_tokenizer_handles_english_vietnamese_and_cjk() -> None:
    # Latin-script terms are lowercased; Vietnamese marks remain part of the token.
    en_upper = text_to_sparse_vector("WISDOM wisdom")
    en_lower = text_to_sparse_vector("wisdom wisdom")
    assert en_upper.indices == en_lower.indices
    assert en_upper.values == en_lower.values
    assert len(en_upper.indices) == 1
    assert en_upper.values[0] == pytest.approx(2.0)

    vi_marked = text_to_sparse_vector("Trí tuệ")
    vi_unmarked = text_to_sparse_vector("Tri tue")
    assert vi_marked.indices
    assert vi_marked.indices != vi_unmarked.indices

    # Four CJK characters produce four unigrams and three adjacent bigrams.
    zh = text_to_sparse_vector("天地玄黃")
    assert len(zh.indices) == 7
    assert len(zh.indices) == len(set(zh.indices))
    assert all(isinstance(index, int) and index >= 0 for index in zh.indices)
    assert all(value > 0 for value in zh.values)


def test_sparse_vector_normalizes_traditional_and_simplified_chinese() -> None:
    traditional = text_to_sparse_vector("天地玄黃，宇宙洪荒。")
    simplified = text_to_sparse_vector("天地玄黄，宇宙洪荒。")

    assert traditional.indices == simplified.indices
    assert traditional.values == simplified.values


def test_remote_and_query_tokenizers_agree_for_english_vietnamese_and_chinese() -> None:
    scripts = ROOT / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    spec = importlib.util.spec_from_file_location(
        "remote_index_philosophy", scripts / "remote_index_philosophy.py",
    )
    assert spec and spec.loader
    remote = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(remote)

    for sample in (
        "Wisdom and wisdom",
        "Trí tuệ trở về, trí tuệ",
        "轉法輪，道德經，道可道，非常道。",
    ):
        assert tokenize(sample) == remote.tokenize(sample)
        local_vector = text_to_sparse_vector(sample)
        remote_vector = remote.sparse_vector(sample)
        assert local_vector.indices == remote_vector.indices
        assert local_vector.values == remote_vector.values


def test_chinese_textcheck_detects_garble_and_accepts_clean_text() -> None:
    garbled = check_text("龘鱻麤", "zh-Hans")
    clean = check_text("道德經，道可道，非常道。", "zh-Hant")

    assert garbled.outside_share > clean.outside_share
    assert garbled.outside_share > 0.5
    assert garbled.passed is False
    assert clean.outside_share == 0
    assert clean.passed is True


def _registry_works() -> list[dict]:
    raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    works = raw.get("works", raw) if isinstance(raw, dict) else raw
    if isinstance(works, dict):
        return [
            ({"work_id": key, **value} if isinstance(value, dict) else {"work_id": key})
            for key, value in works.items()
        ]
    assert isinstance(works, list), "works.json must contain a works list or mapping"
    return works


def _title_blob(work: dict) -> str:
    titles = work.get("titles", work.get("title", ""))
    if isinstance(titles, dict):
        titles = " ".join(str(value) for value in titles.values())
    blob = f"{work.get('work_id', '')} {titles}".casefold()
    return blob.replace("-", " ").replace("_", " ")


def _languages(work: dict) -> dict[str, dict]:
    languages = work.get("languages", {})
    if isinstance(languages, dict):
        return languages
    if isinstance(languages, list):
        return {
            str(item.get("lang", item.get("language"))): item
            for item in languages
            if isinstance(item, dict)
        }
    return {}


def _is_included(language_record: dict) -> bool:
    return str(language_record.get("status", "included")).casefold() not in {
        "skipped", "excluded", "failed", "unavailable",
    }


def _child_metadata(child: dict) -> dict:
    return {**child.get("metadata", {}), **child}


def _load_chunk_file(work_id: str, lang: str) -> tuple[Path, list[dict]]:
    path = PHILOSOPHY_CHUNKS / f"{work_id}.{lang}.json"
    assert path.is_file(), f"Missing philosophy chunk file: {path.name}"
    payload = json.loads(path.read_text(encoding="utf-8"))
    children = payload.get("children", [])
    assert children, f"No child chunks in {path.name}"
    return path, [_child_metadata(child) for child in children]


def _markdown_sections(path: Path, prefix: str) -> dict[str, tuple[str, str]]:
    text = path.read_text(encoding="utf-8")
    matches = list(re.finditer(
        rf"(?m)^# (?P<key>{re.escape(prefix)}[^ ]*) — (?P<title>.*?)\s*$", text,
    ))
    return {
        match.group("key"): (
            match.group("title"),
            text[match.end():matches[index + 1].start() if index + 1 < len(matches) else len(text)].strip(),
        )
        for index, match in enumerate(matches)
    }


def _assert_section_keys(
    work_id: str, lang: str, expected: set[str], *, allow_named_front_sections: bool = False,
    allow_ttc_notes: bool = False,
) -> None:
    _, children = _load_chunk_file(work_id, lang)
    for child in children:
        assert child.get("work_id") == work_id
        assert child.get("lang") == lang
        key = child.get("section_key")
        assert (key in expected
                or (allow_named_front_sections and str(key).startswith("zfl-"))
                or (allow_ttc_notes and key == "ttc-notes"))
        assert child.get("section_title")
        assert child.get("edition") or child.get("translator")
    found = {child["section_key"] for child in children}
    if allow_named_front_sections or allow_ttc_notes:
        assert expected <= found
    else:
        assert found == expected


def test_chunk_files_have_complete_alignment_keys_and_registry_links() -> None:
    works = _registry_works()
    by_id = {str(work["work_id"]): work for work in works}
    assert by_id, "works.json has no work records"

    ol_expected = {f"ol-{index:02d}" for index in range(1, 39)}
    ttc_expected = {f"ttc-{index:03d}" for index in range(1, 82)}
    zfl_expected = {f"zfl-L{index}" for index in range(1, 10)}

    original_library = [
        work for work in works if "original library" in _title_blob(work)
    ]
    assert len(original_library) == 1
    ol_work = original_library[0]
    ol_id = str(ol_work["work_id"])
    ol_langs = _languages(ol_work)
    assert {lang for lang, record in ol_langs.items() if _is_included(record)} >= {
        "en", "vi", "zh-Hant",
    }
    for lang, record in ol_langs.items():
        if _is_included(record):
            _assert_section_keys(ol_id, lang, ol_expected)
        else:
            assert record.get("status") == "skipped"

    tao_works = [
        work for work in works
        if str(work.get("work_id", "")).startswith("tao-te-ching-")
    ]
    assert len(tao_works) == 3, "Expected three independently aligned Tao Te Ching translations"
    for work in tao_works:
        work_id = str(work["work_id"])
        languages = _languages(work)
        included_languages = [lang for lang, record in languages.items() if _is_included(record)]
        assert len(included_languages) == 1
        lang = included_languages[0]
        # The supplied Tse Lao EPUB is actually Spanish; the source language is
        # recorded faithfully while retaining the same 81 aligned chapter keys.
        assert lang == ("es" if work_id == "tao-te-ching-tse-lao" else "en")
        _assert_section_keys(work_id, lang, ttc_expected, allow_ttc_notes=True)
        for lang, record in languages.items():
            if lang != "en" and _is_included(record):
                _assert_section_keys(work_id, lang, ttc_expected, allow_ttc_notes=True)

    zfl_works = [work for work in works if "zhuan falun" in _title_blob(work)]
    assert len(zfl_works) == 1
    zfl_work = zfl_works[0]
    zfl_id = str(zfl_work["work_id"])
    zfl_langs = _languages(zfl_work)
    assert {lang for lang, record in zfl_langs.items() if _is_included(record)} >= {
        "en", "vi", "zh-Hans", "zh-Hant",
    }
    assert {"zh-Hans", "zh-Hant"} <= set(zfl_langs)
    for lang, record in zfl_langs.items():
        if _is_included(record):
            _assert_section_keys(
                zfl_id, lang, zfl_expected, allow_named_front_sections=True
            )
        else:
            # A skipped candidate remains auditable in works.json and has no chunk file.
            assert record.get("status") == "skipped"
            assert not (PHILOSOPHY_CHUNKS / f"{zfl_id}.{lang}.json").exists()

    hant_record = zfl_langs["zh-Hant"]
    assert hant_record.get("derived") is True
    assert hant_record.get("edition") == "derived from zh-Hans via OpenCC s2t"
    rejected_pdf = hant_record.get("rejected_pdf", {})
    assert rejected_pdf.get("text_check", {}).get("passed") is False
    hant_path, hant_children = _load_chunk_file(zfl_id, "zh-Hant")
    hant_payload = json.loads(hant_path.read_text(encoding="utf-8"))
    assert hant_payload.get("derived") is True
    assert all(child.get("derived") is True for child in hant_children)
    assert all(parent["metadata"].get("derived") is True for parent in hant_payload["parents"])
    expected_zfl_keys = ["zfl-front-lunyu", *(f"zfl-L{i}" for i in range(1, 10))]
    assert {child["section_key"] for child in hant_children} == set(expected_zfl_keys)
    hans_path = ROOT / zfl_langs["zh-Hans"]["markdown_file"]
    hant_markdown = ROOT / hant_record["markdown_file"]
    heading_keys = lambda path: [
        line[2:].split(" — ", 1)[0]
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("# zfl-")
    ]
    assert heading_keys(hans_path) == expected_zfl_keys
    assert heading_keys(hant_markdown) == expected_zfl_keys

    # Any language marked included in the registry must point to the chunk output.
    for work_id, work in by_id.items():
        for lang, record in _languages(work).items():
            if _is_included(record):
                chunks_file = record.get("chunks_file")
                if chunks_file:
                    chunk_path = Path(chunks_file)
                    if not chunk_path.is_absolute():
                        chunk_path = ROOT / chunk_path
                    assert chunk_path.is_file()
                else:
                    assert (PHILOSOPHY_CHUNKS / f"{work_id}.{lang}.json").is_file()


def test_mitchell_tao_chapter_81_and_translator_notes_are_separate() -> None:
    work_id = "tao-te-ching-stephen-mitchell"
    markdown_path = ROOT / "data" / "markdown" / "philosophy" / f"{work_id}.en.md"
    sections = _markdown_sections(markdown_path, "ttc-")

    assert len(sections["ttc-081"][1]) < 3000
    assert sections["ttc-notes"][0] == "Notes"
    notes_path, notes_children = _load_chunk_file(work_id, "en")
    assert notes_path.is_file()
    assert any(child.get("section_key") == "ttc-notes" and child.get("text")
               for child in notes_children)


def test_ttc_notes_never_attach_parallels() -> None:
    class NotesClient:
        def scroll(self, **kwargs):
            return ([SimpleNamespace(id="other-notes", payload={
                "work_id": "tao-te-ching-star", "lang": "en", "section_key": "ttc-notes",
                "child_text": "translator commentary", "section_title": "About the Author",
            })], None)

    hit = {"work_id": "tao-te-ching-stephen-mitchell", "lang": "en",
           "work_group": "tao-te-ching",
           "section_key": "ttc-notes"}
    assert philosophy_search._attach_parallels(NotesClient(), hit)["parallels"] == []


def test_tao_parallels_are_ranked_per_translation_and_bounded() -> None:
    client = QdrantClient(location=":memory:")
    client.create_collection(
        collection_name="philosophy",
        vectors_config=models.VectorParams(size=4, distance=models.Distance.COSINE),
    )
    translations = [
        ("tao-te-ching-stephen-mitchell", "en", [
            ("mitchell-1", [1.0, 0.0, 0.0, 0.0]),
        ]),
        ("tao-te-ching-jonathan-star", "en", [
            ("star-1", [1.0, 0.0, 0.0, 0.0]),
            ("star-2", [0.9, 0.1, 0.0, 0.0]),
            ("star-3", [0.0, 1.0, 0.0, 0.0]),
        ]),
        ("tao-te-ching-tse-lao", "es", [
            ("tse-1", [1.0, 0.0, 0.0, 0.0]),
            ("tse-2", [0.9, 0.1, 0.0, 0.0]),
            ("tse-3", [0.0, 1.0, 0.0, 0.0]),
        ]),
    ]
    points = []
    point_id = 1
    for work_id, language, chunks in translations:
        for chunk_id, vector in chunks:
            points.append(models.PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "work_id": work_id,
                    "work_group": "tao-te-ching",
                    "lang": language,
                    "section_key": "ttc-001",
                    "section_title": "The way",
                    "derived": False,
                    "child_id": chunk_id,
                    "child_text": chunk_id + " " + "passage " * 200,
                },
            ))
            point_id += 1
    client.upsert(collection_name="philosophy", points=points)

    hit = {
        "work_id": "tao-te-ching-stephen-mitchell",
        "work_group": "tao-te-ching",
        "lang": "en",
        "section_key": "ttc-001",
    }
    result = philosophy_search._attach_parallels(
        client, hit, [1.0, 0.0, 0.0, 0.0],
    )

    groups = result["parallels"]
    assert {(group["work_id"], group["lang"]) for group in groups} == {
        ("tao-te-ching-jonathan-star", "en"),
        ("tao-te-ching-tse-lao", "es"),
    }
    assert all(len(group["chunks"]) <= 2 for group in groups)
    chunks = [chunk for group in groups for chunk in group["chunks"]]
    assert {chunk["chunk_id"] for chunk in chunks} == {"star-1", "star-2", "tse-1", "tse-2"}
    assert all(len(chunk["excerpt"]) <= 600 for chunk in chunks)
    required = {
        "chunk_id", "work_id", "lang", "section_key", "section_title", "derived", "excerpt",
    }
    assert all(set(chunk) == required for chunk in chunks)


def test_unaligned_philosophy_hit_has_no_parallels() -> None:
    class NoCallsClient:
        def scroll(self, **kwargs):
            raise AssertionError("unaligned hit should not look up parallels")

    hit = {"work_id": "some-work", "work_group": "some-group", "lang": "en"}
    assert philosophy_search._attach_parallels(
        NoCallsClient(), hit, [1.0, 0.0, 0.0, 0.0],
    )["parallels"] == []


class _StubRanker:
    def rank(self, query: str, documents: list[str]) -> list[dict]:
        return [
            {"corpus_id": index, "score": 8.0 - index / 10}
            for index in range(len(documents))
        ]


def test_reranker_receives_at_most_40_title_and_child_documents(monkeypatch) -> None:
    class CandidateClient:
        def __init__(self):
            self.query_limit = None

        def query_points(self, **kwargs):
            self.query_limit = kwargs["limit"]
            return SimpleNamespace(points=[
                SimpleNamespace(
                    id=index,
                    score=1.0,
                    payload={
                        "child_id": f"child-{index}",
                        "section_title": "Useful section",
                        "child_text": f"child passage {index}",
                        "parent_text": "PARENT MUST NOT REACH RERANKER",
                    },
                    vector=None,
                )
                for index in range(kwargs["limit"])
            ])

    captured = {}

    class CapturingRanker:
        def rank(self, query: str, documents: list[str]) -> list[dict]:
            captured["documents"] = documents
            return [{"corpus_id": index, "score": 1.0}
                    for index in range(len(documents))]

    client = CandidateClient()
    monkeypatch.setattr(
        philosophy_search, "embed_texts",
        lambda texts, task="retrieval.query": [[1.0, 0.0, 0.0, 0.0] for _ in texts],
    )
    monkeypatch.setattr(
        philosophy_search, "text_to_sparse_vector",
        lambda text: models.SparseVector(indices=[17], values=[1.0]),
    )
    monkeypatch.setattr(philosophy_search, "_ranker_for", lambda query: CapturingRanker())

    hits = philosophy_search.hybrid_search(
        "query", client=client, top_k=100, parallel=False, rerank=True,
    )

    assert client.query_limit == 40
    assert len(captured["documents"]) == 40
    assert captured["documents"][0] == "Useful section\nchild passage 0"
    assert all("PARENT MUST NOT REACH RERANKER" not in doc for doc in captured["documents"])
    assert len(hits) == 40


def test_bge_reranker_uses_512_tokens_and_default_device(monkeypatch) -> None:
    captured = {}

    class CapturingCrossEncoder:
        def __init__(self, model: str, **kwargs):
            captured["model"] = model
            captured["kwargs"] = kwargs

    monkeypatch.setattr(philosophy_search, "_ranker", None)
    monkeypatch.setattr(philosophy_search, "CrossEncoder", CapturingCrossEncoder)

    philosophy_search.get_ranker()

    assert captured["model"] == philosophy_search.RERANKER_MODEL
    assert captured["kwargs"] == {"trust_remote_code": True, "max_length": 512}


def _parallel_items(value) -> list[dict]:
    if isinstance(value, dict):
        groups = value.values()
    elif isinstance(value, list):
        groups = value
    else:
        return []
    items = []
    for group in groups:
        if isinstance(group, dict) and isinstance(group.get("chunks"), list):
            items.extend(group["chunks"])
        elif isinstance(group, dict):
            items.append(group)
        elif isinstance(group, list):
            items.extend(item for item in group if isinstance(item, dict))
    return items


def test_hybrid_search_in_memory_qdrant_attaches_parallel_passages(monkeypatch) -> None:
    client = QdrantClient(location=":memory:")
    client.create_collection(
        collection_name="philosophy",
        vectors_config=models.VectorParams(size=4, distance=models.Distance.COSINE),
        sparse_vectors_config={
            "sparse": models.SparseVectorParams(
                index=models.SparseIndexParams(on_disk=False),
                modifier=models.Modifier.IDF,
            ),
            "bm25": models.SparseVectorParams(
                index=models.SparseIndexParams(on_disk=False),
            ),
        },
    )

    languages = [
        ("en", "A person's mind can settle by returning attention to the present."),
        ("vi", "Tâm trí có thể lắng lại khi trở về với hiện tại."),
        ("zh-Hans", "心念回到当下，便能渐渐安定。"),
        ("zh-Hant", "心念回到當下，便能漸漸安定。"),
    ]
    points = []
    for point_id, (lang, text) in enumerate(languages, start=1):
        sparse = models.SparseVector(indices=[17], values=[1.0])
        points.append(models.PointStruct(
            id=point_id,
            vector={"": [1.0, 0.0, 0.0, 0.0], "sparse": sparse, "bm25": sparse},
            payload={
                "work_id": "zhuan-falun",
                "work_group": "zhuan-falun",
                "lang": lang,
                "section_key": "zfl-L1",
                "section_title": "Returning to the present",
                "translator": "Edition test",
                "edition": "Edition test",
                "derived": lang == "zh-Hant",
                "child_id": f"zhuan-falun.{lang}.L1-c1",
                "child_text": text,
                "parent_text": text,
                "parent_id": f"zhuan-falun.{lang}-p1",
                "heading_path": "Lecture 1",
            },
        ))
    client.upsert(collection_name="philosophy", points=points)

    monkeypatch.setattr(
        philosophy_search, "embed_texts",
        lambda texts, task="retrieval.query": [[1.0, 0.0, 0.0, 0.0] for _ in texts],
    )
    monkeypatch.setattr(
        philosophy_search, "text_to_sparse_vector",
        lambda text: models.SparseVector(indices=[17], values=[1.0]),
    )
    monkeypatch.setattr(philosophy_search, "get_ranker", lambda: _StubRanker())
    monkeypatch.setattr(philosophy_search, "_ranker_for", lambda query: _StubRanker())

    hits = philosophy_search.hybrid_search(
        "How can attention become calm?",
        client=client,
        top_k=4,
        parallel=True,
        rerank=True,
    )
    assert hits
    traditional_hit = next(hit for hit in hits if hit.get("lang") == "zh-Hant")
    assert traditional_hit["derived"] is True
    english_hit = next(
        hit for hit in hits
        if (hit.get("lang") if isinstance(hit, dict) else getattr(hit, "lang", None)) == "en"
    )
    if isinstance(english_hit, dict):
        assert english_hit["chunk_id"] == "zhuan-falun.en.L1-c1"
        assert english_hit["derived"] is False
        parallels = english_hit["parallels"]
    else:
        assert english_hit.chunk_id == "zhuan-falun.en.L1-c1"
        parallels = english_hit.parallels

    parallel_chunks = _parallel_items(parallels)
    parallel_langs = {item.get("lang") for item in parallel_chunks}
    assert {"vi", "zh-Hans"} <= parallel_langs
    assert all(item.get("chunk_id") and item.get("excerpt") for item in parallel_chunks)


def test_existing_mcp_tool_signatures_remain_unchanged() -> None:
    expected = {
        "search": "(query: str, top_k: int = 10, book: str | None = None, hyde_passage: str | None = None, extra_queries: list[str] | None = None, bm25_keywords: list[str] | None = None, detail: str = 'brief') -> list[dict]",
        "search_book": "(book: str, query: str, top_k: int = 5, detail: str = 'brief') -> list[dict]",
        "read_chunk": "(chunk_id: str, window: int = 1) -> dict",
        "get_chapter": "(book: str, chapter: str | int) -> str",
        "list_books": "(book: str | None = None) -> list[dict] | dict",
        "grep_books": "(pattern: str, book: str | None = None, max_results: int = 20) -> list[dict]",
    }
    for name, signature in expected.items():
        assert str(inspect.signature(getattr(server, name))) == signature


def test_grep_books_does_not_recurse_into_philosophy(monkeypatch, tmp_path) -> None:
    markdown = tmp_path / "markdown"
    markdown.mkdir()
    (markdown / "technical-book.md").write_text(
        "A technical book with ordinary terms.\n", encoding="utf-8"
    )
    philosophy = markdown / "philosophy"
    philosophy.mkdir()
    (philosophy / "original-library.en.md").write_text(
        "PHILOSOPHY_ONLY_MARKER appears only in this nested corpus.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(server, "MARKDOWN_DIR", markdown)
    monkeypatch.setattr(server, "BOOKS", {"technical-book": "Technical Book"})

    results = server.grep_books("PHILOSOPHY_ONLY_MARKER")
    assert results == []
