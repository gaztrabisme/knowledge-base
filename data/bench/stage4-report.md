# Stage 4 interface report

Date: 2026-09-24
Verdict: FAIL — retrieval NDCG@10=0.7699 versus 0.7700 required.

## Changes

- Removed search_book; search(books=[...]) covers single- and multi-book filters.
- Merged chunk and chapter reads into read, with numbered-title matching before positional fallback.
- Added a daemon warm-up thread to main(); module import does not start it.
- scripts/agent_bench.py remains generic over the live tool list. Its parser helper recognizes parent IDs from read chunk IDs.
- Ranking, fusion, cutoffs, and SearchResult were not changed.

## Acceptance

### 1. Retrieval gate

Command: PYTHONPATH=. .venv/bin/python scripts/eval_retrieval.py --golden data/golden/golden_queries_hard.jsonl --label s4-check

The initial shell-background launch before edits did not persist (zero-byte log). It was restarted as persistent execution session 56858 after the code edits. The process loaded the embedding and reranker weights and completed with exit code 0. NDCG@10 was 0.7699, a strict FAIL against 0.7700 by 0.0001.

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

    ===== s4-check  (n=438) =====
      NDCG@10=0.7699  Recall@10=0.9680  MRR=0.8573  Recall@50(ceiling)=0.9886
      per-domain:
        databases    n= 17  NDCG@10=0.818  R@10=1.000  MRR=0.813  R@50=1.000
        distributed  n=  7  NDCG@10=0.730  R@10=0.857  MRR=0.786  R@50=1.000
        ml           n=209  NDCG@10=0.781  R@10=0.967  MRR=0.861  R@50=0.995
        rust         n=137  NDCG@10=0.759  R@10=0.971  MRR=0.883  R@50=0.978
        security     n= 68  NDCG@10=0.749  R@10=0.971  MRR=0.811  R@50=0.985
      per-archetype:
        baseline       n=198  NDCG@10=0.742  R@10=0.950  MRR=0.814  R@50=0.980
        error_symbol   n= 80  NDCG@10=0.795  R@10=0.988  MRR=0.895  R@50=1.000
        keyword        n= 80  NDCG@10=0.775  R@10=0.988  MRR=0.916  R@50=1.000
        navigational   n= 80  NDCG@10=0.810  R@10=0.975  MRR=0.868  R@50=0.988

      retrieval ceiling - delivered recall = 0.0206 (reranker keeping retrieved hits)
      full report + 14 misses -> data/golden/eval_runs/s4-check.json

The JSON artifact reports label s4-check, n_queries 438, and aggregate metrics ndcg 0.7699, recall10 0.9680, mrr 0.8573, and recall_ceiling 0.9886.

### 2. Tool set and JSON token counts

Default asyncio.run(server.mcp.list_tools()) output:

    tools=search, read, list_books, find_books, grep_books
    tool_tokens_head=1237
    tool_tokens_now=1077

Token count serializes each tool's name, description, and parameters as JSON, then counts with tiktoken cl100k_base. The comparison loaded the exact HEAD source and the current module. The KB_TOOL_DOCS=hyde arm was also measured:

    hyde_tool_tokens_head=1225
    hyde_tool_tokens_now=1079

Both arms are below HEAD. Both current search descriptions say read(chunk_id); read_chunk and get_chapter are absent from the current list.
The HyDE comparison printed both counts before the Python process emitted a native recursive-mutex shutdown error.

### 3. Chapter matching

    ai-powered-search chapter="3": # 3 Ranking and content-based relevance
    ai-powered-search chapter=3: # 3 Ranking and content-based relevance
    postgresql-14-internals chapter="4": # Part V Types of Indexes
    crypto-101 chapter="Building blocks": # Building blocks

postgresql-14-internals has no numbered titles in its list_books(book) chapter list. The list is: 1. About This Book; 2. Introduction; 3. Part IV Query Execution; 4. Part V Types of Indexes. Therefore "4" uses the required position-4 fallback. 4 Snapshots is not a title in that chapter list.

### 4. Other read calls

    read_chunk_equal=True
    read_book_error={'error': 'Pass chapter to read a book. First chapters: 1. Building blocks; 2. Complete cryptosystems; 3. Appendices; 4. Glossary'}
    read_empty_error={'error': "Call read(chunk_id='...') for a search hit or read(book='...', chapter='...') for a chapter."}
    parent_ids_read=['crypto-101-p0']
    tool_defs_names=search,read,list_books,find_books,grep_books

The dictionary comparison used HEAD's read_chunk("crypto-101-p0-c1") and current read(chunk_id="crypto-101-p0-c1"). Importing scripts.agent_bench and passing the live tools through _tool_definitions succeeded; parent_ids returned the expected parent.

### 5. Import and warm-up

    tools=search, read, list_books, find_books, grep_books
    import_seconds=7.084
    models_loaded=False
    stderr: [kb] warm-up finished
    warmup_finished=True

The import timing was measured without calling main(); the model singleton checks remained false. For the warm-up check, a subprocess ran from knowledge_base.server import main; main() with stdin held open until the daemon thread logged completion. The harness then sent SIGTERM to end the stdio server (warmup_subprocess_exit=-15). The first probe exited with a native recursive-mutex error before warm-up completed; the held-stdin run completed successfully.

### 6. Agent benchmark constraint

No agent_bench.py model run and no oMLX calls were made.

## Files changed

- knowledge_base/server.py
- data/bench/stage4-report.md
- data/golden/eval_runs/s4-check.json
- wiki/index.md
- wiki/active-work.md
- wiki/log.md

## Code checks

python -m py_compile knowledge_base/server.py and git diff --check completed successfully. No tests were added.
