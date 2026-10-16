# Gate report: v11 (embeddinggemma-2, 768 dimensions)

Reader: Huy, and any agent deciding whether `developer_knowledge` may point at `developer_knowledge_v11`. The machine-readable record is `gate-v11.json`, next to this file.

**Verdict: PASS.** v11 meets all three conditions of the promotion gate against v10.

## What v11 is

`developer_knowledge_v11` is the technical-library search index rebuilt with a new embedding model, Google's `embeddinggemma-2`. An embedding model turns a passage or a question into a list of numbers, a vector, so that similar meanings land close together.

- **Model:** pinned checkpoint `914f7f89`, 768 numbers per vector, run in float32 precision and on text only.
- **Prompts:** questions are prefixed with "task: search result | query:", passages with "title: none | text:".
- **Corpus:** v11 holds 330,833 passages built from the chunk files as they stood on 2026-10-15.
- **Unchanged:** everything else in search is the same as v10. That covers the BM25 keyword index, how keyword and vector results are merged, the 50 candidates passed on, and the Ettin-150m reranker, a second model that re-orders the candidates.

v10, the current live index, uses Jina v5-text-small with 1,024 numbers per vector.

## The gate

The gate has three conditions, carried over from v9 and v10:

1. On the 438 hard questions, NDCG@10 may fall by at most 0.010. NDCG@10 scores how high the labelled right passages rank in the top 10, from 0 to 1.
2. On the hard questions, recall@10 may fall by at most 0.005. Recall@10 is the share of questions with at least one right passage in the top 10.
3. On the 30 sanity questions about recently added documents, recall@10 must be at least 0.80.

The 199 easy questions are reported for information only.

| Set | Measure | v10 | v11 | Change | Condition |
|---|---|---:|---:|---:|---|
| Hard (438) | NDCG@10 | 0.7391 | 0.7360 | −0.0031 | drop ≤ 0.010: pass |
| Hard (438) | recall@10 | 0.9521 | 0.9521 | 0.0000 | drop ≤ 0.005: pass |
| Sanity (30) | recall@10 | 0.9333 | 0.9333 | 0.0000 | ≥ 0.80: pass |
| Easy (199) | NDCG@10 | 0.9044 | 0.8988 | −0.0056 | information |
| Easy (199) | recall@10 | 1.0000 | 1.0000 | 0.0000 | information |

### How the scores were produced

- **v11:** scored on this Mac's CPU (8 threads) on 2026-10-16, with the unchanged `scripts/eval_retrieval.py`.
- **v10:** scored on bppc's CPU on 2026-10-15 with the same evaluator and query files. Its numbers match the original v10 gate within 0.0002.
- **Labels:** v11 uses remapped answer labels for 8 PostgreSQL passages. Re-chunking that book gave those passages new IDs, so each old answer was matched to its new passage by text overlap (88–98% of the old text found). A ninth old answer matched only 9% and was left out rather than guessed.
- **Same run on bppc:** the identical v11 index scored hard NDCG@10 0.7357 there, so the Mac result reproduces it.

## Query speed on this Mac

The test embedded each of 100 hard questions alone, on the CPU with 8 threads, with oMLX busy in the background. It was run 3 times per model. The reference limit is 300 ms.

| Model | Median | Slowest 5% (p95) | Peak memory |
|---|---|---|---|
| Jina v5 (v10) | 138–168 ms | 158–210 ms | 4.1 GB |
| embeddinggemma-2 (v11) | 78–98 ms | 87–120 ms | 2.4 GB |

## Switching and rolling back

The switch moves the alias `developer_knowledge` from v10 to v11. The code that embeds questions must change at the same moment: the live search server has to embed with embeddinggemma-2 to query v11. That code is on branch `unit/gemma-switch`:

- `knowledge_base/embedder.py` registers the new model;
- `knowledge_base/config.py` makes it the default;
- `knowledge_base/philosophy/search.py` keeps philosophy search on Jina, because its index was built with Jina;
- `knowledge_base/search.py` lets the reranker follow the `KB_DEVICE` setting;
- `pyproject.toml` and `uv.lock` add transformers 5.19 and torchvision.

To roll back, point `developer_knowledge` at `developer_knowledge_v10`. Then either set `KB_EMBEDDING_MODEL=jinaai/jina-embeddings-v5-text-small-retrieval` for the search server, or revert the merge, and restart the search servers. v10 stays in Qdrant for that purpose.

## Outcome

On 2026-10-16 at 07:35 ICT, `developer_knowledge` was moved from v10 to v11 on Huy's "Merge and switch", then moved back to v10 within minutes: search servers already running still embedded queries with Jina (1,024 dimensions) and failed against v11. It was moved to v11 again at 07:50, just before the 08:00 Mac restart, which reloads every server onto the new code. The switch is on main at commit 2b35da9. Before the move, a fresh search through main's code against v11 returned the expected passages, and philosophy search worked.
