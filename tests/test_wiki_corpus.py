"""Offline wiki contracts: real in-memory Qdrant, fake dense and BM25 encoders."""

from collections import Counter
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import numpy as np
import pytest
from qdrant_client import QdrantClient, models

from knowledge_base.config import COLLECTION_NAME, EMBEDDING_DIM
from knowledge_base.index import ensure_collection
from knowledge_base.wiki import chunk, index, roots, search


def make_root(tmp_path, project="project"):
    root = tmp_path / project / "wiki"
    root.mkdir(parents=True)
    return root


@pytest.fixture
def corpus(tmp_path, monkeypatch):
    client = QdrantClient(":memory:")
    calls = []

    def embed(texts, task="retrieval.passage"):
        calls.append((list(texts), task))
        return [[1.0, 0.0, 0.0] for _ in texts]

    class SparseEncoder:
        def embed(self, texts):
            for text in texts:
                counts = Counter(
                    int.from_bytes(hashlib.sha256(word.encode()).digest()[:4], "big")
                    for word in text.lower().split()
                )
                yield SimpleNamespace(
                    indices=np.array(sorted(counts)),
                    values=np.array([float(counts[i]) for i in sorted(counts)]),
                )

    monkeypatch.setattr(index, "EMBEDDING_DIM", 3)
    monkeypatch.setattr(index, "embed_texts", embed)
    monkeypatch.setattr(index, "get_sparse_model", SparseEncoder)
    monkeypatch.setattr(search, "get_client", lambda: client)
    monkeypatch.setenv("KB_WIKI_RERANK", "0")
    yield SimpleNamespace(
        client=client, calls=calls, manifest=tmp_path / "manifest.json",
        run=lambda selected, **kw: index.index_roots(
            selected, client=client, manifest_path=tmp_path / "manifest.json", **kw,
        ),
    )
    client.close()


def all_points(corpus):
    return corpus.client.scroll(index.COLLECTION, limit=1000)[0]


def test_ensure_collection_defaults_and_independent_name_dimension():
    with closing(QdrantClient(":memory:")) as client:
        ensure_collection(client)
        ensure_collection(client, name="separate", dim=3)
        ensure_collection(client, name="separate", dim=3)
        assert client.get_collection(COLLECTION_NAME).config.params.vectors.size == EMBEDDING_DIM
        params = client.get_collection("separate").config.params
        assert params.vectors.size == 3
        assert "bm25" in params.sparse_vectors


def test_roots_file_comments_expansion_and_environment_override(tmp_path, monkeypatch):
    config = tmp_path / "roots.txt"
    config.write_text("# projects\n~/project/wiki # canonical\n\n", encoding="utf-8")
    monkeypatch.setattr(roots, "ROOTS_FILE", config)
    monkeypatch.delenv("KB_WIKI_ROOTS", raising=False)
    assert roots.configured_roots() == [(Path.home() / "project/wiki").resolve()]
    a, b = tmp_path / "a/wiki", tmp_path / "b/wiki"
    monkeypatch.setenv("KB_WIKI_ROOTS", os.pathsep.join(map(str, [a, b, a])))
    assert roots.configured_roots() == [a, b]
    monkeypatch.setenv("KB_WIKI_ROOTS", "")
    assert roots.configured_roots() == []


