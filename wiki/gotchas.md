# Gotchas & Known Issues

## PDF Heading Loss

**Problem:** markitdown extracts text from PDFs but loses heading hierarchy. No `#` markers in the output markdown.
**Impact:** Chunker falls back to paragraph-based splitting. Chunks are well-sized but metadata (chapter, section, heading_path) is empty for PDF-sourced books. `get_chapter()` tool won't work for these books.
**Workaround:** Search and grep_books still work fine. For structured browsing, use the original PDF.
**Future fix:** Post-process PDF markdown to detect chapter headings from patterns (numbered sections, "Chapter X", etc.) and inject `#` markers.

## numpy float32 Serialization

**Problem:** FlashRank returns numpy float32 scores. JSON serialization fails on numpy types.
**Fix:** `search.py` wraps all scores in `float()` — in `SearchResult.to_dict()` and `_rerank()`.
**Watch for:** Any new code path that puts numpy values into dicts returned via MCP.

## Remote Script Duplication

**Problem:** `scripts/remote_index.py` is self-contained (no package imports) for rsync deployment. It duplicates BOOKS dict and BM25/embedding logic from the main package.
**Impact:** When adding new books or changing indexing logic, both `knowledge_base/index.py` AND `scripts/remote_index.py` must be updated.
**Mitigation:** Both files now use the same FastEmbed BM25 approach, eliminating the tokenizer divergence. BOOKS dict still duplicated — update both when adding books.

## GPU OOM During Indexing

**Problem:** Jina v5 (677M params) can OOM on 16GB GPU if other processes are using VRAM, or with large batch sizes on long texts.
**Fix:** Check `nvidia-smi` before indexing. Kill stale processes. Use batch_size=4 for large books (e.g., Boneh-Shoup crypto at 2,761 chunks). Set `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`.
**Pattern:** The first indexing run after boot works fine (fresh GPU memory). Subsequent runs may OOM if previous model wasn't freed.

## Qdrant "Already Indexed" Check

**Problem:** `index_book()` and `remote_index.py` check if a book is already indexed by scrolling for any point with matching `book` field. If you need to re-index a book (e.g., after re-chunking), you must delete its points first.
**Fix:** Delete points before re-indexing:
```python
client.delete(
    collection_name="developer_knowledge",
    points_selector=models.FilterSelector(
        filter=models.Filter(must=[
            models.FieldCondition(key="book", match=models.MatchValue(value="book-slug"))
        ])
    ),
)
```

## Enrichment Buffering

**Problem:** `nohup` buffers stdout. Remote enrichment logs may be empty for 30-60s after launch.
**Fix:** Use `python3 -u` (unbuffered) in the nohup command. Check `ps aux | grep python` to confirm process is alive before assuming failure from empty logs.

## Qdrant File Lock

**Problem:** Qdrant file-based storage allows only one client at a time. If the MCP server has the index open and you try to run `test_search.py` simultaneously, one will fail.
**Fix:** The MCP server opens/closes the client per query (`get_client()` → use → `client.close()`). Scripts do the same. Don't leave a Python REPL with an open client.

## Two Corrupted PDFs (Fixed)

**Problem:** `boneh-shoup-applied-cryptography.pdf` (11MB) and `designing-distributed-systems.pdf` (314KB) originally failed with "Unexpected EOF" — incomplete downloads.
**Fix:** Re-downloaded from source. Boneh-Shoup from `crypto.stanford.edu` (8.7MB), Designing Distributed Systems from Microsoft (5.6MB). Both convert cleanly now.
