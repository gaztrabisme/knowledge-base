TARGET
Gary decided on 2026-09-30 to promote the v9 candidate collection. It FAILED its pre-set gate on one condition: sanity recall@10 was 0.793 (23/29) against a threshold of 0.80, while both hard-set conditions passed. A blind review of the sanity queries then scored 0.821 (23/28). Both results are in data/bench/gate-v9.md, and the promotion overrides the failed condition on the owner's decision, as happened for v8.
State, checked on this machine today:
- The Qdrant server at http://127.0.0.1:6333 holds `developer_knowledge_v8` (266,647 points), `developer_knowledge_v9` (286,723 = v8 + 20,076 from 29 new books) and `philosophy` (8,432).
- The alias `developer_knowledge` points to `developer_knowledge_v8`.
- scripts/package_release.py hardcodes `developer_knowledge_v8` (lines 23, 168, 205) and `--tag` default "data-v8" (line 241).
- scripts/install.py has `--release-tag` default "data-v8" (line 968). install.sh and install.ps1 carry no tag.
- knowledge_base/server.py line 17 says "126 technical books".
- gh is logged in as gaztrabisme. Release data-v8 exists; data-v9 does not.
- IMPORTANT: another session is training on this Mac's GPU. Any command that loads a model (scripts/test_search.py, pytest, anything importing sentence_transformers) must run through the CPU wrapper: `.venv/bin/python .claude/plan-goal/verify/cpu.py <script> [args]` or `.venv/bin/python .claude/plan-goal/verify/cpu.py -m pytest tests -q`. Never run them plain.

CHANGE
1. Promote: `.venv/bin/python scripts/merge_collection.py promote --alias developer_knowledge --to developer_knowledge_v9` (check its --help for the exact flags). Keep developer_knowledge_v8 on the server for rollback.
2. Release tooling: in scripts/package_release.py, snapshot `developer_knowledge_v9` as the technical collection (still bundled as kb-core under the alias developer_knowledge), and set the `--tag` default to "data-v9". In scripts/install.py, set the `--release-tag` default to "data-v9". Update any tests that assert the old names.
3. Docs:
   - knowledge_base/server.py: the instruction text states the current technical book count and domains. Take the count from knowledge_base/config.py BOOKS, and include sales and research-methods.
   - README.md: update the book count, the domain count and the installed size (after step 4).
   - CLAUDE.md: update the Status section and Corpus Stats. Say plainly that v9 failed the sanity condition (0.793 against 0.80), that it was promoted on Gary's decision, and that the blind-reviewed set scored 0.821. Also update Distribution (data-v9), the Source Library (new `sales` and `research-methods` domains, plus the v9 additions to existing domains per data/intake/v9-manifest.json), a v9 line in Version History, and the Known Limitations: five sanity queries still miss (Agentic Mesh, Head First PMP, Python for DevOps, Selling to Big Companies, Flawless Consulting Fieldbook Companion), and chunk heading paths repeat "(part 1) (part 1)" (knowledge_base/chunk.py). Keep the file's existing style, and state facts plainly.
4. Build the release: `.venv/bin/python scripts/package_release.py --tag data-v9`. Then run `gh release create data-v9` with every file in dist/release/, titled "Data v9", with notes giving:
   - the point counts;
   - the gate result: hard NDCG@10 drop 0.0020 and recall@10 drop 0 (both pass); sanity 0.793 (FAIL against 0.80); reviewed sanity 0.821;
   - that the promotion was the owner's decision.
5. Commit all changes except wiki/ and dist/ in one commit, with a message ending in the line "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>". Then run `git push origin main`.
In your report, paste: the promote command output, the first 5 hits of `cpu.py scripts/test_search.py "MEDDICC decision criteria" --top-k 5`, the `gh release view data-v9` asset list, and the diff of knowledge_base/server.py.

ACCEPTANCE
`bash .claude/plan-goal/verify/r_u9.sh` prints PASS. Do not edit it.