def test_worktree_root_skipped(tmp_path, corpus, caplog):
    root = make_root(tmp_path, "canonical")
    (root / "index.md").write_text("# Main\n\nCanonical content.")
    repo = root.parent

    def git(*args):
        result = subprocess.run(
            ["git", "-C", str(repo), "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", *args],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    git("init")
    git("add", "wiki/index.md")
    git("-c", "user.name=Tests", "-c", "user.email=tests@example.invalid", "commit", "-m", "initial")
    worktree = tmp_path / "copy"
    git("worktree", "add", "-b", "copy", str(worktree))
    stats = corpus.run([root, worktree / "wiki"])
    assert stats[0].re_embedded == 1
    assert stats[1].skipped_worktree == 1
    assert stats[1].files_seen == 0
    assert len(all_points(corpus)) == 1
    assert "worktree" in caplog.text.lower()
    assert all_points(corpus)[0].payload["project"] == "canonical"


def test_chunk_log_entries_heading_paths_and_dates(tmp_path):
    text = (
        "# Work log\n\n## 2026-10-25 First\n\nFirst entry.\n\n"
        "### Evidence\n\nDetails.\n\n## 2026-10-26 Second\n\nSecond entry.\n"
    )
    chunks = chunk.chunk_page(tmp_path / "log.md", text)
    assert len(chunks) == 2
    assert chunks[0]["heading"] == "Work log > 2026-10-25 First"
    assert chunks[0]["date"] == "2026-10-25"
    assert "### Evidence" in chunks[0]["text"]
    assert "Second entry" not in chunks[0]["text"]
    assert chunks[1]["date"] == "2026-10-26"
    dated = chunk.chunk_page(tmp_path / "2026-09-01-run.md", "# Run\n\n## Result\n\nDone.")
    assert dated[0]["heading"] == "Run > Result"
    assert dated[0]["date"] == "2026-09-01"


def test_nested_wiki_uses_repository_folder_as_project(tmp_path, corpus):
    repo = tmp_path / "actual-project"
    root = repo / "docs/wiki"
    root.mkdir(parents=True)
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    (root / "page.md").write_text("## Facts\n\nContent.")
    assert corpus.run([root])[0].project == "actual-project"
    assert all_points(corpus)[0].payload["project"] == "actual-project"


def test_chunk_caps_paragraphs_and_unbroken_text_without_losing_tail(tmp_path):
    text = "## Section\n\n" + "\n\n".join(["a" * 80, "b" * 500, "tiny tail"])
    chunks = chunk.chunk_page(tmp_path / "page.md", text, max_chars=100)
    assert all(len(item["text"]) <= 100 for item in chunks)
    assert all(item["heading"] == "Section" for item in chunks)
    assert "tiny tail" in chunks[-1]["text"]
    joined = "".join(item["text"] for item in chunks)
    assert joined.count("a") == text.count("a")
    assert joined.count("b") == text.count("b")


def test_fenced_headings_do_not_split_sections(tmp_path):
    text = "# Page\n\n## Real\n\n```md\n## Example\n```\n\n## Next\n\nDone."
    chunks = chunk.chunk_page(tmp_path / "page.md", text)
    assert [item["heading"] for item in chunks] == ["Page > Real", "Page > Next"]
    assert "## Example" in chunks[0]["text"]


def test_inputs_raw_and_symlink_files_skipped(tmp_path, corpus):
    root = make_root(tmp_path)
    for folder in (root, root / "inputs", root / "raw", root / "topics/raw"):
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "page.md").write_text("# Page\n\nFacts.")
    outside = tmp_path / "private.md"
    outside.write_text("Private")
    (root / "link.md").symlink_to(outside)
    stats = corpus.run([root])
    assert stats[0].files_seen == stats[0].re_embedded == 1
    assert len(all_points(corpus)) == 1


def test_incremental_second_pass_reembeds_zero(tmp_path, corpus):
    root = make_root(tmp_path)
    page = root / "page.md"
    page.write_text("# Page\n\n## One\n\nOriginal.\n\n## Two\n\nMore.")
    assert corpus.run([root])[0].re_embedded == 1
    ids = {p.id for p in all_points(corpus)}
    corpus.calls.clear()
    assert corpus.run([root])[0].re_embedded == 0
    assert corpus.calls == []
    assert {p.id for p in all_points(corpus)} == ids
    manifest = json.loads(corpus.manifest.read_text())
    assert set(manifest) == {str(page)}
    assert manifest[str(page)]["hash"] == hashlib.sha256(page.read_bytes()).hexdigest()
    assert set(manifest[str(page)]["point_ids"]) == ids


def test_changed_page_reembedded_and_old_points_removed(tmp_path, corpus):
    root = make_root(tmp_path)
    page = root / "page.md"
    page.write_text("## One\n\nObsolete.\n\n## Two\n\nAlso obsolete.")
    corpus.run([root])
    assert len(all_points(corpus)) == 2
    page.write_text("## Replacement\n\nCurrent content.")
    assert corpus.run([root])[0].re_embedded == 1
    points = all_points(corpus)
    assert len(points) == 1
    assert points[0].payload["text"] == "## Replacement\n\nCurrent content."


def test_deleted_page_points_removed_and_unselected_root_preserved(tmp_path, corpus):
    a, b = make_root(tmp_path, "a"), make_root(tmp_path, "b")
    page = a / "page.md"
    page.write_text("## One\n\nGone soon.")
    (b / "page.md").write_text("## Two\n\nKeep this.")
    corpus.run([a, b])
    page.unlink()
    assert corpus.run([a])[0].deleted == 1
    assert [p.payload["project"] for p in all_points(corpus)] == ["b"]


