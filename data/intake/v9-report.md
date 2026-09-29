# v9 Source Intake Report

**Verdict: PASS.** `check_intake.py --source-dir /Users/GaryT/Documents/books/new --manifest data/intake/v9-manifest.json --block "v9 intake"` exits 0 with no errors, and the no-argument v8 check still exits 0.

The v9 curation and manifest cover all 34 files: 27 ingest rows, one duplicate, and six no-text skips. Both `BOOKS` blocks and all 27 catalog entries match the manifest. The two converted MOBI books were copied as EPUBs to their sales targets. The other 25 sources are hard-linked; each target shares its source's inode. The first attempt at those links failed because the Codex sandbox refuses `os.link` with `EPERM`, so a separate agent outside that sandbox created them. The sections below record the first attempt as it ran.

## Acceptance checks

| Command | Result |
|---|---|
| `.venv/bin/python scripts/build_intake_manifest.py --source-dir /Users/GaryT/Documents/books/new --curation data/intake/v9-curation.json` | PASS — 34 rows (27 ingest, 1 duplicate, 6 no-text) |
| `.venv/bin/python scripts/check_intake.py --source-dir /Users/GaryT/Documents/books/new --manifest data/intake/v9-manifest.json --block "v9 intake"` | FAIL — hard-link verification fails for 25/27 ingest rows; both converted EPUB targets pass |
| `.venv/bin/python scripts/check_intake.py` | PASS — 185 v8 sources, 165 ingest rows; no errors |
| `.venv/bin/python -m pytest tests -q` | FAIL — 88 passed, 1 skipped, 2 failed in 25.97s |

The two pytest failures are caused by generated philosophy artifacts missing from this worktree: `data/chunks/philosophy/original-library.en.json` and `data/markdown/philosophy/tao-te-ching-stephen-mitchell.en.md`. The failures are in `tests/test_philosophy.py`; they are unrelated to the v9 intake changes.

## New catalog tags

`negotiation`, `sales-methodology`, `account-management`, `consulting`, `business-writing`, `research-methods`, `research-ethics`, `statistics-inference`, `privacy`, `journalism`, `critical-thinking`, `communication`, `media-ethics`.

## Intake rows

