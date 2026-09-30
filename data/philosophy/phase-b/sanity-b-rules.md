# Rules for the phase B test set

Reader: the writer of the test queries and, separately, their reviewer. Written 2026-09-30, before either started.

The test set measures whether search finds a known passage from the newly added works. Each row is one query and the one chunk it was written from (the target).

## Sampling
1. 20 rows per language: `en`, `vi`, `zh-Hans`, `zh-Hant`. 80 rows in total.
2. Targets come only from phase B works (not Zhuan Falun, the Original Library or the Tao Te Ching).
3. At most one row per work per language. Within a language, spread the rows over books and writings, and over long and short works.
4. The target chunk is body text of at least 150 characters (80 for Chinese). Not a contents page, a title page, a list of links, a date line, or a translator's note.
5. For `zh-Hant`, at least 10 of the 20 targets come from files that are not flagged `derived`, if that many such works exist.

## Queries
6. The query is in the same language and script as its target.
7. The query is a question or request that a reader could ask without having the passage open, and that the target passage answers.
8. The query is specific to the target: it names the particular point, image, example, event or instruction of that passage. A query that many passages in these works would answer equally well ("What does Master say about cultivation?") is not allowed.
9. The query does not copy more than four consecutive words (eight consecutive characters for Chinese) from the target.
10. The query does not name the work, the conference or the date, unless the passage itself is about that event.

## Row format (JSON Lines)
`{"group": "<language>", "query": "...", "target_chunk_id": "...", "work_id": "...", "language": "...", "section_key": "...", "language_filter": "<language>", "work_filter": null}`
`group` and `language_filter` are `en`, `vi`, `zh-Hans` or `zh-Hant`.

## Review verdicts
- `keep`: the row follows every rule.
- `fix query`: the target is good but the query breaks rule 6–10; the reviewer writes the corrected query.
- `fix label`: another chunk shown to the reviewer in the same section answers the query better; the reviewer names it.
- `drop`: the target breaks rule 4, or no honest query can be written for it.
Every verdict carries a one-sentence reason. The reviewer is not told any retrieval result.