def test_interrupted_new_page_can_be_deleted_on_next_pass(tmp_path, corpus, monkeypatch):
    root = make_root(tmp_path)
    page = root / "page.md"
    page.write_text("## New\n\nContent.")
    original = corpus.client.upsert

    def partial_write(**kwargs):
        original(**kwargs)
        raise RuntimeError("lost response")

    with monkeypatch.context() as patch:
        patch.setattr(corpus.client, "upsert", partial_write)
        with pytest.raises(RuntimeError, match="lost response"):
            corpus.run([root])
    assert json.loads(corpus.manifest.read_text())[str(page)]["hash"] == ""
    page.unlink()
    assert corpus.run([root])[0].deleted == 1
    assert all_points(corpus) == []


def test_missing_root_fails_without_deleting_points(tmp_path, corpus):
    root = make_root(tmp_path)
    (root / "page.md").write_text("## Facts\n\nContent.")
    corpus.run([root])
    root.rename(root.with_name("moved"))
    with pytest.raises(FileNotFoundError):
        corpus.run([root])
    assert len(all_points(corpus)) == 1


def test_dry_run_does_not_connect_embed_or_write_manifest(tmp_path, monkeypatch):
    root = make_root(tmp_path)
    (root / "page.md").write_text("## Facts\n\nContent.")

    def forbidden(*args, **kwargs):
        pytest.fail("dry run tried to connect or load a model")

    monkeypatch.setattr(index, "get_client", forbidden)
    monkeypatch.setattr(index, "embed_texts", forbidden)
    manifest = tmp_path / "manifest.json"
    stats = index.index_roots([root], dry_run=True, manifest_path=manifest)
    assert stats[0].files_seen == stats[0].re_embedded == 1
    assert not manifest.exists()


def test_dry_run_preserves_points_and_manifest_for_changes_and_deletions(tmp_path, corpus):
    root = make_root(tmp_path)
    page, removed = root / "page.md", root / "removed.md"
    page.write_text("## Before\n\nOriginal.")
    removed.write_text("## Gone\n\nSoon.")
    corpus.run([root])
    before = corpus.manifest.read_bytes()
    page.write_text("## After\n\nReplacement.")
    removed.unlink()
    stats = corpus.run([root], dry_run=True)
    assert stats[0].re_embedded == stats[0].deleted == 1
    assert corpus.manifest.read_bytes() == before
    assert len(all_points(corpus)) == 2
    assert any("Original." in p.payload["text"] for p in all_points(corpus))


def test_recreated_collection_reembeds_despite_existing_manifest(tmp_path, corpus):
    root = make_root(tmp_path)
    (root / "page.md").write_text("## Facts\n\nContent.")
    corpus.run([root])
    corpus.client.delete_collection(index.COLLECTION)
    assert corpus.run([root])[0].re_embedded == 1
    assert len(all_points(corpus)) == 1


def test_recreated_collection_crash_leaves_cleared_manifest(tmp_path, corpus, monkeypatch):
    root = make_root(tmp_path)
    (root / "page.md").write_text("## Facts\n\nContent.")
    corpus.run([root])
    corpus.client.delete_collection(index.COLLECTION)

    def crash_after_create(*args, **kwargs):
        ensure_collection(*args, **kwargs)
        assert json.loads(corpus.manifest.read_text()) == {}
        raise RuntimeError("crashed after collection creation")

    with monkeypatch.context() as patch:
        patch.setattr(index, "ensure_collection", crash_after_create)
        with pytest.raises(RuntimeError, match="crashed after collection creation"):
            corpus.run([root])
    assert corpus.run([root])[0].re_embedded == 1
    assert len(all_points(corpus)) == 1


