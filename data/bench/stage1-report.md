# Stage 1 tool interface report

Date: 2026-09-24

## Changes

- Added cached book-domain, fence-aware chapter-list, and slug/title resolution helpers in `knowledge_base/books.py`.
- Updated `knowledge_base/server.py` with brief/full search responses, book resolution, compact catalog output, and indexed chapter lookup.
- `knowledge_base/search.py` and retrieval ranking were not changed.

Files changed for this task: `knowledge_base/server.py`, `knowledge_base/books.py`, and this report. Acceptance artifacts: `data/golden/eval_runs/s1-check.json` and `data/bench/runs/s1smoke-Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B.jsonl`.

## Acceptance results

1. Retrieval gate: **PASS**. Ran `PYTHONPATH=. .venv/bin/python scripts/eval_retrieval.py --golden data/golden/golden_queries_hard.jsonl --label s1-check`.

```text
  25/438...
  50/438...
  75/438...
  100/438...
  125/438...
  150/438...
  175/438...
  200/438...
  225/438...
  250/438...
  275/438...
  300/438...
  325/438...
  350/438...
  375/438...
  400/438...
  425/438...

===== s1-check  (n=438) =====
  NDCG@10=0.7704  Recall@10=0.9680  MRR=0.8573  Recall@50(ceiling)=0.9886
  per-domain:
    databases    n= 17  NDCG@10=0.818  R@10=1.000  MRR=0.813  R@50=1.000
    distributed  n=  7  NDCG@10=0.730  R@10=0.857  MRR=0.786  R@50=1.000
    ml           n=209  NDCG@10=0.781  R@10=0.967  MRR=0.861  R@50=0.995
    rust         n=137  NDCG@10=0.760  R@10=0.971  MRR=0.883  R@50=0.978
    security     n= 68  NDCG@10=0.750  R@10=0.971  MRR=0.811  R@50=0.985
  per-archetype:
    baseline       n=198  NDCG@10=0.742  R@10=0.950  MRR=0.814  R@50=0.980
    error_symbol   n= 80  NDCG@10=0.795  R@10=0.988  MRR=0.895  R@50=1.000
    keyword        n= 80  NDCG@10=0.777  R@10=0.988  MRR=0.916  R@50=1.000
    navigational   n= 80  NDCG@10=0.811  R@10=0.975  MRR=0.868  R@50=0.988

  retrieval ceiling - delivered recall = 0.0206 (reranker keeping retrieved hits)
  full report + 14 misses -> data/golden/eval_runs/s1-check.json
```
2. Catalog: 126 books; `json.dumps(list_books())` = **4,866 cl100k tokens**. Search query `how does MVCC snapshot isolation work in postgres`: brief **2,708 tokens** / 8 hits; full **23,057 tokens** / 8 hits.

```text
catalog_count: 126
catalog_tokens: 4866
brief_tokens: 2708
brief_hits: 8
full_tokens: 23057
full_hits: 8
```

3. Chapters: OWASP cheat sheets has 1 chapter, with no `Dangerous`/`Vulnerable` chapter; Rust ebook has 50 chapters, with no `](` titles.
   - OWASP first 8: `OWASP Cheat Sheet Series`.
   - Rust first 8: `Rust`; `Imprint`; `Notes on Usage`; `Notes on the Screen Presentation`; `Table of Contents`; `Part I   Basic Programming with Rust`; `1   Introduction`; `2   Variables, Data Types, and Functions`.

```text
owasp-cheat-sheets chapter_count: 1 first8: [{'index': 1, 'title': 'OWASP Cheat Sheet Series'}]
bad_owasp: []
rust_ebook chapter_count: 50 first8: [{'index': 1, 'title': 'Rust'}, {'index': 2, 'title': 'Imprint'}, {'index': 3, 'title': 'Notes on Usage'}, {'index': 4, 'title': 'Notes on the Screen Presentation'}, {'index': 5, 'title': 'Table of Contents'}, {'index': 6, 'title': 'Part I   Basic Programming with Rust'}, {'index': 7, 'title': '1   Introduction'}, {'index': 8, 'title': '2   Variables, Data Types, and Functions'}]
bad_rust_link_titles: []
```

4. Resolution: `PostgreSQL 14 Internals` → `postgresql-14-internals`; `postgresql14internals` → `postgresql-14-internals`; `crypto101` → `crypto-101`; `asynchronous programing in rust` → `asynchronousprogramminginrust`; `zzz-no-such-book` → `None` with 5 suggestions (`oauth-rfcs-book`, `rust_ebook`, `swebok`, `ultimateubuntuhandbook`, `little-redis-book`). Searching `vacuum` by title returned only `postgresql-14-internals`; searching book `zzz` returned a closest-slugs error.

