Work only inside /Users/GaryT/Documents/Work/tools/knowledge-base (the current directory). Do not list or search elsewhere. Do not edit wiki/ (the coordinator owns it). Write your final report before you run out of budget, even if the verdict is FAIL.

CONTEXT
The v9 candidate collection passed its pre-set promotion gate (data/bench/gate-v9.md). The owner approved this step in advance: promote, publish the data-v9 release, bump the installer default and push main.
The live Qdrant server is http://127.0.0.1:6333. It holds `developer_knowledge_v8` (266,647 points), `developer_knowledge_v9` (286,723 points = v8 + 29 new books) and `philosophy`, with the alias `developer_knowledge` → `developer_knowledge_v8`. The repo is gaztrabisme/knowledge-base on GitHub; data release `data-v8` holds kb-core.part00, kb-philosophy.part00 and manifest.json.

CHANGE
1. Promote: `.venv/bin/python scripts/merge_collection.py promote --alias developer_knowledge --to developer_knowledge_v9`. Keep `developer_knowledge_v8` on the server for rollback; do not delete it.
2. Release tooling:
   - In scripts/package_release.py, make the snapshotted technical collection `developer_knowledge_v9` (still bundled as kb-core under the alias developer_knowledge) and change the `--tag` default to data-v9.
   - In scripts/install.py, change the `--release-tag` default to data-v9.
   - Check install.sh and install.ps1 for any tag of their own and update it if present.
   - Run the repo's installer/release tests.
3. Docs:
   - knowledge_base/server.py: the MCP instruction text still says "126 technical books". Make it state the current count (320 books: 291 + 29) and the domain list, including the new sales and research-methods domains.
   - README.md: update the core description (book count, domain count, approximate installed size after the release is built).
   - CLAUDE.md: update the status section, corpus stats, the Distribution section (data-v9) and the source-library domain list (the new sales and research-methods domains, and the v9 additions to management and other domains per data/intake/v9-manifest.json). Also add a v9 line to the Version History. Keep the existing style, and state facts plainly.
4. Build the release: `.venv/bin/python scripts/package_release.py --tag data-v9`. Then `gh release create data-v9` with every file in dist/release/ and release notes stating the point counts and the gate result, taken from gate-v9.md.
5. Commit all changes except wiki/ and dist/ in one commit whose message ends with the line "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>", then `git push origin main`.

ACCEPTANCE
- `curl -s http://127.0.0.1:6333/aliases` shows developer_knowledge → developer_knowledge_v9.
- `.venv/bin/python scripts/test_search.py "MEDDICC decision criteria" --top-k 5` returns a hit from the meddicc book.
- `gh release view data-v9` lists manifest.json and the kb-core / kb-philosophy parts.
- `grep -n 'default="data-v9"' scripts/install.py` matches.
- `.venv/bin/python -m pytest tests -q` passes.
- `git status --short -- . ':!wiki'` is clean, and `git log origin/main -1` equals `git log -1`.