def test_unchanged_page_reconciles_ids_and_restores_missing_point(tmp_path, corpus, monkeypatch):
    root = make_root(tmp_path)
    page = root / "page.md"
    page.write_text("## One\n\nFirst.\n\n## Two\n\nSecond.")
    corpus.run([root])
    ids = {point.id for point in all_points(corpus)}
    corpus.client.delete(index.COLLECTION, models.PointIdsList(points=[min(ids)]))
    retrieve = corpus.client.retrieve
    requests = []

    def checked_retrieve(**kwargs):
        requests.append(kwargs)
        return retrieve(**kwargs)

    monkeypatch.setattr(corpus.client, "retrieve", checked_retrieve)
    assert corpus.run([root])[0].re_embedded == 1
    assert {point.id for point in all_points(corpus)} == ids
    assert len(requests) == 1
    assert set(requests[0]["ids"]) == ids
    assert requests[0]["with_payload"] is requests[0]["with_vectors"] is False
    stored = json.loads(corpus.manifest.read_text())[str(page)]
    assert set(stored["point_ids"]) == ids
    corpus.calls.clear()
    stats = corpus.run([root])[0]
    assert stats.re_embedded == 0 and stats.reconciled == 1
    assert corpus.calls == []


def test_update_embeds_all_batches_before_upsert_and_keeps_page_on_failure(tmp_path, corpus, monkeypatch):
    root = make_root(tmp_path)
    page = root / "page.md"
    page.write_text("## Original\n\nSearchable content.")
    corpus.run([root])
    before = all_points(corpus)
    # More than one embedding batch: a later failure must preserve the whole page.
    page.write_text("\n\n".join(f"## Section {i}\n\nReplacement {i}." for i in range(33)))
    calls = []

    def embed_then_fail(texts, **kwargs):
        assert all_points(corpus) == before
        assert search.wiki_search("Searchable")[0]["heading"] == "Original"
        calls.append(texts)
        if len(calls) == 2:
            raise RuntimeError("embedding failed")
        return [[1.0, 0.0, 0.0] for _ in texts]

    # Search uses its own fake query encoder so the probe does not recurse.
    monkeypatch.setattr(search, "embed_texts", lambda *a, **kw: [[1.0, 0.0, 0.0]])
    with monkeypatch.context() as patch:
        patch.setattr(index, "embed_texts", embed_then_fail)
        with pytest.raises(RuntimeError, match="embedding failed"):
            corpus.run([root])
    assert len(calls) == 2
    assert all_points(corpus) == before
    assert corpus.run([root])[0].re_embedded == 1
    assert len(all_points(corpus)) == 33


def test_update_upserts_before_deleting_only_obsolete_ids(tmp_path, corpus, monkeypatch):
    root = make_root(tmp_path)
    page = root / "page.md"
    page.write_text("## One\n\nFirst.\n\n## Two\n\nSecond.")
    corpus.run([root])
    page.write_text("## New\n\nReplacement.")
    delete = corpus.client.delete
    deletions = []

    def checked_delete(**kwargs):
        points = all_points(corpus)
        assert any(p.payload["heading"] == "New" for p in points)
        deletions.append(kwargs)
        return delete(**kwargs)

    monkeypatch.setattr(corpus.client, "delete", checked_delete)
    corpus.run([root])
    assert len(deletions) == 1
    assert [p.payload["heading"] for p in all_points(corpus)] == ["New"]


def test_manifest_profile_isolates_url_collection_model_and_dimension(tmp_path, corpus, monkeypatch):
    root = make_root(tmp_path)
    (root / "page.md").write_text("## Facts\n\nContent.")
    monkeypatch.setattr(index, "ROOT", tmp_path)
    monkeypatch.setenv("KB_QDRANT_URL", "http://localhost:6333")
    paths = set()

    def run_profile():
        assert index.index_roots([root], client=corpus.client)[0].re_embedded == 1
        manifests = set((tmp_path / "data/wiki").glob("manifest-*.json"))
        assert len(manifests - paths) == 1
        paths.update(manifests)
        assert index.index_roots([root], client=corpus.client)[0].re_embedded == 0

    run_profile()
    monkeypatch.setenv("KB_QDRANT_URL", "http://localhost:6334")
    run_profile()
    monkeypatch.setattr(index, "COLLECTION", "another-wiki")
    run_profile()
    monkeypatch.setattr(index, "EMBEDDING_MODEL", "another-model")
    run_profile()
    # Empty pages allow a different vector dimension without altering the fake encoder.
    (root / "page.md").write_text("# Title only")
    monkeypatch.setattr(index, "EMBEDDING_DIM", 4)
    run_profile()


