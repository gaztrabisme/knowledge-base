# Stage 3 Tool Interface Report

**Status:** **FAIL** — the retrieval command completed with NDCG@10 **0.7699**, versus the required **0.7700** (difference: −0.0001).

## Acceptance output

### 1. Retrieval gate

The first detached launch exited without running; the evaluation was restarted in a managed session and completed after about 49 minutes.

```text
Command: `PYTHONPATH=. .venv/bin/python scripts/eval_retrieval.py --golden data/golden/golden_queries_hard.jsonl --label s3-check`
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

===== s3-check  (n=438) =====
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
  full report + 14 misses -> data/golden/eval_runs/s3-check.json
```

### 2. Search output

`search('how does MVCC snapshot isolation work in postgres')` token count: **2817** (`cl100k_base`, serialized with the benchmark's `json.dumps` method).

```json
{
  "results": [
    {
      "score": 9.9735,
      "book": "postgresql-14-internals",
      "book_title": "PostgreSQL 14 Internals",
      "heading_path": "2 Isolation (part 2)",
      "text": "Over time, lock-based protocols for transaction management got replaced with the Snap-\nshot Isolation (��) protocol. The idea behind this approach is that each transaction accesses\na consistent snapshot of data as it appeared at a particular point in time. The snapshot\nincludes all the current changes committed before the snapshot was taken.\n\np. ���\n\nSnapshot isolation minimizes the number of required locks.\nIn fact, a row will be locked\nonly by concurrent update attempts. In all other cases, operations can be executed con-\ncurrently: writes never lock reads, and reads never lock anything.\n\nPostgre��� uses a multiversion flavor of the �� protocol. Multiversion concurrency control\nimplies that at any moment the database system can contain several versions of the same\nrow, so Postgre��� can include an appropriate version into the snapshot rather than abort\ntransactions that attempt to read stale data.\n\n44\n\n\f2.3 Isolation Levels in PostgreSQL",
      "chunk_id": "postgresql-14-internals-p7-c4"
    },
    {
      "score": 9.0502,
      "book": "postgresql-14-internals",
      "book_title": "PostgreSQL 14 Internals",
      "heading_path": "14 Miscellaneous Locks (part 2)",
      "text": "For this reason, it was suggested to lock conditions (predicates) rather than rows. If you\nrun a query with the a > 10 predicate, locking this predicate will not allow adding new\nrows into the table if they satisfy this condition, so phantoms will be avoided. The trouble\nis that if a query with a different predicate appears, such as a < 20, you have to find out\nwhether these predicates overlap. In theory, this problem is algorithmically unsolvable;\nin practice, it can be solved only for a very simple class of predicates (like in this example).\n\nIn Postgre���, the Serializable isolation level is implemented in a different way: it uses\nthe Serializable Snapshot Isolation (���) protocol.2 The term predicate lock still remains,\nbut its sense has radically changed. In fact, such “locks” do not lock anything: they are\nused to track data dependencies between different transactions.\n\nsnapshot isolation at the Repeatable Read level allows no anomalies except\nIt is proved that\nfor the write skew and the read-only transaction anomaly. These two anomalies result in\n\np. ��",
      "chunk_id": "postgresql-14-internals-p59-c1"
    },
    {
      "score": 8.8322,
      "book": "postgresql-14-internals",
      "book_title": "PostgreSQL 14 Internals",
      "heading_path": "4 Snapshots (part 2)",
      "text": "−−−−−−−+−−−−−−−−+−−−−−−−+−−−−−−−\n\n(0,1) | normal | 790 c | 0 a\n(0,2) | normal | 791 c | 792 c\n(0,3) | normal | 792 c | 0 a\n\n(3 rows)\n\nSo how does Postgre��� choose which versions to show? By the above rules, changes are\nincluded into a snapshot only if they are made by committed transactions that satisfy the\nfollowing criteria:\n\n• If xid < xmin, changes are shown unconditionally (like in the case of the transaction\n\nthat created the accounts table).\n\n• If xmin ⩽ xid < xmax, changes are shown only if the corresponding transaction ��s\n\nare not in xip_list.\n\nThe first row (�,�) is invisible because it is inserted by a transaction that appears in xip_list\n(even though this transaction falls into the snapshot range).\n\nThe latest version of the second row (�,�) is invisible because the corresponding transac-\ntion �� is above the upper boundary of the snapshot.",
      "chunk_id": "postgresql-14-internals-p17-c1"
    },
    {
      "score": 8.6705,
      "book": "postgresql-14-internals",
      "book_title": "PostgreSQL 14 Internals",
      "heading_path": "4 Snapshots (part 1)",
      "text": "# 4 Snapshots\n\n4.1 What is a Snapshot?\n\np. ��\n\nA data page can contain several versions of the same row, although each transaction must\nsee only one of them at the most. Together, visible versions of all the different rows con-\nstitute a snapshot\n. A snapshot includes only the current data committed by the time it was\ntaken, thus providing a consistent (in the ���� sense) view of the data for this particular\nmoment.\n\nTo ensure isolation, each transaction uses its own snapshot. It means that different trans-\nactions can see different snapshots taken at different points in time, which are neverthe-\nless consistent.\n\nAt the Read Committed isolation level, a snapshot is taken at the beginning of each state-\nment, and it remains active only for the duration of this statement.\n\nAt the Repeatable Read and Serializable levels, a snapshot is taken at the beginning of\nthe first statement of a transaction, and it remains active until the whole transaction is\ncomplete.\n\nsnapshot1\n\nsnapshot2\n\nsnapshot\n\nstatement1\n\nstatement2\n\nstatement1\n\nstatement2\n\nRead Committed\n\nxid\n\nRepeatable Read,\nSerializable\n\nxid\n\n80\n\n\f4.2 Row Version Visibility\n\n4.2 Row Version Visibility",
      "chunk_id": "postgresql-14-internals-p16-c0"
    },
    {
      "score": 8.6458,
      "book": "postgresql-internals-interdb",
      "book_title": "The Internals of PostgreSQL (Suzuki)",
      "heading_path": "The Internals of PostgreSQL > Chapter 7. HOT and Index-Only Scans",
      "text": "Demonstrates prevention of Dirty Reads, Non-Repeatable Reads, and Phantom Reads. **Hint bits** (HEAP_XMIN_COMMITTED, HEAP_XMAX_COMMITTED, etc.) cached in t_infomask eliminate repeated clog lookups.\n\n### 5.8. Preventing Lost Updates\n\nPostgreSQL uses **first-updater-win** scheme. ExecUpdate has three blocks: (1) wait for concurrent updater, then abort at REPEATABLE READ+ or retry at READ COMMITTED; (2) handle already-updated row; (3) update unmodified row.\n\n### 5.9. Serializable Snapshot Isolation (SSI)\n\nSince v9.1 for true SERIALIZABLE isolation. Uses **SIREAD locks** (predicate locks at tuple/page/relation level with aggregation) and **rw-conflicts** to detect serialization anomalies. Uses **first-committer-win** scheme. False positives possible with sequential scans or shared index pages.\n\n### 5.10. Required Maintenance Processes",
      "chunk_id": "postgresql-internals-interdb-p3-c3"
    },
    {
      "score": 8.5719,
      "book": "postgresql-14-internals",
      "book_title": "PostgreSQL 14 Internals",
      "heading_path": "13 Row-Level Locks (part 1)",
      "text": "# 13 Row-Level Locks\n\n13.1 Lock Design\n\nThanks to snapshot isolation, heap tuples do not have to be locked for reading. However,\ntwo write transactions must not be allowed to modify the same row at the same time.\nRows must be locked in this case, but heavyweight locks are not a very good choice for\nthis purpose: each of them takes space in the server’s shared memory (hundreds of bytes,\nnot to mention all the supporting infrastructure), and Postgre��� internal mechanisms\nare not designed to handle a huge number of concurrent heavyweight locks.\n\nSome database systems solve this problem by lock escalation: if row-level locks are too\nmany, they are replaced by a single lock of finer granularity (for example, by a page-level or\ntable-level lock). It simplifies the implementation, but can greatly limit system through-\nput at the same time.\n\nIn Postgre���, the information on whether a particular row is locked is kept only in the\nheader of its current heap tuple. Row-level locks are virtually attributes in heap pages\nrather than actual locks, and they are not reflected in ��� in any way.\n\np. ��",
      "chunk_id": "postgresql-14-internals-p52-c0"
    },
    {
      "score": 8.3652,
      "book": "postgresql-14-internals",
      "book_title": "PostgreSQL 14 Internals",
      "heading_path": "2 Isolation (part 4)",
      "text": "Write skew. As we have seen, the Postgre��� implementation of the Repeatable Read iso-\nlation level prevents all the anomalies described in the standard. But not all possible\nones: no one knows how many of them exist. However, one important fact is proved for\nsure: snapshot isolation does not prevent only two anomalies, no matter how many other\nanomalies are out there.\n\nThe first one is write skew.\n\nLet’s define the following consistency rule: it is allowed to have a negative balance in some\nof the customer’s accounts as long as the total balance is non-negative.\n\n55\n\n\fChapter 2 Isolation\n\nThe first transaction gets the total balance of Bob’s accounts:\n\n=> BEGIN ISOLATION LEVEL REPEATABLE READ;\n\n=> SELECT sum(amount) FROM accounts WHERE client = 'bob';\n\nsum\n−−−−−−−−\n900.00\n(1 row)\n\nThe second transaction gets the same sum:\n\n=> BEGIN ISOLATION LEVEL REPEATABLE READ;\n\n=> SELECT sum(amount) FROM accounts WHERE client = 'bob';\n\nsum\n−−−−−−−−\n900.00\n(1 row)",
      "chunk_id": "postgresql-14-internals-p9-c7"
    },
    {
      "score": 8.0397,
      "book": "postgresql-14-internals",
      "book_title": "PostgreSQL 14 Internals",
      "heading_path": "PostgreSQL 14 Internals (part 1)",
      "text": "In the introductory chapter, I briefly touch upon the main database concepts that will\nserve as the foundation for all the further narration. I do not expect you to get much new\ninformation from this chapter but still include it to complete the big picture. Besides, this\noverview can be found useful by those who are migrating from other database systems.\n\nPart I is devoted to questions of data consistency and isolation. I first cover them from\nthe user’s perspective (you will learn which isolation levels are available and what are the\nimplications) and then dwell on their internals. For this purpose, I have to explain im-\nplementation details of multiversion concurrency control and snapshot isolation, paying\nspecial attention to cleanup of outdated row versions.\n\nPart II describes buffer cache and ���, which is used to restore data consistency after a\nfailure.\n\nPart III goes into details about the structure and usage of various types of locks:\nlightweight locks for ���, heavyweight locks for relations, and row-level locks.\n\nPart IV explains how the server plans and executes ��� queries. I will tell you which data\naccess methods are available, which join methods can be used, and how the collected\nstatistics are applied.",
      "chunk_id": "postgresql-14-internals-p0-c2"
    }
  ],
  "related_headings": [
    "18 Table Access Methods",
    "7 Freezing",
    "Optimistic Concurrency with Version Numbers",
    "Part III. Practices > Chapter 26. Data Integrity: What You Read Is What You Wrote > Challenges of Maintaining Data Integrity Deep and Wide",
    "Testing for Our Data Integrity Rules > Pessimistic Concurrency Control Example: SELECT FOR UPDATE",
    "Liberating Data Using Change-Data Capture > Snapshotting the Initial Data Set State",
    "19 Index Access Methods",
    "1 Introduction"
  ]
}
```

`search('pin a future in async rust')["related_headings"]`: `["Improving our example 4 – pinning to the rescue > Main.rs", "Pinning in Rust > Pinning to the heap", "Futures and async/await", "Creating Your Own Runtime", "Understanding async and await with Rust", "Coroutines, Self-Referential Structs, and Pinning", "Technical requirements > http.rs", "Step 1 – Improving our runtime design by adding a Reactor and a Waker > Changing the Future definition"]`

Heading checks: first query 8 related headings; second query 8; normalized overlaps with returned `heading_path` values: `[]` and `[]`.

### 3. Tool-list size

HEAD baseline was captured at `2f8fe6e3f884a9cf1276d2dc25fb199d8c62a3e1`.

| Arm | `cl100k_base` tokens |
|---|---:|
| HEAD | 1674 |
| Current default | 1237 |
| Change | -26.11% |

### 4. A3h description swap

Default `search` description: Search the library for passages that answer a technical question. If you don't know which books cover the topic, call find_books first. For follow-up searches, reuse words from related_headings or find_books matching_sections instead of guessing vocabulary. Use read_chunk(chunk_id) to read around a hit.

HyDE `search` description from fresh `KB_TOOL_DOCS=hyde` process: Search the library for passages that answer a technical question. For conceptual questions, always write a hyde_passage: a 3–5 sentence hypothetical textbook answer. If you don't know which books cover the topic, call find_books first. Use read_chunk(chunk_id) to read around a hit.

HyDE `find_books` description: Find books that cover a topic and show the vocabulary used in their sections.

Descriptions differ: `True`. Parameter JSON identical across all tools: `True`.

### 5. Agent benchmark helpers (no model run)

```text
parent_ids(sample): ["postgres-internals-p12"]
is_empty_result({"results": [], "related_headings": []}): True
empty_results counter after empty wrapper: 1
result_count(empty): 0
calllog._ids(sample): (["postgres-internals-p12-c3"], ["postgres-internals-p12"])
calllog._result_count(empty): 0
```

No `agent_bench.py` model run or oMLX call was made.

## Files changed

- `knowledge_base/search.py`
- `knowledge_base/server.py`
- `knowledge_base/calllog.py`
- `scripts/agent_bench.py`
- `tests/test_stage2_contract.py` (updated the search response contract assertion; test suite not run)
- `data/golden/eval_runs/s3-check.json` (retrieval-gate output)
- `wiki/active-work.md`
- `wiki/decisions.md`
- `wiki/index.md`
- `wiki/log.md`
- `wiki/stage-3-interface-report.md` (this report)
