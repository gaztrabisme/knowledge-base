# Ops Runbook

## Adding a New Book

1. Place the file in the appropriate source directory:
   - EPUB → `knowledge-base/applied-ml/`
   - PDF → `knowledge-base/{databases,security,distributed-systems}/`

2. Add entry to BOOKS dict in `knowledge_base/config.py` (slug → title).
   Also add to `scripts/remote_index.py` BOOKS dict (it's duplicated).

3. Run the pipeline:
   ```bash
   python3 scripts/ingest_all.py --step ingest   # converts to markdown
   python3 scripts/ingest_all.py --step chunk    # creates parent/child chunks
   ```

4. (Optional) Enrich new chunks — see "Running Enrichment" below.

5. Index — either local or remote GPU:
   ```bash
   # Local (slow, ~2 hours for large books)
   python3 scripts/ingest_all.py --step index

   # Remote GPU (fast, ~15 min)
   rsync -avz data/chunks/ bppc@100.106.185.34:~/kb-work/chunks/
   rsync -avz scripts/remote_index.py bppc@100.106.185.34:~/kb-work/
   ssh bppc@100.106.185.34 "source ~/kb-env/bin/activate && cd ~/kb-work && python3 remote_index.py ."
   rsync -avz bppc@100.106.185.34:~/kb-work/qdrant/ data/qdrant/
   ```

## Re-Indexing a Book

If you re-chunk a book (e.g., after fixing ingestion), delete its old points first:

```python
from qdrant_client import QdrantClient, models
client = QdrantClient(path="data/qdrant")
client.delete(
    collection_name="developer_knowledge",
    points_selector=models.FilterSelector(
        filter=models.Filter(must=[
            models.FieldCondition(key="book", match=models.MatchValue(value="book-slug"))
        ])
    ),
)
client.close()
```

Then re-run indexing (it will index only the book whose points were deleted).

## Full Re-Index (Nuclear Option)

When changing embeddings, BM25 tokenizer, or collection schema:

```bash
# Build into fresh directory
mv data/qdrant data/qdrant_old

# Remote GPU (recommended)
rsync -avz data/chunks/ bppc@100.106.185.34:~/kb-work/chunks/
ssh bppc@100.106.185.34 "rm -rf ~/kb-work/qdrant"
ssh bppc@100.106.185.34 "source ~/kb-env/bin/activate && cd ~/kb-work && python3 remote_index.py ."
rsync -avz bppc@100.106.185.34:~/kb-work/qdrant/ data/qdrant/

# Verify
python3 scripts/test_search.py "test query" --top-k 3

# Cleanup (after 1 week if no issues)
rm -rf data/qdrant_old
```

## Running Enrichment

Enrichment requires an LLM server. Best option: llama-server on the GPU machine.

```bash
# 1. Start llama-server
ssh bppc@100.106.185.34 "cd ~/projects/llm-server && docker compose --profile llama-cpp-s016 up -d"

# 2. Wait for model load (~30s)
ssh bppc@100.106.185.34 "docker logs llama-cpp-s016 2>&1 | tail -5"

# 3. Sync chunks and run enrichment
rsync -avz data/chunks/ bppc@100.106.185.34:~/kb-work/chunks/
ssh bppc@100.106.185.34 "source ~/kb-env/bin/activate && cd ~/kb-work && \
  nohup bash -c 'exec python3 -u remote_enrich.py . http://localhost:8081/v1 > enrichment.log 2>&1' &"

# 4. Monitor (enrichment saves every 50 chunks, resumable if interrupted)
ssh bppc@100.106.185.34 "tail -f ~/kb-work/enrichment.log"

# 5. When done, pull enriched chunks back and re-index
rsync -avz bppc@100.106.185.34:~/kb-work/chunks/ data/chunks/
# Then re-index (see above)
```

**Time estimates:** ~3.3 sec/chunk with Qwen3.6-27B MTP no-think mode.
- 6,437 new chunks → ~6 hours
- Full corpus (19,103) → ~17.5 hours

## Checking System Health

```bash
# Verify MCP server starts
python3 -c "import asyncio; from knowledge_base.server import mcp; print(asyncio.run(mcp._tool_manager.get_tools()))"

# Check index stats
python3 -c "
from qdrant_client import QdrantClient
c = QdrantClient(path='data/qdrant')
info = c.get_collection('developer_knowledge')
print(f'Points: {info.points_count}')
c.close()
"

# Run test queries across domains
python3 scripts/test_search.py "gradient boosting" --top-k 3
python3 scripts/test_search.py "PostgreSQL vacuum" --top-k 3
python3 scripts/test_search.py "OWASP injection" --top-k 3
python3 scripts/test_search.py "OAuth token refresh" --top-k 3
```

## SSH GPU Machine Setup

The remote machine at `bppc@100.106.185.34` needs:

```bash
# One-time setup (already done)
python3 -m venv ~/kb-env
source ~/kb-env/bin/activate
pip install fastembed sentence-transformers qdrant-client

# Work directory
mkdir -p ~/kb-work/{chunks,qdrant}
```

Check GPU availability:
```bash
ssh bppc@100.106.185.34 "nvidia-smi --query-gpu=memory.free,memory.used --format=csv,noheader"
```

Kill stale GPU processes if OOM:
```bash
ssh bppc@100.106.185.34 "nvidia-smi --query-compute-apps=pid,name,used_gpu_memory --format=csv,noheader"
ssh bppc@100.106.185.34 "kill <pid>"
```