def test_legacy_manifest_migrates_to_default_profile_only(tmp_path, corpus, monkeypatch):
    root = make_root(tmp_path)
    page = root / "page.md"
    page.write_text("## Facts\n\nContent.")
    monkeypatch.setattr(index, "ROOT", tmp_path)
    legacy = tmp_path / "data/wiki/manifest.json"
    legacy.parent.mkdir(parents=True)
    original = json.dumps({str(page): hashlib.sha256(page.read_bytes()).hexdigest()})
    legacy.write_text(original)
    monkeypatch.setenv("KB_QDRANT_URL", "http://other-server:6333")
    assert index.index_roots([root], client=corpus.client)[0].re_embedded == 1
    assert not legacy.exists()
    manifests = list(legacy.parent.glob("manifest-*.json"))
    assert len(manifests) == 2
    assert sum(path.read_text() == original for path in manifests) == 1
    # The migrated default hashes have no ids and must be upgraded through a real pass.
    monkeypatch.setenv("KB_QDRANT_URL", "http://127.0.0.1:6333")
    monkeypatch.setattr(index, "COLLECTION", "wiki")
    monkeypatch.setattr(index, "EMBEDDING_MODEL", "google/embeddinggemma-2")
    monkeypatch.setattr(index, "EMBEDDING_DIM", 768)
    assert index.index_roots([root], client=corpus.client)[0].re_embedded == 1
    assert index.index_roots([root], client=corpus.client)[0].re_embedded == 0


def test_nested_repo_inside_linked_worktree_is_skipped(tmp_path, corpus):
    repo = tmp_path / "main"
    repo.mkdir()

    def git(folder, *args):
        return subprocess.run(
            ["git", "-C", str(folder), "-c", "commit.gpgsign=false", "-c",
             "core.hooksPath=/dev/null", *args], check=True, capture_output=True, text=True,
        )

    git(repo, "init")
    git(repo, "-c", "user.name=Tests", "-c", "user.email=tests@example.invalid",
        "commit", "--allow-empty", "-m", "initial")
    worktree = tmp_path / "copy"
    git(repo, "worktree", "add", "-b", "copy", str(worktree))
    # Two nested repositories require walking past more than the nearest enclosing repo.
    nested = worktree / "outer/inner"
    nested.mkdir(parents=True)
    git(worktree / "outer", "init")
    git(nested, "init")
    root = nested / "docs/wiki"
    root.mkdir(parents=True)
    (root / "page.md").write_text("## Duplicate\n\nDo not index.")
    stats = corpus.run([root])[0]
    assert stats.skipped_worktree == 1 and stats.files_seen == 0
    assert corpus.calls == []
    assert not corpus.client.collection_exists(index.COLLECTION)


@pytest.mark.parametrize("title, expected", [
    ("C#", "C#"), ("C# ###", "C#"), ("Heading###", "Heading###"),
    ("Heading ###  ", "Heading"), ("Heading\t##", "Heading"), ("###", ""),
])
def test_heading_closing_hashes_require_whitespace(tmp_path, title, expected):
    text = f"## {title}\n\nContent."
    assert chunk.headings(text)[0].title == expected
    assert chunk.chunk_page(tmp_path / "page.md", text)[0]["heading"] == expected


def test_cli_repeatable_roots_and_per_root_counts(tmp_path, capsys):
    a, b = make_root(tmp_path, "a"), make_root(tmp_path, "b")
    for root in (a, b):
        (root / "page.md").write_text("## Facts\n\nContent.")
    assert index.main(["--root", str(a), "--root", str(b), "--dry-run"]) == 0
    output = capsys.readouterr().out
    for root in (a, b):
        assert f"{root} ({root.parent.name}): files seen=1, re-embedded=1, deleted=0, skipped (worktree)=0" in output


def test_server_down_raises_clear_error_without_embedded_fallback(monkeypatch):
    calls = []

    def unavailable(**kwargs):
        calls.append(kwargs)
        raise OSError("connection refused")

    monkeypatch.setattr(index, "QdrantClient", unavailable)
    with pytest.raises(RuntimeError, match="Qdrant server.*KB_QDRANT_URL"):
        index.get_client()
    assert len(calls) == 1
    assert "url" in calls[0] and "path" not in calls[0]


def test_project_filter_on_both_hybrid_legs(tmp_path, corpus):
    a, b = make_root(tmp_path, "a"), make_root(tmp_path, "b")
    for root in (a, b):
        (root / "page.md").write_text("## Search\n\nshared keyword facts")
    corpus.run([a, b])
    hits = search.wiki_search("keyword", project="b", limit=8)
    assert len(hits) == 1
    assert hits[0]["project"] == "b"
    assert hits[0]["rel_path"] == "page.md"
    assert hits[0]["path"] == str(b / "page.md")
    assert {"heading", "date", "snippet", "score"} <= hits[0].keys()


