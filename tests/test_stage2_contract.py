"""Deterministic contract tests for the Stage 2 catalog and book filters."""

import asyncio
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from qdrant_client import models

from knowledge_base import books, search, server
from knowledge_base.config import COLLECTION_NAME


def _result(book: str, heading: str, index: int = 0) -> search.SearchResult:
    return search.SearchResult(
        score=1.0,
        book=book,
        book_title=book.replace("-", " ").title(),
        chapter="",
        section="",
        heading_path=heading,
        content="",
        child_match="",
        parent_id=f"{book}-p{index}",
        child_id=f"{book}-p{index}-c0",
    )


class _QueryClient:
    def __init__(self):
        self.kwargs = None

    def query_points(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(points=[])


class Stage2ContractTests(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ)
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("KB_CALL_LOG", None)

    def replace(self, target, name, value):
        patcher = patch.object(target, name, value, create=True)
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def stub_retrieval(self):
        self.replace(search, "embed_texts", lambda texts, task: [[0.1] for _ in texts])
        self.replace(
            search,
            "text_to_sparse_vector",
            lambda _text: SimpleNamespace(indices=[1], values=[1.0]),
        )

    def use_catalog(self, catalog):
        self.replace(server, "load_catalog", lambda: catalog)

    @staticmethod
    def search_call(args, kwargs):
        call = dict(kwargs)
        if args:
            call.setdefault("query", args[0])
        if len(args) > 1:
            call.setdefault("client", args[1])
        return call

    def test_load_catalog_drops_meta_and_caches_catalog_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "data"
            data.mkdir()
            catalog_path = data / "catalog.json"
            catalog_path.write_text(json.dumps({
                "book-a": {
                    "title": "Book A", "domain": "databases",
                    "tags": ["sql"], "summary": "A.",
                },
                "_meta": {"generated": "test"},
            }), encoding="utf-8")

            from knowledge_base import config

            self.replace(config, "ROOT", root)
            if hasattr(books, "ROOT"):
                self.replace(books, "ROOT", root)
            books.load_catalog.cache_clear()
            self.addCleanup(books.load_catalog.cache_clear)

            loaded = books.load_catalog()
            self.assertEqual(loaded, {
                "book-a": {
                    "title": "Book A", "domain": "databases",
                    "tags": ["sql"], "summary": "A.",
                }
            })
            catalog_path.write_text("{}", encoding="utf-8")
            self.assertEqual(books.load_catalog(), loaded)

    def test_load_catalog_missing_file_returns_empty_catalog(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            from knowledge_base import config

            self.replace(config, "ROOT", root)
            if hasattr(books, "ROOT"):
                self.replace(books, "ROOT", root)
            books.load_catalog.cache_clear()
            self.addCleanup(books.load_catalog.cache_clear)

            self.assertEqual(books.load_catalog(), {})

    def test_domains_are_sorted_unique_catalog_domains(self):
        catalog = books.load_catalog()
        self.assertEqual(books.DOMAINS, sorted({entry["domain"] for entry in catalog.values()}))

    @staticmethod
    def _only_filter(client):
        filters = [prefetch.filter for prefetch in client.kwargs["prefetch"]]
        if not filters or not all(item == filters[0] for item in filters):
            raise AssertionError("all dense and sparse legs should share one filter")
        return filters[0]

    def test_hybrid_search_string_book_filter_uses_match_value(self):
        self.stub_retrieval()
        client = _QueryClient()

        search.hybrid_search("vacuum", client, book_filter="postgresql-14-internals", rerank=False)

        condition = self._only_filter(client).must[0]
        self.assertEqual(condition.key, "book")
        self.assertEqual(condition.match, models.MatchValue(value="postgresql-14-internals"))

    def test_hybrid_search_book_list_uses_match_any(self):
        self.stub_retrieval()
        client = _QueryClient()

        search.hybrid_search(
            "vacuum", client,
            book_filter=["postgresql-14-internals", "postgresql-internals-interdb"],
            rerank=False,
        )

        condition = self._only_filter(client).must[0]
        self.assertEqual(condition.key, "book")
        self.assertEqual(condition.match, models.MatchAny(any=[
            "postgresql-14-internals", "postgresql-internals-interdb",
        ]))

    def test_hybrid_search_combines_book_and_domain_filters(self):
        self.stub_retrieval()
        client = _QueryClient()

        search.hybrid_search(
            "attention", client,
            book_filter=["ai-engineering-huyen", "agentic-design-patterns"],
            domain_filter="ai-engineering",
            rerank=False,
        )

        conditions = self._only_filter(client).must
        self.assertEqual([(c.key, c.match) for c in conditions], [
            ("book", models.MatchAny(any=["ai-engineering-huyen", "agentic-design-patterns"])),
            ("domain", models.MatchValue(value="ai-engineering")),
        ])

    def test_hybrid_search_without_filters_passes_none_and_keeps_dbsf_query(self):
        self.stub_retrieval()
        client = _QueryClient()

        search.hybrid_search("vacuum", client, top_k=7, candidates=23, rerank=False)

        self.assertTrue(all(prefetch.filter is None for prefetch in client.kwargs["prefetch"]))
        self.assertEqual(client.kwargs["prefetch"], [
            models.Prefetch(query=[0.1], using="", filter=None, limit=23),
            models.Prefetch(
                query=models.SparseVector(indices=[1], values=[1.0]),
                using="bm25", filter=None, limit=23,
            ),
        ])
        self.assertEqual(client.kwargs["collection_name"], COLLECTION_NAME)
        self.assertEqual(client.kwargs["query"], models.FusionQuery(fusion=models.Fusion.DBSF))
        self.assertEqual(client.kwargs["limit"], 7)
        self.assertIs(client.kwargs["with_payload"], True)

    def test_search_resolves_and_merges_legacy_book_with_books(self):
        resolved = {
            "PostgreSQL 14 Internals": "postgresql-14-internals",
            "postgresql-internals-interdb": "postgresql-internals-interdb",
        }
        calls = []
        self.replace(server, "resolve_book", lambda name: (resolved[name], []))
        self.replace(server, "DOMAINS", ["databases"])
        self.replace(server, "get_client", lambda: object())

        def fake_search(*args, **kwargs):
            calls.append(self.search_call(args, kwargs))
            return []

        self.replace(server, "hybrid_search", fake_search)

        self.assertEqual(server.search(
            "vacuum",
            books=["PostgreSQL 14 Internals"],
            book="postgresql-internals-interdb",
            domain="databases",
        ), {"results": [], "related_headings": []})
        self.assertEqual(set(calls[0]["book_filter"]), {
            "postgresql-14-internals", "postgresql-internals-interdb",
        })
        self.assertEqual(calls[0]["domain_filter"], "databases")

    def test_search_unknown_book_and_domain_return_error_rows(self):
        self.replace(server, "resolve_book", lambda name: (None, ["postgresql-14-internals"]))
        self.replace(server, "DOMAINS", ["ai-engineering", "databases", "security"])

        bad_book = server.search("vacuum", books=["missing-book"])
        self.assertEqual(len(bad_book), 1)
        self.assertIn("Unknown book 'missing-book'.", bad_book[0]["error"])
        self.assertEqual(server.search("x", domain="nope"), [{
            "error": "Unknown domain 'nope'. Domains: ai-engineering, databases, security"
        }])

    def test_find_books_without_query_filters_all_tags_and_sorts(self):
        catalog = {
            "zeta": {"title": "Zeta", "domain": "ai-engineering", "tags": ["rag"], "summary": "Z."},
            "beta": {"title": "Beta", "domain": "databases", "tags": ["sql"], "summary": "B."},
            "alpha": {"title": "Alpha", "domain": "databases", "tags": ["sql", "rag"], "summary": "A."},
        }
        self.use_catalog(catalog)
        self.replace(server, "DOMAINS", ["ai-engineering", "databases"])

        rows = server.find_books(domain="databases", tags=["sql", "rag"])

        self.assertEqual(rows, [{
            "slug": "alpha", "title": "Alpha", "domain": "databases",
            "tags": ["sql", "rag"], "summary": "A.",
        }])
        all_rows = server.find_books()
        self.assertEqual([(row["domain"], row["title"]) for row in all_rows], [
            ("ai-engineering", "Zeta"), ("databases", "Alpha"), ("databases", "Beta")
        ])

    def test_find_books_unknown_domain_and_tag_list_valid_values(self):
        self.use_catalog({
            "a": {"title": "A", "domain": "databases", "tags": ["sql", "rag"], "summary": "A."},
            "b": {"title": "B", "domain": "security", "tags": ["web"], "summary": "B."},
        })
        self.replace(server, "DOMAINS", ["databases", "security"])

        self.assertEqual(server.find_books(domain="nope"), [{
            "error": "Unknown domain 'nope'. Domains: databases, security"
        }])
        tag_error = server.find_books(tags=["nope"])[0]["error"]
        self.assertIn("nope", tag_error)
        self.assertTrue(all(tag in tag_error for tag in ("rag", "sql", "web")))

    def test_list_books_carries_catalog_tags_and_uses_empty_fallback(self):
        self.replace(server, "BOOKS", {"known": "Known Book"})
        self.replace(server, "book_domain", lambda _slug: "databases")
        self.replace(server, "book_chapters", lambda _slug: ["Chapter 1"])
        self.use_catalog({
            "known": {"title": "Known Book", "domain": "databases", "tags": ["sql"], "summary": "S."}
        })

        self.assertEqual(server.list_books()[0]["tags"], ["sql"])
        self.use_catalog({})
        self.assertEqual(server.list_books()[0]["tags"], [])

    def test_find_books_query_aggregates_both_passes_and_strips_part_suffix(self):
        self.use_catalog({
            "ai-engineering-huyen": {
                "title": "AI Engineering", "domain": "ai-engineering",
                "tags": ["rag"], "summary": "AI.",
            },
            "postgresql-14-internals": {
                "title": "PostgreSQL 14 Internals", "domain": "databases",
                "tags": ["sql"], "summary": "DB.",
            },
        })
        self.replace(server, "get_client", lambda: "client")

        reranked = [
            _result("ai-engineering-huyen", "Retrieval (part 1)", 0),
            _result("ai-engineering-huyen", "Generation (part 2)", 1),
            _result("ai-engineering-huyen", "Retrieval (part 4)", 2),
            _result("postgresql-14-internals", "Snapshot isolation (part 1)", 3),
        ]
        fusion_only = [
            _result("postgresql-14-internals", "Snapshot isolation (part 2)", 4),
            _result("ai-engineering-huyen", "Retrieval (part 5)", 5),
        ]
        calls = []

        def fake_search(*args, **kwargs):
            call = self.search_call(args, kwargs)
            calls.append(call)
            return fusion_only if call.get("rerank") is False else reranked

        self.replace(server, "hybrid_search", fake_search)

        rows = server.find_books("topic", domain="ai-engineering", tags=["rag"], top_k=1)

        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0], {
            "query": "topic", "client": "client", "top_k": 40,
            "candidates": 100, "domain_filter": "ai-engineering",
        })
        self.assertEqual(
            {key: calls[1][key] for key in ("query", "client", "rerank", "top_k", "domain_filter")},
            {
                "query": "topic", "client": "client", "rerank": False,
                "top_k": 100, "domain_filter": "ai-engineering",
            },
        )
        self.assertEqual(rows, [{
            "slug": "ai-engineering-huyen",
            "title": "AI Engineering",
            "domain": "ai-engineering",
            "tags": ["rag"],
            "summary": "AI.",
            "score": 2.083,
            "matching_sections": ["Retrieval", "Generation"],
        }])

    def test_registered_tool_schemas_expose_stage_two_parameters(self):
        tools = asyncio.run(server.mcp.list_tools())
        by_name = {tool.name: tool.parameters for tool in tools}

        self.assertTrue({"books", "book", "domain"} <= set(by_name["search"]["properties"]))
        self.assertTrue({"query", "domain", "tags", "top_k"} <= set(by_name["find_books"]["properties"]))


if __name__ == "__main__":
    unittest.main()
