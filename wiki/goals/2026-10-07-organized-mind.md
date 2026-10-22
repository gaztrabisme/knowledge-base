# Goal — 2026-10-07 — organized-mind (run kbu-2026-10-07)

**Status:** APPROVED — Huy said "Go" on 2026-10-10 after the revised plan.

**Decision owner / author:** Huy (owner); coordinator Claude Opus 5.5, 2026-10-10. **Audited by:** coordinator at Close; A1 audits the synthesis. **Contact:** Huy.

Grounding: `data/intake/kbu-2026-10-07/grounded.md`. Workspaces: `~/Documents/Work/tools/kbu-2026-10-07/<unit>/`. Final artifacts are copied to `data/intake/kbu-2026-10-07/`.

## Deliverable — product brief + design spec for one "organized mind" project, backed by research and measurement

| ID | Source / stakeholder | Success criterion | Artifact / evidence | UAT (how to verify) |
|---|---|---|---|---|
| G1 | Huy Q (model) | embeddinggemma-2 fact sheet: size, dimensions, shortenable vectors, context length, input types, license, each sourced or measured; CPU timing for text, code and image at fp32 and int8 | R1/REPORT.md, R1/timing.json | `bash R1/verify.sh` |
| G2 | Huy A3 | Pipeline-optimization survey: every technique has a source, expected gain and fit verdict for this stack | R2/REPORT.md | `bash R2/verify.sh` |
| G3 | Huy A4; KB decisions.md | Knowledge-graph research answers each recorded GraphRAG/LightRAG rejection reason and says how litgraph's typed graph and closed-world absence carry over | R3/REPORT.md | `bash R3/verify.sh` |
| G4 | Huy follow-up 3, 4 | Memory research covers both pointer repos, inventories real lesson-source paths, recommends edit vs annotate, and states how every agent harness reaches the memory | R4/REPORT.md | `bash R4/verify.sh` |
| G5 | Huy A2, follow-up 1 | One-way-in design maps every Domestika safety principle, defines adapters for courses, books, papers and repos, and PDF image extraction | R5/REPORT.md | `bash R5/verify.sh` |
| G6 | Huy A4 | Inventory of KB, litgraph and agent-workflow with reuse verdicts and repo-layout options; the three repos are not modified by the unit | R6/REPORT.md | `bash R6/verify.sh` |
| G7 | Huy A5 | Full text re-embed gated with the existing gate script on hard, easy and sanity sets; verdict computed against the v9 limits (NDCG@10 drop ≤ 0.010, recall@10 drop ≤ 0.005). Passes on either branch: PASS or FAIL is reported as measured | M1/REPORT.md | `bash M1/verify.sh` |
| G8 | Huy A2 | Image and code pilot: labelled queries, text-only vs multimodal results side by side | M2/REPORT.md | `bash M2/verify.sh` |
| G9 | Huy follow-up 2 | Graph-extraction pilot on a local model: documents per hour, spot-checked quality, projected hours for the whole library | M3/REPORT.md | `bash M3/verify.sh` |
| G10 | Huy A4 | Product decision brief per the product-management template; claims cite R/M files | P1/product-brief.md | `bash P1/verify.sh` |
| G11 | Huy A4, follow-up 4 | Design spec covers storage, graph, ingestion, archive core, memory and annotation, agent tools for every harness, repo layout and distribution, migration, open choices; every recommendation cites P1, R or M | D1/design-spec.md | `bash D1/verify.sh` |
| G12 | conductor CERIC Gate 2 | Independent audit gives every claim of P1 and D1 a verdict; D1 is revised; failed claims stay listed as open | A1/audit.md, D1/design-spec.md | `bash A1/verify.sh` |
| G13 | NOT DOING | Live state untouched: alias `developer_knowledge` → `developer_knowledge_v10`; litgraph and agent-workflow `skills/` unchanged by lanes | Qdrant, git | `bash ~/Documents/Work/tools/kbu-2026-10-07/checks/untouched.sh` |
| G14 | Huy (keystone) | Huy approves or redirects the product brief and design at Close | his reply, recorded in log.md | human verdict and date |

## Working pattern (binds this run)
Open lanes at dispatch: per the lane check of 2026-10-10 (recorded in log.md). Research → gemini/codex; code and measurement → codex; inventory → bppc; audit on a different lane from the writer. GPU on bppc is shared with the IELTSy session; GPU units wait for its answer. Mac swap is near full: no model loads on the Mac while other heavy work runs.

## Amendments
- 2026-10-14: G14 met: Huy approved the brief and design as a whole ("Approve as whole", relayed by the pi-mind conductor session; decisions.md).

## Branch resolutions (before dispatch)
- F1: full re-embed (Huy, 2026-10-10, "Go" on the plan's recommendation).
- F2: litgraph is a component; its public repo stays unchanged; the design may argue for moving it (Huy, 2026-10-10).
- F4: Codex units fall back to gemini in scratch folders (Huy, 2026-10-10).

## Goal block
Execute plan "organized-mind" (wiki/goals/2026-10-07-organized-mind.md). Goal rows, run from ~/Documents/Work/tools/kbu-2026-10-07:
1 G1: `bash R1/verify.sh`
2 G2: `bash R2/verify.sh`
3 G3: `bash R3/verify.sh`
4 G4: `bash R4/verify.sh`
5 G5: `bash R5/verify.sh`
6 G6: `bash R6/verify.sh`
7 G7: `bash M1/verify.sh`
8 G8: `bash M2/verify.sh`
9 G9: `bash M3/verify.sh`
10 G10: `bash P1/verify.sh`
11 G11: `bash D1/verify.sh`
12 G12: `bash A1/verify.sh`
13 G13: `bash checks/untouched.sh`