def test_rerank_defaults_on_and_disable_avoids_loading_ranker(tmp_path, corpus, monkeypatch):
    root = make_root(tmp_path)
    (root / "page.md").write_text("## Search\n\nkeyword facts")
    corpus.run([root])
    monkeypatch.delenv("KB_WIKI_RERANK")
    ranker = SimpleNamespace(predict=lambda pairs, **kw: [42.0 for _ in pairs])
    monkeypatch.setattr(search, "get_ranker", lambda: ranker)
    assert search.wiki_search("keyword")[0]["score"] == 42.0
    monkeypatch.setenv("KB_WIKI_RERANK", "false")
    monkeypatch.setattr(search, "get_ranker", lambda: pytest.fail("ranker loaded"))
    assert search.wiki_search("keyword")


def test_rank_api_orders_candidates_before_applying_limit(tmp_path, corpus, monkeypatch):
    root = make_root(tmp_path)
    (root / "page.md").write_text("## First\n\nkeyword first\n\n## Second\n\nkeyword second")
    corpus.run([root])
    monkeypatch.delenv("KB_WIKI_RERANK")

    def rank(query, documents):
        assert len(documents) == 2
        return sorted(
            [{"corpus_id": i, "score": 42.0 if "Second" in doc else -1.0}
             for i, doc in enumerate(documents)],
            key=lambda item: item["score"], reverse=True,
        )

    monkeypatch.setattr(search, "get_ranker", lambda: SimpleNamespace(rank=rank))
    hits = search.wiki_search("keyword", limit=1)
    assert len(hits) == 1
    assert hits[0]["heading"] == "Second"
    assert hits[0]["score"] == 42.0


def test_wiki_read_whole_page_section_and_root_boundary(tmp_path, monkeypatch):
    root = make_root(tmp_path)
    monkeypatch.setenv("KB_WIKI_ROOTS", str(root))
    page = root / "page.md"
    text = "# Page\n\n## First\n\nOne.\n\n### Child\n\nDetails.\n\n## Second\n\nTwo."
    page.write_text(text)
    assert search.wiki_read(str(page)) == text
    section = search.wiki_read(str(page), heading="Page > First")
    assert "One." in section and "Details." in section and "Two." not in section
    assert "Details." in search.wiki_read(str(page), heading="Child")
    with pytest.raises(ValueError, match="heading"):
        search.wiki_read(str(page), heading="Missing")
    outside = tmp_path / "project/wiki-private/secret.md"
    outside.parent.mkdir()
    outside.write_text("Private")
    with pytest.raises(ValueError, match="configured wiki root"):
        search.wiki_read(str(outside))
    (root / "escape.md").symlink_to(outside)
    with pytest.raises(ValueError, match="configured wiki root"):
        search.wiki_read(str(root / "escape.md"))


@pytest.mark.parametrize("config", ["missing", "empty", "comments", "configured", "env"])
def test_tools_registered_only_with_nonempty_roots_config(tmp_path, config):
    config_file = tmp_path / "roots.txt"
    if config != "missing":
        config_file.write_text({"empty": "", "comments": "# no roots\n", "configured": "/project/wiki\n", "env": ""}[config])
    env = os.environ.copy()
    env.pop("KB_WIKI_ROOTS", None)
    env["KB_EDITION"] = "core"
    if config == "env":
        env["KB_WIKI_ROOTS"] = "/project/wiki"
    command = (
        "import asyncio,json; from pathlib import Path; "
        "import knowledge_base.wiki.roots as roots; "
        f"roots.ROOTS_FILE=Path({str(config_file)!r}); "
        "import knowledge_base.server as s; "
        "print(json.dumps({'tools': sorted(t.name for t in asyncio.run(s.mcp.list_tools())), "
        "'instructions': s.mcp.instructions}))"
    )
    result = subprocess.run([sys.executable, "-c", command], env=env, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout.strip().splitlines()[-1])
    enabled = config in {"configured", "env"}
    wiki_tools = {"wiki_search", "wiki_read"}
    assert set(data["tools"]) & wiki_tools == (wiki_tools if enabled else set())
    assert ("wiki_search" in data["instructions"]) == enabled