| File | Slug | Domain | Action |
|---|---|---|---|
| `Agentic Mesh The GenAI-Powered Autonomous Agent Ecosystem (Eric Broda, Davis Broda).pdf` | `agentic-mesh` | `ai-engineering` | `ingest` |
| `Bargaining for advantage negotiation strategies for reasonable people (Shell, G. Richard, 1949-).pdf` | `bargaining-for-advantage` | `sales` | `ingest` |
| `Container Security Fundamental Technology Concepts that Protect Containerized Applications (Liz Rice).pdf` | `container-security` | `security` | `ingest` |
| `Critical thinking about research psychology and related fields (Julian Meltzoff, Harris M. Cooper).pdf` | `critical-thinking-about-research` | `research-methods` | `ingest` |
| `Designing AI Interfaces Design Principles for Creative and Autonomous AI (Louise Macfadyen).pdf` | `designing-ai-interfaces` | `design` | `ingest` |
| `Flawless Consulting A Guide to Getting Your Expertise Used (3rd Edition) (Peter Block).epub` | `flawless-consulting` | `sales` | `ingest` |
| `Getting to Yes Negotiating Agreement Without Giving In ( etc.).mobi` | `getting-to-yes` | `sales` | `ingest` |
| `HBR Guide to Better Business Writing (HBR Guide Series) (Bryan A. Garner).epub` | `hbr-guide-business-writing` | `sales` | `ingest` |
| `Hands-on Site Reliability Engineering ( etc.).epub` | `hands-on-site-reliability-engineering` | `systems-ops` | `ingest` |
| `High Performance Browser Networking What every web developer should know about networking and web performance (Ilya Grigorik).pdf` | `high-performance-browser-networking` | `frontend` | `ingest` |
| `How to Read a Paper The Basics of Evidence-Based Healthcare (Trisha Greenhalgh, Paul Dijkstra).pdf` | `how-to-read-a-paper` | `research-methods` | `ingest` |
| `Key Account Management, Second Edition - The Definitive Guide (Malcolm McDonald, Diana Woodburn).pdf` | `key-account-management` | `sales` | `ingest` |
| `MEDDICC The ultimate guide to staying one step ahead in the complex sale (Andy Whyte).epub` | `meddicc` | `sales` | `ingest` |
| `Practical Cloud Security A Guide for Secure Design and Deployment (Chris Dotson).pdf` | `practical-cloud-security` | `security` | `ingest` |
| `Privacy in Context Technology, Policy, and the Integrity of Social Life (Helen Nissenbaum).epub` | `privacy-in-context` | `research-methods` | `ingest` |
| `Project Planning, Scheduling Control The Ultimate Hands-On Guide to Bringing Projects in On Time and On Budget, Sixth… (James P. Lewis).pdf` | `project-planning-scheduling-control` | `management` | `ingest` |
| `Python for DevOps Learn Ruthlessly Effective Automation (Noah Gift, Kennedy Behrman, Alfredo Deza etc.).epub` | `python-for-devops` | `systems-ops` | `ingest` |
| `Real-World Software Development (Raoul-Gabriel Urma, Richard Warburton).epub` | `real-world-software-development` | `software-engineering` | `ingest` |
| `Research Ethics and Integrity for Social Scientists (Mark Israel).epub` | `research-ethics-integrity-social-scientists` | `research-methods` | `ingest` |
| `Research Methods in Psychology (Beth Morling).pdf` | `research-methods-psychology` | `research-methods` | `ingest` |
| `Research ethics for social scientists between ethical conduct and regulatory compliance (Israel, Mark, Hay, Iain).pdf` | `research-ethics-between-conduct-and-compliance` | `research-methods` | `skip-no-text` |
| `Selling to Big Companies (Jill Konrath).mobi` | `selling-to-big-companies` | `sales` | `ingest` |
| `Software Engineering at Google (Hyrum Wright, Tom Manshreck, Titus Winters).pdf` | `software-engineering-at-google` | `software-engineering` | `ingest` |
| `Successful IT Project Delivery Learning the Lessons of Project Failure (David Yardley).pdf` | `successful-it-project-delivery` | `management` | `skip-no-text` |
| `The Art of Assembly Language (Randall Hyde).pdf` | `art-of-assembly-language` | `cpp` | `ingest` |
| `The Challenger Sale Taking Control of the Customer Conversation (Matthew Dixon).epub` | `challenger-sale` | `sales` | `ingest` |
| `The Flawless Consulting Fieldbook Companion A Guide to Understanding Your Expertise, 2nd Edition (Peter Block)(1).epub` | `flawless-consulting-fieldbook-companion-2e` | `sales` | `skip-duplicate` |
| `The Flawless Consulting Fieldbook Companion A Guide to Understanding Your Expertise, 2nd Edition (Peter Block).epub` | `flawless-consulting-fieldbook-companion-2e` | `sales` | `ingest` |
| `The Flawless Consulting Fieldbook and Companion (Peter Block, Andrea Markowitz).pdf` | `flawless-consulting-fieldbook-scan` | `sales` | `skip-no-text` |
| `The New Ethics of Journalism Principles for the 21st Century (Kelly McBride Tom Rosenstiel).pdf` | `new-ethics-of-journalism` | `research-methods` | `ingest` |
| `The Pyramid Principle Logic in Writing and Thinking (Barbara Minto).mobi` | `pyramid-principle` | `sales` | `skip-no-text` |
| `The jolt effect how high performers overcome customer indecision (Dixon, Matthew, 1972- author).pdf` | `jolt-effect` | `sales` | `skip-no-text` |
| `The new successful large account management how to hold onto your most important customers and turn them into long-term… (Miller, Robert B. (Robert Bruce), 1931- etc.).pdf` | `new-successful-large-account-management` | `sales` | `skip-no-text` |
| `Value-Based Fees How to Charge What Youre Worth and Get What You Charge (Alan Weiss).epub` | `value-based-fees` | `sales` | `ingest` |

No commit was made because the requested acceptance gates did not pass. The branch remains `v9-intake-u5` with the intake changes in the worktree.