```text
resolve: PostgreSQL 14 Internals => ('postgresql-14-internals', [])
resolve: postgresql14internals => ('postgresql-14-internals', [])
resolve: crypto101 => ('crypto-101', [])
resolve: asynchronous programing in rust => ('asynchronousprogramminginrust', [])
resolve: zzz-no-such-book => (None, ['oauth-rfcs-book', 'rust_ebook', 'swebok', 'ultimateubuntuhandbook', 'little-redis-book'])
title_filter_hit_books: ['postgresql-14-internals']
unknown_search: [{'error': "Unknown book 'zzz'. Closest slugs: optimization-algorithms, azureai-102certificationessentials, kagglebook_secondedition, machinelearningwithpytorchandscikit-learn, masteringpytorch_secondedition. Call list_books() for all slugs."}]
```

5. Chapter index: `get_chapter("postgresql-14-internals", "2")` starts `# Introduction`, matching index 2 title `Introduction`.

```text
chapter2_entry: {'index': 2, 'title': 'Introduction'}
chapter2_first_line: # Introduction
```
6. MCP tool parameter schemas (the requested expression output):

```text
[('search', {'additionalProperties': False, 'properties': {'query': {'type': 'string', 'description': 'Natural language search query.'}, 'top_k': {'default': 10, 'type': 'integer', 'description': 'Number of results to return (default 10).'}, 'book': {'anyOf': [{'type': 'string'}, {'type': 'null'}], 'default': None, 'description': 'Optional book slug or title to filter results to a single book.'}, 'hyde_passage': {'anyOf': [{'type': 'string'}, {'type': 'null'}], 'default': None, 'description': 'Optional hypothetical answer paragraph. When provided, this\ntext is embedded instead of the query for the dense retrieval leg,\nbridging vocabulary gaps between questions and textbook prose. The\nBM25 keyword leg still uses the original query (or bm25_keywords).'}, 'extra_queries': {'anyOf': [{'items': {'type': 'string'}, 'type': 'array'}, {'type': 'null'}], 'default': None, 'description': 'Optional list of alternative query phrasings to broaden\nrecall. Each extra query adds its own dense + BM25 retrieval legs,\nand all candidates are fused before reranking.'}, 'bm25_keywords': {'anyOf': [{'items': {'type': 'string'}, 'type': 'array'}, {'type': 'null'}], 'default': None, 'description': 'Optional list of exact terms for the BM25 keyword leg\n(e.g. ["MVCC", "xmin", "snapshot isolation"]). When provided, these\nterms drive lexical matching instead of the natural-language query,\nseparating semantic intent (dense leg) from exact-term matching.\nUse when you know the precise vocabulary the source text would use.'}, 'detail': {'default': 'brief', 'type': 'string', 'description': '"brief" returns short passages for scanning; call read_chunk(chunk_id)\nfor the surrounding passage, or use "full" for the full result.'}}, 'required': ['query'], 'type': 'object'}), ('search_book', {'additionalProperties': False, 'properties': {'book': {'type': 'string', 'description': 'Book slug or title (use list_books() to see available books).'}, 'query': {'type': 'string', 'description': 'Natural language search query.'}, 'top_k': {'default': 5, 'type': 'integer', 'description': 'Number of results to return (default 5).'}, 'detail': {'default': 'brief', 'type': 'string', 'description': '"brief" returns short passages for scanning; call read_chunk(chunk_id)\nfor the surrounding passage, or use "full" for the full result.'}}, 'required': ['book', 'query'], 'type': 'object'}), ('list_books', {'additionalProperties': False, 'properties': {'book': {'anyOf': [{'type': 'string'}, {'type': 'null'}], 'default': None}}, 'type': 'object'})]
```

7. Agent smoke benchmark: it wrote 2 rows, but both stopped with `stop_reason=error` and `calls=0` before tool use. `tool_tokens_total` was **0** for `h0002` and **0** for `h0003`. Command stdout:

```text
[1/2] h0002 stop=error calls=0
[2/2] h0003 stop=error calls=0
```

oMLX rejected both prompts with `prefill_memory_exceeded` (predicted ~71.7 GB; guard cap 69.98 GB). This gate **FAILS**; the single requested run was not repeated.
